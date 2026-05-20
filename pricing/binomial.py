"""
Pricing por árbol binomial.

Dos implementaciones:
- CRR (Cox-Ross-Rubinstein): el clásico de Hull Cap 12. Converge a BS pero oscila.
- Leisen-Reimer: usa Peizer-Pratt inversion method 2 — converge mucho más rápido y
  monotónicamente, ideal para americanas y para mostrar convergencia con pocos pasos.

Ambos soportan ejercicio europeo y americano.
"""
from __future__ import annotations
from math import exp, sqrt, log
from typing import Literal

import numpy as np

OptionType = Literal["call", "put"]
ExerciseStyle = Literal["european", "american"]


def crr_price(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    q: float = 0.0,
    n: int = 500,
    option_type: OptionType = "call",
    exercise: ExerciseStyle = "european",
) -> float:
    """
    Cox-Ross-Rubinstein binomial.

    n=500 da convergencia ±0.01 vs Black-Scholes para casos típicos.
    Para opciones americanas no hay closed-form, este es el camino.
    """
    if n < 1:
        raise ValueError(f"n debe ser >= 1, recibido {n}")
    if T <= 0:
        intrinsic = max(S - K, 0.0) if option_type == "call" else max(K - S, 0.0)
        return intrinsic

    dt = T / n
    u = exp(sigma * sqrt(dt))
    d = 1.0 / u
    p = (exp((r - q) * dt) - d) / (u - d)

    if not 0.0 < p < 1.0:
        raise ValueError(
            f"Probabilidad risk-neutral fuera de (0,1): p={p:.4f}. "
            f"Aumentar n o revisar inputs (σ muy bajo, dt muy grande)."
        )

    disc = exp(-r * dt)

    # Precios terminales del subyacente: S_T(j) = S * u^(n-j) * d^j, j = 0..n
    j = np.arange(n + 1)
    ST = S * (u ** (n - j)) * (d ** j)

    # Payoff terminal
    if option_type == "call":
        V = np.maximum(ST - K, 0.0)
    else:
        V = np.maximum(K - ST, 0.0)

    # Inducción hacia atrás
    for i in range(n - 1, -1, -1):
        V = disc * (p * V[:-1] + (1 - p) * V[1:])
        if exercise == "american":
            j = np.arange(i + 1)
            St = S * (u ** (i - j)) * (d ** j)
            intrinsic = np.maximum(St - K, 0.0) if option_type == "call" else np.maximum(K - St, 0.0)
            V = np.maximum(V, intrinsic)

    return float(V[0])


def _peizer_pratt(z: float, n: int) -> float:
    """Peizer-Pratt inversion method 2 — el truco que hace a Leisen-Reimer rápido."""
    sign = 1.0 if z >= 0 else -1.0
    return 0.5 + sign * 0.5 * sqrt(
        1.0 - exp(-((z / (n + 1.0 / 3.0 + 0.1 / (n + 1))) ** 2) * (n + 1.0 / 6.0))
    )


def leisen_reimer_price(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    q: float = 0.0,
    n: int = 51,
    option_type: OptionType = "call",
    exercise: ExerciseStyle = "european",
) -> float:
    """
    Árbol Leisen-Reimer.

    Mucho más rápido que CRR — n=51 suele dar ±0.001 vs BS.
    El n debe ser impar para que el árbol esté centrado en el strike.
    """
    if n < 3:
        raise ValueError(f"n debe ser >= 3, recibido {n}")
    if n % 2 == 0:
        n += 1  # forzar impar

    if T <= 0:
        intrinsic = max(S - K, 0.0) if option_type == "call" else max(K - S, 0.0)
        return intrinsic

    dt = T / n
    d1 = (log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * sqrt(T))
    d2 = d1 - sigma * sqrt(T)

    p = _peizer_pratt(d2, n)
    p_star = _peizer_pratt(d1, n)
    u = exp((r - q) * dt) * p_star / p
    d = (exp((r - q) * dt) - p * u) / (1 - p)

    disc = exp(-r * dt)

    j = np.arange(n + 1)
    ST = S * (u ** (n - j)) * (d ** j)
    V = np.maximum(ST - K, 0.0) if option_type == "call" else np.maximum(K - ST, 0.0)

    for i in range(n - 1, -1, -1):
        V = disc * (p * V[:-1] + (1 - p) * V[1:])
        if exercise == "american":
            j = np.arange(i + 1)
            St = S * (u ** (i - j)) * (d ** j)
            intrinsic = np.maximum(St - K, 0.0) if option_type == "call" else np.maximum(K - St, 0.0)
            V = np.maximum(V, intrinsic)

    return float(V[0])


def binomial_convergence(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    q: float = 0.0,
    option_type: OptionType = "call",
    n_values: list[int] | None = None,
) -> dict[str, list]:
    """
    Devuelve precios del CRR y LR para distintos n — útil para visualizar convergencia.

    Hull Fig 12.x: el CRR oscila alrededor del precio BS y converge lentamente,
    mientras que LR converge monotónicamente y mucho más rápido.
    """
    if n_values is None:
        n_values = [5, 10, 25, 50, 100, 250, 500]
    crr = [crr_price(S, K, T, r, sigma, q, n, option_type, "european") for n in n_values]
    lr = [leisen_reimer_price(S, K, T, r, sigma, q, n, option_type, "european") for n in n_values]
    return {"n": n_values, "crr": crr, "lr": lr}
