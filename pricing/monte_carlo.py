"""
Monte Carlo pricing y simulación de paths GBM.

Referencia: Hull, "Options, Futures and Other Derivatives", Cap 13 (Wiener processes
y proceso del precio de una acción) y Cap 21 (Monte Carlo simulation).

Movimiento Browniano geométrico (Hull 13.2):

    dS = μ·S·dt + σ·S·dW

Solución cerrada (Hull 13.5, vía Itô's lemma):

    S_T = S_0 · exp( (μ - σ²/2)·T + σ·√T · Z ),  Z ~ N(0,1)

Bajo medida risk-neutral Q, el drift es μ = r − q (Hull Cap 14). Eso es lo que
usamos para pricing de opciones; el drift "físico" (real-world) puede ser distinto
y NO afecta el precio de la opción — solo importa para simulaciones P-measure.

Verificación numérica anclada en Hull Ejemplo 14.6 (Call=4.7594, Put=0.8086):
n_paths=200k, antithetic=True → ±0.05 vs BS.
"""
from __future__ import annotations
from math import exp, sqrt
from typing import Literal

import numpy as np

OptionType = Literal["call", "put"]


def simulate_gbm_paths(
    S0: float,
    mu: float,
    sigma: float,
    T: float,
    steps: int,
    n_paths: int,
    antithetic: bool = False,
    seed: int | None = None,
) -> np.ndarray:
    """
    Simula `n_paths` trayectorias de GBM con `steps` pasos hasta T.

    Discretización exacta (no Euler) — usa la solución log-normal de Itô:
        S_{t+Δt} = S_t · exp( (μ − σ²/2)·Δt + σ·√Δt · Z )

    Parámetros
    ----------
    S0 : precio spot inicial
    mu : drift anualizado. Para pricing risk-neutral usar (r − q).
         Para simulación bajo P (educativo) usar μ real (típicamente > r).
    sigma : volatilidad anualizada
    T : horizonte en años
    steps : pasos de tiempo (1 = solo terminal; 252 = diario; 50 = visualización)
    n_paths : número de trayectorias
    antithetic : si True, espeja la mitad de los paths con -Z (reduce varianza)
    seed : semilla del RNG (reproducibilidad). None = aleatorio.

    Returns
    -------
    np.ndarray con shape (n_paths, steps+1). Columna 0 = S0, columna -1 = S_T.
    """
    if S0 <= 0:
        raise ValueError(f"S0 debe ser > 0, recibido {S0}")
    if sigma < 0:
        raise ValueError(f"sigma debe ser >= 0, recibido {sigma}")
    if T <= 0:
        raise ValueError(f"T debe ser > 0, recibido {T}")
    if steps < 1:
        raise ValueError(f"steps debe ser >= 1, recibido {steps}")
    if n_paths < 1:
        raise ValueError(f"n_paths debe ser >= 1, recibido {n_paths}")
    if antithetic and n_paths % 2 != 0:
        raise ValueError(f"antithetic requiere n_paths par, recibido {n_paths}")

    rng = np.random.default_rng(seed)
    dt = T / steps
    drift = (mu - 0.5 * sigma ** 2) * dt
    diffusion = sigma * sqrt(dt)

    if antithetic:
        half = n_paths // 2
        Z_half = rng.standard_normal(size=(half, steps))
        Z = np.vstack([Z_half, -Z_half])
    else:
        Z = rng.standard_normal(size=(n_paths, steps))

    log_increments = drift + diffusion * Z          # shape (n_paths, steps)
    log_S = np.log(S0) + np.cumsum(log_increments, axis=1)

    paths = np.empty((n_paths, steps + 1))
    paths[:, 0] = S0
    paths[:, 1:] = np.exp(log_S)
    return paths


