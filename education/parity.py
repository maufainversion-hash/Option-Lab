"""
Put-call parity y relaciones de no-arbitraje. Hull Cap 10.

Parity para opciones europeas con dividend yield continuo q:

    C + K * e^(-rT) = P + S * e^(-qT)

Reordenando:
    C - P = S * e^(-qT) - K * e^(-rT)

Si la igualdad no se cumple en el mercado, hay arbitraje (en teoría — en la práctica
hay bid-ask, costos de funding, y restricciones de short que la pueden invalidar).
"""
from __future__ import annotations
from math import exp


def parity_difference(C: float, P: float, S: float, K: float, T: float, r: float, q: float = 0.0) -> float:
    """
    Devuelve LHS - RHS de la parity. Cero = parity se cumple.

    LHS = C - P
    RHS = S*e^(-qT) - K*e^(-rT)
    """
    lhs = C - P
    rhs = S * exp(-q * T) - K * exp(-r * T)
    return lhs - rhs


def synthetic_call(P: float, S: float, K: float, T: float, r: float, q: float = 0.0) -> float:
    """
    Construye un call sintético a partir de: long put + long stock + short cash.
    C = P + S*e^(-qT) - K*e^(-rT)
    """
    return P + S * exp(-q * T) - K * exp(-r * T)


def synthetic_put(C: float, S: float, K: float, T: float, r: float, q: float = 0.0) -> float:
    """
    Construye un put sintético: long call + short stock + long cash.
    P = C - S*e^(-qT) + K*e^(-rT)
    """
    return C - S * exp(-q * T) + K * exp(-r * T)


def implied_rate_from_parity(C: float, P: float, S: float, K: float, T: float, q: float = 0.0) -> float:
    """
    Despeja la tasa libre de riesgo implícita en el par call/put.

    Útil en AR: la rate "oficial" (BADLAR/TAMAR) no necesariamente refleja
    el funding real que usa el market. Lo que importa es la tasa implícita.

    Derivación: C - P = S*e^(-qT) - K*e^(-rT)
                K*e^(-rT) = S*e^(-qT) - (C - P)
                -rT = ln((S*e^(-qT) - (C-P)) / K)
                r = -ln((S*e^(-qT) - (C-P)) / K) / T
    """
    from math import log
    inner = (S * exp(-q * T) - (C - P)) / K
    if inner <= 0:
        raise ValueError(
            f"Imposible despejar r: (S*e^(-qT) - (C-P))/K = {inner:.4f} <= 0. "
            "Los quotes violan no-arbitraje o son ruidosos."
        )
    return -log(inner) / T


def parity_check(
    C: float, P: float, S: float, K: float, T: float, r: float,
    q: float = 0.0, tolerance: float = 0.05,
) -> dict[str, float | bool | str]:
    """
    Reporta status de la parity.

    tolerance: cuánto puede desviar la diferencia en valor absoluto antes de marcar 'violated'.
    """
    diff = parity_difference(C, P, S, K, T, r, q)
    return {
        "lhs_call_minus_put": C - P,
        "rhs_S_minus_K_disc": S * exp(-q * T) - K * exp(-r * T),
        "difference": diff,
        "violated": bool(abs(diff) > tolerance),
        "interpretation": (
            "Call sobreprecio respecto al put" if diff > tolerance
            else "Put sobreprecio respecto al call" if diff < -tolerance
            else "Parity se cumple dentro de tolerancia"
        ),
    }
