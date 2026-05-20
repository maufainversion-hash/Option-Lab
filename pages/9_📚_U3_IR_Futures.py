from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from datetime import date

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from pricing.ir_futures import (
    day_count_factor, conversion_factor, cheapest_to_deliver,
    eurodollar_convexity_adjustment, duration_based_hedge_contracts,
)
from ui.styling import inject_premium_css
from ui.components.header_strip import render_header_strip

st.set_page_config(page_title="U3 — IR Futures", page_icon="📅", layout="wide",
                   initial_sidebar_state="collapsed")
inject_premium_css()
render_header_strip()

st.markdown(
    '<h1 style="margin:0;font-weight:600;">Unidad III · IR Futures (Cap 6)</h1>'
    '<div style="color:var(--text-muted);font-size:13px;margin-bottom:20px;">'
    'Day count conventions · Treasury bond futures · Eurodollar futures · Duration hedging.'
    '</div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs([
    "Day count", "Treasury futures (CTD)", "Eurodollar + convexity", "Duration hedge"
])

with tab1:
    st.markdown(r"""
**Day count conventions** — distintas convenciones para calcular el year fraction entre
dos fechas. Hull 6.1.

| Convención | Uso típico | Fórmula |
|---|---|---|
| ACT/360 | T-bills, LIBOR, money market USA | actual_days / 360 |
| ACT/ACT | T-bonds US | actual_days / actual_days_in_year |
| 30/360 | US corp & muni bonds | (360·Δy + 30·Δm + Δd) / 360 |

Misma fecha, distinto resultado: importa porque define cuánto interés acruee un
instrumento entre dos fechas.
""")
    c1, c2 = st.columns(2)
    d1 = c1.date_input("Fecha 1", value=date(2025, 3, 1), key="dc_d1")
    d2 = c2.date_input("Fecha 2", value=date(2025, 9, 1), key="dc_d2")

    if d2 >= d1:
        results = {conv: day_count_factor(d1, d2, conv)
                   for conv in ["ACT/360", "ACT/ACT", "30/360"]}
        cols = st.columns(3)
        for col, (conv, val) in zip(cols, results.items()):
            col.metric(conv, f"{val:.6f}",
                       help=f"{val*360:.0f} unidades sobre el denominator de la convención")
    else:
        st.error("Fecha 2 debe ser >= Fecha 1")

    st.caption("**Hull says:** la convención ACT/360 hace que un instrumento money-market "
               "siempre acruee un poquito más del 'año verdadero' — eso era una herencia de "
               "cuando los cálculos se hacían a mano.")

with tab2:
    st.markdown(r"""
**Treasury bond futures (CBOT)** — contrato de futuros sobre Treasury bonds de US.
El short tiene la opción de entregar **cualquiera** de varios bonos elegibles. Para
hacer eso equitativo, cada bono tiene un **conversion factor (CF)**: el "precio teórico"
de ese bono al yield estándar de 6% semianual.

**Cash recibido por el short al entregar** = settlement_price × CF + accrued interest

**Cost of delivery** = quoted_price + accrued − cash recibido = quoted_price − settlement × CF

El bono con menor cost of delivery es el **cheapest-to-deliver (CTD)**.
""")
    st.subheader("Calculadora de conversion factor")
    c1, c2 = st.columns(2)
    coupon = c1.slider("Cupón del bono (anual)", 0.0, 0.20, 0.12, 0.005, format="%.3f")
    ttm = c2.slider("Años a vencimiento", 1.0, 30.0, 20.0, 0.5)
    cf = conversion_factor(coupon, ttm)
    st.metric("Conversion factor", f"{cf:.6f}",
              help=f"Cupón {coupon:.1%}, plazo {ttm:.1f} años, descontado a ytm=6% semianual")
    st.caption(f"**Sanity check:** un bono con cupón = 6% (igual al ytm de referencia CBOT) "
               f"debe dar CF = 1.0 exacto. Probá: poné cupón en 0.060.")
    st.caption(f"Hull Cap 6, ejemplo conceptual: cupón 12%, 20 años → CF en el orden de 1.69-1.70. "
               f"Tu cálculo: {cf:.4f}.")

    st.divider()
    st.subheader("Cheapest-to-deliver entre múltiples bonos")
    default_bonds = pd.DataFrame({
        "name": ["Bond A (6% 18y)", "Bond B (12% 20y)", "Bond C (8% 25y)"],
        "quoted_price": [99.50, 143.50, 119.75],
        "conversion_factor": [1.0382, 1.6929, 1.2230],
    })
    edited = st.data_editor(default_bonds, use_container_width=True,
                            num_rows="dynamic", hide_index=True)
    settlement = st.number_input("Settlement price del futuro", value=93.25, step=0.25)

    bonds_list = edited.to_dict(orient="records")
    try:
        ctd = cheapest_to_deliver(bonds_list, settlement)
        costs = []
        for b in bonds_list:
            cost = b["quoted_price"] - settlement * b["conversion_factor"]
            costs.append({
                "Bono": b["name"], "Quoted": f"${b['quoted_price']:.2f}",
                "CF": f"{b['conversion_factor']:.4f}",
                "Cost of delivery": f"${cost:.4f}",
                "CTD?": "✅" if b["name"] == ctd.bond_name else "",
            })
        st.dataframe(pd.DataFrame(costs), hide_index=True, use_container_width=True)
        st.success(f"**Cheapest to deliver: {ctd.bond_name}** "
                   f"(cost = ${ctd.cost_of_delivery:.4f})")
    except (KeyError, ValueError) as e:
        st.error(f"Error: {e}")

