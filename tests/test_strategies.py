"""
Tests de estrategias multi-leg.

Validamos:
- Construcción correcta (legs, quantities, signs).
- Payoffs analíticos en puntos conocidos.
- Net greeks aditivas.
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
import pytest

from pricing.black_scholes import bs_price
from strategies import legs as L
from strategies.payoff import (
    payoff_at_expiry, breakeven_points, max_profit_loss,
)
from strategies.aggregator import net_greeks


class TestLongCall:
    def test_payoff_at_strike_is_minus_premium(self):
        strat = L.long_call(K=100, T=0.5, premium=5)
        payoff = payoff_at_expiry(strat, np.array([100.0]))
        assert payoff[0] == pytest.approx(-5.0)

    def test_payoff_above_strike(self):
        strat = L.long_call(K=100, T=0.5, premium=5)
        payoff = payoff_at_expiry(strat, np.array([120.0]))
        assert payoff[0] == pytest.approx(15.0)  # 120-100-5

    def test_payoff_below_strike(self):
        strat = L.long_call(K=100, T=0.5, premium=5)
        payoff = payoff_at_expiry(strat, np.array([80.0]))
        assert payoff[0] == pytest.approx(-5.0)  # premium perdido

    def test_breakeven_is_K_plus_premium(self):
        strat = L.long_call(K=100, T=0.5, premium=5)
        S_range = np.linspace(50, 150, 500)
        bes = breakeven_points(strat, S_range)
        assert len(bes) == 1
        assert bes[0] == pytest.approx(105.0, abs=0.5)


class TestLongPut:
    def test_payoff_at_strike_is_minus_premium(self):
        strat = L.long_put(K=100, T=0.5, premium=5)
        payoff = payoff_at_expiry(strat, np.array([100.0]))
        assert payoff[0] == pytest.approx(-5.0)

    def test_breakeven_is_K_minus_premium(self):
        strat = L.long_put(K=100, T=0.5, premium=5)
        S_range = np.linspace(50, 150, 500)
        bes = breakeven_points(strat, S_range)
        assert len(bes) == 1
        assert bes[0] == pytest.approx(95.0, abs=0.5)


class TestStraddle:
    def test_straddle_two_breakevens(self):
        strat = L.long_straddle(K=100, T=0.5, call_premium=5, put_premium=5)
        S_range = np.linspace(50, 150, 500)
        bes = breakeven_points(strat, S_range)
        assert len(bes) == 2
        # K ± (call_premium + put_premium) = 100 ± 10
        assert bes[0] == pytest.approx(90.0, abs=0.5)
        assert bes[1] == pytest.approx(110.0, abs=0.5)

    def test_straddle_max_loss_at_strike(self):
        strat = L.long_straddle(K=100, T=0.5, call_premium=5, put_premium=5)
        payoff = payoff_at_expiry(strat, np.array([100.0]))
        assert payoff[0] == pytest.approx(-10.0)  # ambos premiums perdidos


class TestBullCallSpread:
    def test_max_profit_is_spread_minus_cost(self):
        # K_low=100 long @5, K_high=110 short @2 → costo neto = 3, máx profit = 10-3 = 7
        strat = L.bull_call_spread(100, 110, 0.5, premium_low=5, premium_high=2)
        S_range = np.linspace(80, 130, 500)
        max_p, max_l = max_profit_loss(strat, S_range)
        assert max_p == pytest.approx(7.0, abs=0.1)
        assert max_l == pytest.approx(-3.0, abs=0.1)

    def test_breakeven_is_K_low_plus_net_cost(self):
        strat = L.bull_call_spread(100, 110, 0.5, premium_low=5, premium_high=2)
        S_range = np.linspace(80, 130, 500)
        bes = breakeven_points(strat, S_range)
        assert len(bes) == 1
        assert bes[0] == pytest.approx(103.0, abs=0.5)


class TestButterfly:
    def test_butterfly_max_profit_at_middle_strike(self):
        # 95/100/105 calls. premiums típicos para vol 25%, T=0.5, r=5%
        T, r, sigma = 0.5, 0.05, 0.25
        S = 100
        p_low = bs_price(S, 95, T, r, sigma, 0, "call")
        p_mid = bs_price(S, 100, T, r, sigma, 0, "call")
        p_high = bs_price(S, 105, T, r, sigma, 0, "call")
        strat = L.long_butterfly_call(95, 100, 105, T, p_low, p_mid, p_high)
        S_range = np.linspace(80, 120, 500)
        max_p, max_l = max_profit_loss(strat, S_range)
        # Costo neto debe ser bajo positivo, máx profit ~ spread (5)
        net = strat.net_premium()
        assert 0 < net < 5  # debit pequeño
        assert max_p > 0
        # Profit cerca de K_mid debe ser positivo
        payoff_at_100 = payoff_at_expiry(strat, np.array([100.0]))[0]
        assert payoff_at_100 > 0


class TestCoveredCall:
    def test_covered_call_caps_upside(self):
        # Acción a 100 + short call K=110 premium 3
        strat = L.covered_call(S=100, K=110, T=0.5, call_premium=3)
        # Si S termina en 150: action = 150, call short pierde 40, premium cobrado +3
        # P&L = 150 - 100 (costo accion) + 3 (premium) - max(150-110, 0) = 50 + 3 - 40 = 13
        # (que es K - S0 + premium = 110 - 100 + 3 = 13)
        payoff = payoff_at_expiry(strat, np.array([150.0]))
        assert payoff[0] == pytest.approx(13.0, abs=0.1)

    def test_covered_call_at_strike(self):
        strat = L.covered_call(S=100, K=110, T=0.5, call_premium=3)
        payoff = payoff_at_expiry(strat, np.array([110.0]))
        # 110 - 100 + 3 - 0 = 13
        assert payoff[0] == pytest.approx(13.0, abs=0.1)


class TestNetGreeks:
    def test_long_call_delta_positive(self):
        strat = L.long_call(K=100, T=0.5, premium=5)
        ng = net_greeks(strat, S=100, t=0.0, r=0.05, sigma=0.25)
        assert ng["delta"] > 0

    def test_straddle_delta_near_zero_at_strike(self):
        """Straddle ATM tiene delta ≈ 0 (call delta + put delta ~ 1 + (-1) = 0)."""
        strat = L.long_straddle(K=100, T=0.5, call_premium=5, put_premium=5)
        ng = net_greeks(strat, S=100, t=0.0, r=0.05, sigma=0.25)
        # En ATM el delta no es exactamente 0 por la drift en BS, pero está cerca
        assert abs(ng["delta"]) < 0.2

    def test_long_straddle_long_vega(self):
        strat = L.long_straddle(K=100, T=0.5, call_premium=5, put_premium=5)
        ng = net_greeks(strat, S=100, t=0.0, r=0.05, sigma=0.25)
        assert ng["vega"] > 0
        assert ng["gamma"] > 0

    def test_iron_condor_credit_position(self):
        T, r, sigma, S0 = 0.5, 0.05, 0.25, 100
        ps = bs_price(S0, 95, T, r, sigma, 0, "put")
        pl = bs_price(S0, 90, T, r, sigma, 0, "put")
        cl = bs_price(S0, 110, T, r, sigma, 0, "call")
        cs = bs_price(S0, 105, T, r, sigma, 0, "call")
        strat = L.iron_condor(95, 90, 110, 105, T, ps, pl, cl, cs)
        # Credit neto → premium neto debe ser negativo
        assert strat.net_premium() < 0
