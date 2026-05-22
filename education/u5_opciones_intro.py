"""
Unidad V · Opciones intro y propiedades (Hull Cap 10-11).
Reune: Conceptos básicos, los 6 factores, propiedades y put-call parity.
"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")  # backend no-GUI para que st.pyplot no abra ventanas
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from pricing.black_scholes import bs_price, bs_price_both
from greeks.analytical import all_greeks
from strategies import legs as L
from strategies.payoff import max_profit_loss, breakeven_points
from education.parity import parity_check, implied_rate_from_parity
from education import formulario
from education.bounds import check_bounds
from ui.charts.payoff_diagram import payoff_chart


def render() -> None:
    st.markdown(
        '<h1 style="margin:0;font-weight:600;">Unidad V · Opciones — intro y propiedades</h1>'
        '<div style="color:var(--text-muted);font-size:13px;margin-bottom:20px;">'
        'Hull Cap 10 (mercados) y Cap 11 (propiedades, los 6 factores, put-call parity).'
        '</div>', unsafe_allow_html=True)

    tab1, tab2, tab3, tab_f = st.tabs([
        "Conceptos básicos",
        "Los 6 factores",
        "Propiedades y parity",
        "📐 Fórmulas",
    ])

    with tab1:
        st.header("Conceptos básicos")
        st.markdown(
            """
        **Opción** = contrato que da al comprador el **derecho** (no la obligación) de comprar (*call*)
        o vender (*put*) un activo subyacente a un precio fijo (*strike* K) en o hasta una fecha (*expiry* T).

        El **vendedor** (writer) recibe un premium y queda obligado a cumplir si el comprador ejerce.

        **Terminología clave (Hull Cap 9):**

        - **In-the-Money (ITM)**: el ejercicio ya tiene valor intrínseco. Para call: S > K. Para put: S < K.
        - **At-the-Money (ATM)**: S ≈ K.
        - **Out-of-the-Money (OTM)**: el ejercicio no tiene valor. Call: S < K. Put: S > K.
        - **Europea**: solo ejercitable al vencimiento. **Americana**: en cualquier momento hasta T.
        - **Payoff al vencimiento**: lo que vale la opción cuando llega T.
        - Call: max(S_T − K, 0)
        - Put:  max(K − S_T, 0)

        > En el mercado argentino, BYMA lista mayormente opciones de tipo europeo sobre acciones líderes
        > (GGAL, YPF, BMA, PAMP, etc), con vencimientos cuatrimestrales (Feb, Abr, Jun, Ago, Oct, Dic).
        """
        )

        st.subheader("Payoff interactivo")
        c1, c2, c3 = st.columns(3)
        opt_type = c1.radio("Tipo", ["call", "put"], horizontal=True, key="intro_type")
        K = c2.number_input("Strike K", min_value=1.0, value=100.0, step=1.0, key="intro_K")
        premium = c3.number_input("Premium pagado", min_value=0.0, value=5.0, step=0.5, key="intro_prem")

        S_range = np.linspace(K * 0.5, K * 1.5, 200)
        strat = L.long_call(K, 0.5, premium) if opt_type == "call" else L.long_put(K, 0.5, premium)
        fig = payoff_chart(strat, S_current=K, S_range=S_range, show_now=False)
        st.plotly_chart(fig, use_container_width=True)

        bes = breakeven_points(strat, S_range)
        max_p, max_l = max_profit_loss(strat, S_range)
        m1, m2, m3 = st.columns(3)
        m1.metric("Breakeven", f"${bes[0]:.2f}" if bes else "—")
        m2.metric("Máx profit (en rango)", f"${max_p:+.2f}")
        m3.metric("Máx loss", f"${max_l:+.2f}")

        with st.expander("📖 Resumen Cap 1 — qué son los derivados"):
            st.markdown(
                """
        Hull Cap 1 introduce los **3 actores** del mercado de derivados:

        1. **Hedger** — usa derivados para reducir riesgo de una posición existente.
           Ej: importador argentino que sabe que tiene que pagar USD en 90 días → compra
           futuro de dólar para fijar el costo.

        2. **Especulador** — apuesta a una dirección. Compra opciones porque cree que el
           activo va a subir/bajar más de lo que el mercado pricea.

        3. **Arbitrajista** — busca diferencias de precio que violen no-arbitraje y las
           captura. En AR: arbitraje CCL vs MEP, CEDEARs vs subyacente US, parity violations.

        El **forward** (Cap 5) es el primo simple del futuro: contrato bilateral, sin
        clearing, sin mark-to-market diario. El **futuro** estandariza y agrega margen.

        Las **opciones** son el siguiente nivel: introducen **convexidad** (gamma) y por
        eso necesitan modelos más sofisticados (Cap 12 binomial, Cap 14 Black-Scholes).
        """
            )

    with tab2:
        st.header("Los 6 factores")
        st.markdown(r"""
        Seis variables determinan el precio de una opción europea sobre una acción.
        Para americanas se suma una séptima cuestión (early exercise), pero las direcciones son
        las mismas. Esto es **la tabla** que entra en el parcial:
        """)

        import pandas as _pd
        factors_table = _pd.DataFrame({
            "Factor": ["Spot (S₀)", "Strike (K)", "Tiempo (T)", "Volatilidad (σ)",
                       "Tasa libre (r)", "Dividendos (D)"],
            "Eur. Call": ["+", "−", "?", "+", "+", "−"],
            "Eur. Put":  ["−", "+", "?", "+", "−", "+"],
            "Am. Call":  ["+", "−", "+", "+", "+", "−"],
            "Am. Put":   ["−", "+", "+", "+", "−", "+"],
        })
        st.dataframe(factors_table, hide_index=True, use_container_width=True)

        st.markdown(r"""
        **Por qué ?:** para opciones **europeas**, más tiempo NO siempre es mejor — porque si
        hay dividendos grandes a pagar antes del expiry, podés perderte más drawdowns del spot
        (call) o más uplifts (put). Para americanas, más tiempo nunca puede ser peor porque
        siempre podés ejercer hoy mismo si querés, así que T+1 dominates T.

        ### Demo interactiva — variá un factor y mirá qué pasa
        """)
        from pricing.black_scholes import bs_price
        import numpy as _np

        c1, c2 = st.columns(2)
        factor = c1.selectbox("Factor a variar", ["Spot (S₀)", "Strike (K)", "Tiempo (T)",
                                                   "Volatilidad (σ)", "Tasa libre (r)",
                                                   "Dividendos (q)"])
        opt_type_factors = c2.radio("Tipo", ["call", "put"], horizontal=True, key="f_type")

        S_b, K_b, T_b, r_b, sig_b, q_b = 100.0, 100.0, 0.5, 0.05, 0.25, 0.0

        if factor == "Spot (S₀)":
            xs = _np.linspace(50, 150, 100)
            ys = [bs_price(x, K_b, T_b, r_b, sig_b, q_b, opt_type_factors) for x in xs]
            xlab = "S₀"
        elif factor == "Strike (K)":
            xs = _np.linspace(50, 150, 100)
            ys = [bs_price(S_b, x, T_b, r_b, sig_b, q_b, opt_type_factors) for x in xs]
            xlab = "K"
        elif factor == "Tiempo (T)":
            xs = _np.linspace(0.01, 2.0, 100)
            ys = [bs_price(S_b, K_b, x, r_b, sig_b, q_b, opt_type_factors) for x in xs]
            xlab = "T (años)"
        elif factor == "Volatilidad (σ)":
            xs = _np.linspace(0.05, 1.0, 100)
            ys = [bs_price(S_b, K_b, T_b, r_b, x, q_b, opt_type_factors) for x in xs]
            xlab = "σ"
        elif factor == "Tasa libre (r)":
            xs = _np.linspace(0.0, 0.20, 100)
            ys = [bs_price(S_b, K_b, T_b, x, sig_b, q_b, opt_type_factors) for x in xs]
            xlab = "r"
        else:  # Dividendos
            xs = _np.linspace(0.0, 0.15, 100)
            ys = [bs_price(S_b, K_b, T_b, r_b, sig_b, x, opt_type_factors) for x in xs]
            xlab = "q (dividend yield)"

        import plotly.graph_objects as _go
        color = "#3fb950" if opt_type_factors == "call" else "#f85149"
        fig = _go.Figure()
        fig.add_trace(_go.Scatter(x=xs, y=ys, mode="lines",
                                  line=dict(color=color, width=2.5),
                                  name=f"{opt_type_factors} price"))
        fig.update_layout(template="plotly_dark", height=400,
                          title=f"Precio del {opt_type_factors} vs {factor}",
                          xaxis_title=xlab, yaxis_title="Precio",
                          margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig, use_container_width=True)

        st.caption("Base case: S=100, K=100, T=0.5, σ=25%, r=5%, q=0%. "
                   "Sólo se varía el factor seleccionado.")

        with st.expander("📖 Por qué cada factor mueve el precio"):
            st.markdown(r"""
        - **S₀**: el subyacente sube → el call gana valor intrínseco (S−K), el put pierde. Directo.
        - **K**: a más strike, el call tiene menos chance de terminar ITM (S>K más difícil),
          y el put más (K>S más fácil).
        - **T**: para AM, más tiempo = más optionality. Para EU es ambiguo porque dividends pueden
          comerse ese tiempo de ventaja.
        - **σ**: vol más alta significa mayor varianza del payoff. Como las opciones tienen
          payoff *truncado* (max(S-K,0) o max(K-S,0)), más dispersión = más valor esperado.
          Aplica a calls y puts por igual.
        - **r**: más tasa → más caro tener cash, más barato diferir el pago de K (call). Para
          put, más tasa = más caro tener short cash, así que precio cae.
        - **D** (dividendos): los pagos de dividendos reducen el spot ex-date. Calls pierden
          valor (S esperado más bajo), puts ganan.
        """)

    with tab3:
        st.header("Propiedades de opciones y put-call parity")
        st.markdown(
            """
        Sin asumir ningún modelo de pricing, **el simple no-arbitraje** nos da relaciones fuertes.

        **Cotas para opciones europeas** (Hull 10.1–10.5):
        - Call:  max(S·e^(-qT) − K·e^(-rT), 0)  ≤  C  ≤  S·e^(-qT)
        - Put:   max(K·e^(-rT) − S·e^(-qT), 0)  ≤  P  ≤  K·e^(-rT)

        **Put-Call Parity** (Hull 10.6):

        $$
        C + K e^{-rT} = P + S e^{-qT}
        $$

        Si esta igualdad no se cumple, hay arbitraje: armás un portafolio sintético en el
        lado barato y vendés el lado caro.
        """
        )

        st.subheader("Verificador interactivo de parity")
        c1, c2, c3, c4 = st.columns(4)
        S_p = c1.number_input("Spot S", min_value=1.0, value=100.0, step=1.0, key="parity_S")
        K_p = c2.number_input("Strike K", min_value=1.0, value=100.0, step=1.0, key="parity_K")
        T_p = c3.number_input("T (años)", min_value=0.01, value=0.5, step=0.05, key="parity_T")
        r_p = c4.number_input("r (anual)", min_value=0.0, value=0.05, step=0.01, key="parity_r")

        c5, c6, c7 = st.columns(3)
        C_market = c5.number_input("Precio Call de mercado", min_value=0.0, value=8.0, step=0.1, key="parity_C")
        P_market = c6.number_input("Precio Put de mercado", min_value=0.0, value=5.0, step=0.1, key="parity_P")
        q_p = c7.number_input("Dividend yield q", min_value=0.0, value=0.0, step=0.005, key="parity_q")

        pc = parity_check(C_market, P_market, S_p, K_p, T_p, r_p, q_p, tolerance=0.10)
        cA, cB, cC = st.columns(3)
        cA.metric("LHS  (C − P)", f"${pc['lhs_call_minus_put']:.4f}")
        cB.metric("RHS  (S·e^(-qT) − K·e^(-rT))", f"${pc['rhs_S_minus_K_disc']:.4f}")
        cC.metric("Diferencia", f"${pc['difference']:+.4f}",
                  delta_color="off" if not pc["violated"] else "inverse")
        if pc["violated"]:
            st.error(f"⚠️ {pc['interpretation']}. Posible arbitraje (descontando bid-ask, funding y borrow).")
        else:
            st.success(f"✅ {pc['interpretation']}.")

        st.subheader("Tasa implícita en el par call/put")
        st.markdown(
            """
        En AR la tasa libre de riesgo *oficial* (BADLAR/TAMAR) no siempre refleja el funding real.
        Despejando *r* de la parity:

        $$
        r = -\\frac{1}{T} \\ln\\!\\left(\\frac{S e^{-qT} - (C - P)}{K}\\right)
        $$
        """
        )
        try:
            r_imp = implied_rate_from_parity(C_market, P_market, S_p, K_p, T_p, q_p)
            st.info(f"Tasa implícita en estos quotes: **{r_imp:.2%}** (vs tasa input {r_p:.2%})")
        except ValueError as e:
            st.warning(f"No se puede despejar la tasa: {e}")

        with st.expander("📖 Cotas — verificá si un quote es razonable"):
            cc1, cc2, cc3, cc4 = st.columns(4)
            b_price = cc1.number_input("Precio observado", min_value=0.0, value=5.0, step=0.1, key="b_price")
            b_S = cc2.number_input("S", min_value=1.0, value=100.0, step=1.0, key="b_S")
            b_K = cc3.number_input("K", min_value=1.0, value=100.0, step=1.0, key="b_K")
            b_T = cc4.number_input("T", min_value=0.01, value=0.5, step=0.05, key="b_T")
            b_r = st.number_input("r", min_value=0.0, value=0.05, step=0.01, key="b_r")
            b_type = st.radio("Tipo", ["call", "put"], horizontal=True, key="b_type")
            result = check_bounds(b_price, b_S, b_K, b_T, b_r, 0.0, b_type)
            col = st.columns(3)
            col[0].metric("Lower bound", f"${result['lower_bound']:.4f}")
            col[1].metric("Upper bound", f"${result['upper_bound']:.4f}")
            col[2].metric("Status", "✅ OK" if result["in_range"] else "❌ Violado")
            if not result["in_range"]:
                st.error(result["violation"])

        with st.expander("📐 Put-Call Parity — derivación formal (portfolios A y C)"):
            st.markdown(r"""
