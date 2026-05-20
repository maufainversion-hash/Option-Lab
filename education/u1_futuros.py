from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def render() -> None:
    st.markdown(
        '<h1 style="margin:0;font-weight:600;">Unidad I · Intro y mecánica de futuros</h1>'
        '<div style="color:var(--text-muted);font-size:13px;margin-bottom:20px;">'
        'Hull Cap 1 y 2 · UADE IFD I. Mecánica del contrato, mark-to-market, margins.'
        '</div>', unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs([
        "Forward vs Futuro",
        "Mark-to-Market",
        "Convergencia spot-futuro",
        "Especulación y Apalancamiento",
    ])

    with tab1:
        st.markdown("""
    **Forward** — contrato bilateral, sin clearing, sin colateral diario, liquidación una sola
    vez al vencimiento. P&L = (S_T − K) × notional.

    **Futuro** — estandarizado, listado en exchange (CME, ICE, MATBA Rofex), con clearing house,
    margins iniciales y diarios (mark-to-market). Permite cerrar posición offsetting.
    """)

        st.subheader("Comparación completa: Exchange (Futuros) vs OTC (Forwards)")
        comparison_data = pd.DataFrame({
            "Característica": [
                "Negociación", "Contratos", "Liquidez", "Riesgo de contraparte",
                "Margen", "Settlement", "Regulación", "Flexibilidad",
            ],
            "Exchange (Futuros)": [
                "Exchange centralizado (CME, MATBA Rofex)",
                "Estandarizados (tamaño y vencimiento fijo)",
                "Alta — mercado secundario activo",
                "Mínimo — cámara compensadora interviene",
                "Requerido (inicial + mantenimiento)",
                "Daily marking-to-market",
                "Fuerte supervisión regulatoria",
                "Baja — términos fijos",
            ],
            "OTC (Forwards)": [
                "Bilateral entre dos partes",
                "Customizados a medida del cliente",
                "Baja — difícil salir antes del vencimiento",
                "Alto — depende de la contraparte",
                "No requerido (o negociado bilateralmente)",
                "Una sola vez al vencimiento",
                "Menos regulados",
                "Alta — términos negociables",
            ],
        })
        st.dataframe(comparison_data, hide_index=True, use_container_width=True)

        st.info(
            "**Cuándo usar cada uno**: futuros si necesitás liquidez y querés minimizar "
            "riesgo de contraparte. Forwards si necesitás términos exactos (fecha/monto "
            "específicos) y tenés confianza en la contraparte."
        )

        with st.expander("📖 Resumen / Hull pp. 6-10 + Cap 2"):
            st.markdown("""
    Hull Cap 1: el derivado es un instrumento cuyo valor deriva del precio de otro asset.
    Las cuatro categorías: forwards, futuros, opciones, swaps.

    Hull Cap 2: el rol de la **clearing house** es interponerse entre comprador y vendedor —
    cada participante tiene la CH como contraparte, no al otro lado del trade. Por eso
    el counterparty risk se mitiga: si vos default-eás, los demás no sufren porque la CH
    absorbe via el sistema de margins.

    **Margin calls**: si tu balance cae por debajo del *maintenance margin level*, el broker
    te llama para reponer al *initial margin level*. Si no respondés, te liquidan la posición.
    """)

    with tab2:
        st.markdown("""
    **Mark-to-market diario** — la posición se revalúa cada día y la diferencia se cobra o
    se paga via la cuenta de margin. Si la margin baja del *maintenance level*, hay
    **margin call** y hay que reponer al *initial level*.
    """)
        c1, c2, c3, c4 = st.columns(4)
        n_contracts = c1.number_input("Contratos", min_value=1, value=10, step=1)
        contract_size = c2.number_input("Multiplicador", min_value=1.0, value=100.0, step=1.0)
        initial_margin = c3.number_input("Initial margin / contrato", min_value=100.0, value=5000.0, step=100.0)
        maintenance = c4.number_input("Maintenance margin / contrato", min_value=100.0, value=4000.0, step=100.0)

        st.subheader("Path de precios (editá la tabla)")
        default_path = pd.DataFrame({
            "Día": list(range(0, 8)),
            "Precio futuro": [60.0, 59.1, 57.2, 58.4, 56.0, 55.5, 55.8, 57.0],
        })
        edited = st.data_editor(default_path, hide_index=True, use_container_width=True, num_rows="dynamic")

        prices = edited["Precio futuro"].tolist()
        balance = n_contracts * initial_margin
        rows = []
        for i, p in enumerate(prices):
            pnl_day = 0.0 if i == 0 else n_contracts * contract_size * (p - prices[i-1])
            balance += pnl_day
            margin_call = balance < n_contracts * maintenance
            if margin_call:
                topup = n_contracts * initial_margin - balance
                balance += topup
            else:
                topup = 0.0
            rows.append({"Día": i, "Precio": p, "P&L día": pnl_day, "Balance": balance,
                         "Margin call?": "⚠️ SÍ" if margin_call else "—",
                         "Top-up": topup})
        df_mtm = pd.DataFrame(rows)
        st.dataframe(df_mtm.style.format({"Precio": "{:.2f}", "P&L día": "{:+,.0f}",
                                          "Balance": "{:,.0f}", "Top-up": "{:+,.0f}"}),
                     hide_index=True, use_container_width=True)

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_mtm["Día"], y=df_mtm["Balance"], mode="lines+markers",
                                 name="Balance", line=dict(color="#d4af37", width=2.5)))
        fig.add_hline(y=n_contracts * maintenance, line=dict(color="#f85149", dash="dash"),
                      annotation_text="Maintenance level")
        fig.add_hline(y=n_contracts * initial_margin, line=dict(color="#3fb950", dash="dot"),
                      annotation_text="Initial level")
        fig.update_layout(template="plotly_dark", height=380, margin=dict(l=10, r=10, t=40, b=10),
                          title="Evolución del balance de margin")
        st.plotly_chart(fig, use_container_width=True)

        with st.expander("📖 Ejemplo Hull — Oro (200 contratos)"):
            st.markdown("""
**Escenario clásico de Hull:**
- 200 contratos de oro (100 oz cada uno)
- Precio inicial: $1,250/oz
- Margen inicial: $6,000/contrato → **$1,200,000 total**
- Mantenimiento: $4,500/contrato → **$900,000 total**
- Día 1: precio cae a $1,239

**Análisis paso a paso:**

1. **Pérdida diaria:**
   - Caída de $11/oz × 100 oz × 200 contratos = **−$220,000**

2. **Saldo cuenta:**
   - $1,200,000 − $220,000 = **$980,000**

3. **Margin call?**
   - $980,000 > $900,000 (mantenimiento) → **NO hay margin call aún**

4. Si el precio sigue cayendo y el saldo cruza < $900,000, el broker te llama
   para reponer hasta $1,200,000 (initial level).

**Probá los inputs en el simulador**: poné 200 contratos, multiplicador 100, initial
$6000, maintenance $4500, y un path 1250 → 1239 → 1230 → 1225 → ... para reproducir
exactamente este escenario.
""")

    with tab3:
        st.markdown("""
    Al vencimiento de un futuro: **F_T → S_T** (convergencia). Si no convergiera, hay arbitraje:
    - Si F_T > S_T justo antes de vencer: short el futuro, long spot, deliver.
    - Si F_T < S_T: long futuro, recibir entrega, short spot.

    La velocidad de convergencia depende del cost of carry y la liquidez residual del contrato.
    """)
        T_total = 90
        days = np.arange(T_total + 1)
        S_path = 100 + np.cumsum(np.random.RandomState(42).normal(0, 0.3, T_total + 1))
        spread_init = 2.5
        spread_path = spread_init * (1 - days / T_total)
        F_path = S_path + spread_path

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=days, y=S_path, mode="lines", name="Spot",
                                 line=dict(color="#3fb950", width=2)))
        fig.add_trace(go.Scatter(x=days, y=F_path, mode="lines", name="Futuro",
                                 line=dict(color="#d4af37", width=2)))
        fig.update_layout(template="plotly_dark", height=380,
                          title="Convergencia futuro → spot a vencimiento",
                          xaxis_title="Días desde inicio del contrato",
                          yaxis_title="Precio", margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig, use_container_width=True)

    with tab4:
        st.header("Especulación con Futuros — el poder del apalancamiento")
        st.markdown("""
Los futuros permiten **apalancamiento**: controlás una posición grande con un capital
chico (solo el margen). Comparamos dos estrategias que toman la misma exposición:
spot vs futuros.
""")

        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### 💵 Estrategia 1 · Compra spot")
            spot_price = st.number_input("Precio spot (USD/GBP)", value=1.6000,
                                          step=0.01, format="%.4f", key="spec_spot")
            gbp_amount = st.number_input("Cantidad de GBP a controlar", value=250000,
                                          step=10000, key="spec_gbp")
            investment_spot = gbp_amount * spot_price
            st.metric("Inversión requerida", f"${investment_spot:,.0f}")

            future_spot = st.number_input("Precio spot futuro (al cerrar)",
                                           value=1.6500, step=0.01, format="%.4f",
                                           key="spec_future_spot")
            profit_spot = gbp_amount * (future_spot - spot_price)
            roi_spot = (profit_spot / investment_spot) * 100
            st.metric("Ganancia", f"${profit_spot:,.0f}")
            st.metric("ROI", f"{roi_spot:.2f}%")

        with c2:
            st.markdown("#### 📊 Estrategia 2 · Futuros GBP")
            st.markdown(
                "**Contrato GBP futuro**: £62,500 por contrato. Para controlar £"
                f"{gbp_amount:,} → ceil(£{gbp_amount:,}/£62,500) contratos."
            )
            contract_size = 62500
            n_contracts_spec = int(gbp_amount / contract_size)
            margin_per_contract = st.number_input("Margen por contrato (USD)",
                                                    value=5000, step=500,
                                                    key="spec_margin")
            investment_futures = n_contracts_spec * margin_per_contract
            st.metric("Contratos requeridos", f"{n_contracts_spec}")
            st.metric("Inversión (margen total)", f"${investment_futures:,.0f}")

            # Misma ganancia absoluta — exposición equivalente
            profit_futures = gbp_amount * (future_spot - spot_price)
            roi_futures = (profit_futures / investment_futures) * 100 if investment_futures else 0
            st.metric("Ganancia", f"${profit_futures:,.0f}")
            st.metric("ROI", f"{roi_futures:.2f}%")

        st.markdown("---")
        st.subheader("Comparación")
        ratio_investment = investment_spot / investment_futures if investment_futures else 0
        m1, m2, m3 = st.columns(3)
        m1.metric("Ratio de inversión spot/futuros", f"{ratio_investment:.1f}x",
                  help="Spot requiere X veces más capital que futuros")
        m2.metric("ROI Spot", f"{roi_spot:.2f}%")
        m3.metric("ROI Futuros", f"{roi_futures:.2f}%",
                  delta=f"{roi_futures - roi_spot:+.1f}pp")

        if profit_spot > 0:
            st.success(
                f"**Apalancamiento en acción** — ambas estrategias tienen la misma "
                f"ganancia absoluta (${profit_spot:,.0f}) porque controlan la misma "
                f"exposición (£{gbp_amount:,}). Pero futuros requieren {ratio_investment:.1f}x "
                f"menos capital, así que el ROI dispara de {roi_spot:.1f}% a "
                f"{roi_futures:.1f}%. **Cuidado**: el apalancamiento también amplifica "
                f"las pérdidas en proporción."
            )
        else:
            st.error(
                f"**Pérdida amplificada** — con futuros perdés ${abs(profit_futures):,.0f} "
                f"sobre ${investment_futures:,.0f} = {roi_futures:.1f}%. Spot perdería "
                f"lo mismo en absoluto pero sobre ${investment_spot:,.0f} = "
                f"{roi_spot:.1f}%. El apalancamiento corta en los dos sentidos."
            )

        with st.expander("📖 Por qué el ROI es tan distinto"):
            st.markdown(r"""
La ganancia absoluta depende de la **exposición** (cantidad de subyacente controlado),
no del capital invertido. Como ambas estrategias controlan la misma cantidad de GBP,
la ganancia absoluta es idéntica.

El ROI = ganancia / capital invertido. Como en futuros el capital invertido es solo el
margen (típicamente 5-15% del notional), el denominador es chico y el ROI explota.

**Riesgo**: si el spot se mueve en contra y tu balance cae bajo el maintenance level,
recibís margin calls. Sin reservas para reponer, el broker te liquida y perdés todo
el margen depositado.
""")
