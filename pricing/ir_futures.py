"""
Interest rate futures. Hull Cap 6.

Day count conventions, conversion factor de Treasury bond futures, cheapest-to-deliver,
Eurodollar convexity adjustment, duration-based hedging.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from typing import Literal

DayCountConvention = Literal["ACT/360", "ACT/ACT", "30/360"]


def day_count_factor(d1: date, d2: date, convention: DayCountConvention = "ACT/360") -> float:
    """Year fraction entre dos fechas. Hull Cap 6.1."""
    if d2 < d1:
        raise ValueError(f"d2 ({d2}) debe ser >= d1 ({d1})")
    actual = (d2 - d1).days
    if convention == "ACT/360":
        return actual / 360.0
    if convention == "ACT/ACT":
        year_days = 366 if (d1.year % 4 == 0 and d1.year % 100 != 0) or d1.year % 400 == 0 else 365
        return actual / year_days
    if convention == "30/360":
        y1, m1, day1 = d1.year, d1.month, min(d1.day, 30)
        y2, m2, day2 = d2.year, d2.month, min(d2.day, 30 if day1 == 30 else d2.day)
        return (360 * (y2 - y1) + 30 * (m2 - m1) + (day2 - day1)) / 360.0
    raise ValueError(f"Convención desconocida: {convention}")


def conversion_factor(
    coupon_rate: float, years_to_maturity: float,
    ytm: float = 0.06, freq: int = 2,
) -> float:
    """
    Conversion factor para Treasury bond futures (CBOT). Hull 6.2.
    Descuenta los cashflows del bono al ytm asumido (default 6% por convención CBOT)
    y divide por 100.

    Simplificación vs Hull: no redondea time-to-maturity al cuarto de año más cercano.
    """
    n = int(freq * years_to_maturity)
    c = coupon_rate * 100 / freq    # cupón semestral sobre face 100
    r = ytm / freq
    pv_coupons = sum(c / (1 + r) ** i for i in range(1, n + 1))
    pv_face = 100.0 / (1 + r) ** n
    return (pv_coupons + pv_face) / 100.0


@dataclass
class CTDResult:
    bond_index: int
    bond_name: str
    cost_of_delivery: float
    quoted_price: float
    conversion_factor: float


def cheapest_to_deliver(
    bonds: list[dict], settlement_futures_price: float,
) -> CTDResult:
    """
    CTD entre una lista de bonos elegibles. Hull 6.2 ejemplo.
    Cada bono: {name, quoted_price, conversion_factor}.
    Cost of delivery = quoted_price - settlement × CF. El menor gana.
    """
    if not bonds:
        raise ValueError("Lista de bonos vacía")
    best_i, best_cost = 0, float("inf")
    for i, b in enumerate(bonds):
        cost = b["quoted_price"] - settlement_futures_price * b["conversion_factor"]
        if cost < best_cost:
            best_cost, best_i = cost, i
    b = bonds[best_i]
    return CTDResult(
        bond_index=best_i, bond_name=b["name"], cost_of_delivery=best_cost,
        quoted_price=b["quoted_price"], conversion_factor=b["conversion_factor"],
    )


def eurodollar_convexity_adjustment(sigma: float, T1: float, T2: float) -> float:
    """
    Adjustment para pasar de futures rate a forward rate. Hull (6.3):
      forward_rate ≈ futures_rate - 0.5 * σ² * T1 * T2
    Devuelve el valor del ajuste (a restarle al futures rate).
    """
    return 0.5 * sigma ** 2 * T1 * T2


def duration_based_hedge_contracts(
    portfolio_value: float, portfolio_duration: float,
    futures_price: float, futures_duration: float,
    contract_multiplier: float = 1000.0,
) -> float:
    """
    Hull (6.4): N* = P · D_P / (V_F · D_F)
    para hedgear exposición de duration con IR futures. Multiplicador default $1000
    (típico de Treasury bond futures del CBOT).
    """
    V_F = futures_price * contract_multiplier
    if V_F <= 0 or futures_duration <= 0:
        raise ValueError("V_F y futures_duration deben ser > 0")
    return (portfolio_value * portfolio_duration) / (V_F * futures_duration)
