"""
Greeks analíticas closed-form para Black-Scholes-Merton.

Referencia: Hull, Cap 18. Convenciones estándar:
- Delta: ∂V/∂S
- Gamma: ∂²V/∂S²
- Vega:  ∂V/∂σ  (por unidad de σ, NO por 1% — multiplicar por 0.01 para "vega per 1%")
- Theta: ∂V/∂t  (por año — dividir por 365 para "theta per día")
- Rho:   ∂V/∂r  (por unidad — multiplicar por 0.01 para "rho per 1%")
"""
from __future__ import annotations
from math import exp, sqrt

from scipy.stats import norm

from pricing.black_scholes import _d1_d2, OptionType


def delta(
    S: float, K: float, T: float, r: float, sigma: float,
    q: float = 0.0, option_type: OptionType = "call",
) -> float:
    """∂V/∂S — sensibilidad al spot. Call ∈ [0,1], Put ∈ [-1,0]."""
    if T <= 0:
        if option_type == "call":
            return 1.0 if S > K else (0.5 if S == K else 0.0)
        return -1.0 if S < K else (-0.5 if S == K else 0.0)
    d1, _ = _d1_d2(S, K, T, r, sigma, q)
    if option_type == "call":
        return exp(-q * T) * norm.cdf(d1)
    return exp(-q * T) * (norm.cdf(d1) - 1.0)


def gamma(
    S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0,
) -> float:
    """∂²V/∂S² — convexidad. Mismo valor para call y put (es la 2da derivada)."""
    if T <= 0 or sigma <= 0:
        return 0.0
    d1, _ = _d1_d2(S, K, T, r, sigma, q)
    return exp(-q * T) * norm.pdf(d1) / (S * sigma * sqrt(T))


def vega(
    S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0,
) -> float:
    """∂V/∂σ — sensibilidad a la vol. Mismo valor para call y put. Por unidad de σ."""
    if T <= 0:
        return 0.0
    d1, _ = _d1_d2(S, K, T, r, sigma, q)
    return S * exp(-q * T) * norm.pdf(d1) * sqrt(T)


def theta(
    S: float, K: float, T: float, r: float, sigma: float,
    q: float = 0.0, option_type: OptionType = "call",
) -> float:
    """
    ∂V/∂t — decay temporal. Por unidad de tiempo (año). Negativo para opciones long.
    Para "theta por día calendario", dividir por 365.
    Para "theta por día hábil", dividir por 252.
    """
    if T <= 0 or sigma <= 0:
        return 0.0
    d1, d2 = _d1_d2(S, K, T, r, sigma, q)
    first = -S * exp(-q * T) * norm.pdf(d1) * sigma / (2.0 * sqrt(T))
    if option_type == "call":
        return first - r * K * exp(-r * T) * norm.cdf(d2) + q * S * exp(-q * T) * norm.cdf(d1)
    return first + r * K * exp(-r * T) * norm.cdf(-d2) - q * S * exp(-q * T) * norm.cdf(-d1)


def rho(
    S: float, K: float, T: float, r: float, sigma: float,
    q: float = 0.0, option_type: OptionType = "call",
) -> float:
    """∂V/∂r — sensibilidad a la tasa libre de riesgo. Por unidad. Multiplicar por 0.01 para 'per 1%'."""
    if T <= 0:
        return 0.0
    _, d2 = _d1_d2(S, K, T, r, sigma, q)
    if option_type == "call":
        return K * T * exp(-r * T) * norm.cdf(d2)
    return -K * T * exp(-r * T) * norm.cdf(-d2)


def all_greeks(
    S: float, K: float, T: float, r: float, sigma: float,
    q: float = 0.0, option_type: OptionType = "call",
) -> dict[str, float]:
    """Devuelve las 5 griegas principales en un dict. Útil para mostrar en UI."""
    return {
        "delta": delta(S, K, T, r, sigma, q, option_type),
        "gamma": gamma(S, K, T, r, sigma, q),
        "vega": vega(S, K, T, r, sigma, q),
        "theta": theta(S, K, T, r, sigma, q, option_type),
        "rho": rho(S, K, T, r, sigma, q, option_type),
    }
