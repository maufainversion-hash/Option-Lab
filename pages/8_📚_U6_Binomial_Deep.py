from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from math import exp, sqrt, log

import numpy as np
import plotly.graph_objects as go
from scipy.stats import norm
import streamlit as st

from pricing.black_scholes import bs_price
from pricing.binomial import crr_price, leisen_reimer_price, binomial_convergence
from ui.styling import inject_premium_css
from ui.components.header_strip import render_header_strip

st.set_page_config(page_title="U6 — Binomial & BSM", page_icon="🌳", layout="wide",
                   initial_sidebar_state="collapsed")
inject_premium_css()
render_header_strip()

st.markdown(
    '<h1 style="margin:0;font-weight:600;">Unidad VI · Valuación de opciones</h1>'
    '<div style="color:var(--text-muted);font-size:13px;margin-bottom:20px;">'
    'Hull Cap 13 (binomial — el más difícil), 14 (Wiener), 15 (BSM y N(d1)/N(d2)).'
    '</div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs([
    "Árbol 1 paso (intuición)", "Árbol n pasos", "GBM y paths (Cap 14)", "N(d1) y N(d2) (Cap 15)"
])

with tab1:
    st.markdown(r"""
**Un solo paso** (Hull 13.1). Subyacente S puede subir a S·u o bajar a S·d. Un call paga
$f_u = \max(Su - K, 0)$ ó $f_d = \max(Sd - K, 0)$.

Construimos un portfolio **risk-free**: long Δ acciones, short 1 call. Para que no haya
incertidumbre: $\Delta = (f_u - f_d) / (Su - Sd)$.

El portfolio rinde la tasa libre: $\Delta S - f = (\Delta Su - f_u) e^{-rT}$.

De ahí sale la **fórmula risk-neutral**:

$$f = e^{-rT}[p \cdot f_u + (1-p) \cdot f_d], \quad p = \frac{e^{rT} - d}{u - d}$$

p no es la "probabilidad real" de subir — es la **probabilidad risk-neutral** que hace
que valuar descontando a la tasa libre dé el mismo precio que la no-arbitrage.
""")
    st.info("**Hull Ejemplo 13.1**: S=$20, u=1.1, d=0.9, K=$21, r=12%, T=3m. → C ≈ $0.633")

    c1, c2, c3 = st.columns(3)
    S = c1.number_input("Spot S", value=20.0, step=1.0, key="bn1_S")
    K = c2.number_input("Strike K", value=21.0, step=1.0, key="bn1_K")
    T1 = c3.number_input("T (años)", value=0.25, step=0.05, key="bn1_T")

    c4, c5, c6 = st.columns(3)
    u = c4.number_input("u (factor up)", min_value=1.0, value=1.1, step=0.05)
    d = c5.number_input("d (factor down)", min_value=0.01, max_value=1.0, value=0.9, step=0.05)
    r_b = c6.number_input("r (cc)", value=0.12, step=0.005, format="%.4f", key="bn1_r")

    Su, Sd = S * u, S * d
    fu = max(Su - K, 0)
    fd = max(Sd - K, 0)
    if u == d:
        st.error("u y d no pueden ser iguales")
    else:
        delta = (fu - fd) / (Su - Sd) if (Su - Sd) != 0 else 0
        p = (exp(r_b * T1) - d) / (u - d)
        if not (0 < p < 1):
            st.warning(f"p = {p:.4f} fuera de (0,1) — viola no-arbitraje con estos inputs")
        f0 = exp(-r_b * T1) * (p * fu + (1 - p) * fd)

        mm = st.columns(4)
        mm[0].metric("p (risk-neutral)", f"{p:.4f}")
        mm[1].metric("Δ (delta replicante)", f"{delta:.4f}")
        mm[2].metric("Valor call hoy", f"${f0:.4f}")
        mm[3].metric("Verificación Hull 13.1", "✓" if abs(f0 - 0.633) < 0.005 else "—")

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=[0, 1], y=[S, Su], mode="lines+markers+text",
                                 text=["", f"S·u = {Su:.2f}<br>f_u = {fu:.2f}"],
                                 textposition="top right",
                                 line=dict(color="#3fb950", width=2), name="Up"))
        fig.add_trace(go.Scatter(x=[0, 1], y=[S, Sd], mode="lines+markers+text",
                                 text=["", f"S·d = {Sd:.2f}<br>f_d = {fd:.2f}"],
                                 textposition="bottom right",
                                 line=dict(color="#f85149", width=2), name="Down"))
        fig.add_annotation(x=0, y=S, text=f"<b>S₀ = {S:.2f}<br>f₀ = {f0:.4f}</b>",
                           showarrow=False, xshift=-50, font=dict(color="#d4af37", size=14))
        fig.update_layout(template="plotly_dark", height=400, showlegend=False,
                          title="Árbol binomial 1 paso", xaxis=dict(visible=False),
                          yaxis=dict(visible=False), margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.markdown(r"""
**Calibración** (Hull 13.10): para matching de volatilidad σ con un árbol CRR:

$$u = e^{\sigma \sqrt{\Delta t}}, \quad d = 1/u, \quad p = \frac{e^{r\Delta t} - d}{u - d}$$

**Inducción backward**: en cada nodo no terminal, $f = e^{-r\Delta t}[p f_u + (1-p) f_d]$.
Para americanas: tomar $\max(f, \text{intrinsic})$ en cada paso.
""")
    c1, c2, c3, c4 = st.columns(4)
    S2 = c1.number_input("Spot S", value=50.0, step=1.0, key="bnn_S")
    K2 = c2.number_input("Strike K", value=52.0, step=1.0, key="bnn_K")
    T2 = c3.number_input("T", value=2.0, step=0.25, key="bnn_T")
    sigma = c4.number_input("σ", value=0.30, step=0.01, format="%.4f", key="bnn_sig")

    c5, c6, c7 = st.columns(3)
    r2 = c5.number_input("r", value=0.05, step=0.005, format="%.4f", key="bnn_r")
    n2 = c6.slider("n (pasos)", 2, 100, 4)
    ex_type = c7.radio("Ejercicio", ["european", "american"], horizontal=True)

    opt_type = st.radio("Tipo de opción", ["call", "put"], horizontal=True, key="bnn_type")

    try:
        crr = crr_price(S2, K2, T2, r2, sigma, 0.0, n2, opt_type, ex_type)
        lr_n = n2 if n2 % 2 == 1 else n2 + 1
        lr = leisen_reimer_price(S2, K2, T2, r2, sigma, 0.0, max(3, lr_n), opt_type, ex_type)
        bs = bs_price(S2, K2, T2, r2, sigma, 0.0, opt_type) if ex_type == "european" else None

        m = st.columns(3)
        m[0].metric("CRR (n pasos)", f"${crr:.4f}")
        m[1].metric("Leisen-Reimer", f"${lr:.4f}")
        m[2].metric("BSM (referencia)" if bs else "BSM N/A (americana)", f"${bs:.4f}" if bs is not None else "—")
    except ValueError as e:
        st.error(f"Inputs inválidos: {e}")
        crr = lr = bs = None

    if n2 <= 6:
        dt = T2 / n2
        u_ = exp(sigma * sqrt(dt))
        d_ = 1 / u_
        xs, ys, texts = [], [], []
        for i in range(n2 + 1):
            for j in range(i + 1):
                S_node = S2 * (u_ ** (i - j)) * (d_ ** j)
                xs.append(i)
                ys.append(S_node)
                texts.append(f"{S_node:.2f}")
        fig = go.Figure()
        # connect lines
        for i in range(n2):
            for j in range(i + 1):
                S_node = S2 * (u_ ** (i - j)) * (d_ ** j)
                S_up = S2 * (u_ ** (i + 1 - j)) * (d_ ** j)
                S_dn = S2 * (u_ ** (i - j)) * (d_ ** (j + 1))
                fig.add_trace(go.Scatter(x=[i, i+1], y=[S_node, S_up], mode="lines",
                                         line=dict(color="#3fb950", width=1.2),
                                         showlegend=False, hoverinfo="skip"))
                fig.add_trace(go.Scatter(x=[i, i+1], y=[S_node, S_dn], mode="lines",
                                         line=dict(color="#f85149", width=1.2),
                                         showlegend=False, hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="markers+text", text=texts,
                                 textposition="top right",
                                 marker=dict(color="#d4af37", size=10),
                                 showlegend=False))
        fig.update_layout(template="plotly_dark", height=420,
                          title=f"Árbol CRR ({n2} pasos) — precios del subyacente",
                          xaxis_title="Paso", yaxis_title="S",
                          margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.caption("Árbol no renderizado (n > 6 — el gráfico se vuelve ilegible).")

    st.subheader("Convergencia CRR vs Leisen-Reimer vs BSM")
    if ex_type == "european":
        try:
            conv = binomial_convergence(S2, K2, T2, r2, sigma, 0.0, opt_type)
            bs_ref = bs_price(S2, K2, T2, r2, sigma, 0.0, opt_type)
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=conv["n"], y=conv["crr"], mode="lines+markers",
                                     name="CRR", line=dict(color="#d4af37", width=2)))
            fig.add_trace(go.Scatter(x=conv["n"], y=conv["lr"], mode="lines+markers",
                                     name="Leisen-Reimer", line=dict(color="#58a6ff", width=2)))
            fig.add_hline(y=bs_ref, line=dict(color="#3fb950", dash="dash"),
                          annotation_text=f"BSM = {bs_ref:.4f}")
            fig.update_layout(template="plotly_dark", height=380,
                              title="Convergencia al precio Black-Scholes",
                              xaxis_title="n (pasos)", yaxis_title="Precio",
                              margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig, use_container_width=True)
        except ValueError as e:
            st.warning(f"No se pudo calcular convergencia: {e}")
    else:
        st.caption("Convergencia mostrada solo para europeas (BSM no aplica a americanas).")

