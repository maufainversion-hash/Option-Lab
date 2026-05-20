"""
Currency swap valuation. Hull Cap 7 (Eq 7.10 + 7.11).

Dos métodos equivalentes por no-arbitraje:
1. Portfolio of bonds: V = B_f / S − B_d
2. Portfolio of forward contracts: cada pago se valúa con su forward FX implícito

Convención del módulo (importante):
    spot_exchange_rate = unidades de moneda FOREIGN por 1 unidad de moneda DOMESTIC.
    Ejemplo Hull 7.5: USD = domestic, JPY = foreign, spot = 110 (yen por dólar).

Bajo esta convención, el forward FX por covered interest parity es:
    F(T) = S · e^((r_foreign − r_domestic) · T)
La moneda con tasa más alta se DEPRECIA en el forward.

(Nota: en otras funciones del proyecto — ej. pricing.forwards.fx_forward_price y
calculate_forward_fx_rate de este mismo módulo — se usa la convención inversa
"domestic per foreign". Está documentado en cada función.)
"""
from __future__ import annotations

from typing import List

import numpy as np
import pandas as pd


def value_currency_swap_bonds(
    notional_domestic: float,
    notional_foreign: float,
    rate_domestic: float,
    rate_foreign: float,
    swap_rate_domestic: float,
    swap_rate_foreign: float,
    spot_exchange_rate: float,
    payment_times: List[float],
    domestic_zero_rates: List[float],
    foreign_zero_rates: List[float],
    receive_foreign: bool = True,
) -> dict:
    """
    Valúa un currency swap por el método de portfolios de bonos. Hull 7.7 / Eq 7.10.

    Convención: spot_exchange_rate = unidades FOREIGN por 1 DOMESTIC (yen por dólar = 110).

    Args:
        notional_domestic: Notional en moneda doméstica.
        notional_foreign: Notional en moneda foreign.
        rate_domestic: Risk-free doméstica (cc, anual) — no usada en el cálculo del
            valor por el método de bonos, solo se mantiene por simetría con el de forwards.
        rate_foreign: Risk-free foreign (cc, anual) — idem.
        swap_rate_domestic: Tasa fija que se PAGA en moneda doméstica.
        swap_rate_foreign: Tasa fija que se RECIBE en moneda foreign.
        spot_exchange_rate: Spot FX (foreign per domestic).
        payment_times: Tiempos de pago en años [t₁, ..., tₙ].
        domestic_zero_rates: Zero rates por payment_time (doméstica).
        foreign_zero_rates: Zero rates por payment_time (foreign).
        receive_foreign: True si recibís foreign / pagás doméstica.

    Returns:
        dict con bond_domestic, bond_foreign, bond_foreign_converted, swap_value, cashflows.

    Ejemplo (Hull 7.5): USD/JPY swap → swap_value ≈ +$1,543,000.
    """
    if len(payment_times) != len(domestic_zero_rates):
        raise ValueError("payment_times y domestic_zero_rates deben tener mismo largo")
    if len(payment_times) != len(foreign_zero_rates):
        raise ValueError("payment_times y foreign_zero_rates deben tener mismo largo")

    cf_domestic, cf_foreign = [], []
    for i, _ in enumerate(payment_times):
        coupon_d = notional_domestic * swap_rate_domestic
        coupon_f = notional_foreign * swap_rate_foreign
        if i == len(payment_times) - 1:
            cf_domestic.append(coupon_d + notional_domestic)
            cf_foreign.append(coupon_f + notional_foreign)
        else:
            cf_domestic.append(coupon_d)
            cf_foreign.append(coupon_f)

    bond_domestic = sum(
        cf * np.exp(-r * t)
        for cf, t, r in zip(cf_domestic, payment_times, domestic_zero_rates)
    )
    bond_foreign = sum(
        cf * np.exp(-r * t)
        for cf, t, r in zip(cf_foreign, payment_times, foreign_zero_rates)
    )

    bond_foreign_converted = bond_foreign / spot_exchange_rate
    swap_value = bond_foreign_converted - bond_domestic
    if not receive_foreign:
        swap_value = -swap_value

    cashflows = pd.DataFrame({
        "Time": payment_times,
        "Domestic_CF": cf_domestic,
        "Foreign_CF": cf_foreign,
        "Domestic_Zero_Rate": domestic_zero_rates,
        "Foreign_Zero_Rate": foreign_zero_rates,
        "Domestic_DF": [np.exp(-r * t) for r, t in zip(domestic_zero_rates, payment_times)],
        "Foreign_DF": [np.exp(-r * t) for r, t in zip(foreign_zero_rates, payment_times)],
        "Domestic_PV": [
            cf * np.exp(-r * t) for cf, r, t in zip(cf_domestic, domestic_zero_rates, payment_times)
        ],
        "Foreign_PV": [
            cf * np.exp(-r * t) for cf, r, t in zip(cf_foreign, foreign_zero_rates, payment_times)
        ],
    })

    return {
        "bond_domestic": float(bond_domestic),
        "bond_foreign": float(bond_foreign),
        "bond_foreign_converted": float(bond_foreign_converted),
        "swap_value": float(swap_value),
        "cashflows": cashflows,
    }


