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

    tab1, tab2, tab3 = st.tabs(["Forward vs Futuro", "Mark-to-Market", "Convergencia spot-futuro"])

    with tab1:
        st.markdown("""
    **Forward** — contrato bilateral, sin clearing, sin colateral diario, liquidación una sola
    vez al vencimiento. P&L = (S_T − K) × notional.

    **Futuro** — estandarizado, listado en exchange (CME, ICE, MATBA Rofex), con clearing house,
    margins iniciales y diarios (mark-to-market). Permite cerrar posición offsetting.

    | | Forward | Futuro |
    |---|---|---|
    | Mercado | OTC | Exchange |
    | Estandarización | A medida | Sí |
    | Counterparty risk | Sí (bilateral) | Mitigado por CH |
    | Margin | Generalmente no | Inicial + variación diaria |
    | Liquidación | En T | Diaria (MtM) |
    | Custom | Total | No |
    """)

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
