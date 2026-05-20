from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from math import log as ln

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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
    st.header("Contango vs Backwardation")
    st.markdown(
        "Dos regímenes de **estructura de plazos de futuros**. La diferencia clave: "
        "el signo del cost of carry **c = r − q + u − y**."
    )

    col_c, col_b = st.columns(2)
    with col_c:
        st.markdown(
            '<div class="premium-card" style="border-left:3px solid var(--positive); '
            'background: rgba(63,185,80,0.05);">'
            '<div style="color:var(--positive);font-weight:600;font-size:18px;">▲ CONTANGO</div>'
            '<div style="font-family:JetBrains Mono;color:var(--text);font-size:14px;margin-top:8px;">F > S</div>'
            '<div style="color:var(--text-muted);font-size:13px;margin-top:8px;line-height:1.6;">'
            'Forwards <b>más caros</b> que el spot. Cost of carry positivo: pagás r '
            'para financiar el spot, ahorrás q en dividendos.<br><br>'
            '<b>Ejemplos reales:</b><br>'
            '• Oro casi siempre (es asset financiero, almacenable, sin dividend).<br>'
            '• S&P 500 cuando r &gt; div yield (la mayor parte del tiempo).<br>'
            '• Commodities almacenables sin shortage (cobre normal, soja en cosecha).'
            '</div></div>', unsafe_allow_html=True,
        )
    with col_b:
        st.markdown(
            '<div class="premium-card" style="border-left:3px solid var(--negative); '
            'background: rgba(248,81,73,0.05);">'
            '<div style="color:var(--negative);font-weight:600;font-size:18px;">▼ BACKWARDATION</div>'
            '<div style="font-family:JetBrains Mono;color:var(--text);font-size:14px;margin-top:8px;">F < S</div>'
            '<div style="color:var(--text-muted);font-size:13px;margin-top:8px;line-height:1.6;">'
            'Forwards <b>más baratos</b> que el spot. Convenience yield alto o dividend yield &gt; r. '
            'El mercado paga premium por tener el físico ya.<br><br>'
            '<b>Ejemplos reales:</b><br>'
            '• Oil WTI en crisis (2022 invasión Rusia: backwardation fuerte por shortage).<br>'
            '• Gas natural en invierno (demanda inmediata).<br>'
            '• Equity con dividendos muy altos (REITs, MLPs).'
            '</div></div>', unsafe_allow_html=True,
        )

    st.subheader("Curva de forwards (F₀ vs T)")
    S0_v = 100.0
    Ts = np.linspace(0, 2, 50)
    carry_scenarios = {
        "Contango fuerte (c=+8%)": (0.08, "#3fb950"),
        "Contango leve (c=+2%)": (0.02, "#7ee787"),
        "Flat (c=0%)": (0.0, "#8b949e"),
        "Backwardation leve (c=−3%)": (-0.03, "#ffa198"),
        "Backwardation fuerte (c=−8%)": (-0.08, "#f85149"),
    }
    fig = go.Figure()
    for label, (c, color) in carry_scenarios.items():
        Fs = S0_v * np.exp(c * Ts)
        fig.add_trace(go.Scatter(x=Ts, y=Fs, mode="lines", name=label,
                                 line=dict(color=color, width=2.5)))
    fig.add_hline(y=S0_v, line=dict(color="white", dash="dot"), annotation_text="Spot = 100")
    fig.update_layout(template="plotly_dark", height=420,
                      title="F₀ = S₀·e^(c·T) — 5 regímenes",
                      xaxis_title="T (años)", yaxis_title="F₀",
                      margin=dict(l=10, r=10, t=40, b=10),
                      legend=dict(orientation="v", x=0.02, y=0.98))
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Term structure: estructura de plazos de los futuros listados")
    st.caption("Así se ve un panel de futuros listados en un exchange real (ej. CME): "
               "cada barra es un contrato con su propio vencimiento.")
    expiries = ["1M", "3M", "6M", "9M", "1Y", "18M", "2Y"]
    T_expiries = [1/12, 3/12, 6/12, 9/12, 1.0, 1.5, 2.0]
    regimes = {"Contango": 0.05, "Flat": 0.0, "Backwardation": -0.05}
    fig_ts = make_subplots(rows=1, cols=3, subplot_titles=list(regimes.keys()))
    col_idx = 1
    for regime, c in regimes.items():
        Fs = [S0_v * np.exp(c * t) for t in T_expiries]
        color = "#3fb950" if c > 0 else ("#f85149" if c < 0 else "#8b949e")
        fig_ts.add_trace(
            go.Bar(x=expiries, y=Fs, marker_color=color, showlegend=False,
                   text=[f"{f:.1f}" for f in Fs], textposition="outside"),
            row=1, col=col_idx,
        )
        fig_ts.add_hline(y=S0_v, line=dict(color="white", dash="dot"),
                         row=1, col=col_idx)
        col_idx += 1
    fig_ts.update_layout(template="plotly_dark", height=380,
                         margin=dict(l=10, r=10, t=50, b=10),
                         yaxis=dict(range=[88, 112]),
                         yaxis2=dict(range=[88, 112]),
                         yaxis3=dict(range=[88, 112]))
    st.plotly_chart(fig_ts, use_container_width=True)

    st.subheader("Evolución del spread (F − S) a medida que pasa el tiempo")
    st.caption("Asumiendo que el spot no se mueve, el spread futuro-spot **converge a 0** "
               "en el vencimiento. La velocidad depende del cost of carry.")
    T_grid = np.linspace(0, 1, 100)
    fig_sp = go.Figure()
    for label, (c, color) in carry_scenarios.items():
        spread = S0_v * (np.exp(c * (1 - T_grid)) - 1)
        fig_sp.add_trace(go.Scatter(x=T_grid, y=spread, mode="lines",
                                     line=dict(color=color, width=2), name=label))
    fig_sp.add_hline(y=0, line=dict(color="white", dash="dot"),
                     annotation_text="Convergencia: F → S al vencimiento")
    fig_sp.update_layout(template="plotly_dark", height=380,
                         title="Spread (F − S) en función del tiempo (T=1 año)",
                         xaxis_title="t (años transcurridos)", yaxis_title="F − S",
                         margin=dict(l=10, r=10, t=40, b=10),
                         legend=dict(orientation="v", x=1.02, y=1))
    st.plotly_chart(fig_sp, use_container_width=True)

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
