from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from math import exp

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from pricing.interest_rates import (
    to_continuous, from_continuous, forward_rate,
    fra_value, macaulay_duration, modified_duration,
)
from ui.styling import inject_premium_css, output_card, info_box, hull_check
from ui.components.header_strip import render_header_strip

st.set_page_config(page_title="U3 — Tasas y FRAs", page_icon="💱", layout="wide",
                   initial_sidebar_state="collapsed")
inject_premium_css()
render_header_strip()

st.markdown(
    '<h1 style="margin:0;font-weight:600;">Unidad III · Tasas de interés y FRAs</h1>'
    '<div style="color:var(--text-muted);font-size:13px;margin-bottom:20px;">'
    'Hull Cap 4. Compounding, forward rates, <b>FRAs (foco)</b>, duration.'
    '</div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["Compounding", "Forward rates", "FRAs", "Duration"])

with tab1:
    st.markdown(r"""
**Conversión entre compounding frequencies.** Hull (4.2):

$$R_c = m \cdot \ln\!\left(1 + \frac{R_m}{m}\right) \quad \Longleftrightarrow \quad R_m = m \cdot (e^{R_c/m} - 1)$$

A continuous compounding (R_c) lo usás en BSM, binomial, FRA, etc.
""")
    c1, c2, c3 = st.columns(3)
    rate_in = c1.number_input("Tasa input", min_value=0.0, max_value=1.0, value=0.10, step=0.005, format="%.4f")
    m_options = [1, 2, 4, 12, 365, "continuous"]
    m = c2.selectbox("Compounding del input", m_options, index=1)
    direction = c3.radio("Convertir a", ["continuous", "annual (m=1)"], horizontal=True)

    if m == "continuous":
        r_c = rate_in
    else:
        r_c = to_continuous(rate_in, m)
    if direction == "continuous":
        st.metric("Tasa continuous equivalente", f"{r_c:.4%}")
    else:
        r_annual = from_continuous(r_c, 1)
        st.metric("Tasa annual equivalente", f"{r_annual:.4%}")

with tab2:
    st.markdown(r"""
**Forward rate** entre T₁ y T₂ dado por la zero curve (Hull 4.7):

$$f_{T_1, T_2} = \frac{R_2 T_2 - R_1 T_1}{T_2 - T_1}$$

Es la tasa que el mercado **implícitamente** pricea para el período futuro [T₁, T₂].
Si la curva es **upward sloping**, las forward rates son más altas que las spot.
""")
    c1, c2, c3, c4 = st.columns(4)
    T1 = c1.number_input("T₁ (años)", min_value=0.05, value=3.0, step=0.25)
    T2 = c2.number_input("T₂ (años)", min_value=0.10, value=3.25, step=0.25)
    R1 = c3.number_input("Zero rate hasta T₁ (cc)", min_value=0.0, value=0.03, step=0.005, format="%.4f")
    R2 = c4.number_input("Zero rate hasta T₂ (cc)", min_value=0.0, value=0.032, step=0.005, format="%.4f")

    if T2 > T1:
        f = forward_rate(R1, T1, R2, T2)
        st.metric(f"Forward rate f({T1:.2f}, {T2:.2f})", f"{f:.4%}",
                  help="Continuously compounded")
    else:
        st.error("T₂ debe ser > T₁")

    st.subheader("Visualización de zero curve y forwards")
    Ts = np.array([0.25, 0.5, 1, 2, 3, 5, 7, 10])
    zeros = st.text_input("Zero rates por plazo (cc, separados por coma)",
                          value="0.025, 0.027, 0.029, 0.030, 0.032, 0.035, 0.037, 0.038")
    try:
        zs = np.array([float(x.strip()) for x in zeros.split(",")])
        if len(zs) == len(Ts):
            fwds = [forward_rate(zs[i], Ts[i], zs[i+1], Ts[i+1]) for i in range(len(Ts)-1)]
            fwd_x = [(Ts[i] + Ts[i+1]) / 2 for i in range(len(Ts)-1)]
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=Ts, y=zs * 100, mode="lines+markers", name="Zero",
                                     line=dict(color="#d4af37", width=2.5)))
            fig.add_trace(go.Scatter(x=fwd_x, y=[f*100 for f in fwds], mode="lines+markers",
                                     name="Forward", line=dict(color="#58a6ff", width=2, dash="dash")))
            fig.update_layout(template="plotly_dark", height=400,
                              title="Zero curve vs forward curve implícita",
                              xaxis_title="T (años)", yaxis_title="Rate (%)",
                              margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning(f"Necesito {len(Ts)} zero rates, recibí {len(zs)}.")
    except ValueError:
        st.warning("Formato inválido. Usar comas y punto decimal.")

with tab3:
    st.markdown(r"""
**Forward Rate Agreement (FRA)** — contrato que fija una tasa de interés para un período
futuro. Hull 4.8.

- **Receive fixed**: cobrás la tasa pactada R_K. Pagás la flotante R_F que se observe en T₁.
- Payoff en T₂: $L \cdot (R_K - R_F) \cdot (T_2 - T_1)$ (receive fixed)
- Valor hoy: $L \cdot (R_K - R_F) \cdot (T_2 - T_1) \cdot e^{-R_2 T_2}$

donde R_F es la **forward rate** implícita en la zero curve.
""")
    info_box("<b>Setup tipo Hull 4.3</b>: notional $100M, R_K = 4%, T₁=3, T₂=3.25, "
             "zero₃=3% cc, zero₃.₂₅=3.2% cc. Aplicando f=(R₂T₂−R₁T₁)/(T₂−T₁) → "
             "forward ≈ 5.6% cc → payoff en T₂ ≈ -$405k → PV ≈ -$365k.", kind="hull")

    c1, c2, c3 = st.columns(3)
    notional = c1.number_input("Notional", min_value=1000.0, value=100_000_000.0, step=1000.0)
    R_K = c2.number_input("Tasa pactada R_K (cc)", min_value=0.0, value=0.04, step=0.001, format="%.4f")
    position = c3.radio("Posición", ["receive_fixed", "pay_fixed"], horizontal=True)

    c4, c5, c6, c7 = st.columns(4)
    T1_fra = c4.number_input("T₁", min_value=0.05, value=3.0, step=0.25, key="fra_T1")
    T2_fra = c5.number_input("T₂", min_value=0.10, value=3.25, step=0.25, key="fra_T2")
    zero_T1 = c6.number_input("Zero hasta T₁ (cc)", min_value=0.0, value=0.030, step=0.001, format="%.4f", key="fra_z1")
    zero_T2 = c7.number_input("Zero hasta T₂ (cc)", min_value=0.0, value=0.032, step=0.001, format="%.4f", key="fra_z2")

    if T2_fra > T1_fra:
        result = fra_value(notional, R_K, T1_fra, T2_fra, zero_T1, zero_T2, position)
        pv_color = "positive" if result.present_value >= 0 else "negative"
        fc = st.columns(4)
        fc[0].markdown(output_card("Forward rate implícita", f"{result.forward_rate*100:.4f}%",
                                    hint="Continuously compounded", color="info"),
                       unsafe_allow_html=True)
        fc[1].markdown(output_card("Payoff en T₂", f"${result.payoff_at_T2:+,.0f}",
                                    color=pv_color), unsafe_allow_html=True)
        fc[2].markdown(output_card("PV hoy", f"${result.present_value:+,.0f}",
                                    color=pv_color), unsafe_allow_html=True)
        fc[3].markdown(output_card("Posición", result.position.replace("_", " ").title(),
                                    color="muted"), unsafe_allow_html=True)

        # Hull verification (sólo cuando los inputs matchean el ejemplo del libro)
        is_hull_setup = (
            abs(notional - 100_000_000) < 1 and abs(R_K - 0.04) < 1e-6
            and abs(T1_fra - 3.0) < 1e-6 and abs(T2_fra - 3.25) < 1e-6
            and abs(zero_T1 - 0.030) < 1e-6 and abs(zero_T2 - 0.032) < 1e-6
            and position == "receive_fixed"
        )
        if is_hull_setup:
            st.subheader("Verificación")
            hull_check(0.056, result.forward_rate, label="Forward rate (Hull 4.3 setup)",
                       tolerance=0.001)
            hull_check(-365000, result.present_value, label="PV (Hull 4.3 setup)",
                       tolerance=0.05, units=" $")
    else:
        st.error("T₂ debe ser > T₁")

with tab4:
    st.markdown(r"""
**Duration de Macaulay** (Hull 4.10):

$$D = \frac{\sum_i t_i \cdot \text{CF}_i \cdot e^{-y t_i}}{\sum_i \text{CF}_i \cdot e^{-y t_i}} = \frac{\sum_i t_i \cdot \text{CF}_i \cdot e^{-y t_i}}{B}$$

Es el plazo promedio ponderado por el PV de cada cashflow.

**Duration modificada**: D_mod = D / (1 + y/m). Aproxima el cambio porcentual en el precio
del bono ante un cambio en el yield: $\Delta B / B \approx -D_{mod} \cdot \Delta y$.
""")
    face = 100.0
    coupon_rate = st.slider("Cupón anual", 0.0, 0.20, 0.06, 0.005, format="%.3f")
    T_bond = st.slider("Plazo (años)", 0.5, 30.0, 3.0, 0.5)
    y_bond = st.slider("Yield (cc)", 0.0, 0.30, 0.12, 0.005, format="%.3f")
    freq = st.selectbox("Frecuencia de pago", [1, 2, 4], index=1)

    coupon_amount = face * coupon_rate / freq
    cfs = []
    t = 1 / freq
    while t < T_bond - 1e-9:
        cfs.append((t, coupon_amount))
        t += 1 / freq
    cfs.append((T_bond, coupon_amount + face))

    B = sum(cf * exp(-y_bond * t_) for t_, cf in cfs)
    D = macaulay_duration(cfs, y_bond)
    D_mod = modified_duration(D, y_bond, freq)

    m1, m2, m3 = st.columns(3)
    m1.metric("Precio del bono", f"${B:.4f}")
    m2.metric("Macaulay Duration", f"{D:.4f} años")
    m3.metric("Modified Duration", f"{D_mod:.4f}")

    dys = np.linspace(-0.02, 0.02, 41)
    pct_change_actual = [
        (sum(cf * exp(-(y_bond + dy) * t_) for t_, cf in cfs) - B) / B * 100
        for dy in dys
    ]
    pct_change_approx = [-D_mod * dy * 100 for dy in dys]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dys * 100, y=pct_change_actual, mode="lines", name="Real",
                             line=dict(color="#d4af37", width=2.5)))
    fig.add_trace(go.Scatter(x=dys * 100, y=pct_change_approx, mode="lines",
                             name="Aprox. via D_mod", line=dict(color="#58a6ff", width=2, dash="dash")))
    fig.update_layout(template="plotly_dark", height=360,
                      title="ΔB/B real vs aprox. lineal con duration modificada",
                      xaxis_title="Δy (%)", yaxis_title="ΔB/B (%)",
                      margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig, use_container_width=True)