**Demostración por arbitraje.** Probamos que para opciones europeas:
""")
            st.latex(r"c + K \, e^{-rT} = p + S_0")
            st.markdown(r"""
**Estrategia**: construir dos portfolios con **mismo payoff** en t=T. Si tienen
mismo payoff → deben tener mismo precio hoy (ley de precio único).
""")
            pca, pcb = st.columns(2)
            with pca:
                st.markdown(r"""
#### Portfolio A
- Comprás **call europeo** strike K
- Comprás **zero-coupon bond** que paga K en T

**Costo hoy:** $c + K \, e^{-rT}$
""")
            with pcb:
                st.markdown(r"""
#### Portfolio C
- Comprás **put europeo** strike K
- Comprás **una acción** del subyacente

**Costo hoy:** $p + S_0$
""")
            st.markdown("**Payoffs en t=T** — dos escenarios:")
            payoff_df = pd.DataFrame({
                "Componente": ["Call", "Bond", "**= Portfolio A**",
                               "Put", "Share", "**= Portfolio C**"],
                "Si S_T > K": ["S_T − K", "K", "**S_T**",
                               "0", "S_T", "**S_T**"],
                "Si S_T < K": ["0", "K", "**K**",
                               "K − S_T", "S_T", "**K**"],
            })
            st.dataframe(payoff_df, hide_index=True, use_container_width=True)
            st.success(
                "Ambos portfolios valen lo mismo en TODOS los escenarios "
                "(S_T si sube ITM, K si baja OTM). Por ley de precio único: "
                "**c + Ke^(-rT) = p + S₀**."
            )
            st.info(
                "**Uso práctico**: si conocés c, S₀, K, r, T → despejás p = c + Ke^(-rT) − S₀. "
                "O creás un call sintético: c = p + S₀ − Ke^(-rT). Si la relación no se cumple "
                "en el mercado, hay oportunidad de arbitraje."
            )

        with st.expander("📊 American options — desigualdad de paridad"):
            st.markdown(r"""
