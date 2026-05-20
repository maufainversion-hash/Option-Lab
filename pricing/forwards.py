"""
Forward y futures pricing. Hull Cap 3 + 5.

Cost of carry, dividend yield, storage cost, convenience yield, basis y
hedge ratios para coberturas con futuros.
"""
from __future__ import annotations
from math import exp
from typing import Literal


def forward_price(
    S0: float, r: float, T: float,
    q: float = 0.0, storage_cost: float = 0.0, convenience_yield: float = 0.0,
) -> float:
    """
    Forward price genérica. Hull (5.5)(5.7)(5.17):
      F = S0 * e^((r - q + u - y) * T)
    donde q = dividend yield, u = storage cost rate, y = convenience yield.
    """
    return S0 * exp((r - q + storage_cost - convenience_yield) * T)


def forward_value(
    S0: float, K: float, r: float, T: float, q: float = 0.0,
    position: Literal["long", "short"] = "long",
) -> float:
    """
    Valor de un forward existente con strike K. Hull (5.4):
      f_long  = S0*e^(-qT) - K*e^(-rT)
      f_short = K*e^(-rT) - S0*e^(-qT)
    """
    s = S0 * exp(-q * T)
    k = K * exp(-r * T)
    return s - k if position == "long" else k - s


def cost_of_carry(r: float, q: float = 0.0, u: float = 0.0, y: float = 0.0) -> float:
    """c = r - q + u - y."""
    return r - q + u - y


def basis(spot: float, futures: float) -> float:
    """Basis = Spot - Futures. Hull 3.2."""
    return spot - futures


def minimum_variance_hedge_ratio(
    sigma_spot: float, sigma_futures: float, correlation: float,
) -> float:
    """h* = ρ * (σ_S / σ_F). Hull (3.1)."""
    if sigma_futures <= 0:
        raise ValueError("sigma_futures debe ser > 0")
    return correlation * sigma_spot / sigma_futures


def equity_portfolio_hedge_contracts(
    portfolio_value: float, beta: float, futures_price: float, contract_multiplier: float,
) -> float:
    """Número de contratos a vender para hedgear un portfolio. Hull (3.5):
    N* = β * V_A / V_F"""
    v_f = futures_price * contract_multiplier
    if v_f <= 0:
        raise ValueError("futures_price * multiplier debe ser > 0")
    return beta * portfolio_value / v_f
