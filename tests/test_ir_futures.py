from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from datetime import date
import pytest

from pricing.ir_futures import (
    day_count_factor, conversion_factor, cheapest_to_deliver,
    eurodollar_convexity_adjustment, duration_based_hedge_contracts,
)


class TestDayCount:
    def test_act_360_half_year(self):
        d1, d2 = date(2025, 1, 1), date(2025, 7, 1)
        assert day_count_factor(d1, d2, "ACT/360") == pytest.approx(181 / 360, abs=1e-10)

    def test_30_360_half_year(self):
        d1, d2 = date(2025, 1, 1), date(2025, 7, 1)
        assert day_count_factor(d1, d2, "30/360") == pytest.approx(0.5, abs=1e-10)

    def test_d2_before_d1_raises(self):
        with pytest.raises(ValueError):
            day_count_factor(date(2025, 7, 1), date(2025, 1, 1), "ACT/360")


class TestConversionFactor:
    def test_par_bond_at_6_pct(self):
        """Bono al 6% (cupón = ytm) cotiza al par → CF = 1.0."""
        cf = conversion_factor(coupon_rate=0.06, years_to_maturity=10.0, ytm=0.06)
        assert cf == pytest.approx(1.0, abs=1e-6)

    def test_premium_bond(self):
        """Cupón > 6% → bono cotiza premium → CF > 1."""
        cf = conversion_factor(coupon_rate=0.12, years_to_maturity=20.0)
        assert cf > 1.0
        assert 1.65 < cf < 1.75

    def test_discount_bond(self):
        cf = conversion_factor(coupon_rate=0.04, years_to_maturity=10.0)
        assert cf < 1.0


class TestCTD:
    def test_picks_lowest_cost(self):
        bonds = [
            {"name": "A", "quoted_price": 99.50, "conversion_factor": 1.0382},
            {"name": "B", "quoted_price": 143.50, "conversion_factor": 1.6929},
            {"name": "C", "quoted_price": 119.75, "conversion_factor": 1.2230},
        ]
        settlement = 93.25
        ctd = cheapest_to_deliver(bonds, settlement)
        assert ctd.bond_name == "B"

    def test_empty_bonds_raises(self):
        with pytest.raises(ValueError):
            cheapest_to_deliver([], 100.0)


class TestConvexityAdjustment:
    def test_zero_vol_zero_adjustment(self):
        assert eurodollar_convexity_adjustment(0.0, 5.0, 5.25) == 0.0

    def test_grows_with_T(self):
        adj_short = eurodollar_convexity_adjustment(0.012, 1.0, 1.25)
        adj_long = eurodollar_convexity_adjustment(0.012, 8.0, 8.25)
        assert adj_long > adj_short * 5


class TestDurationHedge:
    def test_hedge_neutralizes_parallel_shift(self):
        """Si N* es correcto, un shift paralelo no debería mover el P&L hedgeado."""
        P, D_P = 10_000_000, 6.8
        F, D_F, mult = 93.25, 9.2, 1000.0
        N = duration_based_hedge_contracts(P, D_P, F, D_F, mult)
        dy = 0.01
        delta_P = -P * D_P * dy
        delta_VF = -F * mult * D_F * dy
        net = delta_P - N * delta_VF
        assert abs(net) < 1.0
