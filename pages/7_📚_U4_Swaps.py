from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from pricing.swaps import swap_value_via_bonds, swap_par_rate
from ui.styling import inject_premium_css
from ui.components.header_strip import render_header_strip

st.set_page_config(page_title="U4 — Swaps", page_icon="🔁", layout="wide",
                   initial_sidebar_state="collapsed")
inject_premium_css()
render_header_strip()

st.markdown(
    '<h1 style="margin:0;font-weight:600;">Unidad IV · Swaps</h1>'
    '<div style="color:var(--text-muted);font-size:13px;margin-bottom:20px;">'
    'Hull Cap 7. Plain vanilla IR swap, valuación via bonds, par swap rate.'
    '</div>', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["Mecánica + cashflows", "Valuación (bond approach)"])

with tab1:
    st.markdown(r"""
**Plain vanilla IR swap**: dos contrapartes intercambian flujos basados en un notional.
- Una paga **fixed** (R_fix).
- La otra paga **floating** (típicamente LIBOR/SOFR + spread).

En cada fecha de pago, neta el diferencial. No se intercambia el notional (es un *notional*).

Net cashflow de quien **recibe fijo** en t: $L \cdot (R_{fix} - R_{float,t-1}) \cdot \tau$
""")
    c1, c2, c3, c4 = st.columns(4)
    L = c1.number_input("Notional", value=100_000_000.0, step=1_000_000.0)
    R_fix = c2.number_input("R_fix anual", value=0.05, step=0.005, format="%.4f")
    n_periods = c3.number_input("Períodos", min_value=1, value=6, step=1)
    accrual = c4.number_input("Accrual (años)", min_value=0.05, value=0.5, step=0.25)

    rng = np.random.RandomState(7)
    floatings = 0.04 + 0.01 * np.cumsum(rng.normal(0, 0.3, n_periods))
    floatings = np.clip(floatings, 0.01, 0.10)
    nets_receive_fix = L * (R_fix - floatings) * accrual

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[f"T{i+1}" for i in range(n_periods)], y=nets_receive_fix,
        marker_color=["#3fb950" if v >= 0 else "#f85149" for v in nets_receive_fix],
        name="Net cashflow (recibe fijo)",
    ))
    fig.add_hline(y=0, line=dict(color="#8b949e"))
    fig.update_layout(template="plotly_dark", height=380,
                      title="Cashflows netos para quien recibe fijo",
                      margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(
        {
            "Período": [f"T{i+1}" for i in range(n_periods)],
            "Float observada": [f"{x:.4%}" for x in floatings],
            "Δ vs Fix": [f"{R_fix - x:+.4%}" for x in floatings],
            "Net CF (recibe fijo)": [f"{v:+,.0f}" for v in nets_receive_fix],
        },
        use_container_width=True, hide_index=True,
    )

with tab2:
    st.markdown(r"""
**Valuación por bond approach** (Hull 7.7):

$$V_{swap}^{recibe\_fijo} = B_{fix} - B_{flt}$$

donde B_fix es el PV del bono fijo (cupones + notional al final) y B_flt es el PV del
bono flotante (que vale notional + próximo cupón conocido, descontado).
""")
    c1, c2, c3 = st.columns(3)
    L2 = c1.number_input("Notional", value=100_000_000.0, step=1_000_000.0, key="vs_L")
    R_fix2 = c2.number_input("R_fix", value=0.06, step=0.005, format="%.4f", key="vs_Rfix")
    R_float_set = c3.number_input("Próx. tasa flotante seteada", value=0.057, step=0.001, format="%.4f")

    c4, c5 = st.columns(2)
    accrual2 = c4.number_input("Accrual", value=0.5, step=0.25, key="vs_acc")
    time_since = c5.number_input("Tiempo desde último reset", value=0.0, step=0.05, key="vs_ts")

    n2 = st.slider("Pagos remanentes", 1, 10, 6)
    payment_times = [accrual2 * (i + 1) for i in range(n2)]
    zeros_default = [0.045, 0.048, 0.050, 0.052, 0.054, 0.055, 0.056, 0.057, 0.058, 0.058]
    zeros = zeros_default[:n2]

    result = swap_value_via_bonds(
        notional=L2, fixed_rate=R_fix2, payment_times=payment_times,
        zero_rates=zeros, next_floating_rate=R_float_set,
        time_since_last_reset=time_since, accrual=accrual2,
        position="receive_fixed",
    )

    m1, m2, m3 = st.columns(3)
    m1.metric("B_fix", f"${result.bond_fixed_value:,.0f}")
    m2.metric("B_flt", f"${result.bond_floating_value:,.0f}")
    m3.metric("V_swap (receive fixed)", f"${result.swap_value:+,.0f}",
              delta_color="off" if result.swap_value >= 0 else "inverse")

    par = swap_par_rate(payment_times, zeros, accrual2)
    st.metric("Par swap rate (que haría V=0)", f"{par:.4%}")

    st.subheader("Zero curve usada")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=payment_times, y=[z * 100 for z in zeros],
                             mode="lines+markers",
                             line=dict(color="#d4af37", width=2.5),
                             marker=dict(size=8)))
    fig.update_layout(template="plotly_dark", height=300,
                      xaxis_title="T (años)", yaxis_title="Zero rate (%)",
                      margin=dict(l=10, r=10, t=20, b=10))
    st.plotly_chart(fig, use_container_width=True)
