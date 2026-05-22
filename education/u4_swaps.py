from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from pricing.swaps import swap_value_via_bonds, swap_par_rate
from pricing.currency_swaps import value_currency_swap_bonds, value_currency_swap_forwards
from ui.styling import output_card
from education import formulario


def render() -> None:
    st.markdown(
        '<h1 style="margin:0;font-weight:600;">Unidad IV · Swaps</h1>'
        '<div style="color:var(--text-muted);font-size:13px;margin-bottom:20px;">'
        'Hull Cap 7. Plain vanilla IR swap, valuación via bonds, par swap rate.'
        '</div>', unsafe_allow_html=True)

    tab1, tab2, tab3, tab_f = st.tabs([
        "Mecánica + cashflows",
        "Valuación (bond approach)",
        "Swaps de Monedas",
        "📐 Fórmulas",
    ])

    with tab1:
        st.markdown(r"""
    **Plain vanilla IR swap**: dos contrapartes intercambian flujos basados en un notional.
    - Una paga **fixed** (R_fix).
    - La otra paga **floating** (típicamente LIBOR/SOFR + spread).

    En cada fecha de pago, neta el diferencial. No se intercambia el notional (es un *notional*).

    Net cashflow de quien **recibe fijo** en t: $L \cdot (R_{fix} - R_{float,t-1}) \cdot \tau$
    """)
        c1, c2, c3, c4 = st.columns(4)
        L = c1.number_input("Notional", value=100_000_000.0, step=1_000_000.0)
        R_fix = c2.number_input("R_fix anual", value=0.05, step=0.005, format="%.4f")
        n_periods = c3.number_input("Períodos", min_value=1, value=6, step=1)
        accrual = c4.number_input("Accrual (años)", min_value=0.05, value=0.5, step=0.25)

        rng = np.random.RandomState(7)
        floatings = 0.04 + 0.01 * np.cumsum(rng.normal(0, 0.3, n_periods))
        floatings = np.clip(floatings, 0.01, 0.10)
        nets_receive_fix = L * (R_fix - floatings) * accrual

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=[f"T{i+1}" for i in range(n_periods)], y=nets_receive_fix,
            marker_color=["#3fb950" if v >= 0 else "#f85149" for v in nets_receive_fix],
            name="Net cashflow (recibe fijo)",
        ))
        fig.add_hline(y=0, line=dict(color="#8b949e"))
        fig.update_layout(template="plotly_dark", height=380,
                          title="Cashflows netos para quien recibe fijo",
                          margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(
            {
                "Período": [f"T{i+1}" for i in range(n_periods)],
                "Float observada": [f"{x:.4%}" for x in floatings],
                "Δ vs Fix": [f"{R_fix - x:+.4%}" for x in floatings],
                "Net CF (recibe fijo)": [f"{v:+,.0f}" for v in nets_receive_fix],
            },
            use_container_width=True, hide_index=True,
        )

    with tab2:
        st.markdown(r"""
    **Valuación por bond approach** (Hull 7.7):

    $$V_{swap}^{recibe\_fijo} = B_{fix} - B_{flt}$$

    donde B_fix es el PV del bono fijo (cupones + notional al final) y B_flt es el PV del
    bono flotante (que vale notional + próximo cupón conocido, descontado).
    """)
        c1, c2, c3 = st.columns(3)
        L2 = c1.number_input("Notional", value=100_000_000.0, step=1_000_000.0, key="vs_L")
        R_fix2 = c2.number_input("R_fix", value=0.06, step=0.005, format="%.4f", key="vs_Rfix")
        R_float_set = c3.number_input("Próx. tasa flotante seteada", value=0.057, step=0.001, format="%.4f")

        c4, c5 = st.columns(2)
        accrual2 = c4.number_input("Accrual", value=0.5, step=0.25, key="vs_acc")
        time_since = c5.number_input("Tiempo desde último reset", value=0.0, step=0.05, key="vs_ts")

        n2 = st.slider("Pagos remanentes", 1, 10, 6)
        payment_times = [accrual2 * (i + 1) for i in range(n2)]
        zeros_default = [0.045, 0.048, 0.050, 0.052, 0.054, 0.055, 0.056, 0.057, 0.058, 0.058]
        zeros = zeros_default[:n2]

        result = swap_value_via_bonds(
            notional=L2, fixed_rate=R_fix2, payment_times=payment_times,
            zero_rates=zeros, next_floating_rate=R_float_set,
            time_since_last_reset=time_since, accrual=accrual2,
            position="receive_fixed",
        )

        v_color = "positive" if result.swap_value >= 0 else "negative"
        sc = st.columns(3)
        sc[0].markdown(output_card("B_fix (PV bono fijo)", f"${result.bond_fixed_value:,.0f}",
                                    color="info"), unsafe_allow_html=True)
        sc[1].markdown(output_card("B_flt (PV bono flotante)", f"${result.bond_floating_value:,.0f}",
                                    color="info"), unsafe_allow_html=True)
        sc[2].markdown(output_card("V_swap (recibe fijo)", f"${result.swap_value:+,.0f}",
                                    color=v_color, hint="B_fix − B_flt"),
                       unsafe_allow_html=True)

        par = swap_par_rate(payment_times, zeros, accrual2)
        st.markdown(output_card("Par swap rate (que haría V=0)", f"{par*100:.4f}%",
                                color="accent", hint="La tasa fija que pone V_swap = 0 al iniciar"),
                    unsafe_allow_html=True)

        st.subheader("Zero curve usada")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=payment_times, y=[z * 100 for z in zeros],
                                 mode="lines+markers",
                                 line=dict(color="#d4af37", width=2.5),
                                 marker=dict(size=8)))
        fig.update_layout(template="plotly_dark", height=300,
                          xaxis_title="T (años)", yaxis_title="Zero rate (%)",
                          margin=dict(l=10, r=10, t=20, b=10))
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Cashflows del swap (perspectiva receive-fixed)")
        fixed_cfs = [L2 * R_fix2 * accrual2 for _ in payment_times]
        floating_cfs = [L2 * z * accrual2 for z in zeros]
        fig_cf = go.Figure()
        fig_cf.add_trace(go.Bar(x=[f"T={t:.2f}" for t in payment_times], y=fixed_cfs,
                                 name="Pierna fija (cobra)", marker_color="#3fb950"))
        fig_cf.add_trace(go.Bar(x=[f"T={t:.2f}" for t in payment_times],
                                 y=[-c for c in floating_cfs],
                                 name="Pierna flotante (paga)", marker_color="#f85149"))
        fig_cf.update_layout(template="plotly_dark", barmode="relative", height=350,
                             title="Cashflows nominales: recibe fijo, paga flotante (proyectado)",
                             margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig_cf, use_container_width=True)

        st.markdown("---")
        with st.expander("📊 Ventaja Comparativa — El 'Teorema de la Felicidad Compartida'"):
            st.markdown(r"""
Los swaps permiten **arbitrar ventajas comparativas** entre contrapartes con diferentes
calidades crediticias. Si dos empresas tienen acceso diferenciado a mercados,
pueden hacer swap y **ambas ahorrar**.

### Ejemplo: AAACorp vs BBBCorp

Dos empresas necesitan financiamiento $100M a 5 años:
- **AAACorp** (rating AAA): quiere tasa **flotante**
- **BBBCorp** (rating BBB): quiere tasa **fija**
""")
            rates_df = pd.DataFrame({
                "Empresa": ["AAACorp", "BBBCorp", "**Diferencial**"],
                "Fija": ["4.0%", "5.2%", "**1.2% (120 bps)**"],
                "Flotante": ["LIBOR − 0.1%", "LIBOR + 0.6%", "**0.7% (70 bps)**"],
            })
            st.table(rates_df)

            st.markdown(r"""
**Análisis:**

1. Diferencial en fija: 5.2% − 4.0% = **120 bps**
2. Diferencial en flotante: (LIBOR+0.6%) − (LIBOR−0.1%) = **70 bps**
3. **Ganancia total disponible** = 120 − 70 = **50 bps**

AAACorp tiene **ventaja comparativa en fija** (diferencial mayor ahí).
BBBCorp tiene **ventaja comparativa en flotante**.

### Estructura del swap (con intermediario que cobra 4 bps)

- Total disponible: 50 bps
- Intermediario: 4 bps
- Para repartir: 46 bps → **23 bps a cada empresa**
""")
            cca, ccb = st.columns(2)
            with cca:
                st.markdown("#### AAACorp (quería LIBOR)")
                st.markdown(r"""
Flujos:
- Paga 4.0% fija al mercado externo
- Recibe 4.33% del intermediario (vía swap)
- Paga LIBOR al intermediario

**Costo neto**:
""")
                st.latex(r"4.0\% - 4.33\% + \text{LIBOR} = \text{LIBOR} - 0.33\%")
                st.success("Ahorro: 23 bps vs LIBOR − 0.1% directo ✓")
            with ccb:
                st.markdown("#### BBBCorp (quería fija)")
                st.markdown(r"""
Flujos:
- Paga LIBOR + 0.6% al mercado externo
- Recibe LIBOR del intermediario
- Paga 4.37% al intermediario

**Costo neto**:
""")
                st.latex(r"\text{LIBOR} + 0.6\% - \text{LIBOR} + 4.37\% = 4.97\%")
                st.success("Ahorro: 23 bps vs 5.2% directo ✓")

            st.info(
                "**Teorema de la Felicidad Compartida** — cuando dos partes tienen "
                "ventajas comparativas opuestas en dos mercados, pueden hacer swap "
                "y **ambas mejorar**. Total: 23 + 23 + 4 = **50 bps** ✓"
            )

        with st.expander("📖 Ejemplo Hull 7.2 — WhiteRock (V = $0.5117M)"):
            st.markdown(r"""
**Parámetros:**
- WhiteRock **recibe** LIBOR 6m, **paga** 3% fijo (semestral)
- Notional: $100 millones
- Vida restante: 15 meses
- LIBOR zeros: 3m=2.8%, 9m=3.2%, 15m=3.4%
- Próxima LIBOR fijada: 2.9%
""")
            st.subheader("Pierna fija (paga 3% anual = 1.5% semestral)")
            times_wr = [0.25, 0.75, 1.25]
            fixed_cfs_wr = [1.5, 1.5, 101.5]
            zeros_wr = [0.028, 0.032, 0.034]

            fixed_rows = []
            for t, cf, z in zip(times_wr, fixed_cfs_wr, zeros_wr):
                df = np.exp(-z * t)
                pv = cf * df
                fixed_rows.append({
                    "Time (años)": t,
                    "Cash Flow ($M)": f"${cf:.2f}",
                    "Zero rate": f"{z:.1%}",
                    "DF": f"{df:.4f}",
                    "PV ($M)": f"${pv:.4f}",
                })
            st.dataframe(pd.DataFrame(fixed_rows), hide_index=True, use_container_width=True)

            B_fix_wr = sum(cf * np.exp(-z * t)
                            for cf, t, z in zip(fixed_cfs_wr, times_wr, zeros_wr))
            st.metric("B_fix (PV bono fijo)", f"${B_fix_wr:.4f}M")

            st.markdown(r"""
### Pierna flotante (recibe LIBOR)

El próximo pago ya está **fijado** por la LIBOR observada (2.9%):
- Cupón conocido = $100M × 2.9% × 0.5 = **$1.45M**

Valuación: el bono floating vale (notional + próximo cupón) descontado a la
primera fecha:
""")
            st.latex(r"B_{float} = (L + k^*) \cdot e^{-r_1 \cdot t_1}")

            k_star_wr = 100 * 0.029 * 0.5
            B_float_wr = (100 + k_star_wr) * np.exp(-0.028 * 0.25)
            st.latex(f"B_{{float}} = (100 + {k_star_wr:.2f}) \\cdot e^{{-0.028 \\times 0.25}} = {B_float_wr:.4f}")
            st.metric("B_float", f"${B_float_wr:.4f}M")

            V_swap_wr = B_float_wr - B_fix_wr
            st.markdown("---")
            m1, m2, m3 = st.columns(3)
            m1.metric("B_float", f"${B_float_wr:.4f}M")
            m2.metric("B_fix", f"${B_fix_wr:.4f}M")
            m3.metric("V_swap (recibe float)", f"${V_swap_wr:+.4f}M")

            st.success(
                f"Resultado: V_swap = B_float − B_fix = {B_float_wr:.4f} − {B_fix_wr:.4f} = "
                f"**${V_swap_wr:.4f}M**. WhiteRock (fixed-rate payer) tiene un swap "
                f"con valor positivo de ${V_swap_wr*1_000_000:,.0f}. Si cerraran la "
                f"posición hoy, ganarían exactamente ese monto."
            )

    with tab3:
        st.header("Swaps de Monedas (Currency Swaps)")
        st.markdown(r"""
En un **currency swap**, dos partes intercambian:
1. **Notionales al inicio** (en monedas distintas)
2. **Pagos periódicos de interés** (en cada moneda)
3. **Notionales al vencimiento** (devuelven lo recibido)

**Diferencia clave vs IR swap**: acá SÍ se intercambia el notional (al inicio y al final).
""")

        sub1, sub2, sub3 = st.tabs([
            "Mecánica (IBM / BP)",
            "Valuación USD/JPY",
            "Ventaja comparativa (GE / Qantas)",
        ])

        with sub1:
            st.subheader("Ejemplo: IBM / British Petroleum")
            st.markdown(r"""
**Setup:**
- IBM paga **5% GBP**, recibe **6% USD**
- BP paga **6% USD**, recibe **5% GBP**
- Notionales: USD 15M y GBP 10M
- Pagos anuales por 5 años
""")
            cf_rows = []
            for year in range(2020, 2026):
                if year == 2020:
                    usd, gbp, note = 15_000_000, -10_000_000, "Intercambio inicial notionales"
                elif year == 2025:
                    usd = 15_000_000 * 0.06 + 15_000_000
                    gbp = -(10_000_000 * 0.05 + 10_000_000)
                    note = "Último pago + devolución notionales"
                else:
                    usd, gbp, note = 15_000_000 * 0.06, -10_000_000 * 0.05, "Pago de intereses"
                cf_rows.append({
                    "Año": year,
                    "USD recibido": f"${usd:,.0f}" if usd != 0 else "—",
                    "GBP pagado": f"£{abs(gbp):,.0f}" if gbp != 0 else "—",
                    "Nota": note,
                })
            st.dataframe(pd.DataFrame(cf_rows), hide_index=True, use_container_width=True)
            st.info(
                "**Puntos clave**: 1) los notionales se intercambian al inicio en sentido "
                "opuesto a los flujos posteriores. 2) Los intereses se pagan periódicamente "
                "en cada moneda. 3) Al final se devuelven los notionales — distinto de un "
                "IR swap donde el notional nunca se mueve."
            )

        with sub2:
            st.subheader("Valuación USD/JPY (Hull/UADE)")
            st.markdown(r"""
**Parámetros:**
- Tasas continuas: r_USD = 9%, r_JPY = 4%
- Swap fixed-for-fixed: recibe **5% anual JPY**, paga **8% anual USD**
- Notionales: JPY 1,200M y USD 10M
- Vida restante: 3 años, spot **110 JPY/USD**

### Método 1 — Portfolio de bonos
""")
            st.latex(r"V_{swap} = \frac{B_{JPY}}{S_0} - B_{USD}")

            times_cs = [1.0, 2.0, 3.0]
            usd_zeros_cs = [0.09, 0.09, 0.09]
            jpy_zeros_cs = [0.04, 0.04, 0.04]
            res_bonds = value_currency_swap_bonds(
                notional_domestic=10_000_000,
                notional_foreign=1_200_000_000,
                rate_domestic=0.09,
                rate_foreign=0.04,
                swap_rate_domestic=0.08,
                swap_rate_foreign=0.05,
                spot_exchange_rate=110,
                payment_times=times_cs,
                domestic_zero_rates=usd_zeros_cs,
                foreign_zero_rates=jpy_zeros_cs,
                receive_foreign=True,
            )
            st.dataframe(res_bonds["cashflows"].style.format({
                "Time": "{:.1f}",
                "Domestic_CF": "{:,.0f}",
                "Foreign_CF": "{:,.0f}",
                "Domestic_PV": "{:,.0f}",
                "Foreign_PV": "{:,.0f}",
                "Domestic_DF": "{:.4f}",
                "Foreign_DF": "{:.4f}",
                "Domestic_Zero_Rate": "{:.2%}",
                "Foreign_Zero_Rate": "{:.2%}",
            }), hide_index=True, use_container_width=True)

            c1, c2, c3 = st.columns(3)
            c1.metric("B_USD", f"${res_bonds['bond_domestic']/1e6:.4f}M")
            c2.metric("B_JPY", f"¥{res_bonds['bond_foreign']/1e6:.2f}M")
            c3.metric("B_JPY → USD", f"${res_bonds['bond_foreign_converted']/1e6:.4f}M",
                       help=f"¥{res_bonds['bond_foreign']/1e6:.2f}M ÷ 110")

            st.success(
                f"**V_swap (recibe JPY, paga USD)** = B_JPY/S₀ − B_USD = "
                f"${res_bonds['swap_value']/1e6:.4f}M ≈ **$1.543M**."
            )

            st.markdown("### Método 2 — Portfolio de forwards")
            res_fwd = value_currency_swap_forwards(
                notional_domestic=10_000_000,
                notional_foreign=1_200_000_000,
                rate_domestic=0.09,
                rate_foreign=0.04,
                swap_rate_domestic=0.08,
                swap_rate_foreign=0.05,
                spot_exchange_rate=110,
                payment_times=times_cs,
                domestic_zero_rates=usd_zeros_cs,
                foreign_zero_rates=jpy_zeros_cs,
                receive_foreign=True,
            )
            st.dataframe(res_fwd["cashflows"].style.format({
                "Time": "{:.1f}",
                "Forward_Rate": "{:.4f}",
                "Domestic_CF": "{:,.0f}",
                "Foreign_CF": "{:,.0f}",
                "Foreign_CF_in_Domestic": "{:,.0f}",
                "Net_CF": "{:,.0f}",
                "Discount_Factor": "{:.4f}",
                "PV": "{:,.0f}",
            }), hide_index=True, use_container_width=True)
            st.success(
                f"**V_swap (por forwards)** = Σ PV netos = ${res_fwd['swap_value']/1e6:.4f}M. "
                f"✓ Mismo resultado que el método de bonos."
            )

        with sub3:
            st.subheader("Ventaja Comparativa: GE / Qantas")
            st.markdown(r"""
**Situación:**
- **GE** (USA) necesita AUD 20M para un proyecto en Australia
- **Qantas** (Australia) necesita USD 18M para comprar aviones
""")
            rates_fx_df = pd.DataFrame({
                "Empresa": ["GE", "Qantas", "**Diferencial**"],
                "USD": ["5.0%", "7.0%", "**2.0%**"],
                "AUD": ["7.6%", "8.0%", "**0.4%**"],
            })
            st.table(rates_fx_df)
            st.markdown(r"""
- GE tiene ventaja comparativa en **USD** (diferencial 2.0% vs 0.4%).
- Qantas tiene ventaja comparativa en **AUD**.
- Ganancia disponible: 2.0% − 0.4% = **1.6%**.

Con intermediario cobrando 0.2% en cada moneda → reparto 0.7% GE / 0.5% Qantas.
""")
            ca, cb = st.columns(2)
            with ca:
                st.markdown("#### General Electric")
                st.markdown(r"""
**Estrategia:**
1. Toma USD 18M al 5.0% (su ventaja)
2. Swap: paga AUD 6.9%, recibe USD 5.0%

**Costo neto AUD: 6.9%**

Ahorro: 0.7% vs 7.6% directo ✓
""")
            with cb:
                st.markdown("#### Qantas Airways")
                st.markdown(r"""
**Estrategia:**
1. Toma AUD 20M al 8.0% (su ventaja)
2. Swap: paga USD 6.5%, recibe AUD 8.0%

**Costo neto USD: 6.5%**

Ahorro: 0.5% vs 7.0% directo ✓
""")
            st.warning(
                "**Nota práctica**: Qantas termina descalzado en FX (recibe AUD 8% que "
                "cancela su deuda, pero solo tiene ingresos AUD operativos). En la práctica "
                "esa exposición la administra el intermediario con otros derivados."
            )

    with tab_f:
        formulario.cap7()
