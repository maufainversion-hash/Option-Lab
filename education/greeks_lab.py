"""
Las griegas (Hull Cap 19).
"""
from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from pricing.black_scholes import bs_price, bs_price_both
from pricing.binomial import binomial_convergence
from greeks.analytical import all_greeks
from ui.charts.greeks_visualizer import greek_vs_spot, greek_surface, all_greeks_panel
from education import formulario


def render() -> None:
    st.markdown(
        '<h1 style="margin:0;font-weight:600;">Las griegas (Hull Cap 19)</h1>'
        '<div style="color:var(--text-muted);font-size:13px;margin-bottom:20px;">'
        'Delta, gamma, theta, vega, rho. Sensibilidades a primer y segundo orden.'
        '</div>', unsafe_allow_html=True)

    st.header("Las Griegas y cómo se comportan")
    st.markdown(
        """
    Las **griegas** miden cómo cambia el precio de una opción ante cambios en las variables
    de entrada. Son las primeras (y segundas) derivadas del modelo BSM.

    | Griega | Qué mide | Convención de signo (long call) |
    |---|---|---|
    | **Δ Delta** | ∂V/∂S — sensibilidad al spot | (0, 1) |
    | **Γ Gamma** | ∂²V/∂S² — convexidad | siempre ≥ 0 si long |
    | **ν Vega** | ∂V/∂σ — sensibilidad a la vol | siempre ≥ 0 si long |
    | **Θ Theta** | ∂V/∂t — time decay (por año) | < 0 si long (se evapora) |
    | **ρ Rho** | ∂V/∂r — sensibilidad a la tasa | > 0 si call, < 0 si put |

    Vega y gamma son **siempre positivas** para opciones long, sin importar call/put — porque
    medir la 2da derivada en S (gamma) o la 1ra en σ (vega) no distingue dirección.
    """
    )

    cgl, cgc, cgr = st.columns(3)
    K_g = cgl.number_input("Strike K", min_value=1.0, value=100.0, step=1.0, key="g_K")
    T_g = cgc.slider("T (años)", 0.05, 2.0, 0.5, 0.05, key="g_T")
    sigma_g = cgr.slider("Volatilidad σ", 0.05, 1.0, 0.25, 0.01, key="g_sigma")
    r_g = st.slider("r", 0.0, 0.30, 0.05, 0.005, key="g_r")
    q_g = st.slider("Dividend yield q", 0.0, 0.20, 0.0, 0.005, key="g_q")
    opt_g = st.radio("Tipo", ["call", "put"], horizontal=True, key="g_type")

    st.subheader("Panel de las 5 griegas + precio (en función del spot)")
    fig_panel = all_greeks_panel(K_g, T_g, r_g, sigma_g, q_g, opt_g)
    st.plotly_chart(fig_panel, use_container_width=True)

    st.markdown(
        """
    **Cosas para observar en el panel:**

    1. **Delta** del call sube de 0 (OTM) a 1 (ITM), pasando por ~0.5 en ATM. Para puts, va de 0 a −1.
    2. **Gamma** tiene un pico **en ATM**. Cerca del vencimiento (T chico) el pico se hace mucho más alto y angosto — por eso "gamma explota" cerca del expiry.
    3. **Vega** también pico en ATM, pero más ancho. Aumenta con T (más tiempo = más oportunidad de vol).
    4. **Theta** es más negativo en ATM (la opción "pierde más rápido" donde la incertidumbre vale más).
    5. **Rho** sube linealmente con K para calls — cuanto más alto el strike, más sensible a la tasa.
    """
    )

    st.subheader("Superficie 3D de una griega (S, T)")
    cgg = st.columns(2)
    greek_pick = cgg[0].selectbox("Griega", ["gamma", "vega", "delta", "theta", "rho"], key="g_pick")
    st.plotly_chart(
        greek_surface(greek_pick, K_g, r_g, sigma_g, q_g, opt_g),
        use_container_width=True,
    )

    st.markdown(
        """
    **Interpretación práctica en AR:**

    - Si comprás opciones ATM **cerca del vencimiento**, estás muy expuesto a gamma — un mov del subyacente
      cambia tu delta dramáticamente. Bueno si acertás, malo si no.
    - Si comprás opciones largas y vol baja → vega te juega a favor si la vol sube (lo que pasa antes de
      resultados o eventos macro AR).
    - Si vendés opciones (covered call, iron condor) → theta te juega a favor pero gamma en contra.
      Sos "long theta, short gamma".
    """
    )

    st.subheader("Convergencia binomial → Black-Scholes (Hull Cap 12)")
    st.markdown(
        """
    El árbol binomial CRR converge al precio BS cuando n → ∞, pero **oscila**. El Leisen-Reimer
    converge mucho más rápido y monotónicamente.
    """
    )

    convergence = binomial_convergence(
        100.0, K_g, T_g, r_g, sigma_g, q_g, opt_g,
        n_values=[3, 5, 7, 11, 21, 51, 101, 201, 501],
    )
    bs_ref = bs_price(100.0, K_g, T_g, r_g, sigma_g, q_g, opt_g)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=convergence["n"], y=convergence["crr"],
        mode="lines+markers", name="CRR",
        line=dict(color="#ef5350", width=2),
    ))
    fig.add_trace(go.Scatter(
        x=convergence["n"], y=convergence["lr"],
        mode="lines+markers", name="Leisen-Reimer",
        line=dict(color="#26a69a", width=2),
    ))
    fig.add_hline(y=bs_ref, line=dict(color="#ffa726", width=2, dash="dash"),
                  annotation_text=f"BS = ${bs_ref:.4f}", annotation_position="right")
    fig.update_layout(
        title="Convergencia al precio BS",
        xaxis_title="n (pasos del árbol)",
        yaxis_title="Precio",
        xaxis_type="log",
        template="plotly_dark",
        height=400,
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    formulario.cap19()
