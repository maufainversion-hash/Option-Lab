"""
Black-Scholes-Merton pricing for European options.

Referencia: Hull, "Options, Futures and Other Derivatives", Cap 14.
Verificación numérica anclada en Ejemplo 14.6 (S=42, K=40, T=0.5, r=0.10, σ=0.20):
  - Call: 4.7594
  - Put:  0.8086
"""
from __future__ import annotations
from math import log, sqrt, exp
from typing import Literal

from scipy.stats import norm

OptionType = Literal["call", "put"]


def _d1_d2(S: float, K: float, T: float, r: float, sigma: float, q: float) -> tuple[float, float]:
    """Componentes d1 y d2 del modelo BSM. Se reusan en greeks analíticas."""
    if sigma <= 0:
        raise ValueError(f"sigma debe ser > 0, recibido {sigma}")
    if T <= 0:
        raise ValueError(f"T debe ser > 0, recibido {T}")
    if S <= 0 or K <= 0:
        raise ValueError(f"S y K deben ser > 0, recibido S={S}, K={K}")
    d1 = (log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * sqrt(T))
    d2 = d1 - sigma * sqrt(T)
    return d1, d2


def bs_price(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    q: float = 0.0,
    option_type: OptionType = "call",
) -> float:
    """
    Precio Black-Scholes-Merton para opción europea con dividendo continuo q.

    Parámetros
    ----------
    S : precio spot del subyacente
    K : strike
    T : tiempo a vencimiento en años (T=0.5 = medio año)
    r : tasa libre de riesgo continua anualizada (0.10 = 10%)
    sigma : volatilidad anualizada (0.20 = 20%)
    q : dividend yield continuo (default 0)
    option_type : 'call' o 'put'

    Returns
    -------
    float : precio teórico de la opción
    """
    if T <= 0:
        # Opción al vencimiento → valor intrínseco
        if option_type == "call":
            return max(S - K, 0.0)
        if option_type == "put":
            return max(K - S, 0.0)
        raise ValueError(f"option_type debe ser 'call' o 'put', recibido {option_type!r}")

    d1, d2 = _d1_d2(S, K, T, r, sigma, q)

    if option_type == "call":
        return S * exp(-q * T) * norm.cdf(d1) - K * exp(-r * T) * norm.cdf(d2)
    if option_type == "put":
        return K * exp(-r * T) * norm.cdf(-d2) - S * exp(-q * T) * norm.cdf(-d1)
    raise ValueError(f"option_type debe ser 'call' o 'put', recibido {option_type!r}")


def bs_price_both(
    S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0
) -> tuple[float, float]:
    """Devuelve (call_price, put_price) en una sola llamada — más eficiente que dos calls."""
    return bs_price(S, K, T, r, sigma, q, "call"), bs_price(S, K, T, r, sigma, q, "put")
