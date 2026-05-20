"""
Tests de Black-Scholes anclados en valores tabulados de Hull.

Referencia: Hull, "Options, Futures and Other Derivatives".
Ejemplo 14.6: S=42, K=40, T=0.5, r=0.10, σ=0.20, q=0
  - Call: 4.7594
  - Put:  0.8086
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pytest
from pricing.black_scholes import bs_price, bs_price_both, _d1_d2


HULL_14_6 = dict(S=42.0, K=40.0, T=0.5, r=0.10, sigma=0.20, q=0.0)


class TestHullExample14_6:
    """Replicación del Ejemplo 14.6 de Hull — single-source-of-truth para BS."""

    def test_call_price(self):
        c = bs_price(**HULL_14_6, option_type="call")
        assert c == pytest.approx(4.7594, abs=1e-3)

    def test_put_price(self):
        p = bs_price(**HULL_14_6, option_type="put")
        assert p == pytest.approx(0.8086, abs=1e-3)

    def test_both(self):
        c, p = bs_price_both(**HULL_14_6)
        assert c == pytest.approx(4.7594, abs=1e-3)
        assert p == pytest.approx(0.8086, abs=1e-3)

    def test_d1_d2(self):
        d1, d2 = _d1_d2(**HULL_14_6)
        # Hull cita d1 = 0.7693, d2 = 0.6278
        assert d1 == pytest.approx(0.7693, abs=1e-3)
        assert d2 == pytest.approx(0.6278, abs=1e-3)

    def test_put_call_parity(self):
        """C - P = S*e^(-qT) - K*e^(-rT)"""
        from math import exp
        c, p = bs_price_both(**HULL_14_6)
        lhs = c - p
        rhs = HULL_14_6["S"] * exp(-HULL_14_6["q"] * HULL_14_6["T"]) - \
              HULL_14_6["K"] * exp(-HULL_14_6["r"] * HULL_14_6["T"])
        assert lhs == pytest.approx(rhs, abs=1e-6)


class TestBSEdgeCases:
    def test_T_zero_call_intrinsic(self):
        assert bs_price(50, 45, 0, 0.05, 0.2, 0, "call") == 5.0
        assert bs_price(40, 45, 0, 0.05, 0.2, 0, "call") == 0.0

    def test_T_zero_put_intrinsic(self):
        assert bs_price(40, 45, 0, 0.05, 0.2, 0, "put") == 5.0
        assert bs_price(50, 45, 0, 0.05, 0.2, 0, "put") == 0.0

    def test_invalid_sigma(self):
        with pytest.raises(ValueError, match="sigma"):
            bs_price(100, 100, 0.5, 0.05, 0, 0, "call")

    def test_invalid_option_type(self):
        with pytest.raises(ValueError, match="option_type"):
            bs_price(100, 100, 0.5, 0.05, 0.2, 0, "banana")  # type: ignore

    def test_high_strike_call_low_value(self):
        """Call OTM lejos del strike vale poco."""
        c = bs_price(50, 100, 0.5, 0.05, 0.2, 0, "call")
        assert c < 0.5

    def test_low_strike_call_high_value(self):
        """Call ITM lejos del strike vale aprox. S - K*e^(-rT)."""
        from math import exp
        c = bs_price(100, 50, 0.5, 0.05, 0.2, 0, "call")
        # Lower bound: max(S - K*e^(-rT), 0)
        lower = 100 - 50 * exp(-0.05 * 0.5)
        assert c >= lower
        assert c <= 100  # upper bound: S


class TestDividends:
    """q > 0 reduce calls y aumenta puts (dividendos benefician al holder del subyacente)."""

    def test_call_decreases_with_dividend(self):
        c0 = bs_price(100, 100, 1.0, 0.05, 0.2, 0.0, "call")
        c5 = bs_price(100, 100, 1.0, 0.05, 0.2, 0.05, "call")
        assert c5 < c0

    def test_put_increases_with_dividend(self):
        p0 = bs_price(100, 100, 1.0, 0.05, 0.2, 0.0, "put")
        p5 = bs_price(100, 100, 1.0, 0.05, 0.2, 0.05, "put")
        assert p5 > p0
