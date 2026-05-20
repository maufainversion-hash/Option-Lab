from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pytest

from pricing.forward_valuation import value_forward_position


def test_hull_5_3_style():
    """Hull-style example: S=$25, K=$24, r=5%, T=0.5.
    F₀ = 25·e^0.025 = 25.6329 → f = (25.6329 − 24)·e^(-0.025) ≈ 1.5926."""
    result = value_forward_position(
        spot_price=25.0,
        delivery_price=24.0,
        risk_free_rate=0.05,
        time_to_maturity=0.5,
    )
    assert result["position_value"] == pytest.approx(1.5926, abs=0.001)
    assert result["forward_price"] == pytest.approx(25.6329, abs=0.001)
    assert result["discount_factor"] == pytest.approx(0.9753, abs=0.001)
    assert result["position_value_short"] == pytest.approx(-1.5926, abs=0.001)


def test_zero_value_at_inception():
    """Forward should have zero value when F₀ ≈ K (delivery_price = S·e^(rT))."""
    result = value_forward_position(
        spot_price=100.0,
        delivery_price=100.0 * 1.02020134,  # = 100 · e^(0.02 × 1)
        risk_free_rate=0.02,
        time_to_maturity=1.0,
    )
    assert abs(result["position_value"]) < 0.001


def test_negative_value_for_long_when_F_below_K():
    """Si F₀ < K, posición long tiene valor negativo (y short positivo)."""
    result = value_forward_position(
        spot_price=95.0,
        delivery_price=100.0,
        risk_free_rate=0.05,
        time_to_maturity=0.5,
    )
    assert result["position_value"] < 0
    assert result["position_value_short"] > 0
    # Simetría exacta
    assert result["position_value"] == pytest.approx(-result["position_value_short"], abs=1e-10)


def test_dividend_yield_via_negative_carry():
    """Para acciones con dividendos, pasar cost_of_carry = -q ajusta F₀ correctamente.
    F₀ = S · e^((r − q) T). Con S=100, r=5%, q=3%, T=1 → F₀ ≈ 102.02."""
    result = value_forward_position(
        spot_price=100.0,
        delivery_price=100.0,
        risk_free_rate=0.05,
        time_to_maturity=1.0,
        cost_of_carry=-0.03,  # -q
    )
    assert result["forward_price"] == pytest.approx(102.0201, abs=0.01)
