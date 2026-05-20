from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from math import exp

import numpy as np
import pytest

from pricing.currency_swaps import (
    value_currency_swap_bonds,
    value_currency_swap_forwards,
    calculate_forward_fx_rate,
)


# Inputs comunes — Hull 7.5 / UADE slide U4 p.24
TIMES = [1.0, 2.0, 3.0]
DOM_ZEROS = [0.09, 0.09, 0.09]
FOR_ZEROS = [0.04, 0.04, 0.04]
KWARGS = dict(
    notional_domestic=10_000_000,
    notional_foreign=1_200_000_000,
    rate_domestic=0.09,
    rate_foreign=0.04,
    swap_rate_domestic=0.08,
    swap_rate_foreign=0.05,
    spot_exchange_rate=110.0,
    payment_times=TIMES,
    domestic_zero_rates=DOM_ZEROS,
    foreign_zero_rates=FOR_ZEROS,
    receive_foreign=True,
)


class TestBondsMethodHull75:
    def test_bond_domestic(self):
        result = value_currency_swap_bonds(**KWARGS)
        # B_d ≈ 9.6439M USD
        assert result["bond_domestic"] == pytest.approx(9_643_860, abs=10_000)

    def test_bond_foreign(self):
        result = value_currency_swap_bonds(**KWARGS)
        # B_f ≈ 1,230.55M JPY
        assert result["bond_foreign"] == pytest.approx(1_230_554_000, abs=100_000)

    def test_swap_value(self):
        """Hull 7.5: V = B_f/spot − B_d ≈ $1,543,000."""
        result = value_currency_swap_bonds(**KWARGS)
        assert result["swap_value"] == pytest.approx(1_543_000, abs=5_000)

    def test_position_flip_negates(self):
        """receive_foreign=False debería invertir el signo."""
        r1 = value_currency_swap_bonds(**KWARGS)
        kw = dict(KWARGS, receive_foreign=False)
        r2 = value_currency_swap_bonds(**kw)
        assert r2["swap_value"] == pytest.approx(-r1["swap_value"], abs=1.0)


class TestForwardsMethodHull75:
    def test_swap_value_matches_bonds(self):
        """Hull 7.5: el método de forwards debe dar el MISMO valor que bonds."""
        result = value_currency_swap_forwards(**KWARGS)
        assert result["swap_value"] == pytest.approx(1_543_000, abs=5_000)

    def test_forward_rates_decreasing(self):
        """Con r_domestic (USD) > r_foreign (JPY), la moneda doméstica se deprecia
        en el forward → menos yen por dólar a medida que crece T."""
        result = value_currency_swap_forwards(**KWARGS)
        Fs = result["forward_rates"]
        assert Fs[0] > Fs[1] > Fs[2]
        # Sanity: F(1) = 110 · e^(0.04 − 0.09) ≈ 104.64
        assert Fs[0] == pytest.approx(104.64, abs=0.05)


class TestMethodsAgreeByNoArbitrage:
    def test_methods_match_simple(self):
        """Para un caso simple: bonds method == forwards method (no-arbitrage)."""
        kw = dict(
            notional_domestic=1.0,
            notional_foreign=100.0,
            rate_domestic=0.10,
            rate_foreign=0.05,
            swap_rate_domestic=0.10,
            swap_rate_foreign=0.05,
            spot_exchange_rate=100.0,
            payment_times=[1.0],
            domestic_zero_rates=[0.10],
            foreign_zero_rates=[0.05],
            receive_foreign=True,
        )
        v_bonds = value_currency_swap_bonds(**kw)["swap_value"]
        v_fwds = value_currency_swap_forwards(**kw)["swap_value"]
        assert v_bonds == pytest.approx(v_fwds, abs=1e-6)


class TestForwardFxRate:
    def test_irp_formula(self):
        """F = S · e^((r_d − r_f) · T) bajo convención 'domestic per foreign'."""
        spot = 0.009091
        forward = calculate_forward_fx_rate(spot, 0.09, 0.04, 1.0)
        expected = spot * np.exp((0.09 - 0.04) * 1.0)
        assert forward == pytest.approx(expected, abs=1e-9)

    def test_zero_time_returns_spot(self):
        assert calculate_forward_fx_rate(1.5, 0.05, 0.03, 0.0) == 1.5
