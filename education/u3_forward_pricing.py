from __future__ import annotations

from math import log as ln

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from pricing.forwards import forward_price, cost_of_carry
from pricing.forward_valuation import value_forward_position


def render() -> None:
    st.markdown(
        '<h1 style="margin:0;font-weight:600;">Unidad III · Valuación de forwards y futuros</h1>'
        '<div style="color:var(--text-muted);font-size:13px;margin-bottom:20px;">'
        'Hull Cap 5 y 6. Cost of carry, dividends, storage, contango/backwardation.'
        '</div>', unsafe_allow_html=True)

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Pricing genérico",
        "Contango vs Backwardation",
        "Convenience yield",
        "Valor de la Posición",
        "C&C vs RC&C (timeline)",
        "Forward FX (escenarios)",
    ])

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

    with tab4:
        st.header("Valor de una Posición Forward Existente")
        st.markdown(r"""
**Concepto**

Una vez que entrás en un contrato forward a un precio de entrega K, su valor cambia
a medida que el precio forward actual F₀ se mueve.

**Fórmula** (Hull 5.4):

$$f = (F_0 - K) \cdot e^{-rT}$$

Donde:
- **f**: valor de la posición long (positivo si ganaste, negativo si perdiste)
- **F₀**: precio forward actual para vencimiento T (calculado desde el spot)
- **K**: precio de entrega pactado en tu contrato
- **r**: tasa risk-free continua
- **T**: tiempo al vencimiento (años)

**Intuición:** la diferencia F₀ − K es lo que ganarías/perderías en el futuro.
Lo traés a presente con e^(−rT).
""")
        st.markdown("---")
        st.subheader("📊 Calculadora")

        cA, cB = st.columns(2)
        with cA:
            spot_pos = st.number_input(
                "Precio Spot Actual (S₀)", value=25.0, step=0.5,
                help="Precio actual del activo subyacente",
                key="fp_spot",
            )
            delivery_pos = st.number_input(
                "Precio de Entrega Pactado (K)", value=24.0, step=0.5,
                help="Precio K acordado en tu contrato forward",
                key="fp_K",
            )
            rf_pos = st.number_input(
                "Tasa Risk-Free (%)", value=5.0, step=0.5,
                help="Tasa continua anual", key="fp_r",
            ) / 100
        with cB:
            ttm_pos = st.number_input(
                "Tiempo al Vencimiento (años)", value=0.5, step=0.1,
                min_value=0.01, key="fp_T",
            )
            carry_pos = st.number_input(
                "Cost of Carry (% anual)", value=0.0, step=0.5,
                help="Storage − income. Para acciones con dividendos: poner −yield",
                key="fp_carry",
            ) / 100

        result = value_forward_position(spot_pos, delivery_pos, rf_pos, ttm_pos, carry_pos)

        st.markdown("---")
        st.subheader("📈 Resultados")
        m1, m2, m3 = st.columns(3)
        m1.metric("Forward Actual (F₀)", f"${result['forward_price']:.4f}",
                  help="Precio forward para este vencimiento hoy")
        valor = result["position_value"]
        m2.metric("Valor Posición Long", f"${valor:.4f}",
                  delta="ganancia" if valor > 0 else ("pérdida" if valor < 0 else "—"),
                  help="Si entraste long forward a K, este es tu P&L actual descontado")
        m3.metric("Valor Posición Short", f"${result['position_value_short']:.4f}",
                  help="Valor si entraste short forward a K")

        st.markdown("---")
        st.subheader("💡 Interpretación")
        if valor > 0.005:
            st.success(
                f"**Posición long ganando ${abs(valor):.2f}**\n\n"
                f"El precio forward actual (F₀ = ${result['forward_price']:.2f}) es "
                f"mayor que tu precio de entrega (K = ${delivery_pos:.2f}). Si cerraras "
                f"la posición hoy entrando short a F₀, ganarías "
                f"(F₀ − K)·e^(−rT) = ${valor:.4f}."
            )
        elif valor < -0.005:
            st.error(
                f"**Posición long perdiendo ${abs(valor):.2f}**\n\n"
                f"El precio forward actual (F₀ = ${result['forward_price']:.2f}) es "
                f"menor que tu precio de entrega (K = ${delivery_pos:.2f}). La posición "
                f"tiene valor negativo."
            )
        else:
            st.info("La posición está at-the-money (F₀ ≈ K), valor cercano a cero.")

        with st.expander("📖 Ejemplo paso a paso (Hull-style 5.3)"):
            st.markdown(r"""
**Enunciado:**

- Entraste **long forward** en petróleo a K = $24/barril
- Hoy el spot está en S₀ = $25
- Tasa risk-free r = 5% continua
- Vencimiento en T = 6 meses (0.5 años)

**Solución paso a paso:**

1. **Calculá el forward actual:**
   $$F_0 = S_0 \cdot e^{rT} = 25 \cdot e^{0.05 \times 0.5} = 25 \cdot 1.02532 = \$25.633$$

2. **Valor de tu posición long:**
   $$f = (F_0 - K) \cdot e^{-rT} = (25.633 - 24) \cdot e^{-0.025}$$
   $$f = 1.633 \times 0.9753 = \$1.5926$$

**Interpretación:** tu contrato long a $24 tiene un valor actual de **$1.5926
por barril**. Ganaste porque F₀ ($25.633) > K ($24).

> Probá los inputs default (S₀=25, K=24, r=5%, T=0.5) en la calculadora de
> arriba y deberías ver exactamente este resultado.
""")

    with tab5:
        st.header("Cash & Carry vs Reverse Cash & Carry — Timeline")
        st.markdown(r"""
Estas son las dos estrategias de **arbitraje** que enforce el forward price.

**Cash & Carry (C&C)** se ejecuta cuando el **forward está caro** (F₀ > S₀·e^{rT}):
1. **t=0**: pedís prestado $S₀$, comprás el activo spot, shorteás el forward a F₀.
2. **t=T**: entregás el activo, cobrás K=F₀, devolvés el préstamo S₀·e^{rT}.
3. **Profit risk-free**: F₀ − S₀·e^{rT} > 0. Arbitraje puro.

**Reverse Cash & Carry (RC&C)** se ejecuta cuando el **forward está barato** (F₀ < S₀·e^{rT}):
1. **t=0**: shorteás el activo (cobrás S₀), invertís a la tasa, vas long el forward a F₀.
2. **t=T**: cobrás S₀·e^{rT}, comprás el activo a F₀, devolvés el short.
3. **Profit risk-free**: S₀·e^{rT} − F₀ > 0.

En equilibrio: **F₀ = S₀·e^{rT}** (los arbitrajistas presionan el precio hasta ahí).
""")

        st.subheader("Calculadora — dos escenarios lado a lado")
        c1, c2, c3 = st.columns(3)
        S_cc = c1.number_input("Spot S₀", value=40.0, step=1.0, key="cc_S")
        r_cc = c2.number_input("Tasa r (cc)", value=0.05, step=0.005,
                                format="%.4f", key="cc_r")
        T_cc = c3.number_input("T (años)", value=1.0, step=0.25, key="cc_T")

        F_fair = S_cc * np.exp(r_cc * T_cc)
        st.caption(f"**Forward justo (no-arbitraje)**: F₀* = S₀·e^(rT) = {F_fair:.4f}")

        c4, c5 = st.columns(2)
        F_high = c4.number_input("F₀ observado (escenario CARO)",
                                  value=float(F_fair) + 3.0, step=0.5, key="cc_Fhigh")
        F_low = c5.number_input("F₀ observado (escenario BARATO)",
                                 value=float(F_fair) - 3.0, step=0.5, key="cc_Flow")

        st.markdown("---")
        col_cc, col_rc = st.columns(2)
        with col_cc:
            st.markdown(
                f'<div class="premium-card" style="border-left:3px solid var(--positive);'
                f'background:rgba(63,185,80,0.05);">'
                f'<div style="color:var(--positive);font-weight:600;font-size:16px;">'
                f'▲ CASH & CARRY (F₀={F_high:.2f} &gt; F* = {F_fair:.2f})</div>'
                f'<div style="font-family:JetBrains Mono;font-size:13px;color:var(--text);'
                f'margin-top:10px;line-height:1.7;">'
                f'<b>t=0</b>:<br>'
                f'&nbsp;&nbsp;• Pedís prestado ${S_cc:.2f} a tasa {r_cc*100:.2f}%<br>'
                f'&nbsp;&nbsp;• Comprás activo spot (cash out ${S_cc:.2f})<br>'
                f'&nbsp;&nbsp;• Shorteás forward a {F_high:.2f}<br>'
                f'&nbsp;&nbsp;• Cash flow neto: <b>$0</b><br><br>'
                f'<b>t=T (T={T_cc:.2f} años)</b>:<br>'
                f'&nbsp;&nbsp;• Entregás activo (sale del balance)<br>'
                f'&nbsp;&nbsp;• Cobrás forward: <b style="color:var(--positive);">+${F_high:.2f}</b><br>'
                f'&nbsp;&nbsp;• Devolvés préstamo: <b style="color:var(--negative);">−${F_fair:.2f}</b><br>'
                f'&nbsp;&nbsp;• Profit risk-free: <b style="color:var(--accent);font-size:18px;">'
                f'${F_high - F_fair:+.4f}</b>'
                f'</div></div>', unsafe_allow_html=True,
            )
        with col_rc:
            st.markdown(
                f'<div class="premium-card" style="border-left:3px solid var(--negative);'
                f'background:rgba(248,81,73,0.05);">'
                f'<div style="color:var(--negative);font-weight:600;font-size:16px;">'
                f'▼ REVERSE C&C (F₀={F_low:.2f} &lt; F* = {F_fair:.2f})</div>'
                f'<div style="font-family:JetBrains Mono;font-size:13px;color:var(--text);'
                f'margin-top:10px;line-height:1.7;">'
                f'<b>t=0</b>:<br>'
                f'&nbsp;&nbsp;• Shorteás activo spot (cash in ${S_cc:.2f})<br>'
                f'&nbsp;&nbsp;• Invertís ${S_cc:.2f} a tasa {r_cc*100:.2f}%<br>'
                f'&nbsp;&nbsp;• Long forward a {F_low:.2f}<br>'
                f'&nbsp;&nbsp;• Cash flow neto: <b>$0</b><br><br>'
                f'<b>t=T (T={T_cc:.2f} años)</b>:<br>'
                f'&nbsp;&nbsp;• Recibís inversión: <b style="color:var(--positive);">+${F_fair:.2f}</b><br>'
                f'&nbsp;&nbsp;• Comprás activo via forward: <b style="color:var(--negative);">−${F_low:.2f}</b><br>'
                f'&nbsp;&nbsp;• Cubrís el short (activo va al lender)<br>'
                f'&nbsp;&nbsp;• Profit risk-free: <b style="color:var(--accent);font-size:18px;">'
                f'${F_fair - F_low:+.4f}</b>'
                f'</div></div>', unsafe_allow_html=True,
            )

        st.info(
            "**Cuando el mercado está en equilibrio**, F₀ = F* exactamente y NO hay "
            "arbitraje. Cualquier desvío (asumiendo costos de transacción cero) sería "
            "explotado por los arbitrajistas hasta cerrar el spread."
        )

    with tab6:
        st.header("Forward de Monedas — escenarios AUDUSD")
        st.markdown(r"""
Un exportador australiano va a cobrar **AUD 1,000,000** en T años. Para fijar
el valor en USD, puede entrar a un forward FX. Veamos cómo termina el resultado
en distintos escenarios de spot al vencimiento.

**Datos**: spot AUDUSD = 0.8000, forward 1Y = 0.8100, monto cobrado AUD 1M, T=1.

El forward implícito (covered interest parity): el AUD se aprecia (USD se deprecia)
hacia 0.8100 a 1 año.
""")
        cc1, cc2, cc3, cc4 = st.columns(4)
        spot_fx = cc1.number_input("Spot AUDUSD (USD por AUD)", value=0.8000,
                                    step=0.01, format="%.4f", key="fx_spot")
        fwd_fx = cc2.number_input("Forward 1Y", value=0.8100, step=0.01,
                                   format="%.4f", key="fx_fwd")
        aud_amount = cc3.number_input("Monto AUD a cobrar", value=1_000_000,
                                       step=10000, key="fx_aud")
        t_fwd = cc4.number_input("T (años)", value=1.0, step=0.25, key="fx_T")

        st.markdown("---")
        st.subheader("Comparación: con hedge vs sin hedge bajo 4 escenarios de spot a vencimiento")

        scenarios = []
        for st_t in [0.7500, 0.8000, 0.8500, 0.9000]:
            # Sin hedge: cobra AUD, convierte al spot del momento
            usd_unhedged = aud_amount * st_t
            # Con hedge (long forward AUD): convierte al rate forward
            usd_hedged = aud_amount * fwd_fx
            # P&L del hedge (con respecto a no hedgear)
            hedge_pnl = usd_hedged - usd_unhedged
            scenarios.append({
                "Spot AUDUSD en T": f"{st_t:.4f}",
                "USD sin hedge": f"${usd_unhedged:,.0f}",
                "USD con forward": f"${usd_hedged:,.0f}",
                "P&L hedge": f"${hedge_pnl:+,.0f}",
            })

        df_fx = pd.DataFrame(scenarios)
        st.dataframe(df_fx, hide_index=True, use_container_width=True)

        st.markdown("---")
        # Plot del payoff del hedge
        st_grid = np.linspace(0.65, 0.95, 60)
        usd_unhedged_grid = aud_amount * st_grid
        usd_hedged_grid = np.full_like(st_grid, aud_amount * fwd_fx)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=st_grid, y=usd_unhedged_grid / 1e6, mode="lines",
                                  name="Sin hedge", line=dict(color="#f85149", width=2)))
        fig.add_trace(go.Scatter(x=st_grid, y=usd_hedged_grid / 1e6, mode="lines",
                                  name="Con forward (fija a F₀)", line=dict(color="#3fb950", width=2.5)))
        fig.add_vline(x=spot_fx, line=dict(color="white", dash="dot"),
                       annotation_text=f"Spot inicial {spot_fx:.4f}")
        fig.add_vline(x=fwd_fx, line=dict(color="#d4af37", dash="dash"),
                       annotation_text=f"Forward {fwd_fx:.4f}")
        fig.update_layout(template="plotly_dark", height=380,
                           title="USD recibidos al vencimiento por AUD 1M cobrados",
                           xaxis_title="Spot AUDUSD al vencimiento",
                           yaxis_title="USD recibidos (millones)",
                           margin=dict(l=10, r=10, t=40, b=10),
                           legend=dict(orientation="h", yanchor="bottom", y=1.02))
        st.plotly_chart(fig, use_container_width=True)

        st.info(
            f"**Insight**: el forward te fija el USD a recibir en exactamente "
            f"${aud_amount * fwd_fx:,.0f}, sin importar dónde termine el spot. "
            f"Si el AUD se aprecia más allá de {fwd_fx:.4f}, hubieras estado mejor "
            f"sin hedge — pero ese es el precio de la **certeza**."
        )
