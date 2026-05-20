"""
Tests del Monte Carlo / paths GBM.

Validaciones:
- GBM analítico: E[S_T] = S_0·e^(μT)  y  Var[S_T] = S_0²·e^(2μT)·(e^(σ²T) − 1)  (Hull 13.5)
- MC converge a BS (Hull 14.6 anchor)
- Antithetic variates reducen el stderr
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
import pytest

from pricing.black_scholes import bs_price
from pricing.monte_carlo import (
    simulate_gbm_paths,
    mc_price_european,
    mc_convergence,
)


HULL_14_6 = dict(S=42.0, K=40.0, T=0.5, r=0.10, sigma=0.20, q=0.0)


# ---------------------------------------------------------------
# Paths GBM — verificación de momentos analíticos
# ---------------------------------------------------------------
class TestGBMMoments:
    """Hull 13.5: S_T es log-normal con momentos conocidos."""

    def test_terminal_mean_matches_analytical(self):
        S0, mu, sigma, T = 100.0, 0.08, 0.20, 1.0
        paths = simulate_gbm_paths(S0, mu, sigma, T, steps=1, n_paths=200_000, seed=0)
        ST = paths[:, -1]
        analytical_mean = S0 * np.exp(mu * T)
        # tolerancia 1% del valor analítico
        assert ST.mean() == pytest.approx(analytical_mean, rel=0.01)

    def test_terminal_variance_matches_analytical(self):
        S0, mu, sigma, T = 100.0, 0.08, 0.20, 1.0
        paths = simulate_gbm_paths(S0, mu, sigma, T, steps=1, n_paths=200_000, seed=1)
        ST = paths[:, -1]
        analytical_var = (S0 ** 2) * np.exp(2 * mu * T) * (np.exp(sigma ** 2 * T) - 1)
        assert ST.var(ddof=1) == pytest.approx(analytical_var, rel=0.03)

    def test_paths_start_at_S0(self):
        paths = simulate_gbm_paths(100.0, 0.05, 0.2, 1.0, steps=50, n_paths=10, seed=2)
        assert np.all(paths[:, 0] == 100.0)

    def test_paths_shape(self):
        paths = simulate_gbm_paths(100.0, 0.05, 0.2, 1.0, steps=50, n_paths=100, seed=3)
        assert paths.shape == (100, 51)

    def test_seed_reproducibility(self):
        a = simulate_gbm_paths(100.0, 0.05, 0.2, 1.0, steps=20, n_paths=100, seed=42)
        b = simulate_gbm_paths(100.0, 0.05, 0.2, 1.0, steps=20, n_paths=100, seed=42)
        np.testing.assert_array_equal(a, b)

    def test_zero_vol_is_deterministic(self):
        """Con σ=0, GBM colapsa a crecimiento exponencial: S_T = S_0·e^(μT)."""
        paths = simulate_gbm_paths(100.0, 0.05, 0.0, 1.0, steps=10, n_paths=5, seed=7)
        expected_terminal = 100.0 * np.exp(0.05)
        np.testing.assert_allclose(paths[:, -1], expected_terminal, rtol=1e-12)


# ---------------------------------------------------------------
# MC pricing — convergencia a BS (Hull 14.6)
# ---------------------------------------------------------------
class TestMCvsBS:
    def test_mc_call_converges_to_bs(self):
        bs_c = bs_price(**HULL_14_6, option_type="call")
        result = mc_price_european(**HULL_14_6, option_type="call",
                                   n_paths=200_000, antithetic=True, seed=11)
        # ±0.05 con 200k antithetic
        assert result["price"] == pytest.approx(bs_c, abs=0.05)
        # BS analítico debe caer dentro del CI95
        assert result["ci95_lo"] <= bs_c <= result["ci95_hi"]

    def test_mc_put_converges_to_bs(self):
        bs_p = bs_price(**HULL_14_6, option_type="put")
        result = mc_price_european(**HULL_14_6, option_type="put",
                                   n_paths=200_000, antithetic=True, seed=13)
        assert result["price"] == pytest.approx(bs_p, abs=0.05)
        assert result["ci95_lo"] <= bs_p <= result["ci95_hi"]

    def test_mc_with_dividend_converges_to_bs(self):
        params = dict(S=100.0, K=100.0, T=1.0, r=0.05, sigma=0.30, q=0.03)
        bs_c = bs_price(**params, option_type="call")
        result = mc_price_european(**params, option_type="call",
                                   n_paths=200_000, antithetic=True, seed=17)
        assert result["price"] == pytest.approx(bs_c, abs=0.10)


# ---------------------------------------------------------------
# Antithetic variates — reducción de varianza
# ---------------------------------------------------------------
class TestAntithetic:
    def test_antithetic_reduces_stderr(self):
        """Antithetic debe dar un stderr menor que MC plain, mismos n_paths."""
        params = dict(**HULL_14_6, option_type="call", n_paths=20_000)
        plain = mc_price_european(**params, antithetic=False, seed=23)
        anti = mc_price_european(**params, antithetic=True, seed=23)
        assert anti["stderr"] < plain["stderr"]

    def test_antithetic_requires_even_n_in_paths(self):
        with pytest.raises(ValueError):
            simulate_gbm_paths(100.0, 0.05, 0.2, 1.0,
                               steps=10, n_paths=101, antithetic=True, seed=0)

    def test_antithetic_bumps_odd_n_in_pricer(self):
        """En el pricer somos tolerantes: subimos n_paths a par."""
        result = mc_price_european(**HULL_14_6, option_type="call",
                                   n_paths=101, antithetic=True, seed=29)
        assert result["n_paths"] == 102


# ---------------------------------------------------------------
# Convergencia (output para el chart)
# ---------------------------------------------------------------
class TestConvergence:
    def test_convergence_returns_aligned_arrays(self):
        out = mc_convergence(**HULL_14_6, option_type="call",
                             n_values=[1000, 5000, 10_000], seed=0)
        assert len(out["n"]) == len(out["price"]) == len(out["stderr"]) == 3

    def test_stderr_shrinks_with_n(self):
        out = mc_convergence(**HULL_14_6, option_type="call",
                             n_values=[1000, 10_000, 100_000], seed=31)
        # No es estrictamente monotónico por randomness, pero el último debe ser < primero
        assert out["stderr"][-1] < out["stderr"][0]


# ---------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------
class TestEdgeCases:
    def test_T_zero_returns_intrinsic_call(self):
        r = mc_price_european(50, 45, 0, 0.05, 0.2, 0, option_type="call",
                              n_paths=1000, seed=0)
        assert r["price"] == 5.0
        assert r["stderr"] == 0.0

    def test_T_zero_returns_intrinsic_put(self):
        r = mc_price_european(40, 45, 0, 0.05, 0.2, 0, option_type="put",
                              n_paths=1000, seed=0)
        assert r["price"] == 5.0

    def test_invalid_option_type_raises(self):
        with pytest.raises(ValueError):
            mc_price_european(100, 100, 0.5, 0.05, 0.2, 0, option_type="banana",
                              n_paths=100, seed=0)

    def test_negative_sigma_raises_in_paths(self):
        with pytest.raises(ValueError):
            simulate_gbm_paths(100.0, 0.05, -0.1, 1.0, steps=10, n_paths=10, seed=0)
