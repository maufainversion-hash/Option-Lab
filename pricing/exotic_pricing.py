"""
Wrappers sobre BSM para opciones sobre índices, monedas y futuros. Hull Cap 17 + 18.

- index_option_price: BSM con dividend yield del índice (Hull 17.1, Merton 1973)
- currency_option_price: Garman-Kohlhagen 1983 (Hull 17.2)
- black_option_price: Black's model 1976 para opciones sobre futuros (Hull 18.6)
- fx_forward_price: covered interest parity
- range_forward_strikes: collar FX zero-cost via brentq
"""
from __future__ import annotations
from math import exp, log, sqrt

from scipy.stats import norm

from pricing.black_scholes import bs_price, OptionType


# ============================================================
# Index options — Hull 17.1
# ============================================================
def index_option_price(
    S: float, K: float, T: float, r: float, sigma: float,
    dividend_yield: float = 0.02,
    option_type: OptionType = "call",
) -> float:
    """
    Opción europea sobre un índice con dividend yield continuo q.
    Idéntico a BSM con q = dividend_yield.
    Hull 17.1: para S&P 500, q típica 1.5-2.5%.
    """
    return bs_price(S, K, T, r, sigma, q=dividend_yield, option_type=option_type)


# ============================================================
# Currency options — Garman-Kohlhagen — Hull 17.2
# ============================================================
def currency_option_price(
    S: float, K: float, T: float, r_domestic: float, r_foreign: float,
    sigma: float, option_type: OptionType = "call",
) -> float:
    """
    Opción europea sobre tipo de cambio. Garman-Kohlhagen (1983):
      c = S·e^(-r_f·T)·N(d1) − K·e^(-r_d·T)·N(d2)

    S: spot FX en unidades de doméstica por unidad de extranjera.
    r_d: tasa libre de riesgo doméstica.
    r_f: tasa libre de riesgo extranjera (juega el rol de "dividend yield").

    Hull Ejemplo 17.2: Currency call USD/GBP, S=1.6, K=1.6, T=4/12, σ=14.1%,
    r_d=8%, r_f=11% → call ≈ 0.0639
    """
    return bs_price(S, K, T, r_domestic, sigma, q=r_foreign, option_type=option_type)


def fx_forward_price(S: float, T: float, r_domestic: float, r_foreign: float) -> float:
    """
    Forward FX rate por covered interest parity:
      F = S · e^((r_d − r_f)·T)
    Si r_d > r_f → currency doméstica forward en descuento (F > S).
    Hull 17.2.
    """
    return S * exp((r_domestic - r_foreign) * T)


# ============================================================
# Futures options — Black's model — Hull 18.6
# ============================================================
def black_option_price(
    F: float, K: float, T: float, r: float, sigma: float,
    option_type: OptionType = "call",
) -> float:
    """
    Opción europea sobre un futuro. Black's model (1976):
      c = e^(-rT) · [F · N(d1) − K · N(d2)]
      p = e^(-rT) · [K · N(-d2) − F · N(-d1)]

    donde
      d1 = [ln(F/K) + (σ²/2)·T] / (σ·√T)
      d2 = d1 − σ·√T

    Equivalente a BSM con S₀=F y q=r (lo cual cancela el growth term y deja solo
    descuento por r). Útil cuando el subyacente es un futuro porque el futures price
    ya incorpora el cost of carry.

    Hull Ejemplo 18.1: F=20, K=20, T=4/12, σ=25%, r=10% → call ≈ 1.116
    """
    if T <= 0:
        if option_type == "call":
            return max(F - K, 0.0)
        return max(K - F, 0.0)
    if sigma <= 0:
        raise ValueError(f"sigma debe ser > 0, recibido {sigma}")
    if F <= 0 or K <= 0:
        raise ValueError(f"F y K deben ser > 0, recibido F={F}, K={K}")

    d1 = (log(F / K) + 0.5 * sigma ** 2 * T) / (sigma * sqrt(T))
    d2 = d1 - sigma * sqrt(T)
    disc = exp(-r * T)

    if option_type == "call":
        return disc * (F * norm.cdf(d1) - K * norm.cdf(d2))
    if option_type == "put":
        return disc * (K * norm.cdf(-d2) - F * norm.cdf(-d1))
    raise ValueError(f"option_type inválido: {option_type}")


def black_delta(
    F: float, K: float, T: float, r: float, sigma: float,
    option_type: OptionType = "call",
) -> float:
    """
    Delta de futures option (Hull 18.7).
    Δ_call = e^(-rT) · N(d1)
    Δ_put = -e^(-rT) · N(-d1)
    Notar el factor de descuento e^(-rT) — la delta es respecto al FUTURO, no al spot.
    """
    if T <= 0 or sigma <= 0:
        return 0.0
    d1 = (log(F / K) + 0.5 * sigma ** 2 * T) / (sigma * sqrt(T))
    disc = exp(-r * T)
    if option_type == "call":
        return disc * norm.cdf(d1)
    return -disc * norm.cdf(-d1)


# ============================================================
# Range forward (collar zero-cost en FX) — Hull 17.4
# ============================================================
def range_forward_strikes(
    S: float, T: float, r_domestic: float, r_foreign: float, sigma: float,
    K_call: float,
) -> float:
    """
    Para un importador que necesita comprar moneda extranjera en T:
    - Long call FX en K_call (techo de compra)
    - Short put FX en K_put (piso, que financia el call)
    Para que sea zero-cost: premium_call = premium_put.

    Dado K_call, despeja K_put numéricamente que iguale las primas (put-call parity
    variation: bisección o brentq).
    """
    from scipy.optimize import brentq
    call_prem = currency_option_price(S, K_call, T, r_domestic, r_foreign, sigma, "call")

    def diff(K_put: float) -> float:
        put_prem = currency_option_price(S, K_put, T, r_domestic, r_foreign, sigma, "put")
        return put_prem - call_prem

    F = fx_forward_price(S, T, r_domestic, r_foreign)
    try:
        return brentq(diff, 0.5 * S, F * 0.999, xtol=1e-6)
    except ValueError as e:
        raise ValueError(
            f"No se encontró K_put zero-cost. K_call={K_call} puede estar muy lejos del forward."
        ) from e
