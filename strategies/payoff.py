"""
Cálculo de payoff y P&L de estrategias.

Dos modos:
- `payoff_at_expiry`: valor intrínseco de cada pata al vencimiento, neto de premiums.
- `pnl_at_time`: valor de mercado vía BS si t < T. Útil para mostrar cómo evoluciona
  el P&L de una estrategia antes del vencimiento (efecto theta, vega, etc).
"""
from __future__ import annotations

import numpy as np

from pricing.black_scholes import bs_price
from strategies.legs import Leg, Strategy


def _leg_intrinsic_at_expiry(leg: Leg, S_T: np.ndarray) -> np.ndarray:
    """Valor de UNA pata al vencimiento, sin restar premium."""
    if leg.option_type == "stock":
        return leg.quantity * S_T
    if leg.option_type == "call":
        return leg.quantity * np.maximum(S_T - leg.strike, 0.0)
    if leg.option_type == "put":
        return leg.quantity * np.maximum(leg.strike - S_T, 0.0)
    raise ValueError(f"option_type inválido: {leg.option_type}")


def payoff_at_expiry(strategy: Strategy, S_range: np.ndarray) -> np.ndarray:
    """
    Payoff (intrínseco neto de premiums) al vencimiento, para cada spot en S_range.

    Si la estrategia tiene varias expiries, asume que todas vencen al mismo tiempo —
    para estrategias multi-expiry como calendar spreads, usar `pnl_at_time` con el
    expiry corto y dejar la pata larga revaluándose por BS.
    """
    total = np.zeros_like(S_range, dtype=float)
    for leg in strategy.legs:
        # Valor al vencimiento - premium pagado/recibido
        leg_value = _leg_intrinsic_at_expiry(leg, S_range)
        leg_cost = leg.quantity * leg.premium
        total += leg_value - leg_cost
    return total


def _leg_value_at_time(
    leg: Leg, S: np.ndarray, t: float, r: float, sigma: float, q: float = 0.0,
) -> np.ndarray:
    """Valor de mercado de UNA pata en tiempo t (donde t es 'tiempo transcurrido' desde 0)."""
    if leg.option_type == "stock":
        return leg.quantity * S

    tau = leg.expiry - t  # tiempo remanente
    if tau <= 0:
        return _leg_intrinsic_at_expiry(leg, S)

    # BS no acepta arrays nativamente acá, vectorizamos
    values = np.array([
        bs_price(float(s), leg.strike, tau, r, sigma, q, leg.option_type)
        for s in S
    ])
    return leg.quantity * values


def pnl_at_time(
    strategy: Strategy, S_range: np.ndarray, t: float,
    r: float, sigma: float, q: float = 0.0,
) -> np.ndarray:
    """
    P&L de la estrategia en tiempo t (años desde apertura), para cada spot en S_range.

    A t=0 debería dar aproximadamente cero (descontando bid-ask).
    A t=T es equivalente a payoff_at_expiry.
    """
    total = np.zeros_like(S_range, dtype=float)
    for leg in strategy.legs:
        leg_value = _leg_value_at_time(leg, S_range, t, r, sigma, q)
        leg_cost = leg.quantity * leg.premium
        total += leg_value - leg_cost
    return total


def breakeven_points(strategy: Strategy, S_range: np.ndarray) -> list[float]:
    """
    Encuentra los puntos de breakeven al vencimiento (donde payoff cruza cero).

    Devuelve los spots donde el payoff cambia de signo (interpolación lineal).
    """
    payoff = payoff_at_expiry(strategy, S_range)
    crossings = []
    for i in range(len(S_range) - 1):
        if payoff[i] * payoff[i + 1] < 0:
            # Interpolación lineal
            s0, s1 = S_range[i], S_range[i + 1]
            p0, p1 = payoff[i], payoff[i + 1]
            be = s0 - p0 * (s1 - s0) / (p1 - p0)
            crossings.append(float(be))
    return crossings


def max_profit_loss(strategy: Strategy, S_range: np.ndarray) -> tuple[float, float]:
    """Devuelve (max_profit, max_loss) sobre S_range al vencimiento."""
    payoff = payoff_at_expiry(strategy, S_range)
    return float(np.max(payoff)), float(np.min(payoff))