with tab3:
    st.markdown(r"""
**Geometric Brownian Motion** (Hull 14.3) — el modelo de S bajo la medida risk-neutral:

$$dS = (r - q) S \, dt + \sigma S \, dW$$

donde $dW$ es un proceso de Wiener. Su solución cerrada:

$$S_T = S_0 \cdot \exp\!\left[(r - q - \tfrac{1}{2}\sigma^2) T + \sigma \sqrt{T} \, Z\right], \quad Z \sim N(0, 1)$$

La **drift** real de la acción ($\mu$) **no aparece** en pricing: bajo risk-neutral todo activo
rinde r. Esto es el corazón del *no-arbitrage pricing*.
""")
    c1, c2, c3, c4 = st.columns(4)
    S0_p = c1.number_input("S₀", value=100.0, step=1.0, key="gbm_S")
    sigma_p = c2.number_input("σ", value=0.25, step=0.01, format="%.4f", key="gbm_sig")
    r_p = c3.number_input("r (cc)", value=0.05, step=0.005, format="%.4f", key="gbm_r")
    T_p = c4.number_input("T (años)", value=1.0, step=0.25, key="gbm_T")

    n_paths = st.slider("Cantidad de paths", 5, 200, 50)
    n_steps = 252
    dt = T_p / n_steps

    rng = np.random.RandomState(42)
    Z = rng.normal(0, 1, (n_paths, n_steps))
    log_returns = (r_p - 0.5 * sigma_p ** 2) * dt + sigma_p * sqrt(dt) * Z
    log_S = np.cumsum(log_returns, axis=1)
    paths = S0_p * np.exp(log_S)
    paths = np.concatenate([np.full((n_paths, 1), S0_p), paths], axis=1)

    times = np.linspace(0, T_p, n_steps + 1)
    fig = go.Figure()
    for i in range(n_paths):
        fig.add_trace(go.Scatter(x=times, y=paths[i], mode="lines",
                                 line=dict(color="rgba(212, 175, 55, 0.15)", width=1),
                                 showlegend=False, hoverinfo="skip"))
    # E[S_T] = S0 * exp(r*T)
    mean_path = S0_p * np.exp(r_p * times)
    fig.add_trace(go.Scatter(x=times, y=mean_path, mode="lines", name="E[S_t] = S₀·e^{rt}",
                             line=dict(color="#3fb950", width=2.5)))
    fig.update_layout(template="plotly_dark", height=400,
                      title=f"Paths GBM (μ=r=q en risk-neutral) — {n_paths} simulaciones",
                      xaxis_title="t (años)", yaxis_title="S",
                      margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig, use_container_width=True)

    # Histograma de S_T
    S_T = paths[:, -1]
    fig2 = go.Figure()
    fig2.add_trace(go.Histogram(x=S_T, marker_color="#d4af37", nbinsx=30, name="S_T sim"))
    fig2.add_vline(x=S0_p * exp(r_p * T_p), line=dict(color="#3fb950", dash="dash"),
                   annotation_text=f"E[S_T] = {S0_p * exp(r_p * T_p):.2f}")
    fig2.update_layout(template="plotly_dark", height=300,
                       title="Distribución terminal S_T (lognormal)",
                       margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig2, use_container_width=True)

