"""
Página de Educación.

4 tabs interactivos cubriendo:
- Tab 1: Conceptos básicos (Hull Cap 1 y 9)
- Tab 2: Propiedades y put-call parity (Hull Cap 10)
- Tab 3: Estrategias multi-leg (Hull Cap 11)
- Tab 4: Las griegas y cómo se comportan (Hull Cap 18)
"""
from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import streamlit as st

# Permitir imports desde la raíz del proyecto
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pricing.black_scholes import bs_price, bs_price_both
from pricing.binomial import binomial_convergence
from greeks.analytical import all_greeks
from strategies import legs as L
from strategies.payoff import max_profit_loss, breakeven_points
from strategies.aggregator import net_greeks
from education.parity import parity_check, implied_rate_from_parity
from education.bounds import check_bounds
from ui.charts.payoff_diagram import payoff_chart
from ui.charts.greeks_visualizer import greek_vs_spot, greek_surface, all_greeks_panel
from ui.styling import inject_premium_css
from ui.components.header_strip import render_header_strip
import plotly.graph_objects as go


st.set_page_config(page_title="Education — Options Lab", page_icon="📚", layout="wide",
                   initial_sidebar_state="collapsed")
inject_premium_css()
render_header_strip()

st.markdown(
    '<h1 style="margin:0;font-weight:600;">Educación · Hull-driven</h1>'
    '<div style="color:var(--text-muted);font-size:13px;margin-bottom:24px;">'
    'Recorrido interactivo para parcial. Cada tab cubre uno o dos capítulos de '
    '<i>Options, Futures and Other Derivatives</i> (Hull).'
    '</div>',
    unsafe_allow_html=True,
)

tab_intro, tab_props, tab_strats, tab_greeks = st.tabs([
    "1. Conceptos básicos (Cap 1 + 9)",
    "2. Propiedades y parity (Cap 10)",
    "3. Estrategias (Cap 11)",
    "4. Griegas (Cap 18)",
])


# ============================================================
# TAB 1 — Conceptos básicos
# ============================================================
with tab_intro:
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


# ============================================================
# TAB 2 — Propiedades y parity
# ============================================================
with tab_props:
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


