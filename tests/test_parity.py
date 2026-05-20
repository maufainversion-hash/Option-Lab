"""
Tests de put-call parity y cotas de no-arbitraje.
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pytest
from math import exp
from pricing.black_scholes import bs_price_both
from education.parity import (
    parity_difference, synthetic_call, synthetic_put,
    implied_rate_from_parity, parity_check,
)
from education.bounds import (
    call_lower_bound, call_upper_bound,
    put_lower_bound, put_upper_bound,
    check_bounds,
)


class TestParity:
    """BS satisface parity por construcción — sanity check."""

    @pytest.mark.parametrize("S,K,T,r,sigma,q", [
        (100, 100, 0.5, 0.05, 0.2, 0.0),
        (100, 110, 1.0, 0.03, 0.30, 0.02),
        (42, 40, 0.5, 0.10, 0.20, 0.0),  # Hull 14.6
        (150, 100, 0.25, 0.06, 0.15, 0.01),
    ])
    def test_bs_satisfies_parity(self, S, K, T, r, sigma, q):
        C, P = bs_price_both(S, K, T, r, sigma, q)
        diff = parity_difference(C, P, S, K, T, r, q)
        assert abs(diff) < 1e-8

    def test_synthetic_call_matches_real(self):
        S, K, T, r, sigma, q = 100, 100, 0.5, 0.05, 0.2, 0.0
        C, P = bs_price_both(S, K, T, r, sigma, q)
        C_synthetic = synthetic_call(P, S, K, T, r, q)
        assert C == pytest.approx(C_synthetic, abs=1e-8)

    def test_synthetic_put_matches_real(self):
        S, K, T, r, sigma, q = 100, 100, 0.5, 0.05, 0.2, 0.0
        C, P = bs_price_both(S, K, T, r, sigma, q)
        P_synthetic = synthetic_put(C, S, K, T, r, q)
        assert P == pytest.approx(P_synthetic, abs=1e-8)


class TestImpliedRate:
    def test_recover_rate_from_bs_prices(self):
        """Si priceamos con r=5%, despejando r de C y P debe darnos 5%."""
        S, K, T, r, sigma, q = 100, 100, 0.5, 0.05, 0.2, 0.0
        C, P = bs_price_both(S, K, T, r, sigma, q)
        r_implied = implied_rate_from_parity(C, P, S, K, T, q)
        assert r_implied == pytest.approx(0.05, abs=1e-6)

    def test_invalid_quotes_raise(self):
        """Quotes que violan no-arb deben levantar. C-P > S e^(-qT) hace inner <= 0."""
        with pytest.raises(ValueError):
            # C-P = 200, S=100, K=100 → inner = (100 - 200)/100 = -1 < 0 → raises
            implied_rate_from_parity(C=200.0, P=0.0, S=100, K=100, T=0.5)


class TestBounds:
    def test_bs_call_within_bounds(self):
        S, K, T, r, sigma = 100, 100, 0.5, 0.05, 0.2
        C, _ = bs_price_both(S, K, T, r, sigma)
        lb = call_lower_bound(S, K, T, r)
        ub = call_upper_bound(S, T)
        assert lb <= C <= ub

    def test_bs_put_within_bounds(self):
        S, K, T, r, sigma = 100, 100, 0.5, 0.05, 0.2
        _, P = bs_price_both(S, K, T, r, sigma)
        lb = put_lower_bound(S, K, T, r)
        ub = put_upper_bound(K, T, r)
        assert lb <= P <= ub

    def test_check_bounds_flags_violation_low(self):
        result = check_bounds(0.01, 100, 50, 0.5, 0.05, 0, "call")
        assert not result["in_range"]

    def test_check_bounds_flags_violation_high(self):
        result = check_bounds(200.0, 100, 100, 0.5, 0.05, 0, "call")
        assert not result["in_range"]


class TestParityCheck:
    def test_clean_parity_not_violated(self):
        S, K, T, r, sigma, q = 100, 100, 0.5, 0.05, 0.2, 0.0
        C, P = bs_price_both(S, K, T, r, sigma, q)
        result = parity_check(C, P, S, K, T, r, q, tolerance=0.01)
        assert result["violated"] is False

    def test_dirty_parity_violated(self):
        """Si forzamos C muy alto, parity debe romperse."""
        S, K, T, r, sigma, q = 100, 100, 0.5, 0.05, 0.2, 0.0
        _, P = bs_price_both(S, K, T, r, sigma, q)
        C_inflated = 50.0
        result = parity_check(C_inflated, P, S, K, T, r, q, tolerance=0.10)
        assert result["violated"] is True