with tab4:
    st.markdown(r"""
**Black-Scholes-Merton** (Hull 15.8):

$$c = S_0 e^{-qT} N(d_1) - K e^{-rT} N(d_2)$$
$$p = K e^{-rT} N(-d_2) - S_0 e^{-qT} N(-d_1)$$

con

$$d_1 = \frac{\ln(S_0/K) + (r - q + \tfrac{1}{2}\sigma^2)T}{\sigma \sqrt{T}}, \quad d_2 = d_1 - \sigma \sqrt{T}$$

**Interpretación rioplatense**:
- $N(d_2)$ = probabilidad risk-neutral de terminar **in-the-money**, $P^Q(S_T > K)$.
- $N(d_1)$ = derivada del call respecto a S (es **delta** del call con q=0).
""")
    st.info("**Hull Ejemplo 14.6**: S=42, K=40, T=0.5, r=10%, σ=20%. → Call ≈ 4.7594, Put ≈ 0.8086")

    c1, c2, c3 = st.columns(3)
    S4 = c1.number_input("S₀", value=42.0, step=1.0, key="bs4_S")
    K4 = c2.number_input("K", value=40.0, step=1.0, key="bs4_K")
    T4 = c3.number_input("T", value=0.5, step=0.05, key="bs4_T")
    c4, c5, c6 = st.columns(3)
    r4 = c4.number_input("r", value=0.10, step=0.005, format="%.4f", key="bs4_r")
    sigma4 = c5.number_input("σ", value=0.20, step=0.01, format="%.4f", key="bs4_sig")
    q4 = c6.number_input("q", value=0.0, step=0.005, format="%.4f", key="bs4_q")

    try:
        d1 = (log(S4 / K4) + (r4 - q4 + 0.5 * sigma4 ** 2) * T4) / (sigma4 * sqrt(T4))
        d2 = d1 - sigma4 * sqrt(T4)
        Nd1 = norm.cdf(d1)
        Nd2 = norm.cdf(d2)
        c_val = bs_price(S4, K4, T4, r4, sigma4, q4, "call")
        p_val = bs_price(S4, K4, T4, r4, sigma4, q4, "put")

        m = st.columns(4)
        m[0].metric("d₁", f"{d1:.4f}")
        m[1].metric("d₂", f"{d2:.4f}")
        m[2].metric("N(d₁) = delta call (q=0)", f"{Nd1:.4f}")
        m[3].metric("N(d₂) = P^Q(S_T > K)", f"{Nd2:.4f}")

        m2 = st.columns(2)
        m2[0].metric("Call BSM", f"${c_val:.4f}",
                     help="Verificá Hull 14.6: si S=42,K=40,T=0.5,r=10%,σ=20% → 4.7594")
        m2[1].metric("Put BSM", f"${p_val:.4f}",
                     help="Hull 14.6 → 0.8086")
    except ValueError as e:
        st.error(f"Inputs inválidos: {e}")

    # Densidades intuitivas: pdf de S_T y región in-the-money
    if S4 > 0 and K4 > 0 and sigma4 > 0 and T4 > 0:
        S_grid = np.linspace(max(0.01, S4 * 0.2), S4 * 2.0, 400)
        mu_ln = log(S4) + (r4 - q4 - 0.5 * sigma4 ** 2) * T4
        sd_ln = sigma4 * sqrt(T4)
        pdf = (1 / (S_grid * sd_ln * sqrt(2 * np.pi))) * np.exp(
            -((np.log(S_grid) - mu_ln) ** 2) / (2 * sd_ln ** 2)
        )
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=S_grid, y=pdf, mode="lines",
                                 line=dict(color="#d4af37", width=2), name="pdf S_T"))
        mask = S_grid > K4
        fig.add_trace(go.Scatter(x=S_grid[mask], y=pdf[mask], mode="lines",
                                 fill="tozeroy", fillcolor="rgba(63, 185, 80, 0.3)",
                                 line=dict(color="#3fb950", width=1),
                                 name=f"S_T > K (área = N(d₂))"))
        fig.add_vline(x=K4, line=dict(color="#f85149", dash="dash"),
                      annotation_text="K")
        fig.update_layout(template="plotly_dark", height=380,
                          title="Densidad risk-neutral de S_T — el área verde es N(d₂)",
                          xaxis_title="S_T", yaxis_title="Densidad",
                          margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig, use_container_width=True)
