"""
Tests de las griegas.

Validación cruzada: analíticas vs numéricas (bump-and-reprice) deben coincidir.
Más sanity checks sobre signos y rangos.
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pytest
from greeks.analytical import delta, gamma, vega, theta, rho, all_greeks
from greeks.numerical import (
    delta_numeric, gamma_numeric, vega_numeric, rho_numeric,
)


PARAMS = dict(S=100.0, K=100.0, T=0.5, r=0.05, sigma=0.25, q=0.0)


class TestAnalyticalVsNumerical:
    """Las analíticas deben coincidir con las numéricas hasta ~4 decimales."""

    def test_call_delta(self):
        a = delta(**PARAMS, option_type="call")
        n = delta_numeric(**PARAMS, option_type="call")
        assert a == pytest.approx(n, abs=1e-4)

    def test_put_delta(self):
        a = delta(**PARAMS, option_type="put")
        n = delta_numeric(**PARAMS, option_type="put")
        assert a == pytest.approx(n, abs=1e-4)

    def test_gamma(self):
        a = gamma(**PARAMS)
        n = gamma_numeric(**PARAMS, option_type="call")
        assert a == pytest.approx(n, abs=1e-3)

    def test_vega(self):
        a = vega(**PARAMS)
        n = vega_numeric(**PARAMS, option_type="call")
        assert a == pytest.approx(n, abs=1e-3)

    def test_rho_call(self):
        a = rho(**PARAMS, option_type="call")
        n = rho_numeric(**PARAMS, option_type="call")
        assert a == pytest.approx(n, abs=1e-3)


class TestGreekSigns:
    """Sanity checks sobre signos."""

    def test_call_delta_positive(self):
        assert 0 < delta(**PARAMS, option_type="call") < 1

    def test_put_delta_negative(self):
        assert -1 < delta(**PARAMS, option_type="put") < 0

    def test_gamma_always_positive(self):
        assert gamma(**PARAMS) > 0

    def test_vega_always_positive(self):
        assert vega(**PARAMS) > 0

    def test_call_theta_typically_negative(self):
        """Theta de call ATM/OTM sin dividendo es negativo (time decay)."""
        assert theta(**PARAMS, option_type="call") < 0

    def test_call_rho_positive(self):
        assert rho(**PARAMS, option_type="call") > 0

    def test_put_rho_negative(self):
        assert rho(**PARAMS, option_type="put") < 0


class TestGreekBehavior:
    """Comportamiento de las griegas según moneyness y tiempo."""

    def test_atm_call_delta_around_05(self):
        """Delta de call ATM ≈ 0.5 + un poquito por la drift."""
        d = delta(100, 100, 0.5, 0.05, 0.20, 0, "call")
        assert 0.55 < d < 0.65

    def test_deep_itm_call_delta_near_1(self):
        d = delta(150, 100, 0.5, 0.05, 0.20, 0, "call")
        assert d > 0.95

    def test_deep_otm_call_delta_near_0(self):
        d = delta(50, 100, 0.5, 0.05, 0.20, 0, "call")
        assert d < 0.05

    def test_gamma_peaks_at_money(self):
        """Gamma es más alta en ATM que en ITM/OTM."""
        g_atm = gamma(100, 100, 0.5, 0.05, 0.20, 0)
        g_otm = gamma(120, 100, 0.5, 0.05, 0.20, 0)
        g_itm = gamma(80, 100, 0.5, 0.05, 0.20, 0)
        assert g_atm > g_otm
        assert g_atm > g_itm

    def test_gamma_explodes_near_expiry_at_money(self):
        """Para ATM, gamma debe ser mucho más alta a T=0.01 que a T=1.0."""
        g_short = gamma(100, 100, 0.01, 0.05, 0.20, 0)
        g_long = gamma(100, 100, 1.00, 0.05, 0.20, 0)
        assert g_short > g_long * 5


class TestAllGreeksDict:
    def test_returns_all_five(self):
        g = all_greeks(**PARAMS, option_type="call")
        assert set(g.keys()) == {"delta", "gamma", "vega", "theta", "rho"}

    def test_call_vs_put_same_gamma_vega(self):
        """Gamma y Vega son iguales para call y put con mismos params."""
        gc = all_greeks(**PARAMS, option_type="call")
        gp = all_greeks(**PARAMS, option_type="put")
        assert gc["gamma"] == pytest.approx(gp["gamma"], abs=1e-10)
        assert gc["vega"] == pytest.approx(gp["vega"], abs=1e-10)
