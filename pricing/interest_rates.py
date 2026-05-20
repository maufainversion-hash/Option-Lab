"""
Engine de tasas de interés. Hull Cap 4.

Cubre: conversión de compounding, descuento, bond pricing, yield-to-maturity,
forward rates desde zero curve, FRAs, duration y bootstrap de zero curve.
"""
from __future__ import annotations
from dataclasses import dataclass
from math import exp, log
from typing import Literal

import numpy as np


# ============================================================
# Compounding conversion — Hull 4.2
# ============================================================
def to_continuous(rate: float, m: int) -> float:
    """De compounding m veces/año a continuo. R_c = m * ln(1 + R_m/m)."""
    return m * log(1 + rate / m)


def from_continuous(rate_c: float, m: int) -> float:
    """De continuo a compounding m veces/año. R_m = m*(e^(R_c/m) - 1)."""
    return m * (exp(rate_c / m) - 1)


# ============================================================
# Discount factors — Hull 4.3
# ============================================================
def discount_factor(
    rate: float, T: float, compounding: Literal["continuous", "annual"] = "continuous"
) -> float:
    if compounding == "continuous":
        return exp(-rate * T)
    return 1.0 / (1.0 + rate) ** T


# ============================================================
# Bond pricing — Hull 4.4
# ============================================================
def bond_price(
    cashflows: list[tuple[float, float]], zero_rates: list[tuple[float, float]]
) -> float:
    """
    Precio de un bono dado un set de cashflows (T, CF) y una zero curve [(T, R_c)].
    Interpola linealmente la curva si falta el plazo.
    """
    Ts_curve, Rs_curve = zip(*sorted(zero_rates))
    price = 0.0
    for T, cf in cashflows:
        r = float(np.interp(T, Ts_curve, Rs_curve))
        price += cf * exp(-r * T)
    return price


def bond_yield_continuous(
    price: float, cashflows: list[tuple[float, float]], y_init: float = 0.05
) -> float:
    """Despeja el yield-to-maturity continuo via Newton iterativo."""
    y = y_init
    for _ in range(100):
        f = sum(cf * exp(-y * T) for T, cf in cashflows) - price
        df = -sum(T * cf * exp(-y * T) for T, cf in cashflows)
        if abs(df) < 1e-12:
            break
        y -= f / df
        if abs(f) < 1e-8:
            break
    return y


# ============================================================
# Forward rates desde zero curve — Hull 4.7
# ============================================================
def forward_rate(R1: float, T1: float, R2: float, T2: float) -> float:
    """f_{T1,T2} = (R2*T2 - R1*T1) / (T2 - T1). Ambos continuos."""
    if T2 <= T1:
        raise ValueError(f"T2 ({T2}) debe ser > T1 ({T1})")
    return (R2 * T2 - R1 * T1) / (T2 - T1)


# ============================================================
# FRA — Hull 4.8 + Ejemplo 4.3
# ============================================================
@dataclass
class FRAResult:
    forward_rate: float        # tasa forward del período (continuous)
    contract_rate: float       # tasa pactada
    notional: float
    T1: float                  # inicio del período
    T2: float                  # fin del período
    payoff_at_T2: float        # cashflow en T2 (puede ser negativo)
    present_value: float       # valor descontado a hoy
    position: str              # 'receive_fixed' | 'pay_fixed'


def fra_value(
    notional: float,
    contract_rate: float,
    T1: float,
    T2: float,
    zero_T1: float,
    zero_T2: float,
    position: Literal["receive_fixed", "pay_fixed"] = "receive_fixed",
) -> FRAResult:
    """
    Valor de un FRA. Hull Ejemplo 4.3:
      notional = 100M, contract_rate = 4% (recibe fijo),
      T1=3, T2=3.25, zero_T1=3% cc, zero_T2=3.2% cc
      → forward = 5.4% cc → payoff T2 ≈ -$350k → PV ≈ -$315.572

    Devuelve un FRAResult con los componentes para mostrar en UI.
    """
    f = forward_rate(zero_T1, T1, zero_T2, T2)
    tau = T2 - T1
    f_simple = (exp(f * tau) - 1) / tau
    k_simple = (exp(contract_rate * tau) - 1) / tau
    if position == "receive_fixed":
        payoff = notional * (k_simple - f_simple) * tau
    else:
        payoff = notional * (f_simple - k_simple) * tau
    pv = payoff * exp(-zero_T2 * T2)
    return FRAResult(
        forward_rate=f, contract_rate=contract_rate, notional=notional,
        T1=T1, T2=T2, payoff_at_T2=payoff, present_value=pv, position=position,
    )


# ============================================================
# Duration — Hull 4.10
# ============================================================
def macaulay_duration(cashflows: list[tuple[float, float]], y: float) -> float:
    """D = Σ T_i * CF_i*e^(-y*T_i) / Σ CF_i*e^(-y*T_i). y continuo."""
    weights = [(T, cf * exp(-y * T)) for T, cf in cashflows]
    total = sum(w for _, w in weights)
    if total <= 0:
        return 0.0
    return sum(T * w for T, w in weights) / total


def modified_duration(macaulay: float, y: float, m: int = 1) -> float:
    """D_modified = D_macaulay / (1 + y/m). Si m → ∞ (continuo), D_mod = D_mac."""
    return macaulay / (1 + y / m)


# ============================================================
# Bootstrap de zero curve desde Treasury yields — Hull 4.5
# ============================================================
def bootstrap_zero_curve(
    instruments: list[tuple[float, float, float, str]],
) -> list[tuple[float, float]]:
    """
    Bootstrap simple. instruments: lista de (maturity_T, coupon_rate, market_price, kind)
    donde kind ∈ {'zero', 'coupon_semi'}. Devuelve [(T, R_continuous)] ordenado.
    """
    zeros: list[tuple[float, float]] = []
    instruments = sorted(instruments, key=lambda x: x[0])
    for T, coupon, price, kind in instruments:
        if kind == "zero":
            r = -log(price / 100.0) / T
            zeros.append((T, r))
        else:  # coupon_semi: cupones semestrales, face 100
            cfs = []
            t = 0.5
            while t < T - 1e-9:
                cfs.append((t, coupon * 100 / 2))
                t += 0.5
            cfs.append((T, coupon * 100 / 2 + 100))
            Ts_known, Rs_known = (zip(*zeros) if zeros else ([0], [0]))
            pv_known = sum(
                cf * exp(-float(np.interp(t, Ts_known, Rs_known)) * t)
                for t, cf in cfs[:-1]
            )
            last_t, last_cf = cfs[-1]
            if price - pv_known <= 0:
                raise ValueError(f"Bootstrap inviable en T={T}")
            r = -log((price - pv_known) / last_cf) / last_t
            zeros.append((last_t, r))
    return zeros
