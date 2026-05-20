"""
Tests del árbol binomial.

Convergencia esperada (Hull Cap 12-14):
- CRR con n=500: ±0.01 vs BS para casos típicos
- LR con n=51: ±0.005 vs BS

Para americanas, validamos:
- Call americano sin dividendos == call europeo (Hull 10.2)
- Put americano > put europeo (early exercise tiene valor)
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pytest
from pricing.black_scholes import bs_price
from pricing.binomial import crr_price, leisen_reimer_price


HULL_14_6 = dict(S=42.0, K=40.0, T=0.5, r=0.10, sigma=0.20, q=0.0)


class TestCRRConvergence:
    def test_crr_converges_to_bs_call(self):
        bs_c = bs_price(**HULL_14_6, option_type="call")
        crr_c = crr_price(**HULL_14_6, n=500, option_type="call", exercise="european")
        assert crr_c == pytest.approx(bs_c, abs=0.02)

    def test_crr_converges_to_bs_put(self):
        bs_p = bs_price(**HULL_14_6, option_type="put")
        crr_p = crr_price(**HULL_14_6, n=500, option_type="put", exercise="european")
        assert crr_p == pytest.approx(bs_p, abs=0.02)


class TestLRConvergence:
    """LR converge mucho más rápido."""

    def test_lr_call_few_steps(self):
        bs_c = bs_price(**HULL_14_6, option_type="call")
        lr_c = leisen_reimer_price(**HULL_14_6, n=51, option_type="call", exercise="european")
        assert lr_c == pytest.approx(bs_c, abs=0.01)

    def test_lr_put_few_steps(self):
        bs_p = bs_price(**HULL_14_6, option_type="put")
        lr_p = leisen_reimer_price(**HULL_14_6, n=51, option_type="put", exercise="european")
        assert lr_p == pytest.approx(bs_p, abs=0.01)

    def test_lr_forces_odd_n(self):
        """Si pasamos n par, LR lo fuerza impar internamente. No debe romper."""
        price = leisen_reimer_price(**HULL_14_6, n=50, option_type="call")
        assert price > 0


class TestAmericanVsEuropean:
    def test_american_call_no_dividend_equals_european(self):
        """Hull 10.2: sin dividendos, no conviene ejercer un call americano antes del expiry."""
        eu = crr_price(100, 100, 1.0, 0.05, 0.30, 0.0, n=500, option_type="call", exercise="european")
        am = crr_price(100, 100, 1.0, 0.05, 0.30, 0.0, n=500, option_type="call", exercise="american")
        assert am == pytest.approx(eu, abs=0.01)

    def test_american_put_greater_than_european(self):
        """Put americano vale más por la opción de early exercise."""
        eu = crr_price(80, 100, 1.0, 0.05, 0.30, 0.0, n=500, option_type="put", exercise="european")
        am = crr_price(80, 100, 1.0, 0.05, 0.30, 0.0, n=500, option_type="put", exercise="american")
        assert am > eu

    def test_american_call_with_dividend_can_exceed_european(self):
        """Con dividendos, sí puede convenir ejercer un call americano antes."""
        eu = crr_price(100, 100, 1.0, 0.05, 0.30, 0.10, n=500, option_type="call", exercise="european")
        am = crr_price(100, 100, 1.0, 0.05, 0.30, 0.10, n=500, option_type="call", exercise="american")
        assert am >= eu


class TestBinomialEdgeCases:
    def test_T_zero_returns_intrinsic(self):
        assert crr_price(50, 45, 0, 0.05, 0.2, 0, n=10, option_type="call") == 5.0
        assert crr_price(40, 45, 0, 0.05, 0.2, 0, n=10, option_type="put") == 5.0

    def test_n_must_be_positive(self):
        with pytest.raises(ValueError):
            crr_price(100, 100, 0.5, 0.05, 0.2, 0, n=0, option_type="call")
