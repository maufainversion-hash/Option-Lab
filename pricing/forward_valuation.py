"""
Forward contract position valuation. Hull (5.4):

    f = (F₀ − K) · e^(−rT)

donde:
- F₀: precio forward actual para vencimiento T
- K: delivery price pactado en el contrato
- r: tasa risk-free (continuous compounding)
- T: tiempo al vencimiento en años
- f: valor de la posición long (negativo si short)

Si el usuario no observa F₀ directamente, la función lo calcula del spot:
F₀ = S₀ · e^((r + cost_of_carry) · T).
"""
from __future__ import annotations

import numpy as np


def value_forward_position(
    spot_price: float,
    delivery_price: float,
    risk_free_rate: float,
    time_to_maturity: float,
    cost_of_carry: float = 0.0,
) -> dict:
    """
    Calcula el valor de una posición forward existente.

    Args:
        spot_price: Precio spot actual del subyacente.
        delivery_price: Delivery price K pactado en el contrato forward.
        risk_free_rate: Tasa libre de riesgo continua anualizada.
        time_to_maturity: Tiempo al vencimiento en años.
        cost_of_carry: Storage costs menos income (continuo, anual).
            Para acciones con dividendos: usar -dividend_yield.

    Returns:
        dict con:
            - forward_price (F₀): precio forward actual
            - position_value (f): valor de la posición LONG
            - position_value_short: valor de la posición SHORT (= -f)
            - discount_factor: e^(-rT)

    Ejemplo (Hull-style con r=5%):
        >>> # S=25, K=24, r=5%, T=0.5 → F₀ ≈ 25.633, f ≈ 1.5926
        >>> result = value_forward_position(25, 24, 0.05, 0.5)
        >>> round(result['position_value'], 4)
        1.5926
    """
    forward_price = spot_price * np.exp((risk_free_rate + cost_of_carry) * time_to_maturity)
    discount_factor = np.exp(-risk_free_rate * time_to_maturity)
    position_value = (forward_price - delivery_price) * discount_factor

    return {
        "forward_price": float(forward_price),
        "position_value": float(position_value),
        "position_value_short": float(-position_value),
        "discount_factor": float(discount_factor),
    }