def mc_price_european(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    q: float = 0.0,
    option_type: OptionType = "call",
    n_paths: int = 100_000,
    antithetic: bool = True,
    seed: int | None = None,
) -> dict[str, float]:
    """
    Precio Monte Carlo de opción europea bajo medida risk-neutral.

    Como solo necesitamos S_T (no la trayectoria), usamos un único paso terminal.
    Para visualizar paths usar `simulate_gbm_paths` con steps > 1.

    Drift bajo Q: μ = r − q. Hull Cap 14.7.

    Returns
    -------
    dict con keys:
        - price: estimador del precio (media descontada de payoffs)
        - stderr: error estándar del estimador
        - ci95_lo, ci95_hi: extremos del intervalo de confianza al 95%
        - n_paths: paths efectivamente usados
    """
    if option_type not in ("call", "put"):
        raise ValueError(f"option_type debe ser 'call' o 'put', recibido {option_type!r}")
    if T <= 0:
        intrinsic = max(S - K, 0.0) if option_type == "call" else max(K - S, 0.0)
        return {"price": intrinsic, "stderr": 0.0,
                "ci95_lo": intrinsic, "ci95_hi": intrinsic, "n_paths": 0}
    if antithetic and n_paths % 2 != 0:
        n_paths += 1   # tolerante: subimos a par sin romper

    rng = np.random.default_rng(seed)
    disc = exp(-r * T)
    drift_term = (r - q - 0.5 * sigma ** 2) * T
    diffusion_term = sigma * sqrt(T)

    if antithetic:
        half = n_paths // 2
        Z = rng.standard_normal(size=half)
        ST_pos = S * np.exp(drift_term + diffusion_term * Z)
        ST_neg = S * np.exp(drift_term - diffusion_term * Z)
        if option_type == "call":
            payoff_pos = np.maximum(ST_pos - K, 0.0)
            payoff_neg = np.maximum(ST_neg - K, 0.0)
        else:
            payoff_pos = np.maximum(K - ST_pos, 0.0)
            payoff_neg = np.maximum(K - ST_neg, 0.0)
        # Promediamos cada par antitético — el estimador queda con varianza de pares
        pair_means = 0.5 * (payoff_pos + payoff_neg)
        discounted = disc * pair_means
        price = float(discounted.mean())
        stderr = float(discounted.std(ddof=1) / sqrt(half))
        n_effective = n_paths
    else:
        Z = rng.standard_normal(size=n_paths)
        ST = S * np.exp(drift_term + diffusion_term * Z)
        payoff = np.maximum(ST - K, 0.0) if option_type == "call" else np.maximum(K - ST, 0.0)
        discounted = disc * payoff
        price = float(discounted.mean())
        stderr = float(discounted.std(ddof=1) / sqrt(n_paths))
        n_effective = n_paths

    return {
        "price": price,
        "stderr": stderr,
        "ci95_lo": price - 1.96 * stderr,
        "ci95_hi": price + 1.96 * stderr,
        "n_paths": n_effective,
    }


def mc_convergence(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    q: float = 0.0,
    option_type: OptionType = "call",
    n_values: list[int] | None = None,
    antithetic: bool = True,
    seed: int | None = 42,
) -> dict[str, list]:
    """
    Estimadores MC a distintos n_paths — para visualizar convergencia y banda de ±1.96σ.

    Returns dict con keys "n", "price", "stderr", "ci95_lo", "ci95_hi".
    """
    if n_values is None:
        n_values = [500, 1_000, 2_500, 5_000, 10_000, 25_000, 50_000, 100_000]

    rows = [
        mc_price_european(S, K, T, r, sigma, q, option_type,
                          n_paths=n, antithetic=antithetic,
                          seed=None if seed is None else seed + i)
        for i, n in enumerate(n_values)
    ]
    return {
        "n": list(n_values),
        "price": [r_["price"] for r_ in rows],
        "stderr": [r_["stderr"] for r_ in rows],
        "ci95_lo": [r_["ci95_lo"] for r_ in rows],
        "ci95_hi": [r_["ci95_hi"] for r_ in rows],
    }
