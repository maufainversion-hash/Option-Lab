from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from math import exp

import pytest

from pricing.exotic_pricing import (
    index_option_price, currency_option_price, black_option_price,
    black_delta, fx_forward_price,
)
from pricing.black_scholes import bs_price


class TestHull_17_2_GarmanKohlhagen:
    """Hull Ejemplo 17.2: Currency call USD/GBP. Hull cita 4.3 cents = 0.0430."""
    def test_call_price(self):
        c = currency_option_price(
            S=1.6, K=1.6, T=4/12, r_domestic=0.08, r_foreign=0.11, sigma=0.141,
            option_type="call",
        )
        assert c == pytest.approx(0.0430, abs=0.001)


class TestHull_18_1_BlackModel:
    """Hull Ejemplo 18.1: Futures option sobre crude oil."""
    def test_call_price(self):
        c = black_option_price(F=20, K=20, T=4/12, r=0.10, sigma=0.25,
                                option_type="call")
        assert c == pytest.approx(1.116, abs=0.005)

    def test_put_call_parity_for_futures(self):
        """Para futures options: c - p = e^(-rT) · (F - K)."""
        F, K, T, r, sigma = 20, 20, 4/12, 0.10, 0.25
        c = black_option_price(F, K, T, r, sigma, "call")
        p = black_option_price(F, K, T, r, sigma, "put")
        assert (c - p) == pytest.approx(exp(-r * T) * (F - K), abs=1e-8)


class TestBlackVsBSM:
    def test_black_equals_bsm_with_q_equals_r(self):
        """Black(F,K,T,r,σ) ≡ BSM(F,K,T,r,σ,q=r)."""
        F, K, T, r, sigma = 100, 105, 0.5, 0.05, 0.25
        black = black_option_price(F, K, T, r, sigma, "call")
        bsm = bs_price(F, K, T, r, sigma, q=r, option_type="call")
        assert black == pytest.approx(bsm, abs=1e-10)


class TestFXForward:
    def test_covered_interest_parity(self):
        """F = S · e^((r_d − r_f) T)."""
        S, T, r_d, r_f = 1.6, 1.0, 0.08, 0.11
        F = fx_forward_price(S, T, r_d, r_f)
        assert F < S  # r_d < r_f → forward de doméstica al revés
        assert F == pytest.approx(S * exp((r_d - r_f) * T), abs=1e-10)


class TestBlackDelta:
    def test_delta_call_in_range(self):
        d = black_delta(20, 20, 4/12, 0.10, 0.25, "call")
        assert 0 < d < exp(-0.10 * 4/12)

    def test_delta_put_negative(self):
        d = black_delta(20, 20, 4/12, 0.10, 0.25, "put")
        assert -exp(-0.10 * 4/12) < d < 0


class TestIndexOption:
    def test_index_call_below_no_div(self):
        """Index call con q > 0 vale menos que sin dividendos."""
        with_q = index_option_price(4500, 4500, 0.5, 0.05, 0.20, 0.02, "call")
        no_q = index_option_price(4500, 4500, 0.5, 0.05, 0.20, 0.0, "call")
        assert with_q < no_q

    def test_index_put_above_no_div(self):
        """Index put con q > 0 vale más que sin dividendos."""
        with_q = index_option_price(4500, 4500, 0.5, 0.05, 0.20, 0.02, "put")
        no_q = index_option_price(4500, 4500, 0.5, 0.05, 0.20, 0.0, "put")
        assert with_q > no_q
