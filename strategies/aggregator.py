"""
Agregación de greeks de estrategias multi-leg.

Las greeks son aditivas (con signo y cantidad de la pata). Esto permite ver
"el delta neto del combo es +0.30" o "el theta neto es -$5/día".
"""
from __future__ import annotations

from greeks.analytical import all_greeks
from strategies.legs import Strategy


def _stock_greeks() -> dict[str, float]:
    """Una acción tiene delta=1, gamma=theta=vega=rho=0."""
    return {"delta": 1.0, "gamma": 0.0, "vega": 0.0, "theta": 0.0, "rho": 0.0}


def net_greeks(
    strategy: Strategy, S: float, t: float, r: float, sigma: float, q: float = 0.0,
) -> dict[str, float]:
    """
    Greeks netas del combo en el momento t (años desde apertura).

    Suma cantidad * greek de cada pata. Para patas tipo stock usa (delta=1, otras=0).
    """
    totals = {"delta": 0.0, "gamma": 0.0, "vega": 0.0, "theta": 0.0, "rho": 0.0}

    for leg in strategy.legs:
        if leg.option_type == "stock":
            leg_greeks = _stock_greeks()
        else:
            tau = leg.expiry - t
            if tau <= 0:
                # Vencida — greeks bien definidas son discontinuas, las pasamos a 0
                leg_greeks = {"delta": 0.0, "gamma": 0.0, "vega": 0.0, "theta": 0.0, "rho": 0.0}
            else:
                leg_greeks = all_greeks(S, leg.strike, tau, r, sigma, q, leg.option_type)

        for k in totals:
            totals[k] += leg.quantity * leg_greeks[k]

    return totals


def greek_profile(
    strategy: Strategy, S_range, t: float, r: float, sigma: float, q: float = 0.0,
    greek_name: str = "delta",
) -> list[float]:
    """
    Devuelve el valor de UNA griega del combo a través de un rango de spots.

    Útil para gráficos tipo "cómo cambia delta del combo con S".
    """
    if greek_name not in ("delta", "gamma", "vega", "theta", "rho"):
        raise ValueError(f"greek_name inválido: {greek_name}")
    return [net_greeks(strategy, float(s), t, r, sigma, q)[greek_name] for s in S_range]
