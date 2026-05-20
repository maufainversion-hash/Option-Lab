"""
Construcción de estrategias multi-leg.

Una estrategia es una lista de Legs. Cada Leg tiene:
- option_type: 'call' o 'put'  (o 'stock' para combos con subyacente)
- strike: K (irrelevante si stock)
- expiry: T en años
- quantity: positivo = long, negativo = short
- premium: precio pagado (positivo) o recibido (negativo si short)

Las funciones helper construyen estrategias clásicas de Hull Cap 11:
- bull/bear spreads
- straddle / strangle
- butterfly / iron condor
- collar / risk reversal
- calendar spread
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal

LegType = Literal["call", "put", "stock"]


@dataclass
class Leg:
    """Una pata de una estrategia."""
    option_type: LegType
    quantity: float  # +1 long, -1 short
    strike: float = 0.0  # ignorado si stock
    expiry: float = 0.0  # años — ignorado si stock
    premium: float = 0.0  # precio pagado (long) o recibido (short, valor negativo)

    def __post_init__(self) -> None:
        if self.option_type not in ("call", "put", "stock"):
            raise ValueError(f"option_type inválido: {self.option_type}")
        if self.option_type != "stock":
            if self.strike <= 0:
                raise ValueError(f"strike debe ser > 0, recibido {self.strike}")
            if self.expiry <= 0:
                raise ValueError(f"expiry debe ser > 0, recibido {self.expiry}")


@dataclass
class Strategy:
    """Combinación de patas con un nombre descriptivo."""
    name: str
    legs: list[Leg] = field(default_factory=list)
    description: str = ""

    def net_premium(self) -> float:
        """
        Premium neto pagado por la estrategia.
        Positivo = costo (debit), Negativo = crédito recibido.
        """
        return sum(leg.quantity * leg.premium for leg in self.legs)


# ============================================================
# Constructores de estrategias clásicas (Hull Cap 11)
# ============================================================

def long_call(K: float, T: float, premium: float, quantity: float = 1.0) -> Strategy:
    return Strategy(
        name=f"Long Call K={K:.2f}",
        legs=[Leg("call", quantity, K, T, premium)],
        description="Apuesta direccional alcista. Pérdida limitada al premium, ganancia ilimitada.",
    )


def long_put(K: float, T: float, premium: float, quantity: float = 1.0) -> Strategy:
    return Strategy(
        name=f"Long Put K={K:.2f}",
        legs=[Leg("put", quantity, K, T, premium)],
        description="Apuesta direccional bajista o seguro. Pérdida limitada al premium.",
    )


def covered_call(S: float, K: float, T: float, call_premium: float) -> Strategy:
    """Largo en acción + corto en call. Hull 11.1."""
    return Strategy(
        name=f"Covered Call K={K:.2f}",
        legs=[
            Leg("stock", 1.0, premium=S),
            Leg("call", -1.0, K, T, call_premium),
        ],
        description="Acción + venta de call. Generación de income. Techo en K + premium recibido.",
    )


def protective_put(S: float, K: float, T: float, put_premium: float) -> Strategy:
    """Largo en acción + largo en put. Hull 11.1."""
    return Strategy(
        name=f"Protective Put K={K:.2f}",
        legs=[
            Leg("stock", 1.0, premium=S),
            Leg("put", 1.0, K, T, put_premium),
        ],
        description="Seguro sobre la acción. Piso en K - premium pagado.",
    )


def bull_call_spread(
    K_low: float, K_high: float, T: float, premium_low: float, premium_high: float
) -> Strategy:
    """Long call ITM + short call OTM. Hull 11.2. Apuesta alcista con riesgo limitado."""
    if K_low >= K_high:
        raise ValueError(f"K_low ({K_low}) debe ser < K_high ({K_high})")
    return Strategy(
        name=f"Bull Call Spread {K_low:.2f}/{K_high:.2f}",
        legs=[
            Leg("call", 1.0, K_low, T, premium_low),
            Leg("call", -1.0, K_high, T, premium_high),
        ],
        description="Alcista con costo y riesgo capados. Máx profit = (K_high - K_low) - costo neto.",
    )


def bear_put_spread(
    K_low: float, K_high: float, T: float, premium_low: float, premium_high: float
) -> Strategy:
    """Long put OTM + short put más OTM. Hull 11.2. Apuesta bajista con riesgo limitado."""
    if K_low >= K_high:
        raise ValueError(f"K_low ({K_low}) debe ser < K_high ({K_high})")
    return Strategy(
        name=f"Bear Put Spread {K_high:.2f}/{K_low:.2f}",
        legs=[
            Leg("put", 1.0, K_high, T, premium_high),
            Leg("put", -1.0, K_low, T, premium_low),
        ],
        description="Bajista con costo y riesgo capados. Máx profit = (K_high - K_low) - costo neto.",
    )


def long_straddle(K: float, T: float, call_premium: float, put_premium: float) -> Strategy:
    """Long call + Long put mismo strike. Hull 11.3. Apuesta a vol alta sin dirección."""
    return Strategy(
        name=f"Long Straddle K={K:.2f}",
        legs=[
            Leg("call", 1.0, K, T, call_premium),
            Leg("put", 1.0, K, T, put_premium),
        ],
        description="Apuesta a movimiento grande en cualquier dirección. Costo = ambos premiums.",
    )


def long_strangle(
    K_put: float, K_call: float, T: float, put_premium: float, call_premium: float
) -> Strategy:
    """Long put OTM + Long call OTM. Hull 11.3. Versión barata del straddle."""
    if K_put >= K_call:
        raise ValueError(f"K_put ({K_put}) debe ser < K_call ({K_call})")
    return Strategy(
        name=f"Long Strangle {K_put:.2f}/{K_call:.2f}",
        legs=[
            Leg("put", 1.0, K_put, T, put_premium),
            Leg("call", 1.0, K_call, T, call_premium),
        ],
        description="Versión más barata del straddle. Requiere movimiento más grande para profit.",
    )


def long_butterfly_call(
    K_low: float, K_mid: float, K_high: float, T: float,
    p_low: float, p_mid: float, p_high: float,
) -> Strategy:
    """
    Long call K_low + 2x Short call K_mid + Long call K_high. Hull 11.3.
    Apuesta a vol BAJA, máx profit si S termina en K_mid.
    Strikes deben ser equidistantes para butterfly clásico.
    """
    if not (K_low < K_mid < K_high):
        raise ValueError(f"Strikes deben ser K_low < K_mid < K_high, recibido {K_low}/{K_mid}/{K_high}")
    return Strategy(
        name=f"Butterfly Call {K_low:.2f}/{K_mid:.2f}/{K_high:.2f}",
        legs=[
            Leg("call", 1.0, K_low, T, p_low),
            Leg("call", -2.0, K_mid, T, p_mid),
            Leg("call", 1.0, K_high, T, p_high),
        ],
        description="Apuesta a vol baja, S terminando cerca de K_mid. Riesgo y profit limitados.",
    )


def iron_condor(
    K_put_short: float, K_put_long: float, K_call_long: float, K_call_short: float,
    T: float,
    p_put_short: float, p_put_long: float, p_call_long: float, p_call_short: float,
) -> Strategy:
    """
    Short put + Long put OTM + Long call OTM + Short call.
    Apuesta a vol BAJA con crédito neto. Riesgo y profit limitados.
    """
    if not (K_put_long < K_put_short < K_call_short < K_call_long):
        raise ValueError("Strikes desordenados para iron condor")
    return Strategy(
        name="Iron Condor",
        legs=[
            Leg("put", 1.0, K_put_long, T, p_put_long),
            Leg("put", -1.0, K_put_short, T, p_put_short),
            Leg("call", -1.0, K_call_short, T, p_call_short),
            Leg("call", 1.0, K_call_long, T, p_call_long),
        ],
        description="Apuesta a que S queda entre los strikes shorts. Crédito neto.",
    )


def collar(
    S: float, K_put: float, K_call: float, T: float,
    put_premium: float, call_premium: float,
) -> Strategy:
    """Largo en acción + Long put + Short call. Range-bound bracket."""
    if K_put >= K_call:
        raise ValueError("K_put debe ser < K_call para collar")
    return Strategy(
        name=f"Collar {K_put:.2f}/{K_call:.2f}",
        legs=[
            Leg("stock", 1.0, premium=S),
            Leg("put", 1.0, K_put, T, put_premium),
            Leg("call", -1.0, K_call, T, call_premium),
        ],
        description="Acción + put (piso) + call short (techo). Bracket con costo bajo o cero.",
    )
