from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from pricing.exotic_pricing import (
    index_option_price, currency_option_price, black_option_price,
    black_delta, fx_forward_price, range_forward_strikes,
)
from pricing.black_scholes import bs_price
from ui.styling import output_card, info_box, hull_check


def render() -> None:
    st.markdown(
        '<h1 style="margin:0;font-weight:600;">Unidad VII · Opciones sobre índices, monedas y futuros</h1>'
        '<div style="color:var(--text-muted);font-size:13px;margin-bottom:20px;">'
        'Hull Cap 17 (índices + FX, Garman-Kohlhagen) y Cap 18 (futures options, Black\'s model).'
        '</div>', unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs([
        "Index options", "Currency options (G-K)", "Futures options (Black)", "Range forward"
    ])

    # ============================================================
    # TAB 1 — Index options
    # ============================================================
    with tab1:
        st.header("Opciones sobre índices (Hull 17.1)")
        st.markdown(r"""
    Una opción europea sobre un índice (S&P 500, Nasdaq, Russell) se valúa con BSM
    extendido por **Merton (1973)** para incorporar dividend yield continuo q:
    """)
        st.latex(r"c = S_0 \, e^{-qT} \, N(d_1) \;-\; K \, e^{-rT} \, N(d_2)")
        st.latex(r"d_1 = \frac{\ln(S_0/K) + (r - q + \tfrac{1}{2}\sigma^2)\,T}{\sigma\sqrt{T}}, \qquad d_2 = d_1 - \sigma\sqrt{T}")
        st.markdown(r"""
    Para el S&P 500, q típicamente está entre 1.5% y 2.5% anual continuous compounded.
    Como q es positivo, el call vale **menos** que sobre un asset sin dividendos.
    """)

        c1, c2, c3 = st.columns(3)
        S_idx = c1.number_input("Spot índice", value=4500.0, step=10.0, key="idx_S")
        K_idx = c2.number_input("Strike", value=4500.0, step=10.0, key="idx_K")
        T_idx = c3.number_input("T (años)", value=0.5, step=0.05, key="idx_T")

        c4, c5, c6 = st.columns(3)
        r_idx = c4.number_input("r", value=0.05, step=0.005, format="%.4f", key="idx_r")
        q_idx = c5.number_input("Dividend yield q", value=0.02, step=0.005, format="%.4f", key="idx_q")
        sig_idx = c6.number_input("σ", value=0.20, step=0.01, format="%.4f", key="idx_sig")

        call_idx = index_option_price(S_idx, K_idx, T_idx, r_idx, sig_idx, q_idx, "call")
        put_idx = index_option_price(S_idx, K_idx, T_idx, r_idx, sig_idx, q_idx, "put")
        call_noq = bs_price(S_idx, K_idx, T_idx, r_idx, sig_idx, 0.0, "call")
        put_noq = bs_price(S_idx, K_idx, T_idx, r_idx, sig_idx, 0.0, "put")

        st.subheader("Outputs")
        cc = st.columns(4)
        cc[0].markdown(output_card("Call (con q)", f"${call_idx:.2f}",
                                    color="positive"), unsafe_allow_html=True)
        cc[1].markdown(output_card("Put (con q)", f"${put_idx:.2f}",
                                    color="negative"), unsafe_allow_html=True)
        cc[2].markdown(output_card("Call (sin div, q=0)", f"${call_noq:.2f}",
                                    hint=f"Δ = {call_idx - call_noq:+.2f}", color="muted"),
                       unsafe_allow_html=True)
        cc[3].markdown(output_card("Put (sin div, q=0)", f"${put_noq:.2f}",
                                    hint=f"Δ = {put_idx - put_noq:+.2f}", color="muted"),
                       unsafe_allow_html=True)

        info_box("<b>Efecto de q</b>: dividendos esperados reducen el spot ex-date, "
                 "lo que <b>baja</b> el precio del call y <b>sube</b> el del put respecto al "
                 "caso sin dividendos.", kind="info")

    # ============================================================
    # TAB 2 — Currency options (Garman-Kohlhagen)
    # ============================================================
    with tab2:
        st.header("Currency options — Garman-Kohlhagen (Hull 17.2)")
        st.markdown(r"""
    Para opciones sobre tipo de cambio, la tasa extranjera $r_f$ juega el rol del
    dividend yield (porque tener la moneda extranjera te paga $r_f$):
    """)
        st.latex(r"c = S_0 \, e^{-r_f T} \, N(d_1) \;-\; K \, e^{-r_d T} \, N(d_2)")
        st.latex(r"d_1 = \frac{\ln(S_0/K) + (r_d - r_f + \tfrac{1}{2}\sigma^2)\,T}{\sigma\sqrt{T}}, \qquad d_2 = d_1 - \sigma\sqrt{T}")
        st.markdown("El **forward FX** sale de covered interest parity:")
        st.latex(r"F = S \cdot e^{(r_d - r_f) \cdot T}")
        st.markdown(r"""
    Si la tasa doméstica es más alta que la extranjera (típico USD vs JPY hace años),
    el forward **descuenta** la moneda doméstica (F > S).
    """)

        info_box("<b>Hull Ejemplo 17.2</b>: USD/GBP. S=1.6, K=1.6, T=4/12, σ=14.1%, "
                 "r_d=8%, r_f=11%. Hull cita la prima en <b>4.3 cents</b> = 0.0430.", kind="hull")

        c1, c2, c3 = st.columns(3)
        S_fx = c1.number_input("Spot FX (dom/ext)", value=1.6, step=0.01, format="%.4f", key="fx_S")
        K_fx = c2.number_input("Strike", value=1.6, step=0.01, format="%.4f", key="fx_K")
        T_fx = c3.number_input("T (años)", value=4/12, step=0.05, format="%.4f", key="fx_T")

        c4, c5, c6 = st.columns(3)
        r_d = c4.number_input("r doméstica", value=0.08, step=0.005, format="%.4f", key="fx_rd")
        r_f = c5.number_input("r extranjera", value=0.11, step=0.005, format="%.4f", key="fx_rf")
        sig_fx = c6.number_input("σ", value=0.141, step=0.005, format="%.4f", key="fx_sig")

        call_fx = currency_option_price(S_fx, K_fx, T_fx, r_d, r_f, sig_fx, "call")
        put_fx = currency_option_price(S_fx, K_fx, T_fx, r_d, r_f, sig_fx, "put")
        F_fx = fx_forward_price(S_fx, T_fx, r_d, r_f)

        st.subheader("Outputs")
        cc = st.columns(3)
        cc[0].markdown(output_card("Forward FX implícito", f"{F_fx:.6f}",
                                    hint="Por covered interest parity", color="info"),
                       unsafe_allow_html=True)
        cc[1].markdown(output_card("Call (USD por GBP)", f"{call_fx:.6f}",
                                    color="positive"), unsafe_allow_html=True)
        cc[2].markdown(output_card("Put (USD por GBP)", f"{put_fx:.6f}",
                                    color="negative"), unsafe_allow_html=True)

        hull_check(0.0430, call_fx, label="Hull 17.2 — Call USD/GBP",
                   tolerance=0.001)

        st.subheader("Sensibilidad al diferencial de tasas")
        diff_grid = np.linspace(-0.05, 0.10, 50)
        call_curve = [currency_option_price(S_fx, K_fx, T_fx, r_d, r_d - d, sig_fx, "call")
                      for d in diff_grid]
        put_curve = [currency_option_price(S_fx, K_fx, T_fx, r_d, r_d - d, sig_fx, "put")
                     for d in diff_grid]
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=diff_grid * 100, y=call_curve, mode="lines",
                                 line=dict(color="#3fb950", width=2.5), name="Call"))
        fig.add_trace(go.Scatter(x=diff_grid * 100, y=put_curve, mode="lines",
                                 line=dict(color="#f85149", width=2.5), name="Put"))
        fig.add_vline(x=(r_d - r_f) * 100, line=dict(color="#d4af37", dash="dash"),
                      annotation_text=f"Actual: {(r_d-r_f)*100:.2f}%")
        fig.update_layout(template="plotly_dark", height=380,
                          title="Precio de la opción FX vs (r_d − r_f) en %",
                          xaxis_title="Diferencial r_d − r_f (%)", yaxis_title="Premium",
                          margin=dict(l=10, r=10, t=40, b=10),
                          legend=dict(orientation="h", yanchor="bottom", y=1.02))
        st.plotly_chart(fig, use_container_width=True)

    # ============================================================
    # TAB 3 — Futures options (Black's model)
    # ============================================================
    with tab3:
        st.header("Futures options — Black's model (Hull 18.6)")
        st.markdown(r"""
    Las opciones sobre futuros se valúan con **Black's model** (1976). La diferencia
    con BSM: el subyacente es el FUTURO, no el spot. El futuro ya incorpora el cost of
    carry, así que el "growth term" en d₁ desaparece (queda solo σ²/2):
    """)
        st.latex(r"c = e^{-rT} \left[ F_0 \, N(d_1) - K \, N(d_2) \right]")
        st.latex(r"p = e^{-rT} \left[ K \, N(-d_2) - F_0 \, N(-d_1) \right]")
        st.latex(r"d_1 = \frac{\ln(F_0/K) + \tfrac{1}{2}\sigma^2 T}{\sigma\sqrt{T}}, \qquad d_2 = d_1 - \sigma\sqrt{T}")
        st.markdown(r"""
    **Equivalencia**: Black(F, K, T, r, σ) = BSM(F, K, T, r, σ, q=r). El parámetro q=r
    cancela el drift en d₁ porque (r − q) = 0.

    **Para qué se usa**: opciones sobre commodity futures (WTI crude, gold, corn),
    Treasury bond futures, Eurodollar futures. Mucho más liquidez en CME que sobre spot.
    """)

        info_box("<b>Hull Ejemplo 18.1</b>: Futures option sobre crude oil. F=20, K=20, "
                 "T=4/12, σ=25%, r=10%. Esperado call ≈ 1.116.", kind="hull")

        c1, c2, c3 = st.columns(3)
        F_in = c1.number_input("Precio futuro F₀", value=20.0, step=0.5, key="bk_F")
        K_in = c2.number_input("Strike", value=20.0, step=0.5, key="bk_K")
        T_in = c3.number_input("T (años)", value=4/12, step=0.05, format="%.4f", key="bk_T")

        c4, c5 = st.columns(2)
        r_in = c4.number_input("r (cc)", value=0.10, step=0.005, format="%.4f", key="bk_r")
        sig_in = c5.number_input("σ", value=0.25, step=0.01, format="%.4f", key="bk_sig")

        call_bk = black_option_price(F_in, K_in, T_in, r_in, sig_in, "call")
        put_bk = black_option_price(F_in, K_in, T_in, r_in, sig_in, "put")
        delta_call = black_delta(F_in, K_in, T_in, r_in, sig_in, "call")
        delta_put = black_delta(F_in, K_in, T_in, r_in, sig_in, "put")

        st.subheader("Outputs")
        cc = st.columns(4)
        cc[0].markdown(output_card("Call (Black)", f"${call_bk:.4f}",
                                    color="positive"), unsafe_allow_html=True)
        cc[1].markdown(output_card("Put (Black)", f"${put_bk:.4f}",
                                    color="negative"), unsafe_allow_html=True)
        cc[2].markdown(output_card("Δ Call", f"{delta_call:+.4f}",
                                    hint="e^(-rT)·N(d₁)", color="info"),
                       unsafe_allow_html=True)
        cc[3].markdown(output_card("Δ Put", f"{delta_put:+.4f}",
                                    hint="-e^(-rT)·N(-d₁)", color="info"),
                       unsafe_allow_html=True)

        hull_check(1.116, call_bk, label="Hull 18.1 — Call crude oil futures",
                   tolerance=0.005, units=" $")

        st.subheader("Comparación: Black vs BSM cuando F ≠ S·e^(rT)")
        st.markdown(
            "Si tomás el F del futuro y lo metés directo en BSM tratándolo como spot, "
            "obtenés un precio **diferente**. Black es el modelo correcto cuando el subyacente "
            "es el futuro."
        )
        wrong_call = bs_price(F_in, K_in, T_in, r_in, sig_in, 0.0, "call")
        comp = st.columns(2)
        comp[0].markdown(output_card("Black (correcto)", f"${call_bk:.4f}",
                                      color="positive"), unsafe_allow_html=True)
        comp[1].markdown(output_card("BSM con S=F, q=0 (mal usado)",
                                      f"${wrong_call:.4f}",
                                      hint=f"Δ vs Black: {wrong_call - call_bk:+.4f}",
                                      color="negative"), unsafe_allow_html=True)

    # ============================================================
    # TAB 4 — Range forward (FX collar zero-cost)
    # ============================================================
    with tab4:
        st.header("Range forward — collar FX zero-cost (Hull 17.4)")
        st.markdown(r"""
    Estrategia común en empresas que hedgean exposición FX. Para un **importador**
    que en T necesita comprar moneda extranjera:

    - **Long call FX** en K_call: techo a lo que va a pagar.
    - **Short put FX** en K_put: piso (renunciás a apreciaciones del FX).

    Si elegís los strikes simétricos al forward de manera tal que el premium recibido
    por el put financie el premium pagado por el call, el costo neto es **zero**.

    El precio que vas a pagar termina entre K_put y K_call: te "auto-impusiste" un
    bracket. Muy popular en commodities (range forward de oil para refinerías).
    """)

        c1, c2, c3 = st.columns(3)
        S_rf = c1.number_input("Spot FX", value=1.20, step=0.01, format="%.4f", key="rf_S")
        T_rf = c2.number_input("T (años)", value=0.5, step=0.05, key="rf_T")
        sig_rf = c3.number_input("σ", value=0.10, step=0.01, format="%.4f", key="rf_sig")

        c4, c5 = st.columns(2)
        r_d_rf = c4.number_input("r doméstica", value=0.05, step=0.005, format="%.4f", key="rf_rd")
        r_f_rf = c5.number_input("r extranjera", value=0.02, step=0.005, format="%.4f", key="rf_rf")

        F_rf = fx_forward_price(S_rf, T_rf, r_d_rf, r_f_rf)
        K_call_rf = st.slider("K_call (techo)", min_value=float(F_rf * 1.001),
                              max_value=float(F_rf * 1.15), value=float(F_rf * 1.05),
                              step=0.001, format="%.4f")

        try:
            K_put_rf = range_forward_strikes(S_rf, T_rf, r_d_rf, r_f_rf, sig_rf, K_call_rf)
            call_p = currency_option_price(S_rf, K_call_rf, T_rf, r_d_rf, r_f_rf, sig_rf, "call")
            put_p = currency_option_price(S_rf, K_put_rf, T_rf, r_d_rf, r_f_rf, sig_rf, "put")

            cc = st.columns(4)
            cc[0].markdown(output_card("Forward implícito", f"{F_rf:.4f}",
                                        color="info"), unsafe_allow_html=True)
            cc[1].markdown(output_card("K_put (piso, derivado)", f"{K_put_rf:.4f}",
                                        color="negative"), unsafe_allow_html=True)
            cc[2].markdown(output_card("K_call (techo, elegido)", f"{K_call_rf:.4f}",
                                        color="positive"), unsafe_allow_html=True)
            cc[3].markdown(output_card("Costo neto", f"{call_p - put_p:+.6f}",
                                        hint="Debería ser ≈ 0 (zero-cost)",
                                        color="muted"), unsafe_allow_html=True)

            S_grid = np.linspace(K_put_rf * 0.9, K_call_rf * 1.1, 200)
            effective_cost = np.clip(S_grid, K_put_rf, K_call_rf)
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=S_grid, y=effective_cost, mode="lines",
                                     line=dict(color="#d4af37", width=3),
                                     name="Costo efectivo (importador)"))
            fig.add_trace(go.Scatter(x=S_grid, y=S_grid, mode="lines",
                                     line=dict(color="#8b949e", width=1.5, dash="dot"),
                                     name="Sin hedge"))
            fig.add_vline(x=K_put_rf, line=dict(color="#f85149", dash="dash"),
                          annotation_text=f"K_put={K_put_rf:.4f}")
            fig.add_vline(x=K_call_rf, line=dict(color="#3fb950", dash="dash"),
                          annotation_text=f"K_call={K_call_rf:.4f}")
            fig.update_layout(template="plotly_dark", height=420,
                              title="Costo efectivo al vencimiento (importador con range forward)",
                              xaxis_title="Spot FX en T", yaxis_title="Costo efectivo",
                              margin=dict(l=10, r=10, t=40, b=10),
                              legend=dict(orientation="h", yanchor="bottom", y=1.02))
            st.plotly_chart(fig, use_container_width=True)
        except ValueError as e:
            st.error(str(e))
