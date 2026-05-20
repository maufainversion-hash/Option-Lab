from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from math import log as ln

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from pricing.forwards import forward_price, cost_of_carry
from ui.styling import inject_premium_css
from ui.components.header_strip import render_header_strip

st.set_page_config(page_title="U3 — Forward Pricing", page_icon="📐", layout="wide",
                   initial_sidebar_state="collapsed")
inject_premium_css()
render_header_strip()

st.markdown(
    '<h1 style="margin:0;font-weight:600;">Unidad III · Valuación de forwards y futuros</h1>'
    '<div style="color:var(--text-muted);font-size:13px;margin-bottom:20px;">'
    'Hull Cap 5 y 6. Cost of carry, dividends, storage, contango/backwardation.'
    '</div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["Pricing genérico", "Contango vs Backwardation", "Convenience yield"])

with tab1:
    st.markdown(r"""
**Forward price genérico** (Hull 5.17):

$$F_0 = S_0 \cdot e^{(r - q + u - y) T}$$

- r: risk-free rate (cc)
- q: dividend yield (o costo de financiamiento ahorrado si tenés el asset)
- u: storage cost rate
- y: convenience yield (beneficio de tener el físico, no el papel)

Cost of carry **c = r − q + u − y**. Si c > 0 → mercado en contango (F > S).
""")
    c1, c2, c3 = st.columns(3)
    S0 = c1.number_input("Spot S₀", min_value=0.01, value=100.0, step=1.0)
    r = c2.number_input("Tasa r (cc)", min_value=0.0, value=0.05, step=0.005, format="%.4f")
    T = c3.number_input("T (años)", min_value=0.01, value=1.0, step=0.25)

    c4, c5, c6 = st.columns(3)
    q = c4.number_input("Dividend yield q", min_value=0.0, value=0.02, step=0.005, format="%.4f")
    u_cost = c5.number_input("Storage cost u", min_value=0.0, value=0.0, step=0.005, format="%.4f")
    y_conv = c6.number_input("Convenience yield y", min_value=0.0, value=0.0, step=0.005, format="%.4f")

    F = forward_price(S0, r, T, q, u_cost, y_conv)
    carry = cost_of_carry(r, q, u_cost, y_conv)

    m1, m2, m3 = st.columns(3)
    m1.metric("Forward price F₀", f"${F:.4f}")
    m2.metric("Cost of carry c", f"{carry:.4%}")
    m3.metric("Mercado en", "Contango" if F > S0 else ("Backwardation" if F < S0 else "Flat"))

with tab2:
    st.markdown("""
**Contango**: F > S → forward prices más altos. Típico en assets con cost of carry positivo
(commodities almacenables sin escasez, equity sin dividendos altos).

**Backwardation**: F < S → forwards más baratos. Indica escasez física, demanda inmediata
del activo (convenience yield alto: oil en crisis, gas en invierno) o dividend yield > r.
""")
    S0_v = 100.0
    Ts = np.linspace(0, 2, 50)
    carry_scenarios = {"Contango fuerte (c=8%)": 0.08, "Contango leve (c=2%)": 0.02,
                       "Flat (c=0%)": 0.0, "Backwardation (c=-5%)": -0.05}
    fig = go.Figure()
    colors = ["#d4af37", "#58a6ff", "#8b949e", "#f85149"]
    for (label, c), color in zip(carry_scenarios.items(), colors):
        Fs = S0_v * np.exp(c * Ts)
        fig.add_trace(go.Scatter(x=Ts, y=Fs, mode="lines", name=label,
                                 line=dict(color=color, width=2)))
    fig.add_hline(y=S0_v, line=dict(color="white", dash="dot"), annotation_text="Spot")
    fig.update_layout(template="plotly_dark", height=420,
                      title="Curva de forwards bajo distintos cost of carry",
                      xaxis_title="T (años)", yaxis_title="F₀",
                      margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.markdown(r"""
**Convenience yield** y (Hull 5.17): el beneficio implícito de poseer el activo físico
en lugar del forward. Típico en commodities cuando hay riesgo de shortage.

Se despeja de las cotizaciones de mercado: si observás F₀, S₀, r, u, q:

$$y = r - q + u - \frac{1}{T}\ln\frac{F_0}{S_0}$$
""")
    c1, c2, c3, c4 = st.columns(4)
    F_obs = c1.number_input("F observado", value=98.0, step=0.5)
    S_obs = c2.number_input("S observado", value=100.0, step=0.5)
    T_obs = c3.number_input("T", value=0.5, step=0.25)
    r_obs = c4.number_input("r (cc)", value=0.05, step=0.005, format="%.4f")
    u_obs = st.number_input("Storage u", value=0.0, step=0.005, format="%.4f")
    q_obs = st.number_input("Dividend q", value=0.0, step=0.005, format="%.4f")

    if S_obs > 0 and F_obs > 0 and T_obs > 0:
        y_implied = r_obs - q_obs + u_obs - (1 / T_obs) * ln(F_obs / S_obs)
        st.metric("Convenience yield implícita", f"{y_implied:.4%}",
                  help="Si es muy alta → mercado prioriza tener el físico ya (escasez)")
    else:
        st.error("S, F, T deben ser > 0")
