"""
Greeks numéricas vía bump-and-reprice.

Sirven para:
1. Validar las analíticas (deben coincidir hasta ~5 decimales).
2. Calcular greeks de instrumentos sin closed-form (americanas, exóticas).

Métodos:
- Primera derivada: differencia central (P(x+h) - P(x-h)) / (2h)
- Segunda derivada: (P(x+h) - 2*P(x) + P(x-h)) / h²

h se elige proporcional a la escala del input — h = 1e-4 * S para spot, etc.
"""
from __future__ import annotations
from typing import Callable

from pricing.black_scholes import bs_price, OptionType


def _make_pricer(
    S: float, K: float, T: float, r: float, sigma: float, q: float, option_type: OptionType
) -> Callable[..., float]:
    """Closure que devuelve precio BS con los parámetros cerrados."""
    def pricer(S_=S, K_=K, T_=T, r_=r, sigma_=sigma, q_=q):
        return bs_price(S_, K_, T_, r_, sigma_, q_, option_type)
    return pricer


def delta_numeric(
    S: float, K: float, T: float, r: float, sigma: float,
    q: float = 0.0, option_type: OptionType = "call", h: float | None = None,
) -> float:
    if h is None:
        h = 1e-4 * S
    p_up = bs_price(S + h, K, T, r, sigma, q, option_type)
    p_dn = bs_price(S - h, K, T, r, sigma, q, option_type)
    return (p_up - p_dn) / (2 * h)


def gamma_numeric(
    S: float, K: float, T: float, r: float, sigma: float,
    q: float = 0.0, option_type: OptionType = "call", h: float | None = None,
) -> float:
    if h is None:
        h = 1e-3 * S  # gamma necesita h más grande por la 2da derivada
    p_up = bs_price(S + h, K, T, r, sigma, q, option_type)
    p_mid = bs_price(S, K, T, r, sigma, q, option_type)
    p_dn = bs_price(S - h, K, T, r, sigma, q, option_type)
    return (p_up - 2 * p_mid + p_dn) / (h * h)


def vega_numeric(
    S: float, K: float, T: float, r: float, sigma: float,
    q: float = 0.0, option_type: OptionType = "call", h: float = 1e-4,
) -> float:
    p_up = bs_price(S, K, T, r, sigma + h, q, option_type)
    p_dn = bs_price(S, K, T, r, sigma - h, q, option_type)
    return (p_up - p_dn) / (2 * h)


def theta_numeric(
    S: float, K: float, T: float, r: float, sigma: float,
    q: float = 0.0, option_type: OptionType = "call", h: float = 1 / 365,
) -> float:
    """Forward difference porque T no puede ser negativo."""
    p_now = bs_price(S, K, T, r, sigma, q, option_type)
    p_later = bs_price(S, K, T - h, r, sigma, q, option_type)
    # Hull define theta = -∂V/∂t pero acá usamos convención de derivada normal
    # (matches analytical.theta), then later = T - h is "más cerca del vencimiento"
    return (p_later - p_now) / h


def rho_numeric(
    S: float, K: float, T: float, r: float, sigma: float,
    q: float = 0.0, option_type: OptionType = "call", h: float = 1e-4,
) -> float:
    p_up = bs_price(S, K, T, r + h, sigma, q, option_type)
    p_dn = bs_price(S, K, T, r - h, sigma, q, option_type)
    return (p_up - p_dn) / (2 * h)
