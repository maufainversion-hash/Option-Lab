from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
import streamlit as st

import pandas as pd

from pricing.forwards import minimum_variance_hedge_ratio, equity_portfolio_hedge_contracts
from education import formulario


def render() -> None:
    st.markdown(
        '<h1 style="margin:0;font-weight:600;">Unidad II · Coberturas con futuros</h1>'
        '<div style="color:var(--text-muted);font-size:13px;margin-bottom:20px;">'
        'Hull Cap 3. Hedge ratio óptimo, basis risk, cobertura de equity portfolios via beta.'
        '</div>', unsafe_allow_html=True)

    tab1, tab2, tab3, tab4, tab_f = st.tabs([
        "Hedge ratio óptimo",
        "Basis risk",
        "Hedge de equity portfolio",
        "Cross Hedging Descompuesto",
        "📐 Fórmulas",
    ])

    with tab1:
        st.markdown(r"""
    **Hedge ratio de mínima varianza** (Hull 3.4):

    $$h^* = \rho \cdot \frac{\sigma_S}{\sigma_F}$$

    Donde σ_S es la desviación del cambio de precio spot, σ_F la del futuro, y ρ la correlación
    entre ambos. Si la correlación es 1 y las vols iguales, h* = 1 (cobertura perfecta).
    """)
        c1, c2, c3 = st.columns(3)
        sigma_s = c1.slider("σ del cambio en spot (Δ por período)", 0.001, 5.0, 0.65, 0.01)
        sigma_f = c2.slider("σ del cambio en futuro", 0.001, 5.0, 0.81, 0.01)
        rho = c3.slider("Correlación ρ", -1.0, 1.0, 0.928, 0.01)

        h_star = minimum_variance_hedge_ratio(sigma_s, sigma_f, rho)
        hedge_effectiveness = rho ** 2

        m1, m2 = st.columns(2)
        m1.metric("Hedge ratio óptimo h*", f"{h_star:.4f}")
        m2.metric("Hedge effectiveness", f"{hedge_effectiveness:.2%}",
                  help="ρ² = porcentaje de varianza eliminado por el hedge")

        h_range = np.linspace(0, 2, 200)
        var_hedged = sigma_s**2 + (h_range**2) * sigma_f**2 - 2 * h_range * rho * sigma_s * sigma_f
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=h_range, y=var_hedged, mode="lines",
                                 line=dict(color="#d4af37", width=2.5)))
        fig.add_vline(x=h_star, line=dict(color="#3fb950", dash="dash"),
                      annotation_text=f"h* = {h_star:.3f}")
        fig.update_layout(template="plotly_dark", height=380,
                          title="Varianza del portfolio hedgeado vs hedge ratio",
                          xaxis_title="h (hedge ratio)", yaxis_title="Var(ΔS - h·ΔF)",
                          margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig, use_container_width=True)

        with st.expander("📖 Resumen / Hull pp. 56-62"):
            st.markdown(r"""
    La derivación parte de minimizar Var(ΔS − h·ΔF) respecto de h. Derivando e igualando a cero:
    $h^* = \text{Cov}(ΔS, ΔF) / \text{Var}(ΔF) = ρ \cdot σ_S / σ_F$.

    La **hedge effectiveness** ρ² mide qué proporción de la varianza del cambio de precio
    spot fue eliminada por el hedge. Si ρ = 1, eliminás todo. Si ρ = 0, no estás hedgeando nada.
    """)

    with tab2:
        st.markdown(r"""
    **Basis = Spot − Futuro**. Cuando hedgeás un asset con un futuro que no es exactamente
    sobre ese asset (ej: hedgear jet fuel con heating oil futures), te queda **basis risk**:
    el spread spot-futuro al cerrar el hedge no es predecible.

    Hull 3.1: el resultado de un hedge corto en un punto t₂ ≠ vencimiento es:
    $$S_2 - F_1 = F_2 + (S_2 - F_2) = F_2 + b_2$$
    """)

        b_init = st.slider("Basis inicial (cuando se entra al hedge)", -5.0, 5.0, 0.5, 0.1)
        b_end_low = st.slider("Basis al cerrar (low scenario)", -5.0, 5.0, -1.5, 0.1)
        b_end_high = st.slider("Basis al cerrar (high scenario)", -5.0, 5.0, 2.0, 0.1)

        c1, c2 = st.columns(2)
        c1.metric("Δ basis (low)", f"{b_end_low - b_init:+.2f}",
                  help="Pérdida adicional para un short hedge si basis baja más de lo previsto")
        c2.metric("Δ basis (high)", f"{b_end_high - b_init:+.2f}")

        days = np.arange(60)
        rng = np.random.RandomState(11)
        basis_path_low = np.linspace(b_init, b_end_low, 60) + rng.normal(0, 0.15, 60)
        basis_path_high = np.linspace(b_init, b_end_high, 60) + rng.normal(0, 0.15, 60)

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=days, y=basis_path_low, mode="lines", name="Escenario low",
                                 line=dict(color="#f85149", width=2)))
        fig.add_trace(go.Scatter(x=days, y=basis_path_high, mode="lines", name="Escenario high",
                                 line=dict(color="#3fb950", width=2)))
        fig.add_hline(y=b_init, line=dict(color="#d4af37", dash="dot"),
                      annotation_text="Basis inicial")
        fig.update_layout(template="plotly_dark", height=360, title="Path de la basis",
                          xaxis_title="Días", yaxis_title="Basis (S − F)",
                          margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.markdown(r"""
    **Hedge de un portfolio de acciones con index futures** (Hull 3.5):

    $$N^* = \beta \cdot \frac{V_A}{V_F}$$

    Donde V_A es el valor del portfolio, V_F es el valor de un contrato futuro (precio × multiplicador),
    y β es la beta del portfolio respecto al índice.
    """)
        c1, c2, c3, c4 = st.columns(4)
        V_A = c1.number_input("Valor portfolio (USD)", min_value=10000.0, value=5_000_000.0, step=10000.0)
        beta = c2.number_input("Beta vs índice", min_value=-3.0, value=1.2, step=0.05)
        F = c3.number_input("Precio futuro S&P", min_value=100.0, value=5500.0, step=10.0)
        mult = c4.number_input("Multiplicador (E-mini = 50)", min_value=1.0, value=50.0, step=1.0)

        n_star = equity_portfolio_hedge_contracts(V_A, beta, F, mult)
        st.metric("Contratos a vender (N*)", f"{n_star:.1f}",
                  help="Redondear al entero más cercano al ejecutar")

        st.markdown(r"""
    **Cambiar la beta del portfolio.** Si tu β actual es β y querés llegar a β*:

    $$N^* = (\beta^* - \beta) \cdot \frac{V_A}{V_F}$$

    Si β* < β → vendés futuros (reducir exposición). Si β* > β → comprás futuros.
    """)

        c5, c6 = st.columns(2)
        beta_target = c5.number_input("β target", min_value=0.0, value=0.5, step=0.05)
        n_change = (beta_target - beta) * V_A / (F * mult)
        c6.metric(f"Contratos para mover β de {beta:.2f} → {beta_target:.2f}",
                  f"{n_change:+.1f}", help="Positivo = comprar; negativo = vender")

        with st.expander("📈 Sensibilidad S&P 500: portfolio hedged vs sin hedge"):
            st.markdown(
                "Un portfolio cubierto con futuros se comporta **como risk-free**: gana "
                "aproximadamente la tasa libre independientemente del movimiento del índice."
            )
            sp1, sp2 = st.columns(2)
            with sp1:
                V0_sp = sp1.number_input("Valor portfolio ($M)", value=5.0, step=0.1,
                                          key="sp_V0") * 1_000_000
                S0_sp = sp1.number_input("S&P 500 inicial", value=1000, step=10, key="sp_S0")
                rf_sp = sp1.number_input("Tasa risk-free (%)", value=2.0, step=0.1,
                                          key="sp_rf") / 100
            with sp2:
                T_sp = sp2.number_input("Período (meses)", value=3, min_value=1,
                                         max_value=12, key="sp_T") / 12
                mult_sp = sp2.number_input("Multiplicador S&P", value=250, key="sp_mult")

            N_sp = V0_sp / (S0_sp * mult_sp)
            st.info(
                f"**Setup**: portfolio ${V0_sp/1e6:.2f}M, "
                f"N* contratos short = {N_sp:.1f} (cada contrato cubre "
                f"${S0_sp * mult_sp:,.0f})."
            )

            scenarios = []
            for ST in range(900, 1101, 20):
                portfolio_return = (ST - S0_sp) / S0_sp
                V_unhedged = V0_sp * (1 + portfolio_return)
                futures_gain = N_sp * (S0_sp - ST) * mult_sp
                V_hedged = V_unhedged + futures_gain
                V_rf = V0_sp * np.exp(rf_sp * T_sp)
                scenarios.append({
                    "S&P 500 final": ST,
                    "Portfolio sin hedge": V_unhedged,
                    "Ganancia futuros": futures_gain,
                    "Portfolio hedged": V_hedged,
                    "Target risk-free": V_rf,
                })
            df_sp = pd.DataFrame(scenarios)
            df_display = df_sp.copy()
            df_display["S&P 500 final"] = df_display["S&P 500 final"].apply(lambda x: f"{x:,}")
            for col in ["Portfolio sin hedge", "Ganancia futuros", "Portfolio hedged",
                        "Target risk-free"]:
                df_display[col] = df_sp[col].apply(
                    lambda x: f"${x/1e6:+.3f}M" if col == "Ganancia futuros" else f"${x/1e6:.3f}M"
                )
            st.dataframe(df_display, hide_index=True, use_container_width=True)

            avg_hedged = df_sp["Portfolio hedged"].mean()
            std_hedged = df_sp["Portfolio hedged"].std()
            target_rf = df_sp["Target risk-free"].iloc[0]
            st.success(
                f"**Portfolio hedged promedio**: ${avg_hedged/1e6:.3f}M ± "
                f"${std_hedged/1e3:.1f}k. **Target risk-free**: ${target_rf/1e6:.3f}M. "
                f"El portfolio hedged se mantiene cuasi-constante a través de un rango "
                f"de ±10% del S&P — el hedge convierte el riesgo de mercado en rendimiento risk-free."
            )

    with tab4:
        st.header("Cross Hedging — descomposición del ingreso")
        st.markdown(r"""
En **cross hedging** cubrís un activo (S₂) usando futuros de OTRO activo relacionado (F₁).
Ejemplo clásico: aerolínea cubre **costo de nafta** usando futuros de **crudo WTI**.

Al vencimiento, tu ingreso total tiene **tres componentes**:

$$\text{Ingreso} = F_1 + (S_2^* - F_2) + (S_2 - S_2^*)$$

- **F₁**: ganancia/pérdida en el futuro que tradeaste
- **(S₂* − F₂)**: "riesgo de base" si el futuro fuera sobre tu mismo activo (inevitable)
- **(S₂ − S₂*)**: efecto correlación imperfecta (costo del cross-hedging)
""")

        cca, ccb = st.columns(2)
        with cca:
            st.markdown("#### Inputs")
            F1 = st.number_input("F₁: precio futuro al cerrar la posición", value=65.0,
                                  step=0.5, help="Cierre del futuro que usaste (ej: crudo)")
            S2_star = st.number_input("S₂*: spot del activo SUBYACENTE del futuro",
                                       value=63.0, step=0.5,
                                       help="Spot del activo del futuro al vencimiento (ej: crudo spot)")
            F2 = st.number_input("F₂: precio futuro inicial del activo subyacente",
                                  value=62.0, step=0.5)
            S2 = st.number_input("S₂: spot de TU activo (el que necesitabas hedgear)",
                                  value=64.5, step=0.5, help="Ej: nafta spot al vencimiento")
        with ccb:
            st.markdown("#### Descomposición")
            comp_1 = F1
            comp_2 = S2_star - F2
            comp_3 = S2 - S2_star
            total = comp_1 + comp_2 + comp_3
            st.metric("① F₁ (ganancia futuro)", f"${comp_1:.2f}")
            st.metric("② (S₂* − F₂) — base mismo activo", f"${comp_2:+.2f}")
            st.metric("③ (S₂ − S₂*) — efecto correlación", f"${comp_3:+.2f}")
            st.markdown("---")
            st.metric("**Ingreso total por unidad**", f"${total:.2f}")

        st.markdown("---")
        if abs(comp_3) > abs(comp_2):
            st.warning(
                f"El efecto de correlación imperfecta (③ = ${comp_3:+.2f}) es **mayor** "
                f"que el riesgo de base (② = ${comp_2:+.2f}). En este escenario, el "
                f"cross-hedging agrega más riesgo del que resuelve — habría que buscar "
                f"un futuro más correlacionado o aceptar quedar sin hedge."
            )
        else:
            st.success(
                f"El riesgo de base (② = ${comp_2:+.2f}) **domina** sobre el efecto "
                f"de correlación (③ = ${comp_3:+.2f}). El cross-hedging está "
                f"funcionando razonablemente bien."
            )

        with st.expander("📖 Ejemplo: aerolínea cubre nafta con crudo WTI"):
            st.markdown(r"""
**Situación:**
- Aerolínea consume **2,000,000 galones de nafta** por mes
- No hay futuros líquidos de nafta → usa futuros de **crudo WTI**
- Correlación nafta-crudo: ρ = 0.928

**Datos históricos:**
- σ_nafta = 0.0263 (vol cambios de precio nafta)
- σ_crudo = 0.0313 (vol cambios futuro crudo)

**Hedge ratio óptimo:**

$$h^* = \rho \cdot \frac{\sigma_S}{\sigma_F} = 0.928 \cdot \frac{0.0263}{0.0313} = 0.78$$

**Conversión de unidades:**
- Futuro crudo: 1,000 barriles por contrato
- 1 barril ≈ 42 galones
- 2,000,000 galones = 47,619 barriles

**Número de contratos:**

$$N^* = h^* \cdot \frac{Q_A}{Q_F} = 0.78 \cdot \frac{47{,}619}{1{,}000} \approx 37 \text{ contratos}$$

La aerolínea shortea **37 contratos** de crudo WTI para cubrir 2M galones de nafta.
""")

    with tab_f:
        formulario.cap3()
