"""
Unidad VIII · Estrategias multi-leg (Hull Cap 12).
"""
from __future__ import annotations

import numpy as np
import streamlit as st

from strategies import legs as L
from strategies.payoff import max_profit_loss, breakeven_points
from strategies.aggregator import net_greeks
from ui.charts.payoff_diagram import payoff_chart


def render() -> None:
    st.markdown(
        '<h1 style="margin:0;font-weight:600;">Unidad VIII · Estrategias multi-leg</h1>'
        '<div style="color:var(--text-muted);font-size:13px;margin-bottom:20px;">'
        'Hull Cap 12. Bull/bear spreads, straddle, strangle, butterfly, iron condor.'
        '</div>', unsafe_allow_html=True)

    st.header("Estrategias multi-leg")
    st.markdown(
        """
    Combinando varias opciones podés construir payoffs arbitrarios. Hull Cap 11 cubre las
    principales. Acá las podés armar y ver el payoff al vencimiento + cómo se ve hoy (vía BS).
    """
    )

    strat_name = st.selectbox(
        "Elegí una estrategia",
        [
            "Long Call",
            "Long Put",
            "Covered Call",
            "Protective Put",
            "Bull Call Spread",
            "Bear Put Spread",
            "Long Straddle",
            "Long Strangle",
            "Butterfly (calls)",
            "Iron Condor",
            "Collar",
        ],
    )

    # Parámetros de mercado del tab — DENTRO del tab, no en sidebar global
    with st.expander("⚙️  Parámetros de mercado", expanded=True):
        ec1, ec2, ec3, ec4, ec5 = st.columns(5)
        S0 = ec1.number_input("Spot", min_value=1.0, value=100.0, step=1.0, key="strat_S")
        sigma_strat = ec2.slider("Vol σ", 0.05, 1.0, 0.25, 0.01, key="strat_sigma")
        r_strat = ec3.slider("Tasa r", 0.0, 0.5, 0.05, 0.005, key="strat_r")
        q_strat = ec4.slider("Div yield q", 0.0, 0.20, 0.0, 0.005, key="strat_q")
        T_strat = ec5.slider("T (años)", 0.05, 2.0, 0.5, 0.05, key="strat_T")

    # Construcción de la estrategia con BS premiums por default
    def bs_call(K_):
        return bs_price(S0, K_, T_strat, r_strat, sigma_strat, q_strat, "call")

    def bs_put(K_):
        return bs_price(S0, K_, T_strat, r_strat, sigma_strat, q_strat, "put")

    if strat_name == "Long Call":
        K = st.slider("Strike", S0 * 0.5, S0 * 1.5, S0, 0.5)
        strat = L.long_call(K, T_strat, bs_call(K))
    elif strat_name == "Long Put":
        K = st.slider("Strike", S0 * 0.5, S0 * 1.5, S0, 0.5)
        strat = L.long_put(K, T_strat, bs_put(K))
    elif strat_name == "Covered Call":
        K = st.slider("Strike Call (vendido)", S0 * 1.0, S0 * 1.5, S0 * 1.1, 0.5)
        strat = L.covered_call(S0, K, T_strat, bs_call(K))
    elif strat_name == "Protective Put":
        K = st.slider("Strike Put (comprado)", S0 * 0.5, S0 * 1.0, S0 * 0.95, 0.5)
        strat = L.protective_put(S0, K, T_strat, bs_put(K))
    elif strat_name == "Bull Call Spread":
        c1, c2 = st.columns(2)
        K_low = c1.slider("K_low (long)", S0 * 0.7, S0 * 1.0, S0 * 0.95, 0.5)
        K_high = c2.slider("K_high (short)", S0 * 1.0, S0 * 1.4, S0 * 1.1, 0.5)
        strat = L.bull_call_spread(K_low, K_high, T_strat, bs_call(K_low), bs_call(K_high))
    elif strat_name == "Bear Put Spread":
        c1, c2 = st.columns(2)
        K_low = c1.slider("K_low (short)", S0 * 0.6, S0 * 1.0, S0 * 0.9, 0.5)
        K_high = c2.slider("K_high (long)", S0 * 1.0, S0 * 1.3, S0 * 1.05, 0.5)
        strat = L.bear_put_spread(K_low, K_high, T_strat, bs_put(K_low), bs_put(K_high))
    elif strat_name == "Long Straddle":
        K = st.slider("Strike (mismo para call y put)", S0 * 0.7, S0 * 1.3, S0, 0.5)
        strat = L.long_straddle(K, T_strat, bs_call(K), bs_put(K))
    elif strat_name == "Long Strangle":
        c1, c2 = st.columns(2)
        K_put = c1.slider("K_put (OTM)", S0 * 0.6, S0 * 0.99, S0 * 0.9, 0.5)
        K_call = c2.slider("K_call (OTM)", S0 * 1.01, S0 * 1.4, S0 * 1.1, 0.5)
        strat = L.long_strangle(K_put, K_call, T_strat, bs_put(K_put), bs_call(K_call))
    elif strat_name == "Butterfly (calls)":
        c1, c2, c3 = st.columns(3)
        K_low = c1.slider("K_low", S0 * 0.7, S0 * 0.95, S0 * 0.9, 0.5)
        K_mid = c2.slider("K_mid", S0 * 0.95, S0 * 1.05, S0, 0.5)
        K_high = c3.slider("K_high", S0 * 1.05, S0 * 1.3, S0 * 1.1, 0.5)
        strat = L.long_butterfly_call(
            K_low, K_mid, K_high, T_strat,
            bs_call(K_low), bs_call(K_mid), bs_call(K_high),
        )
    elif strat_name == "Iron Condor":
        c1, c2, c3, c4 = st.columns(4)
        K_pl = c1.slider("Put long", S0 * 0.6, S0 * 0.85, S0 * 0.85, 0.5)
        K_ps = c2.slider("Put short", S0 * 0.85, S0 * 0.99, S0 * 0.95, 0.5)
        K_cs = c3.slider("Call short", S0 * 1.01, S0 * 1.15, S0 * 1.05, 0.5)
        K_cl = c4.slider("Call long", S0 * 1.15, S0 * 1.4, S0 * 1.15, 0.5)
        strat = L.iron_condor(
            K_ps, K_pl, K_cl, K_cs, T_strat,
            bs_put(K_ps), bs_put(K_pl), bs_call(K_cl), bs_call(K_cs),
        )
    elif strat_name == "Collar":
        c1, c2 = st.columns(2)
        K_put = c1.slider("Put (piso)", S0 * 0.7, S0 * 0.99, S0 * 0.95, 0.5)
        K_call = c2.slider("Call (techo)", S0 * 1.01, S0 * 1.3, S0 * 1.05, 0.5)
        strat = L.collar(S0, K_put, K_call, T_strat, bs_put(K_put), bs_call(K_call))

    # Render
    S_range = np.linspace(S0 * 0.5, S0 * 1.5, 200)
    fig = payoff_chart(strat, S_current=S0, S_range=S_range,
                       sigma=sigma_strat, r=r_strat, q=q_strat, show_now=True)
    st.plotly_chart(fig, use_container_width=True)
    st.caption(f"💡 {strat.description}")

    # Métricas
    max_p, max_l = max_profit_loss(strat, S_range)
    bes = breakeven_points(strat, S_range)
    net_prem = strat.net_premium()

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Premium neto",
              f"${net_prem:+.2f}",
              help="Positivo = debit (paga). Negativo = credit (cobra).")
    m2.metric("Máx profit (en rango)", f"${max_p:+.2f}")
    m3.metric("Máx loss", f"${max_l:+.2f}")
    m4.metric("Breakevens", ", ".join(f"${be:.2f}" for be in bes) if bes else "—")

    # Greeks netas del combo
    st.subheader("Greeks netas del combo (en spot actual, hoy)")
    ng = net_greeks(strat, S0, 0.0, r_strat, sigma_strat, q_strat)
    g1, g2, g3, g4, g5 = st.columns(5)
    g1.metric("Δ Delta", f"{ng['delta']:+.4f}")
    g2.metric("Γ Gamma", f"{ng['gamma']:+.4f}")
    g3.metric("ν Vega", f"{ng['vega']:+.2f}")
    g4.metric("Θ Theta/año", f"{ng['theta']:+.2f}")
    g5.metric("ρ Rho", f"{ng['rho']:+.2f}")