def value_currency_swap_forwards(
    notional_domestic: float,
    notional_foreign: float,
    rate_domestic: float,
    rate_foreign: float,
    swap_rate_domestic: float,
    swap_rate_foreign: float,
    spot_exchange_rate: float,
    payment_times: List[float],
    domestic_zero_rates: List[float],
    foreign_zero_rates: List[float],
    receive_foreign: bool = True,
) -> dict:
    """
    Valúa un currency swap por el método de portfolio of forwards. Hull Eq 7.11.

    IMPORTANTE — convención del forward FX en este método:
    spot_exchange_rate está en "foreign per domestic" (yen por dólar).
    Bajo esta convención, F(t) = S · e^((r_foreign − r_domestic) · t)
    (la moneda con tasa MAYOR se deprecia en forward).

    Por no-arbitraje, devuelve EL MISMO swap_value que value_currency_swap_bonds.
    """
    if len(payment_times) != len(domestic_zero_rates):
        raise ValueError("payment_times y domestic_zero_rates deben tener mismo largo")
    if len(payment_times) != len(foreign_zero_rates):
        raise ValueError("payment_times y foreign_zero_rates deben tener mismo largo")

    forward_rates = [
        spot_exchange_rate * np.exp((rate_foreign - rate_domestic) * t)
        for t in payment_times
    ]

    cf_data = []
    net_pv = 0.0
    for i, t in enumerate(payment_times):
        cf_d = notional_domestic * swap_rate_domestic
        cf_f = notional_foreign * swap_rate_foreign
        if i == len(payment_times) - 1:
            cf_d += notional_domestic
            cf_f += notional_foreign

        cf_foreign_in_domestic = cf_f / forward_rates[i]
        net_cf = cf_foreign_in_domestic - cf_d
        df = np.exp(-domestic_zero_rates[i] * t)
        pv = net_cf * df
        net_pv += pv

        cf_data.append({
            "Time": t,
            "Domestic_CF": cf_d,
            "Foreign_CF": cf_f,
            "Forward_Rate": forward_rates[i],
            "Foreign_CF_in_Domestic": cf_foreign_in_domestic,
            "Net_CF": net_cf,
            "Discount_Factor": df,
            "PV": pv,
        })

    swap_value = net_pv if receive_foreign else -net_pv
    return {
        "swap_value": float(swap_value),
        "forward_rates": [float(f) for f in forward_rates],
        "cashflows": pd.DataFrame(cf_data),
    }


def calculate_forward_fx_rate(
    spot_rate: float,
    domestic_rate: float,
    foreign_rate: float,
    time_to_maturity: float,
) -> float:
    """
    Forward FX rate por covered interest parity.

    Convención estándar de esta función: spot = "domestic per foreign"
    (cuántas unidades de moneda doméstica por 1 unidad de foreign).
    Bajo esta convención: F = S · e^((r_domestic − r_foreign) · T).

    Notar que es la convención INVERSA a la usada en value_currency_swap_*.
    """
    return float(spot_rate * np.exp((domestic_rate - foreign_rate) * time_to_maturity))
