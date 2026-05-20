"""
Cotas de no-arbitraje sobre el precio de opciones europeas. Hull Cap 10.

Lower bounds:
    Call europeo: C >= max(S*e^(-qT) - K*e^(-rT), 0)
    Put europeo:  P >= max(K*e^(-rT) - S*e^(-qT), 0)

Upper bounds:
    Call europeo: C <= S*e^(-qT)
    Put europeo:  P <= K*e^(-rT)

Si el precio de mercado viola estas cotas, hay arbitraje en teoría. En la práctica
sirven para flagear quotes ruidosos en chains AR de baja liquidez.
"""
from __future__ import annotations
from math import exp
from typing import Literal


def call_lower_bound(S: float, K: float, T: float, r: float, q: float = 0.0) -> float:
    """Cota inferior call europeo. Hull (10.4)."""
    return max(S * exp(-q * T) - K * exp(-r * T), 0.0)


def call_upper_bound(S: float, T: float, q: float = 0.0) -> float:
    """Cota superior call europeo. Hull (10.1)."""
    return S * exp(-q * T)


def put_lower_bound(S: float, K: float, T: float, r: float, q: float = 0.0) -> float:
    """Cota inferior put europeo. Hull (10.5)."""
    return max(K * exp(-r * T) - S * exp(-q * T), 0.0)


def put_upper_bound(K: float, T: float, r: float) -> float:
    """Cota superior put europeo. Hull (10.3)."""
    return K * exp(-r * T)


def check_bounds(
    price: float, S: float, K: float, T: float, r: float,
    q: float = 0.0, option_type: Literal["call", "put"] = "call",
) -> dict[str, float | bool | str]:
    """Verifica si un precio observado respeta las cotas de no-arbitraje."""
    if option_type == "call":
        lb = call_lower_bound(S, K, T, r, q)
        ub = call_upper_bound(S, T, q)
    else:
        lb = put_lower_bound(S, K, T, r, q)
        ub = put_upper_bound(K, T, r)

    in_range = bool(lb <= price <= ub)
    return {
        "price": price,
        "lower_bound": lb,
        "upper_bound": ub,
        "in_range": in_range,
        "violation": (
            "Precio por debajo de cota inferior — arbitraje al comprar" if price < lb
            else "Precio por encima de cota superior — arbitraje al vender" if price > ub
            else "OK"
        ),
    }