# ============================================================
# TAB 3 — Estrategias
# ============================================================
with tab_strats:
    st.header("Estrategias multi-leg")
    st.markdown(
        """
Combinando varias opciones podés construir payoffs arbitrarios. Hull Cap 11 cubre las
principales. Acá las podés armar y ver el payoff al vencimiento + cómo se ve hoy (vía BS).
"""
    )

    strat_name = st.selectbox(
        "Elegí una estrategia",
        [
            "Long Call",
            "Long Put",
            "Covered Call",
            "Protective Put",
            "Bull Call Spread",
            "Bear Put Spread",
            "Long Straddle",
            "Long Strangle",
            "Butterfly (calls)",
            "Iron Condor",
            "Collar",
        ],
    )

    # Parámetros de mercado del tab — DENTRO del tab, no en sidebar global
    with st.expander("⚙️  Parámetros de mercado", expanded=True):
        ec1, ec2, ec3, ec4, ec5 = st.columns(5)
        S0 = ec1.number_input("Spot", min_value=1.0, value=100.0, step=1.0, key="strat_S")
        sigma_strat = ec2.slider("Vol σ", 0.05, 1.0, 0.25, 0.01, key="strat_sigma")
        r_strat = ec3.slider("Tasa r", 0.0, 0.5, 0.05, 0.005, key="strat_r")
        q_strat = ec4.slider("Div yield q", 0.0, 0.20, 0.0, 0.005, key="strat_q")
        T_strat = ec5.slider("T (años)", 0.05, 2.0, 0.5, 0.05, key="strat_T")

    # Construcción de la estrategia con BS premiums por default
    def bs_call(K_):
        return bs_price(S0, K_, T_strat, r_strat, sigma_strat, q_strat, "call")

    def bs_put(K_):
        return bs_price(S0, K_, T_strat, r_strat, sigma_strat, q_strat, "put")

    if strat_name == "Long Call":
        K = st.slider("Strike", S0 * 0.5, S0 * 1.5, S0, 0.5)
        strat = L.long_call(K, T_strat, bs_call(K))
    elif strat_name == "Long Put":
        K = st.slider("Strike", S0 * 0.5, S0 * 1.5, S0, 0.5)
        strat = L.long_put(K, T_strat, bs_put(K))
    elif strat_name == "Covered Call":
        K = st.slider("Strike Call (vendido)", S0 * 1.0, S0 * 1.5, S0 * 1.1, 0.5)
        strat = L.covered_call(S0, K, T_strat, bs_call(K))
    elif strat_name == "Protective Put":
        K = st.slider("Strike Put (comprado)", S0 * 0.5, S0 * 1.0, S0 * 0.95, 0.5)
        strat = L.protective_put(S0, K, T_strat, bs_put(K))
    elif strat_name == "Bull Call Spread":
        c1, c2 = st.columns(2)
        K_low = c1.slider("K_low (long)", S0 * 0.7, S0 * 1.0, S0 * 0.95, 0.5)
        K_high = c2.slider("K_high (short)", S0 * 1.0, S0 * 1.4, S0 * 1.1, 0.5)
        strat = L.bull_call_spread(K_low, K_high, T_strat, bs_call(K_low), bs_call(K_high))
    elif strat_name == "Bear Put Spread":
        c1, c2 = st.columns(2)
        K_low = c1.slider("K_low (short)", S0 * 0.6, S0 * 1.0, S0 * 0.9, 0.5)
        K_high = c2.slider("K_high (long)", S0 * 1.0, S0 * 1.3, S0 * 1.05, 0.5)
        strat = L.bear_put_spread(K_low, K_high, T_strat, bs_put(K_low), bs_put(K_high))
    elif strat_name == "Long Straddle":
        K = st.slider("Strike (mismo para call y put)", S0 * 0.7, S0 * 1.3, S0, 0.5)
        strat = L.long_straddle(K, T_strat, bs_call(K), bs_put(K))
    elif strat_name == "Long Strangle":
        c1, c2 = st.columns(2)
        K_put = c1.slider("K_put (OTM)", S0 * 0.6, S0 * 0.99, S0 * 0.9, 0.5)
        K_call = c2.slider("K_call (OTM)", S0 * 1.01, S0 * 1.4, S0 * 1.1, 0.5)
        strat = L.long_strangle(K_put, K_call, T_strat, bs_put(K_put), bs_call(K_call))
    elif strat_name == "Butterfly (calls)":
        c1, c2, c3 = st.columns(3)
        K_low = c1.slider("K_low", S0 * 0.7, S0 * 0.95, S0 * 0.9, 0.5)
        K_mid = c2.slider("K_mid", S0 * 0.95, S0 * 1.05, S0, 0.5)
        K_high = c3.slider("K_high", S0 * 1.05, S0 * 1.3, S0 * 1.1, 0.5)
        strat = L.long_butterfly_call(
            K_low, K_mid, K_high, T_strat,
            bs_call(K_low), bs_call(K_mid), bs_call(K_high),
        )
    elif strat_name == "Iron Condor":
        c1, c2, c3, c4 = st.columns(4)
        K_pl = c1.slider("Put long", S0 * 0.6, S0 * 0.85, S0 * 0.85, 0.5)
        K_ps = c2.slider("Put short", S0 * 0.85, S0 * 0.99, S0 * 0.95, 0.5)
        K_cs = c3.slider("Call short", S0 * 1.01, S0 * 1.15, S0 * 1.05, 0.5)
        K_cl = c4.slider("Call long", S0 * 1.15, S0 * 1.4, S0 * 1.15, 0.5)
        strat = L.iron_condor(
            K_ps, K_pl, K_cl, K_cs, T_strat,
            bs_put(K_ps), bs_put(K_pl), bs_call(K_cl), bs_call(K_cs),
        )
    elif strat_name == "Collar":
        c1, c2 = st.columns(2)
        K_put = c1.slider("Put (piso)", S0 * 0.7, S0 * 0.99, S0 * 0.95, 0.5)
        K_call = c2.slider("Call (techo)", S0 * 1.01, S0 * 1.3, S0 * 1.05, 0.5)
        strat = L.collar(S0, K_put, K_call, T_strat, bs_put(K_put), bs_call(K_call))

    # Render
    S_range = np.linspace(S0 * 0.5, S0 * 1.5, 200)
    fig = payoff_chart(strat, S_current=S0, S_range=S_range,
                       sigma=sigma_strat, r=r_strat, q=q_strat, show_now=True)
    st.plotly_chart(fig, use_container_width=True)
    st.caption(f"💡 {strat.description}")

    # Métricas
    max_p, max_l = max_profit_loss(strat, S_range)
    bes = breakeven_points(strat, S_range)
    net_prem = strat.net_premium()

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Premium neto",
              f"${net_prem:+.2f}",
              help="Positivo = debit (paga). Negativo = credit (cobra).")
    m2.metric("Máx profit (en rango)", f"${max_p:+.2f}")
    m3.metric("Máx loss", f"${max_l:+.2f}")
    m4.metric("Breakevens", ", ".join(f"${be:.2f}" for be in bes) if bes else "—")

    # Greeks netas del combo
    st.subheader("Greeks netas del combo (en spot actual, hoy)")
    ng = net_greeks(strat, S0, 0.0, r_strat, sigma_strat, q_strat)
    g1, g2, g3, g4, g5 = st.columns(5)
    g1.metric("Δ Delta", f"{ng['delta']:+.4f}")
    g2.metric("Γ Gamma", f"{ng['gamma']:+.4f}")
    g3.metric("ν Vega", f"{ng['vega']:+.2f}")
    g4.metric("Θ Theta/año", f"{ng['theta']:+.2f}")
    g5.metric("ρ Rho", f"{ng['rho']:+.2f}")