Para americanas no hay igualdad exacta (por early exercise), pero sí desigualdades:
""")
            st.latex(r"S_0 - K \;\leq\; C - P \;\leq\; S_0 - K\,e^{-rT}")
            st.markdown(r"""
- **Cota inferior**: $S_0 - K$ (intrinsic)
- **Cota superior**: $S_0 - K e^{-rT}$ (paridad europea)

### Ejemplo numérico

Parámetros: c = $1.50 (call europea conocida), K = $20, T = 5/12 años, S₀ = $19, r = 10%.
Objetivo: acotar el precio del **put americano P**.
""")
            c_val = 1.5
            K_val = 20.0
            T_val = 5 / 12
            S0_val = 19.0
            r_val = 0.10
            lower_cp = S0_val - K_val
            upper_cp = S0_val - K_val * np.exp(-r_val * T_val)

            st.latex(f"S_0 - K = 19 - 20 = -1")
            st.latex(
                f"S_0 - K\\,e^{{-rT}} = 19 - 20\\,e^{{-0.10 \\times 5/12}} "
                f"= 19 - {K_val * np.exp(-r_val * T_val):.4f} = {upper_cp:.4f}"
            )
            st.markdown(f"Entonces **{lower_cp:.2f} ≤ C − P ≤ {upper_cp:.4f}**.")

            st.markdown(r"""
