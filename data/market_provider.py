"""
yfinance wrapper con cache, sanity gates y normalización.

Importante — Yahoo bloquea las IPs de Streamlit Cloud cuando la TLS fingerprint
es la del Python `urllib3` default. Solución: usar `curl_cffi.Session(impersonate=
'chrome')` para que las requests parezcan venir de Chrome real. Esto es la fix
recomendada por yfinance.

La UI puede confiar en que:
- Quote es None ⟺ provider falló (jamás traceback al usuario)
- Chain DataFrame siempre tiene columnas: strike, bid, ask, mid, volume,
  openInterest, impliedVolatility, spread_pct, valid, option_type
- valid=False marca quotes con bid=0 o spread > 50%

Cache TTLs:
- prices: 60s
- chains: 5 min
- risk-free rate (^TNX): 1h
"""
from __future__ import annotations
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

import pandas as pd
import streamlit as st
import yfinance as yf

log = logging.getLogger(__name__)

OptionType = Literal["call", "put"]


@st.cache_resource(show_spinner=False)
def _get_session():
    """
    Session de curl_cffi que impersonates Chrome — la fix para Yahoo throttling
    en Streamlit Cloud. cache_resource para reusar la session entre re-runs.

    Si curl_cffi no está disponible (entorno raro), cae a None y yfinance usa
    su session default — peor para Cloud pero al menos no rompe.
    """
    try:
        from curl_cffi import requests as curl_requests
        return curl_requests.Session(impersonate="chrome")
    except ImportError:
        log.warning("curl_cffi no disponible, usando session default de yfinance")
        return None


def _ticker(symbol: str) -> "yf.Ticker":
    """Construye un yf.Ticker con la session impersonada."""
    sess = _get_session()
    return yf.Ticker(symbol, session=sess) if sess is not None else yf.Ticker(symbol)


@dataclass
class Quote:
    symbol: str
    price: float
    change: float
    change_pct: float
    prev_close: float
    volume: int
    timestamp: datetime

    @property
    def is_up(self) -> bool:
        return self.change >= 0


def _quote_from_history(hist: pd.DataFrame, symbol: str) -> Quote | None:
    """Construye Quote desde DataFrame OHLCV. Devuelve None si data insuficiente."""
    if hist is None or hist.empty or len(hist) < 2:
        return None
    try:
        price = float(hist["Close"].iloc[-1])
        prev = float(hist["Close"].iloc[-2])
        vol = int(hist["Volume"].iloc[-1]) if "Volume" in hist.columns else 0
        if price <= 0 or prev <= 0:
            return None
        change = price - prev
        change_pct = (change / prev) * 100.0 if prev else 0.0
        return Quote(symbol, price, change, change_pct, prev, vol,
                     datetime.now(timezone.utc))
    except (KeyError, ValueError, IndexError) as e:
        log.warning(f"No se pudo armar Quote para {symbol}: {e}")
        return None


@st.cache_data(ttl=60, show_spinner=False)
def get_quote(symbol: str) -> Quote | None:
    """
    Devuelve el quote actual. Triple estrategia para sobrevivir el throttling de
    Yahoo en Streamlit Cloud:
      1) yf.Ticker(...).history(period='5d')  — endpoint principal
      2) yf.download(...)                     — endpoint alternativo, otro path
      3) None graceful
    """
    # Strategy 1: Ticker.history con session impersonada (fix Streamlit Cloud)
    try:
        t = _ticker(symbol)
        hist = t.history(period="5d", auto_adjust=False)
        q = _quote_from_history(hist, symbol)
        if q is not None:
            return q
    except Exception as e:
        log.info(f"Ticker.history falló para {symbol}: {e}")

    # Strategy 2: yf.download como fallback
    try:
        sess = _get_session()
        kwargs = {"progress": False, "auto_adjust": False, "threads": False}
        if sess is not None:
            kwargs["session"] = sess
        df = yf.download(symbol, period="5d", **kwargs)
        if df is not None and not df.empty:
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            q = _quote_from_history(df, symbol)
            if q is not None:
                return q
    except Exception as e:
        log.warning(f"yf.download también falló para {symbol}: {e}")

    log.warning(f"Sin datos para {symbol} en ningún endpoint")
    return None


@st.cache_data(ttl=60, show_spinner=False)
def get_quotes_batch(symbols: tuple[str, ...]) -> dict[str, Quote | None]:
    """Tuple en signature para que Streamlit pueda hashear el arg al cachear."""
    return {s: get_quote(s) for s in symbols}


@st.cache_data(ttl=300, show_spinner="Cargando expirations...")
def get_options_expirations(symbol: str) -> list[str]:
    try:
        t = _ticker(symbol)
        return list(t.options or [])
    except Exception as e:
        log.warning(f"Falló traer expirations de {symbol}: {e}")
        return []


@st.cache_data(ttl=300, show_spinner="Cargando chain...")
def get_option_chain(symbol: str, expiry: str) -> dict[str, pd.DataFrame] | None:
    try:
        t = _ticker(symbol)
        chain = t.option_chain(expiry)
        calls = _normalize_chain(chain.calls, "call")
        puts = _normalize_chain(chain.puts, "put")
        if calls.empty and puts.empty:
            return None
        return {"calls": calls, "puts": puts}
    except Exception as e:
        log.warning(f"Falló chain {symbol} @ {expiry}: {e}")
        return None


def _normalize_chain(df: pd.DataFrame, option_type: str) -> pd.DataFrame:
    """Garantiza columnas, llena NaN, calcula mid/spread y marca quotes válidos."""
    if df is None or df.empty:
        return pd.DataFrame()

    keep = ["strike", "lastPrice", "bid", "ask", "volume", "openInterest",
            "impliedVolatility", "inTheMoney"]
    out = df[[c for c in keep if c in df.columns]].copy()
    out["option_type"] = option_type

    # Sanity gates
    for col in ("bid", "ask", "lastPrice", "impliedVolatility"):
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0).clip(lower=0)
    for col in ("volume", "openInterest"):
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0).astype(int)
    if "inTheMoney" in out.columns:
        out["inTheMoney"] = out["inTheMoney"].fillna(False).astype(bool)

    out["mid"] = (out["bid"] + out["ask"]) / 2.0
    out["spread_pct"] = ((out["ask"] - out["bid"]) / out["mid"]).where(out["mid"] > 0, float("nan"))
    out["valid"] = (out["bid"] > 0) & (out["spread_pct"] < 0.5)
    return out.reset_index(drop=True)


def time_to_expiry_years(expiry: str) -> float:
    """yfinance da expiry en 'YYYY-MM-DD'. Devuelve años hasta vencimiento (clamp >= 0)."""
    exp_dt = datetime.strptime(expiry, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    days = (exp_dt - now).total_seconds() / 86400.0
    return max(days / 365.0, 0.0)


@st.cache_data(ttl=3600, show_spinner=False)
def risk_free_rate() -> float:
    """Tasa libre de riesgo ≈ yield del 10y treasury (^TNX). Fallback 4%."""
    try:
        q = get_quote("^TNX")
        if q is None:
            return 0.04
        return float(q.price) / 100.0   # ^TNX se cotiza en pct directo
    except Exception:
        return 0.04
