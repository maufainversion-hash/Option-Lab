"""
Smoke tests del data layer.

Los tests marcados con @pytest.mark.integration golpean yfinance real y se excluyen
del corrido normal (`pytest -m "not integration"`).
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd
import pytest

from data.market_provider import time_to_expiry_years, _normalize_chain


def test_time_to_expiry_positive():
    T = time_to_expiry_years("2030-12-31")
    assert T > 0


def test_time_to_expiry_past_clamps_zero():
    assert time_to_expiry_years("2000-01-01") == 0.0


def test_normalize_empty_chain_returns_empty():
    out = _normalize_chain(pd.DataFrame(), "call")
    assert out.empty


def test_normalize_chain_adds_required_columns():
    df = pd.DataFrame({
        "strike": [100.0, 105.0, 110.0],
        "bid": [5.0, 2.5, 0.0],
        "ask": [5.5, 3.0, 0.5],
        "lastPrice": [5.25, 2.75, 0.25],
        "volume": [100, 50, 0],
        "openInterest": [200, 100, 10],
        "impliedVolatility": [0.25, 0.27, 0.30],
        "inTheMoney": [True, False, False],
    })
    out = _normalize_chain(df, "call")
    assert {"mid", "spread_pct", "valid", "option_type"} <= set(out.columns)
    assert (out["option_type"] == "call").all()
    # Mid: (bid+ask)/2
    assert out["mid"].iloc[0] == pytest.approx(5.25)
    # El strike con bid=0 debe quedar marcado invalid
    assert not out["valid"].iloc[2]


def test_normalize_chain_handles_nan():
    df = pd.DataFrame({
        "strike": [100.0],
        "bid": [float("nan")],
        "ask": [5.0],
        "volume": [float("nan")],
        "openInterest": [float("nan")],
        "impliedVolatility": [float("nan")],
    })
    out = _normalize_chain(df, "put")
    assert out["bid"].iloc[0] == 0.0
    assert out["volume"].iloc[0] == 0
    assert out["openInterest"].iloc[0] == 0


# Solo se corre cuando se pide -m integration. Requiere internet.
@pytest.mark.integration
def test_get_quote_live_spy():
    from data.market_provider import get_quote
    q = get_quote("SPY")
    assert q is not None
    assert q.price > 0
