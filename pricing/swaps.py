"""
Swap valuation. Hull Cap 7.

Plain vanilla IR swap valuation via el bond approach.
"""
from __future__ import annotations
from dataclasses import dataclass
from math import exp


@dataclass
class SwapValuationResult:
    bond_fixed_value: float
    bond_floating_value: float
    swap_value: float   # para receive_fixed = fixed - floating
    position: str       # 'receive_fixed' o 'receive_floating'


def swap_value_via_bonds(
    notional: float,
    fixed_rate: float,             # tasa fija anual del swap
    payment_times: list[float],    # fechas de pagos remanentes
    zero_rates: list[float],       # rates continuos en cada payment_time
    next_floating_rate: float,     # tasa flotante seteada en el reset anterior
    time_since_last_reset: float,  # años desde el último reset
    accrual: float,                # años por período (e.g. 0.5 semestral)
    position: str = "receive_fixed",
) -> SwapValuationResult:
    """
    Hull 7.7 — bond approach.
    B_fix  = Σ k*e^(-r_i*t_i)  + L*e^(-r_n*t_n)  donde k = notional*fixed*accrual
    B_flt  = (L + k*)*e^(-r_1*t_1) donde k* = notional*next_floating*accrual
    """
    if len(payment_times) != len(zero_rates):
        raise ValueError("payment_times y zero_rates deben tener misma longitud")
    k = notional * fixed_rate * accrual
    b_fix = sum(k * exp(-r * t) for r, t in zip(zero_rates, payment_times)) \
            + notional * exp(-zero_rates[-1] * payment_times[-1])
    accrued_floating = notional * next_floating_rate * accrual
    first_t, first_r = payment_times[0], zero_rates[0]
    b_flt = (notional + accrued_floating) * exp(-first_r * first_t)
    if position == "receive_fixed":
        v = b_fix - b_flt
    else:
        v = b_flt - b_fix
    return SwapValuationResult(b_fix, b_flt, v, position)


def swap_par_rate(
    payment_times: list[float], zero_rates: list[float], accrual: float
) -> float:
    """
    Hull 7.5: la fixed rate que hace B_fix = B_flt = notional al iniciar el swap.
    r_par = (1 - e^(-r_n*t_n)) / (accrual * Σ e^(-r_i*t_i))
    """
    if len(payment_times) != len(zero_rates):
        raise ValueError("payment_times y zero_rates deben tener misma longitud")
    num = 1 - exp(-zero_rates[-1] * payment_times[-1])
    den = accrual * sum(exp(-r * t) for r, t in zip(zero_rates, payment_times))
    return num / den