with tab3:
    st.markdown(r"""
**Eurodollar futures** — futuros sobre la tasa LIBOR de 3 meses. Quoted como 100 − rate.
Una posición LONG en el futuro gana si la tasa BAJA.

**Convexity adjustment** (Hull 6.3): el forward rate implícito en el futures rate NO es
idéntico al forward rate verdadero porque el daily mark-to-market introduce convexidad:

$$\text{forward\_rate} \approx \text{futures\_rate} - \frac{1}{2}\sigma^2 T_1 T_2$$

El ajuste crece cuadráticamente con T — para plazos cortos es despreciable, para 5-10
años se vuelve significativo.
""")
    c1, c2, c3, c4 = st.columns(4)
    sigma = c1.slider("σ (vol del corto)", 0.001, 0.03, 0.012, 0.001, format="%.4f")
    T1 = c2.slider("T₁ (maturity futuro, años)", 0.25, 10.0, 8.0, 0.25)
    T2 = c3.slider("T₂ (fin del rate, años)", 0.25, 10.5, 8.25, 0.25)
    futures_rate = c4.number_input("Futures rate", value=0.065, step=0.005, format="%.4f")

    if T2 > T1:
        adj = eurodollar_convexity_adjustment(sigma, T1, T2)
        forward = futures_rate - adj
        m1, m2, m3 = st.columns(3)
        m1.metric("Convexity adjustment", f"{adj*10000:.2f} bps")
        m2.metric("Futures rate", f"{futures_rate:.4%}")
        m3.metric("Forward rate implícita", f"{forward:.4%}")

        T1s = np.linspace(0.25, 10, 50)
        adjs = [eurodollar_convexity_adjustment(sigma, t, t + 0.25) * 10000 for t in T1s]
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=T1s, y=adjs, mode="lines",
                                 line=dict(color="#d4af37", width=2.5)))
        fig.add_vline(x=T1, line=dict(color="#3fb950", dash="dash"),
                      annotation_text=f"T₁ = {T1:.2f}")
        fig.update_layout(template="plotly_dark", height=380,
                          title="Convexity adjustment (bps) vs maturity del futuro",
                          xaxis_title="T₁ (años)", yaxis_title="Adjustment (bps)",
                          margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("T₂ debe ser > T₁")

    st.caption("**Hull says:** el ajuste viene de que el largo del futuro recibe cash diariamente "
               "cuando los rates bajan (y los reinviste a tasas más bajas), un efecto malo. "
               "Por eso el futures rate cotiza más alto que el forward rate teórico.")

with tab4:
    st.markdown(r"""
**Duration-based hedge** (Hull 6.4): hedgeás un portfolio de duration $D_P$ con futuros
de IR de duration $D_F$. El número óptimo de contratos a vender:

$$N^* = \frac{P \cdot D_P}{V_F \cdot D_F}$$

donde $P$ es el valor del portfolio, $V_F$ = precio del futuro × multiplicador del contrato.
Asumimos shift paralelo de la curva (la limitación clásica de duration hedging).
""")
    c1, c2 = st.columns(2)
    P = c1.number_input("Valor del portfolio", value=10_000_000.0, step=100_000.0)
    D_P = c2.number_input("Duration del portfolio (años)", value=6.80, step=0.10)

    c3, c4, c5 = st.columns(3)
    F = c3.number_input("Precio del futuro (cotizado)", value=93.25, step=0.25)
    D_F = c4.number_input("Duration del CTD (años)", value=9.20, step=0.10)
    mult = c5.number_input("Multiplicador (T-bond = $1.000)", value=1000.0, step=100.0)

    try:
        N = duration_based_hedge_contracts(P, D_P, F, D_F, mult)
        st.metric("Contratos a vender (N*)", f"{N:.1f}",
                  help="Redondear al entero más cercano en la operativa real")

        delta_y = st.slider("Shift paralelo de la curva (bps)", -200, 200, 100, 10)
        d_yield = delta_y / 10000
        delta_P_unhedged = -P * D_P * d_yield
        delta_VF = -F * mult * D_F * d_yield
        delta_P_hedged = delta_P_unhedged - N * delta_VF
        m1, m2 = st.columns(2)
        m1.metric("ΔP portfolio sin hedge", f"${delta_P_unhedged:+,.0f}")
        m2.metric("ΔP portfolio con hedge", f"${delta_P_hedged:+,.0f}",
                  help="Debería estar cerca de 0 si el shift es paralelo y N* es correcto")
    except ValueError as e:
        st.error(f"Inputs inválidos: {e}")

    st.caption("**Hull says:** la duration hedge solo neutraliza el riesgo de un shift "
               "paralelo. Si la curva cambia de pendiente (steepening / flattening), te queda "
               "exposición residual. Por eso bancos usan key-rate duration o full revaluation.")
