"""
Inversión de Black-Scholes para obtener volatilidad implícita.

Usa Brent's method de scipy.optimize — robusto y sin necesidad de derivada (Vega).
Para chains AR donde los quotes son ruidosos, Brent es preferible a Newton-Raphson
porque no diverge cuando Vega ≈ 0 (opciones muy OTM o muy ITM).
"""
from __future__ import annotations
from math import exp

from scipy.optimize import brentq

from pricing.black_scholes import bs_price, OptionType


def implied_vol(
    market_price: float,
    S: float,
    K: float,
    T: float,
    r: float,
    q: float = 0.0,
    option_type: OptionType = "call",
    tol: float = 1e-6,
    max_iter: int = 100,
    sigma_low: float = 1e-4,
    sigma_high: float = 5.0,
) -> float | None:
    """
    Vol implícita por Brent.

    Devuelve None si:
    - market_price <= 0
    - T <= 0
    - market_price viola lower bound (no-arb), o sea quote ruidoso
    - Brent no converge en max_iter iteraciones

    sigma_high = 5.0 (500%) cubre casi cualquier opción razonable.
    AR puede tener IV alta en eventos pero pasar 500% es señal de quote roto.
    """
    if market_price <= 0 or T <= 0:
        return None

    # Lower bound de no-arbitraje
    if option_type == "call":
        lower_bound = max(S * exp(-q * T) - K * exp(-r * T), 0.0)
    else:
        lower_bound = max(K * exp(-r * T) - S * exp(-q * T), 0.0)

    if market_price < lower_bound - 1e-6:
        return None  # viola arbitraje → quote sin sentido

    # Upper bound: call <= S*e^(-qT), put <= K*e^(-rT)
    upper_bound = S * exp(-q * T) if option_type == "call" else K * exp(-r * T)
    if market_price > upper_bound + 1e-6:
        return None

    def f(sigma: float) -> float:
        return bs_price(S, K, T, r, sigma, q, option_type) - market_price

    try:
        return float(brentq(f, sigma_low, sigma_high, xtol=tol, maxiter=max_iter))
    except (ValueError, RuntimeError):
        return None


def implied_vol_curve(
    market_prices: list[float],
    strikes: list[float],
    S: float,
    T: float,
    r: float,
    q: float = 0.0,
    option_type: OptionType = "call",
) -> list[float | None]:
    """
    Calcula IV para una serie de strikes (un slice de la vol surface).

    Útil para visualizar el smile/skew en un vencimiento dado.
    """
    if len(market_prices) != len(strikes):
        raise ValueError("market_prices y strikes deben tener la misma longitud")
    return [
        implied_vol(p, S, K, T, r, q, option_type)
        for p, K in zip(market_prices, strikes)
    ]