Como $C \geq c = 1.5$ (americana ≥ europea), reordenando para P:
""")
            P_lower_from_C = c_val - upper_cp
            P_lower_intrinsic = max(K_val - S0_val, 0.0)
            P_lower_final = max(P_lower_from_C, P_lower_intrinsic)
            P_upper_final = c_val + abs(lower_cp)

            st.latex(rf"P \geq c - (S_0 - K\,e^{{-rT}}) = {c_val:.2f} - {upper_cp:.4f} = {P_lower_from_C:.4f}")
            st.latex(rf"P \leq c + (K - S_0) = {c_val:.2f} + {abs(lower_cp):.2f} = {P_upper_final:.4f}")
            st.markdown(
                f"También $P \\geq \\max(K - S_0, 0) = ${P_lower_intrinsic:.2f}$ (intrinsic). "
                f"Tomando el máximo de cotas inferiores: **${P_lower_final:.4f}**."
            )
            st.success(
                f"Resultado: **${P_lower_final:.4f} < P < ${P_upper_final:.4f}**. "
                f"El put americano debe estar entre ~$1.68 y $2.50."
            )

        with st.expander("📈 Early exercise — call y put americano vs europeo"):
            st.markdown(r"""
- **Calls americanos** sobre activos sin dividendos: **nunca** ejercer temprano.
- **Puts americanos**: pueden convenir ejercerlos si están muy ITM.

