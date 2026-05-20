from __future__ import annotations

from math import exp, sqrt, log

import numpy as np
import plotly.graph_objects as go
from scipy.stats import norm
import streamlit as st

from pricing.black_scholes import bs_price
from pricing.binomial import crr_price, leisen_reimer_price, binomial_convergence


def render() -> None:
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
        from ui.styling import info_box as _info_box, hull_check as _hull_check
        _info_box("<b>Hull Ejemplo 13.1</b>: S=$20, u=1.1, d=0.9, K=$21, r=12%, T=3m. → C ≈ $0.633", kind="hull")

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

            mm = st.columns(3)
            mm[0].metric("p (risk-neutral)", f"{p:.4f}")
            mm[1].metric("Δ (delta replicante)", f"{delta:.4f}")
            mm[2].metric("Valor call hoy", f"${f0:.4f}")
            _hull_check(0.633, f0, label="Call price (Hull 13.1)", tolerance=0.005, units=" $")

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

        st.markdown("---")
        with st.expander("🎓 Ejemplo del docente: S=41, K=40 (dual approach)"):
            st.markdown(r"""
Resolvemos el **mismo problema con dos métodos lado a lado** para mostrar la
equivalencia conceptual entre arbitraje (replicating portfolio) y valuación
risk-neutral.

**Parámetros:**
- S₀ = $41, K = $40 (call europeo)
- T = 1 año, r = 8% (continua)
- Su = $60, Sd = $30
""")
            S0_doc, K_doc = 41.0, 40.0
            r_doc, T_doc = 0.08, 1.0
            Su_doc, Sd_doc = 60.0, 30.0
            Cu_doc = max(Su_doc - K_doc, 0)  # 20
            Cd_doc = max(Sd_doc - K_doc, 0)  # 0

            col_a, col_b = st.columns(2)

            with col_a:
                st.markdown("### Método 1 · Replicating portfolio")
                st.markdown(r"""
**Idea:** replicar el payoff del call con Δ acciones + $B en risk-free bond.
""")
                st.markdown(f"""
**Payoffs:**
- Si sube: Cu = max({Su_doc:.0f} − {K_doc:.0f}, 0) = **${Cu_doc:.0f}**
- Si baja: Cd = max({Sd_doc:.0f} − {K_doc:.0f}, 0) = **${Cd_doc:.0f}**
""")
                st.markdown("**Sistema de ecuaciones:**")
                st.latex(r"""
\begin{cases}
\Delta \cdot 60 + B \cdot e^{0.08} = 20 \\
\Delta \cdot 30 + B \cdot e^{0.08} = 0
\end{cases}
""")
                Delta_doc = (Cu_doc - Cd_doc) / (Su_doc - Sd_doc)
                B_doc = -(Sd_doc * Delta_doc) / np.exp(r_doc * T_doc)
                st.latex(rf"\Delta = \frac{{C_u - C_d}}{{S_u - S_d}} = \frac{{20 - 0}}{{60 - 30}} = \frac{{2}}{{3}}")
                st.latex(rf"B = -\frac{{S_d \cdot \Delta}}{{e^{{rT}}}} = -\frac{{30 \times (2/3)}}{{e^{{0.08}}}} = {B_doc:.4f}")
                C0_replicating = Delta_doc * S0_doc + B_doc
                st.success(
                    f"**Precio del call:** C₀ = Δ·S₀ + B = (2/3)×41 + ({B_doc:.4f}) = "
                    f"**${C0_replicating:.4f}**"
                )

            with col_b:
                st.markdown("### Método 2 · Risk-neutral valuation")
                st.markdown(r"""
**Idea:** calcular valor esperado del payoff bajo probabilidad **neutral al riesgo**.
""")
                u_doc = Su_doc / S0_doc
                d_doc = Sd_doc / S0_doc
                st.markdown(f"""
**Factores:**
- u = Su / S₀ = 60/41 = **{u_doc:.4f}**
- d = Sd / S₀ = 30/41 = **{d_doc:.4f}**
""")
                st.markdown("**Probabilidad risk-neutral:**")
                st.latex(r"p = \frac{e^{rT} - d}{u - d}")
                p_doc = (np.exp(r_doc * T_doc) - d_doc) / (u_doc - d_doc)
                st.latex(
                    rf"p = \frac{{e^{{0.08}} - {d_doc:.4f}}}{{{u_doc:.4f} - {d_doc:.4f}}} "
                    rf"= {p_doc:.4f}"
                )
                st.markdown("**Valor esperado descontado:**")
                st.latex(r"C_0 = e^{-rT}\,[p \cdot C_u + (1-p) \cdot C_d]")
                C0_riskneutral = np.exp(-r_doc * T_doc) * (p_doc * Cu_doc + (1 - p_doc) * Cd_doc)
                st.latex(
                    rf"C_0 = e^{{-0.08}}\,[{p_doc:.4f} \times 20 + {1-p_doc:.4f} \times 0] "
                    rf"= {C0_riskneutral:.4f}"
                )
                st.success(f"**Precio del call:** C₀ = **${C0_riskneutral:.4f}**")

            st.markdown("---")
            mm1, mm2, mm3 = st.columns(3)
            mm1.metric("Método 1 (Replicating)", f"${C0_replicating:.4f}")
            mm2.metric("Método 2 (Risk-Neutral)", f"${C0_riskneutral:.4f}")
            mm3.metric("Diferencia", f"${abs(C0_replicating - C0_riskneutral):.2e}",
                        help="Debería ser cero hasta precisión flotante")

            st.success(
                "**Ambos métodos dan el mismo precio**, lo cual demuestra la equivalencia "
                "conceptual entre arbitraje (replicating portfolio) y valuación risk-neutral. "
                "**Para el examen**: el docente puede pedir cualquiera de los dos métodos, "
                "o ambos. Dominá los dos."
            )

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
        from ui.styling import output_card, info_box, hull_check

        st.header("Black-Scholes-Merton — descomposición completa")
        st.markdown(r"""
    El modelo BSM (Hull Cap 15) supone que el subyacente sigue un GBM bajo la medida
    risk-neutral $\mathbb{Q}$, y deriva el precio de una opción europea como **valor esperado
    descontado** del payoff bajo esa medida.

    **Las dos fórmulas:**
    """)
        st.latex(r"c = S_0 \, e^{-qT} \, N(d_1) \;-\; K \, e^{-rT} \, N(d_2)")
        st.latex(r"p = K \, e^{-rT} \, N(-d_2) \;-\; S_0 \, e^{-qT} \, N(-d_1)")
        st.markdown("con")
        st.latex(r"d_1 = \frac{\ln(S_0/K) + (r - q + \tfrac{1}{2}\sigma^2)\,T}{\sigma\sqrt{T}}, \qquad d_2 = d_1 - \sigma\sqrt{T}")

        st.subheader("Inputs (Hull Ejemplo 14.6)")
        c1, c2, c3 = st.columns(3)
        S4 = c1.number_input("S₀", value=42.0, step=1.0, key="bsm_S")
        K4 = c2.number_input("K", value=40.0, step=1.0, key="bsm_K")
        T4 = c3.number_input("T", value=0.5, step=0.05, key="bsm_T")
        c4, c5, c6 = st.columns(3)
        r4 = c4.number_input("r (cc)", value=0.10, step=0.005, format="%.4f", key="bsm_r")
        sig4 = c5.number_input("σ", value=0.20, step=0.01, format="%.4f", key="bsm_sig")
        q4 = c6.number_input("q (div yield)", value=0.0, step=0.005, format="%.4f", key="bsm_q")

        try:
            d1 = (log(S4 / K4) + (r4 - q4 + 0.5 * sig4 ** 2) * T4) / (sig4 * sqrt(T4))
            d2 = d1 - sig4 * sqrt(T4)
            Nd1, Nd2 = norm.cdf(d1), norm.cdf(d2)
            Nmd1, Nmd2 = norm.cdf(-d1), norm.cdf(-d2)
            S_disc = S4 * exp(-q4 * T4)
            K_disc = K4 * exp(-r4 * T4)
            c_price = S_disc * Nd1 - K_disc * Nd2
            p_price = K_disc * Nmd2 - S_disc * Nmd1

            st.subheader("Descomposición del CALL en sus 4 piezas")
            cc = st.columns(4)
            cc[0].markdown(output_card("S₀·e^(-qT)", f"{S_disc:.4f}",
                                        hint="Spot ajustado por divs", color="info"),
                           unsafe_allow_html=True)
            cc[1].markdown(output_card("N(d₁)", f"{Nd1:.4f}",
                                        hint="Delta del call", color="positive"),
                           unsafe_allow_html=True)
            cc[2].markdown(output_card("K·e^(-rT)", f"{K_disc:.4f}",
                                        hint="Strike descontado a hoy", color="info"),
                           unsafe_allow_html=True)
            cc[3].markdown(output_card("N(d₂)", f"{Nd2:.4f}",
                                        hint="P risk-neutral de ejercer", color="positive"),
                           unsafe_allow_html=True)

            st.markdown(
                f'<div style="text-align:center; margin:20px 0; font-family:JetBrains Mono; '
                f'font-size:16px; color:var(--text);">'
                f'<span style="color:var(--info);">{S_disc:.4f}</span> × '
                f'<span style="color:var(--positive);">{Nd1:.4f}</span> '
                f'<span style="color:var(--text-muted);">−</span> '
                f'<span style="color:var(--info);">{K_disc:.4f}</span> × '
                f'<span style="color:var(--positive);">{Nd2:.4f}</span> = '
                f'<span style="color:var(--accent); font-size:22px; font-weight:700;">{c_price:.4f}</span>'
                f'</div>', unsafe_allow_html=True,
            )

            st.subheader("Descomposición del PUT")
            pp = st.columns(4)
            pp[0].markdown(output_card("K·e^(-rT)", f"{K_disc:.4f}",
                                        hint="Strike descontado", color="info"),
                           unsafe_allow_html=True)
            pp[1].markdown(output_card("N(−d₂)", f"{Nmd2:.4f}",
                                        hint="P risk-neutral de NO ejercer call", color="negative"),
                           unsafe_allow_html=True)
            pp[2].markdown(output_card("S₀·e^(-qT)", f"{S_disc:.4f}",
                                        hint="Spot ajustado por divs", color="info"),
                           unsafe_allow_html=True)
            pp[3].markdown(output_card("N(−d₁)", f"{Nmd1:.4f}",
                                        hint="1 − delta del call", color="negative"),
                           unsafe_allow_html=True)

            st.markdown(
                f'<div style="text-align:center; margin:20px 0; font-family:JetBrains Mono; '
                f'font-size:16px; color:var(--text);">'
                f'<span style="color:var(--info);">{K_disc:.4f}</span> × '
                f'<span style="color:var(--negative);">{Nmd2:.4f}</span> '
                f'<span style="color:var(--text-muted);">−</span> '
                f'<span style="color:var(--info);">{S_disc:.4f}</span> × '
                f'<span style="color:var(--negative);">{Nmd1:.4f}</span> = '
                f'<span style="color:var(--accent); font-size:22px; font-weight:700;">{p_price:.4f}</span>'
                f'</div>', unsafe_allow_html=True,
            )

            st.subheader("Los componentes intermedios")
            dd = st.columns(4)
            dd[0].markdown(output_card("d₁", f"{d1:.4f}"), unsafe_allow_html=True)
            dd[1].markdown(output_card("d₂", f"{d2:.4f}"), unsafe_allow_html=True)
            dd[2].markdown(output_card("σ√T", f"{sig4*sqrt(T4):.4f}",
                                        hint="d₁ − d₂", color="muted"),
                           unsafe_allow_html=True)
            dd[3].markdown(output_card("ln(S/K)", f"{log(S4/K4):.4f}",
                                        hint="Moneyness logarítmica", color="muted"),
                           unsafe_allow_html=True)

            st.subheader("Verificación contra Hull Ejemplo 14.6")
            info_box("Inputs default reproducen Hull Ejemplo 14.6. Valores esperados: "
                     "d₁=0.7693, d₂=0.6278, Call=4.7594, Put=0.8086.", kind="hull")
            hull_check(0.7693, d1, label="d₁")
            hull_check(0.6278, d2, label="d₂")
            hull_check(4.7594, c_price, label="Call price", units=" $")
            hull_check(0.8086, p_price, label="Put price", units=" $")

            st.subheader("Interpretación de cada pieza (Nielsen 1992)")
            ic1, ic2 = st.columns(2)
            with ic1:
                st.markdown(
                    '<div class="premium-card" style="border-left:3px solid var(--positive);">'
                    '<div style="color:var(--positive);font-weight:600;font-size:14px;">N(d₁) — la "delta"</div>'
                    '<div style="color:var(--text-muted);font-size:13px;margin-top:8px;line-height:1.6;">'
                    'Es la <b>fracción del subyacente</b> que necesitás mantener para replicar el call '
                    '(hedge ratio). También es la probabilidad de ejercicio bajo la medida en la que el '
                    'numerario es el stock (no el cash). Va de 0 (deep OTM) a 1 (deep ITM).'
                    '</div></div>', unsafe_allow_html=True)
            with ic2:
                st.markdown(
                    '<div class="premium-card" style="border-left:3px solid var(--accent);">'
                    '<div style="color:var(--accent);font-weight:600;font-size:14px;">N(d₂) — la probabilidad</div>'
                    '<div style="color:var(--text-muted);font-size:13px;margin-top:8px;line-height:1.6;">'
                    'Es la <b>probabilidad risk-neutral</b> de que el call termine ITM:<br>'
                    'N(d₂) = P^Q(S_T &gt; K). Es la probabilidad bajo la medida $\\mathbb{Q}$ donde todos '
                    'los activos rinden la tasa libre de riesgo r — NO bajo la medida del mundo real.'
                    '</div></div>', unsafe_allow_html=True)

            with st.expander("📐 Derivación step-by-step del PDE de BSM (Hull 15.6)"):
                st.markdown("**Paso 1 — Modelo del subyacente bajo medida real $\\mathbb{P}$:**")
                st.latex(r"dS = \mu S \, dt + \sigma S \, dz")
                st.markdown("**Paso 2 — Construir un portfolio sin riesgo.** Long Δ acciones, short 1 call:")
                st.latex(r"\Pi = -c + \Delta \cdot S")
                st.markdown("Aplicando Itô a $c(S, t)$:")
                st.latex(r"dc = \left(\frac{\partial c}{\partial t} + \mu S \frac{\partial c}{\partial S} + \frac{1}{2}\sigma^2 S^2 \frac{\partial^2 c}{\partial S^2}\right)dt + \sigma S \frac{\partial c}{\partial S}\, dz")
                st.markdown("**Paso 3 — Elegir Δ = ∂c/∂S** para cancelar el término estocástico (dz):")
                st.latex(r"d\Pi = \left(-\frac{\partial c}{\partial t} - \frac{1}{2}\sigma^2 S^2 \frac{\partial^2 c}{\partial S^2}\right)dt")
                st.markdown("**Paso 4 — Como Π es libre de riesgo**, debe rendir r:")
                st.latex(r"d\Pi = r \Pi \, dt = r\left(-c + S\frac{\partial c}{\partial S}\right)dt")
                st.markdown("**Paso 5 — Igualando y reordenando, sale el PDE de BSM:**")
                st.latex(r"\boxed{\frac{\partial c}{\partial t} + rS\frac{\partial c}{\partial S} + \frac{1}{2}\sigma^2 S^2 \frac{\partial^2 c}{\partial S^2} = rc}")
                st.markdown(r"""
    **Paso 6 — Condiciones de frontera** (call europeo): $c(S, T) = \max(S - K, 0)$.

    **Paso 7 — Solución del PDE** vía cambio de variable a heat equation, o equivalentemente
    vía valuación risk-neutral:
    """)
                st.latex(r"c = e^{-rT} \, \mathbb{E}^Q\!\left[\max(S_T - K, 0)\right]")
                st.markdown(r"""
    Bajo $\mathbb{Q}$, $S_T$ es lognormal con drift r (en lugar de μ). La integral cerrada de
    $(S_T - K)^+$ contra la densidad lognormal da exactamente la fórmula de arriba — los
    dos términos vienen de partir la integral en "valor esperado de $S_T$ dado ITM" (que da el
    término $S_0 \cdot N(d_1)$) y "K veces probabilidad de ITM" (que da $K \cdot e^{-rT} \cdot N(d_2)$).
    """)

            st.subheader("N(d₁) y N(d₂) vs moneyness")
            st.caption("Mirá cómo ambas crecen de 0 a 1 a medida que el call se vuelve ITM. "
                       "Siempre N(d₁) ≥ N(d₂) (porque d₁ ≥ d₂).")
            S_grid = np.linspace(K4 * 0.5, K4 * 1.5, 100)
            d1_grid = [(log(s/K4) + (r4 - q4 + 0.5*sig4**2)*T4) / (sig4*sqrt(T4)) for s in S_grid]
            d2_grid = [d - sig4*sqrt(T4) for d in d1_grid]
            Nd1_grid = [norm.cdf(d) for d in d1_grid]
            Nd2_grid = [norm.cdf(d) for d in d2_grid]
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=S_grid, y=Nd1_grid, mode="lines",
                                     line=dict(color="#3fb950", width=2.5), name="N(d₁) — delta"))
            fig.add_trace(go.Scatter(x=S_grid, y=Nd2_grid, mode="lines",
                                     line=dict(color="#d4af37", width=2.5), name="N(d₂) — P^Q(ITM)"))
            fig.add_vline(x=K4, line=dict(color="white", dash="dot"),
                          annotation_text=f"K = {K4:.2f}")
            fig.add_vline(x=S4, line=dict(color="#58a6ff", dash="dash"),
                          annotation_text=f"S₀ = {S4:.2f}")
            fig.update_layout(template="plotly_dark", height=400,
                              title="N(d₁) y N(d₂) vs spot",
                              xaxis_title="S", yaxis_title="Probabilidad",
                              margin=dict(l=10, r=10, t=40, b=10),
                              legend=dict(orientation="h", yanchor="bottom", y=1.02))
            st.plotly_chart(fig, use_container_width=True)
        except ValueError as e:
            st.error(f"Inputs inválidos: {e}")