# ============================================================
# TAB 4 — Greeks
# ============================================================
with tab_greeks:
    st.header("Las Griegas y cómo se comportan")
    st.markdown(
        """
Las **griegas** miden cómo cambia el precio de una opción ante cambios en las variables
de entrada. Son las primeras (y segundas) derivadas del modelo BSM.

| Griega | Qué mide | Convención de signo (long call) |
|---|---|---|
| **Δ Delta** | ∂V/∂S — sensibilidad al spot | (0, 1) |
| **Γ Gamma** | ∂²V/∂S² — convexidad | siempre ≥ 0 si long |
| **ν Vega** | ∂V/∂σ — sensibilidad a la vol | siempre ≥ 0 si long |
| **Θ Theta** | ∂V/∂t — time decay (por año) | < 0 si long (se evapora) |
| **ρ Rho** | ∂V/∂r — sensibilidad a la tasa | > 0 si call, < 0 si put |

Vega y gamma son **siempre positivas** para opciones long, sin importar call/put — porque
medir la 2da derivada en S (gamma) o la 1ra en σ (vega) no distingue dirección.
"""
    )

    cgl, cgc, cgr = st.columns(3)
    K_g = cgl.number_input("Strike K", min_value=1.0, value=100.0, step=1.0, key="g_K")
    T_g = cgc.slider("T (años)", 0.05, 2.0, 0.5, 0.05, key="g_T")
    sigma_g = cgr.slider("Volatilidad σ", 0.05, 1.0, 0.25, 0.01, key="g_sigma")
    r_g = st.slider("r", 0.0, 0.30, 0.05, 0.005, key="g_r")
    q_g = st.slider("Dividend yield q", 0.0, 0.20, 0.0, 0.005, key="g_q")
    opt_g = st.radio("Tipo", ["call", "put"], horizontal=True, key="g_type")

    st.subheader("Panel de las 5 griegas + precio (en función del spot)")
    fig_panel = all_greeks_panel(K_g, T_g, r_g, sigma_g, q_g, opt_g)
    st.plotly_chart(fig_panel, use_container_width=True)

    st.markdown(
        """
**Cosas para observar en el panel:**

1. **Delta** del call sube de 0 (OTM) a 1 (ITM), pasando por ~0.5 en ATM. Para puts, va de 0 a −1.
2. **Gamma** tiene un pico **en ATM**. Cerca del vencimiento (T chico) el pico se hace mucho más alto y angosto — por eso "gamma explota" cerca del expiry.
3. **Vega** también pico en ATM, pero más ancho. Aumenta con T (más tiempo = más oportunidad de vol).
4. **Theta** es más negativo en ATM (la opción "pierde más rápido" donde la incertidumbre vale más).
5. **Rho** sube linealmente con K para calls — cuanto más alto el strike, más sensible a la tasa.
"""
    )

    st.subheader("Superficie 3D de una griega (S, T)")
    cgg = st.columns(2)
    greek_pick = cgg[0].selectbox("Griega", ["gamma", "vega", "delta", "theta", "rho"], key="g_pick")
    st.plotly_chart(
        greek_surface(greek_pick, K_g, r_g, sigma_g, q_g, opt_g),
        use_container_width=True,
    )

    st.markdown(
        """
**Interpretación práctica en AR:**

- Si comprás opciones ATM **cerca del vencimiento**, estás muy expuesto a gamma — un mov del subyacente
  cambia tu delta dramáticamente. Bueno si acertás, malo si no.
- Si comprás opciones largas y vol baja → vega te juega a favor si la vol sube (lo que pasa antes de
  resultados o eventos macro AR).
- Si vendés opciones (covered call, iron condor) → theta te juega a favor pero gamma en contra.
  Sos "long theta, short gamma".
"""
    )

    st.subheader("Convergencia binomial → Black-Scholes (Hull Cap 12)")
    st.markdown(
        """
El árbol binomial CRR converge al precio BS cuando n → ∞, pero **oscila**. El Leisen-Reimer
converge mucho más rápido y monotónicamente.
"""
    )

    convergence = binomial_convergence(
        100.0, K_g, T_g, r_g, sigma_g, q_g, opt_g,
        n_values=[3, 5, 7, 11, 21, 51, 101, 201, 501],
    )
    bs_ref = bs_price(100.0, K_g, T_g, r_g, sigma_g, q_g, opt_g)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=convergence["n"], y=convergence["crr"],
        mode="lines+markers", name="CRR",
        line=dict(color="#ef5350", width=2),
    ))
    fig.add_trace(go.Scatter(
        x=convergence["n"], y=convergence["lr"],
        mode="lines+markers", name="Leisen-Reimer",
        line=dict(color="#26a69a", width=2),
    ))
    fig.add_hline(y=bs_ref, line=dict(color="#ffa726", width=2, dash="dash"),
                  annotation_text=f"BS = ${bs_ref:.4f}", annotation_position="right")
    fig.update_layout(
        title="Convergencia al precio BS",
        xaxis_title="n (pasos del árbol)",
        yaxis_title="Precio",
        xaxis_type="log",
        template="plotly_dark",
        height=400,
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)