Veámoslo gráficamente.
""")

            S_grid = np.linspace(0, 200, 200)
            K_plot = 100.0
            r_plot = 0.05
            T_plot = 1.0

            # Plot 1: call americano vs europeo
            fig1, ax1 = plt.subplots(figsize=(10, 5.2), facecolor="#0e1117")
            ax1.set_facecolor("#0e1117")
            intrinsic_call = np.maximum(S_grid - K_plot, 0)
            euro_call_lower = np.maximum(S_grid - K_plot * np.exp(-r_plot * T_plot), 0)
            ax1.plot(S_grid, intrinsic_call, "w--", linewidth=2,
                     label="Intrinsic (S − K)", alpha=0.7)
            ax1.plot(S_grid, euro_call_lower, "#3fb950", linewidth=2.5,
                     label="Call europeo (lower bound)")
            ax1.plot(S_grid, euro_call_lower, "#f85149", linewidth=2.5, alpha=0.7,
                     label="Call americano (sin div) = mismo")
            ax1.fill_between(S_grid, intrinsic_call, euro_call_lower, alpha=0.2,
                              color="#3fb950", label="Valor del 'seguro' (no ejercer)")
            ax1.axvline(K_plot, color="gray", linestyle=":", alpha=0.5)
            ax1.axhline(0, color="gray", linestyle="-", linewidth=0.5)
            ax1.set_xlabel("Precio spot S₀", color="white")
            ax1.set_ylabel("Valor del call", color="white")
            ax1.set_title("Call americano vs europeo — sin dividendos",
                           color="white", fontweight="bold")
            ax1.legend(loc="upper left", facecolor="#1e1e1e", edgecolor="gray",
                       labelcolor="white")
            ax1.grid(alpha=0.2, color="gray")
            ax1.tick_params(colors="white")
            ax1.set_xlim(0, 200)
            ax1.set_ylim(-5, 110)
            st.pyplot(fig1)
            plt.close(fig1)

            st.info(
                "El call europeo siempre vale **más** que el intrinsic (S − K). La región "
                "verde es el 'valor del seguro' — lo que perdés si ejercés temprano. "
                "Por eso nunca conviene ejercer un call americano sin dividendos. "
                "**Con dividendos** sí puede convenir, justo antes del ex-date para capturarlo."
            )

            # Plot 2: put americano vs europeo
            fig2, ax2 = plt.subplots(figsize=(10, 5.2), facecolor="#0e1117")
            ax2.set_facecolor("#0e1117")
            intrinsic_put = np.maximum(K_plot - S_grid, 0)
            euro_put_lower = np.maximum(K_plot * np.exp(-r_plot * T_plot) - S_grid, 0)
            american_put = np.maximum(intrinsic_put, euro_put_lower)
            ax2.plot(S_grid, intrinsic_put, "w--", linewidth=2,
                     label="Intrinsic (K − S)", alpha=0.7)
            ax2.plot(S_grid, euro_put_lower, "#3fb950", linewidth=2.5,
                     label="Put europeo (lower bound)")
            ax2.plot(S_grid, american_put, "#f85149", linewidth=2.5, alpha=0.7,
                     label="Put americano")
            ax2.axhline(K_plot * np.exp(-r_plot * T_plot), color="#d29922",
                         linestyle=":", alpha=0.6,
                         label=f"Ke^(-rT) = {K_plot * np.exp(-r_plot * T_plot):.1f}")
            mask = american_put > euro_put_lower
            ax2.fill_between(S_grid, euro_put_lower, american_put, where=mask,
                              alpha=0.3, color="orange", label="Valor early exercise")
            ax2.axvline(K_plot, color="gray", linestyle=":", alpha=0.5)
            ax2.axhline(0, color="gray", linestyle="-", linewidth=0.5)
            ax2.set_xlabel("Precio spot S₀", color="white")
            ax2.set_ylabel("Valor del put", color="white")
            ax2.set_title("Put americano vs europeo", color="white", fontweight="bold")
            ax2.legend(loc="upper right", facecolor="#1e1e1e", edgecolor="gray",
                       labelcolor="white")
            ax2.grid(alpha=0.2, color="gray")
            ax2.tick_params(colors="white")
            ax2.set_xlim(0, 200)
            ax2.set_ylim(-5, K_plot + 10)
            st.pyplot(fig2)
            plt.close(fig2)

            st.warning(
                "El put americano puede **tocar** la línea intrinsic (K − S) cuando S es "
                "muy bajo. Si S → 0, ejercer ya te da K. Esperar te da solo Ke^(-rT) < K "
                "(perdés la tasa). Por eso puede convenir **ejercer un put americano temprano** "
                "si está muy ITM. La región naranja muestra dónde el put americano vale más "
                "que el europeo."
            )

    with tab_f:
        formulario.cap10_11()
