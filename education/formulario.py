"""
Formulario — machete consolidado de todas las fórmulas del curso.

Organizado por tema en tabs. Para parcial UADE IFD I: forwards/futuros,
coberturas, tasas, swaps, opciones (propiedades + valuación) y griegas.
"""
from __future__ import annotations

import streamlit as st


def render() -> None:
    st.markdown(
        '<h1 style="margin:0;font-weight:600;">📐 Formulario — machete completo</h1>'
        '<div style="color:var(--text-muted);font-size:13px;margin-bottom:20px;">'
        'Todas las fórmulas del cronograma UADE IFD I, organizadas por tema. '
        'Notación: cc = continuous compounding.'
        '</div>', unsafe_allow_html=True)

    tabs = st.tabs([
        "Forwards y Futuros",
        "Coberturas",
        "Tasas de interés",
        "Swaps",
        "Opciones — propiedades",
        "Opciones — valuación",
        "Griegas",
    ])

    # ============================================================
    # TAB 1 — Forwards y Futuros
    # ============================================================
    with tabs[0]:
        st.subheader("Pricing de forwards y futuros (Hull Cap 5)")

        st.markdown("**Forward price — activo sin income**")
        st.latex(r"F_0 = S_0 \, e^{rT}")

        st.markdown("**Forward price — activo con income conocido $I$** (valor presente de los ingresos)")
        st.latex(r"F_0 = (S_0 - I)\, e^{rT}")

        st.markdown("**Forward price — activo con dividend yield continuo $q$**")
        st.latex(r"F_0 = S_0 \, e^{(r - q)T}")

        st.markdown("**Forward price — commodity con storage $u$ y convenience yield $y$**")
        st.latex(r"F_0 = S_0 \, e^{(r + u - y)T}")

        st.markdown("**Cost of carry** $c$ — generaliza todos los casos: $F_0 = S_0 e^{cT}$")
        st.latex(r"c = r - q + u - y")

        st.markdown("**Valor de un forward existente** con delivery price $K$")
        st.latex(r"f_{\text{long}} = (F_0 - K)\, e^{-rT} = S_0 e^{-qT} - K e^{-rT}")
        st.latex(r"f_{\text{short}} = (K - F_0)\, e^{-rT}")

        st.markdown("**Basis** — diferencia spot vs futuro")
        st.latex(r"b = S - F \quad\longrightarrow\quad b \to 0 \text{ al vencimiento}")

        st.markdown("**Forward FX — covered interest parity** ($r_d$ doméstica, $r_f$ extranjera)")
        st.latex(r"F_0 = S_0 \, e^{(r_d - r_f)T}")

        st.info("**Mark-to-market de futuros**: la posición se revalúa diariamente. "
                "P&L diario = (F_t − F_{t-1}) × multiplicador × n_contratos.")

    # ============================================================
    # TAB 2 — Coberturas
    # ============================================================
    with tabs[1]:
        st.subheader("Coberturas con futuros (Hull Cap 3)")

        st.markdown("**Hedge ratio de mínima varianza**")
        st.latex(r"h^* = \rho \, \frac{\sigma_S}{\sigma_F}")
        st.caption("σ_S = desvío del cambio de precio spot · σ_F = del futuro · ρ = correlación.")

        st.markdown("**Hedge effectiveness** — proporción de varianza eliminada")
        st.latex(r"\text{effectiveness} = \rho^2")

        st.markdown("**Número óptimo de contratos** (ajustado por tamaño)")
        st.latex(r"N^* = h^* \, \frac{Q_A}{Q_F}")
        st.caption("Q_A = tamaño de la posición a cubrir · Q_F = tamaño de un contrato.")

        st.markdown("**Hedge de un equity portfolio con index futures**")
        st.latex(r"N^* = \beta \, \frac{V_A}{V_F}")
        st.caption("β = beta del portfolio · V_A = valor del portfolio · V_F = valor de un contrato futuro.")

        st.markdown("**Cambiar la beta del portfolio** de $\\beta$ a $\\beta^*$")
        st.latex(r"N^* = (\beta^* - \beta)\, \frac{V_A}{V_F}")
        st.caption("β* < β → vender futuros (reducir exposición). β* > β → comprar.")

        st.markdown("**Cross hedging — descomposición del ingreso**")
        st.latex(r"\text{Ingreso} = F_1 + \underbrace{(S_2^* - F_2)}_{\text{base risk}} + \underbrace{(S_2 - S_2^*)}_{\text{correlación imperfecta}}")

    # ============================================================
    # TAB 3 — Tasas de interés
    # ============================================================
    with tabs[2]:
        st.subheader("Tasas de interés, FRAs y duration (Hull Cap 4)")

        st.markdown("**Conversión de compounding** — de $m$ veces/año a continuo y viceversa")
        st.latex(r"R_c = m \, \ln\!\left(1 + \frac{R_m}{m}\right)")
        st.latex(r"R_m = m \left(e^{R_c/m} - 1\right)")

        st.markdown("**Discount factor**")
        st.latex(r"DF(T) = e^{-rT} \quad\text{(continuo)} \qquad DF(T) = \frac{1}{(1+r)^T}\ \text{(anual)}")

        st.markdown("**Forward rate** entre $T_1$ y $T_2$ desde la zero curve")
        st.latex(r"f_{T_1,T_2} = \frac{R_2 T_2 - R_1 T_1}{T_2 - T_1}")

        st.markdown("**Precio de un bono** — suma de cashflows descontados")
        st.latex(r"B = \sum_i \text{CF}_i \, e^{-R_i \, t_i}")

        st.markdown("**Valor de un FRA** (receive fixed $R_K$)")
        st.latex(r"V_{FRA} = L \,(R_K - R_F)\,(T_2 - T_1)\, e^{-R_2 T_2}")
        st.caption("R_F = forward rate implícita en la curva · L = notional.")

        st.markdown("**Duration de Macaulay**")
        st.latex(r"D = \frac{\sum_i t_i \, \text{CF}_i \, e^{-y t_i}}{B}")

        st.markdown("**Duration modificada** y la aproximación de primer orden")
        st.latex(r"D^* = \frac{D}{1 + y/m} \qquad \frac{\Delta B}{B} \approx -D^* \, \Delta y")

        st.markdown("**Conversion factor (Treasury futures)** — descontado al 6% semianual de convención CBOT")
        st.latex(r"\text{CF} = \frac{1}{100}\left[\sum_i \frac{c}{(1+r)^i} + \frac{100}{(1+r)^n}\right]")

        st.markdown("**Convexity adjustment (Eurodollar futures)**")
        st.latex(r"\text{forward rate} \approx \text{futures rate} - \tfrac{1}{2}\sigma^2 T_1 T_2")

        st.markdown("**Duration-based hedge con IR futures**")
        st.latex(r"N^* = \frac{P \cdot D_P}{V_F \cdot D_F}")

    # ============================================================
    # TAB 4 — Swaps
    # ============================================================
    with tabs[3]:
        st.subheader("Swaps (Hull Cap 7)")

        st.markdown("**Valuación de IR swap — bond approach** (receive fixed)")
        st.latex(r"V_{swap} = B_{\text{fix}} - B_{\text{flt}}")
        st.latex(r"B_{\text{fix}} = \sum_i k\, e^{-r_i t_i} + L\, e^{-r_n t_n}, \qquad k = L \cdot r_{\text{fix}} \cdot \tau")
        st.latex(r"B_{\text{flt}} = (L + k^*)\, e^{-r_1 t_1}")
        st.caption("k* = próximo cupón flotante ya fijado en el reset anterior.")

        st.markdown("**Par swap rate** — la tasa fija que hace $V_{swap}=0$ al iniciar")
        st.latex(r"r_{\text{par}} = \frac{1 - e^{-r_n t_n}}{\tau \sum_i e^{-r_i t_i}}")

        st.markdown("**Valuación de currency swap — bond approach**")
        st.latex(r"V_{swap} = \frac{B_{\text{foreign}}}{S_0} - B_{\text{domestic}}")
        st.caption("S₀ = spot FX (doméstica por unidad de extranjera).")

        st.markdown("**Valuación de currency swap — forward approach**")
        st.latex(r"V_{swap} = \sum_i \left(\text{CF}_i^{\text{foreign}} \cdot F_i - \text{CF}_i^{\text{domestic}}\right) e^{-r_i t_i}")

        st.info("**Ventaja comparativa**: la ganancia total a repartir = "
                "(diferencial en mercado fijo) − (diferencial en mercado flotante).")

    # ============================================================
    # TAB 5 — Opciones, propiedades
    # ============================================================
    with tabs[4]:
        st.subheader("Propiedades de opciones (Hull Cap 11)")

        st.markdown("**Payoff al vencimiento**")
        st.latex(r"\text{Call} = \max(S_T - K,\, 0) \qquad \text{Put} = \max(K - S_T,\, 0)")

        st.markdown("**Put-call parity — opciones europeas**")
        st.latex(r"c + K e^{-rT} = p + S_0 e^{-qT}")

        st.markdown("**Cotas de un call europeo**")
        st.latex(r"\max\!\left(S_0 e^{-qT} - K e^{-rT},\ 0\right) \;\leq\; c \;\leq\; S_0 e^{-qT}")

        st.markdown("**Cotas de un put europeo**")
        st.latex(r"\max\!\left(K e^{-rT} - S_0 e^{-qT},\ 0\right) \;\leq\; p \;\leq\; K e^{-rT}")

        st.markdown("**Desigualdad de paridad — opciones americanas**")
        st.latex(r"S_0 - K \;\leq\; C - P \;\leq\; S_0 - K e^{-rT}")

        st.info("**Los 6 factores** (efecto sobre el precio): S₀, K, T, σ, r, dividendos. "
                "Para europeas T es ambiguo (?), para americanas siempre positivo.")

    # ============================================================
    # TAB 6 — Opciones, valuación
    # ============================================================
    with tabs[5]:
        st.subheader("Valuación de opciones (Hull Cap 13-15, 17-18)")

        st.markdown("**Binomial de un paso — probabilidad risk-neutral**")
        st.latex(r"p = \frac{e^{(r-q)\Delta t} - d}{u - d}")
        st.latex(r"f = e^{-r\Delta t}\left[p\, f_u + (1-p)\, f_d\right]")

        st.markdown("**Calibración CRR** (Cox-Ross-Rubinstein)")
        st.latex(r"u = e^{\sigma\sqrt{\Delta t}}, \qquad d = \frac{1}{u}")

        st.markdown("**Delta replicante (binomial)**")
        st.latex(r"\Delta = \frac{f_u - f_d}{S u - S d}")

        st.markdown("**Black-Scholes-Merton** — call y put europeos")
        st.latex(r"c = S_0 e^{-qT} N(d_1) - K e^{-rT} N(d_2)")
        st.latex(r"p = K e^{-rT} N(-d_2) - S_0 e^{-qT} N(-d_1)")
        st.latex(r"d_1 = \frac{\ln(S_0/K) + (r - q + \tfrac{1}{2}\sigma^2)T}{\sigma\sqrt{T}}, \qquad d_2 = d_1 - \sigma\sqrt{T}")

        st.markdown("**Black's model** — opciones sobre futuros")
        st.latex(r"c = e^{-rT}\left[F_0 N(d_1) - K N(d_2)\right]")
        st.latex(r"d_1 = \frac{\ln(F_0/K) + \tfrac{1}{2}\sigma^2 T}{\sigma\sqrt{T}}, \qquad d_2 = d_1 - \sigma\sqrt{T}")

        st.markdown("**Garman-Kohlhagen** — opciones sobre divisas ($r_f$ = tasa extranjera)")
        st.latex(r"c = S_0 e^{-r_f T} N(d_1) - K e^{-r_d T} N(d_2)")

        st.markdown("**GBM — modelo del subyacente bajo medida risk-neutral**")
        st.latex(r"dS = (r-q) S\, dt + \sigma S\, dW")
        st.latex(r"S_T = S_0 \exp\!\left[\left(r - q - \tfrac{1}{2}\sigma^2\right)T + \sigma\sqrt{T}\,Z\right], \quad Z \sim N(0,1)")

    # ============================================================
    # TAB 7 — Griegas
    # ============================================================
    with tabs[6]:
        st.subheader("Las griegas (Hull Cap 19)")
        st.caption("N'(x) = densidad normal estándar. Fórmulas para opción europea con dividend yield q.")

        st.markdown("**Delta** — sensibilidad al spot ($\\partial V/\\partial S$)")
        st.latex(r"\Delta_{\text{call}} = e^{-qT} N(d_1) \qquad \Delta_{\text{put}} = e^{-qT}\left[N(d_1) - 1\right]")

        st.markdown("**Gamma** — sensibilidad de la delta ($\\partial^2 V/\\partial S^2$); igual call y put")
        st.latex(r"\Gamma = \frac{e^{-qT} N'(d_1)}{S_0 \, \sigma \sqrt{T}}")

        st.markdown("**Vega** — sensibilidad a la volatilidad ($\\partial V/\\partial\\sigma$); igual call y put")
        st.latex(r"\nu = S_0 \, e^{-qT} N'(d_1) \sqrt{T}")

        st.markdown("**Theta** — decaimiento temporal ($\\partial V/\\partial t$)")
        st.latex(r"\Theta_{\text{call}} = -\frac{S_0 e^{-qT} N'(d_1)\sigma}{2\sqrt{T}} - r K e^{-rT} N(d_2) + q S_0 e^{-qT} N(d_1)")

        st.markdown("**Rho** — sensibilidad a la tasa ($\\partial V/\\partial r$)")
        st.latex(r"\rho_{\text{call}} = K T e^{-rT} N(d_2) \qquad \rho_{\text{put}} = -K T e^{-rT} N(-d_2)")

        st.info("**Relación delta-gamma-theta** (para un portfolio delta-neutral): "
                "Θ + ½σ²S²Γ = rΠ. Es el PDE de Black-Scholes reescrito en griegas.")


# ============================================================
# Fórmulas por capítulo — usadas en la tab "📐 Fórmulas" de cada módulo
# ============================================================
def _formula_header(titulo: str) -> None:
    st.markdown(
        f'<div style="border-left:3px solid var(--accent);background:rgba(212,175,55,0.06);'
        f'padding:8px 14px;border-radius:4px;margin-bottom:12px;">'
        f'<b>📐 {titulo}</b> — fórmulas que se usan en esta unidad</div>',
        unsafe_allow_html=True,
    )


def cap1_2() -> None:
    """Cap 1-2 · Futuros y forwards (mecánica)."""
    _formula_header("Capítulos 1 y 2 · Futuros")
    st.markdown("**Payoff de un forward/futuro al vencimiento**")
    st.latex(r"\text{Long} = S_T - K \qquad \text{Short} = K - S_T")
    st.markdown("**P&L diario de mark-to-market** (posición long de $n$ contratos)")
    st.latex(r"\text{P\&L}_t = (F_t - F_{t-1}) \times \text{multiplicador} \times n")
    st.markdown("**Margin call** — se dispara cuando el balance cae bajo el maintenance level")
    st.latex(r"\text{balance} < \text{maintenance} \;\Rightarrow\; \text{reponer hasta initial margin}")
    st.markdown("**ROI con apalancamiento** — la ganancia es sobre el margen, no el notional")
    st.latex(r"\text{ROI} = \frac{\text{ganancia}}{\text{margen invertido}}")
    st.markdown("**Convergencia** — al vencimiento el futuro converge al spot")
    st.latex(r"F_T \;\longrightarrow\; S_T")
    st.info("En Cap 1-2 las fórmulas son operativas (MtM, margen). El **pricing** de "
            "forwards (F₀ = S₀·e^{rT}) se ve en Cap 5.")


def cap3() -> None:
    """Cap 3 · Coberturas."""
    _formula_header("Capítulo 3 · Coberturas con futuros")
    st.markdown("**Hedge ratio de mínima varianza**")
    st.latex(r"h^* = \rho \, \frac{\sigma_S}{\sigma_F}")
    st.markdown("**Hedge effectiveness** — varianza eliminada")
    st.latex(r"\text{effectiveness} = \rho^2")
    st.markdown("**Número óptimo de contratos**")
    st.latex(r"N^* = h^* \, \frac{Q_A}{Q_F}")
    st.markdown("**Hedge de equity portfolio con index futures**")
    st.latex(r"N^* = \beta \, \frac{V_A}{V_F}")
    st.markdown("**Cambio de beta** de $\\beta$ a $\\beta^*$")
    st.latex(r"N^* = (\beta^* - \beta)\, \frac{V_A}{V_F}")
    st.markdown("**Cross hedging — descomposición del ingreso**")
    st.latex(r"\text{Ingreso} = F_1 + (S_2^* - F_2) + (S_2 - S_2^*)")


def cap4() -> None:
    """Cap 4 · Tasas de interés."""
    _formula_header("Capítulo 4 · Tasas de interés y FRAs")
    st.markdown("**Conversión de compounding**")
    st.latex(r"R_c = m \ln\!\left(1 + \tfrac{R_m}{m}\right) \qquad R_m = m\left(e^{R_c/m} - 1\right)")
    st.markdown("**Discount factor**")
    st.latex(r"DF(T) = e^{-rT}")
    st.markdown("**Forward rate** entre $T_1$ y $T_2$")
    st.latex(r"f_{T_1,T_2} = \frac{R_2 T_2 - R_1 T_1}{T_2 - T_1}")
    st.markdown("**Precio de un bono**")
    st.latex(r"B = \sum_i \text{CF}_i \, e^{-R_i t_i}")
    st.markdown("**Valor de un FRA** (receive fixed)")
    st.latex(r"V_{FRA} = L\,(R_K - R_F)\,(T_2 - T_1)\,e^{-R_2 T_2}")
    st.markdown("**Duration de Macaulay y modificada**")
    st.latex(r"D = \frac{\sum_i t_i \,\text{CF}_i\, e^{-y t_i}}{B} \qquad D^* = \frac{D}{1 + y/m}")
    st.markdown("**Aproximación de primer orden del precio del bono**")
    st.latex(r"\frac{\Delta B}{B} \approx -D^* \, \Delta y")


def cap5() -> None:
    """Cap 5 · Pricing de forwards y futuros."""
    _formula_header("Capítulo 5 · Valuación de forwards y futuros")
    st.markdown("**Forward price — sin income**")
    st.latex(r"F_0 = S_0 \, e^{rT}")
    st.markdown("**Con income conocido $I$** (valor presente de los ingresos)")
    st.latex(r"F_0 = (S_0 - I)\, e^{rT}")
    st.markdown("**Con dividend yield continuo $q$**")
    st.latex(r"F_0 = S_0 \, e^{(r-q)T}")
    st.markdown("**Commodity con storage $u$ y convenience yield $y$**")
    st.latex(r"F_0 = S_0 \, e^{(r+u-y)T}")
    st.markdown("**Cost of carry**")
    st.latex(r"c = r - q + u - y")
    st.markdown("**Valor de un forward existente** con delivery price $K$")
    st.latex(r"f = (F_0 - K)\, e^{-rT}")
    st.markdown("**Convenience yield despejada de cotizaciones de mercado**")
    st.latex(r"y = r - q + u - \tfrac{1}{T}\ln\!\left(\tfrac{F_0}{S_0}\right)")


def cap6() -> None:
    """Cap 6 · IR futures."""
    _formula_header("Capítulo 6 · Interest rate futures")
    st.markdown("**Day count — fracción de año**")
    st.latex(r"\tau_{30/360} = \frac{360(y_2-y_1) + 30(m_2-m_1) + (d_2-d_1)}{360}")
    st.latex(r"\tau_{\text{ACT}/360} = \frac{\text{días reales}}{360}")
    st.markdown("**Conversion factor (Treasury bond futures)** — al 6% semianual CBOT")
    st.latex(r"\text{CF} = \frac{1}{100}\left[\sum_i \frac{c}{(1+r)^i} + \frac{100}{(1+r)^n}\right]")
    st.markdown("**Cheapest-to-deliver** — el bono que minimiza el costo de entrega")
    st.latex(r"\text{cost} = \text{quoted price} - \text{settlement} \times \text{CF}")
    st.markdown("**Convexity adjustment (Eurodollar futures)**")
    st.latex(r"\text{forward rate} \approx \text{futures rate} - \tfrac{1}{2}\sigma^2 T_1 T_2")
    st.markdown("**Duration-based hedge con IR futures**")
    st.latex(r"N^* = \frac{P \cdot D_P}{V_F \cdot D_F}")


def cap7() -> None:
    """Cap 7 · Swaps."""
    _formula_header("Capítulo 7 · Swaps")
    st.markdown("**Valuación de IR swap — bond approach** (receive fixed)")
    st.latex(r"V_{swap} = B_{\text{fix}} - B_{\text{flt}}")
    st.latex(r"B_{\text{fix}} = \sum_i k\,e^{-r_i t_i} + L\,e^{-r_n t_n}, \quad k = L\,r_{\text{fix}}\,\tau")
    st.latex(r"B_{\text{flt}} = (L + k^*)\,e^{-r_1 t_1}")
    st.markdown("**Par swap rate** — la fija que hace $V_{swap}=0$")
    st.latex(r"r_{\text{par}} = \frac{1 - e^{-r_n t_n}}{\tau \sum_i e^{-r_i t_i}}")
    st.markdown("**Currency swap — bond approach**")
    st.latex(r"V_{swap} = \frac{B_{\text{foreign}}}{S_0} - B_{\text{domestic}}")
    st.markdown("**Currency swap — forward approach**")
    st.latex(r"V_{swap} = \sum_i \left(\text{CF}_i^{f}\,F_i - \text{CF}_i^{d}\right)e^{-r_i t_i}")


def cap10_11() -> None:
    """Cap 10-11 · Propiedades de opciones."""
    _formula_header("Capítulos 10 y 11 · Propiedades de opciones")
    st.markdown("**Payoff al vencimiento**")
    st.latex(r"\text{Call} = \max(S_T - K,\,0) \qquad \text{Put} = \max(K - S_T,\,0)")
    st.markdown("**Put-call parity — opciones europeas**")
    st.latex(r"c + K e^{-rT} = p + S_0 e^{-qT}")
    st.markdown("**Cotas del call europeo**")
    st.latex(r"\max\!\left(S_0 e^{-qT} - K e^{-rT},\,0\right) \leq c \leq S_0 e^{-qT}")
    st.markdown("**Cotas del put europeo**")
    st.latex(r"\max\!\left(K e^{-rT} - S_0 e^{-qT},\,0\right) \leq p \leq K e^{-rT}")
    st.markdown("**Desigualdad de paridad — opciones americanas**")
    st.latex(r"S_0 - K \leq C - P \leq S_0 - K e^{-rT}")


def cap12() -> None:
    """Cap 12 · Estrategias."""
    _formula_header("Capítulo 12 · Estrategias multi-leg")
    st.markdown("**Payoff de un combo** — suma de los payoffs de cada pata")
    st.latex(r"\text{Payoff}_{\text{combo}}(S_T) = \sum_j q_j \cdot \text{payoff}_j(S_T)")
    st.markdown("**Premium neto** — positivo = debit (pagás), negativo = credit (cobrás)")
    st.latex(r"\text{premium neto} = \sum_j q_j \cdot \text{premium}_j")
    st.markdown("**Breakeven** — spot donde el P&L total cruza cero")
    st.latex(r"\text{Payoff}_{\text{combo}}(S_T^{BE}) - \text{premium neto} = 0")
    st.markdown("**Bull call spread — profit máximo acotado**")
    st.latex(r"\text{máx profit} = (K_2 - K_1) - \text{premium neto}")
    st.markdown("**Straddle — breakevens simétricos**")
    st.latex(r"S_T^{BE} = K \pm (\text{premium}_{\text{call}} + \text{premium}_{\text{put}})")


def cap13_15() -> None:
    """Cap 13-15 · Valuación de opciones."""
    _formula_header("Capítulos 13-15 · Binomial, GBM y Black-Scholes")
    st.markdown("**Binomial — probabilidad risk-neutral**")
    st.latex(r"p = \frac{e^{(r-q)\Delta t} - d}{u - d}")
    st.markdown("**Inducción backward**")
    st.latex(r"f = e^{-r\Delta t}\left[p\,f_u + (1-p)\,f_d\right]")
    st.markdown("**Calibración CRR**")
    st.latex(r"u = e^{\sigma\sqrt{\Delta t}} \qquad d = \tfrac{1}{u}")
    st.markdown("**Delta replicante (1 paso)**")
    st.latex(r"\Delta = \frac{f_u - f_d}{Su - Sd}")
    st.markdown("**GBM bajo medida risk-neutral**")
    st.latex(r"dS = (r-q)S\,dt + \sigma S\,dW")
    st.markdown("**Black-Scholes-Merton**")
    st.latex(r"c = S_0 e^{-qT} N(d_1) - K e^{-rT} N(d_2)")
    st.latex(r"p = K e^{-rT} N(-d_2) - S_0 e^{-qT} N(-d_1)")
    st.latex(r"d_1 = \frac{\ln(S_0/K) + (r-q+\tfrac{1}{2}\sigma^2)T}{\sigma\sqrt{T}}, \quad d_2 = d_1 - \sigma\sqrt{T}")


def cap17_18() -> None:
    """Cap 17-18 · Opciones sobre índices, FX y futuros."""
    _formula_header("Capítulos 17-18 · Index / FX / Futures options")
    st.markdown("**Opción sobre índice** — BSM con dividend yield del índice")
    st.latex(r"c = S_0 e^{-qT} N(d_1) - K e^{-rT} N(d_2)")
    st.markdown("**Garman-Kohlhagen** — opción sobre divisas ($r_f$ = tasa extranjera)")
    st.latex(r"c = S_0 e^{-r_f T} N(d_1) - K e^{-r_d T} N(d_2)")
    st.markdown("**Forward FX — covered interest parity**")
    st.latex(r"F_0 = S_0 \, e^{(r_d - r_f)T}")
    st.markdown("**Black's model** — opción sobre futuros")
    st.latex(r"c = e^{-rT}\left[F_0 N(d_1) - K N(d_2)\right]")
    st.latex(r"d_1 = \frac{\ln(F_0/K) + \tfrac{1}{2}\sigma^2 T}{\sigma\sqrt{T}}, \quad d_2 = d_1 - \sigma\sqrt{T}")
    st.markdown("**Delta de futures option**")
    st.latex(r"\Delta_{\text{call}} = e^{-rT} N(d_1)")


def cap19() -> None:
    """Cap 19 · Griegas."""
    _formula_header("Capítulo 19 · Las griegas")
    st.caption("N'(x) = densidad normal estándar. Opción europea con dividend yield q.")
    st.markdown("**Delta**")
    st.latex(r"\Delta_{\text{call}} = e^{-qT} N(d_1) \qquad \Delta_{\text{put}} = e^{-qT}[N(d_1)-1]")
    st.markdown("**Gamma** (igual call y put)")
    st.latex(r"\Gamma = \frac{e^{-qT} N'(d_1)}{S_0 \sigma \sqrt{T}}")
    st.markdown("**Vega** (igual call y put)")
    st.latex(r"\nu = S_0 e^{-qT} N'(d_1) \sqrt{T}")
    st.markdown("**Theta (call)**")
    st.latex(r"\Theta_{\text{call}} = -\frac{S_0 e^{-qT} N'(d_1)\sigma}{2\sqrt{T}} - rKe^{-rT}N(d_2) + qS_0 e^{-qT}N(d_1)")
    st.markdown("**Rho**")
    st.latex(r"\rho_{\text{call}} = KTe^{-rT}N(d_2) \qquad \rho_{\text{put}} = -KTe^{-rT}N(-d_2)")
    st.markdown("**Relación delta-gamma-theta** (portfolio delta-neutral)")
    st.latex(r"\Theta + \tfrac{1}{2}\sigma^2 S^2 \Gamma = r\Pi")


def cap8() -> None:
    """Cap 8 · Securitization."""
    _formula_header("Capítulo 8 · Securitization")
    st.markdown("**Pérdida de un tranche** dado el pool loss rate $L$")
    st.latex(r"\text{loss}_{\text{tranche}} = \text{clip}\!\left(\frac{L - \text{attach}}{\text{detach} - \text{attach}},\;0,\;1\right)")
    st.markdown("**Cópula gaussiana de un factor** — modelo de correlación de defaults")
    st.latex(r"X_i = \sqrt{\rho}\,M + \sqrt{1-\rho}\,Z_i")
    st.caption("M = factor sistémico común · Z_i = factor idiosincrático · ρ = correlación.")
    st.markdown("**Default del crédito $i$** — ocurre si $X_i$ cae bajo el umbral")
    st.latex(r"\text{default}_i \iff X_i < N^{-1}(p_{\text{default}})")


def cap9() -> None:
    """Cap 9 · OIS y colateral."""
    _formula_header("Capítulo 9 · OIS y colateral")
    st.markdown("**Descuento con OIS** — para derivados colateralizados")
    st.latex(r"PV = \text{CF} \cdot e^{-r_{\text{OIS}}\, T}")
    st.markdown("**LIBOR-OIS spread** — termómetro de stress interbancario")
    st.latex(r"\text{spread} = R_{\text{LIBOR}} - R_{\text{OIS}}")
    st.markdown("**Multi-curve framework** — descuento y forecast con curvas distintas")
    st.latex(r"V = \sum_i \text{CF}_i(\text{curva LIBOR}) \cdot e^{-r_i^{\text{OIS}}\, t_i}")
    st.caption("Forecast de cashflows flotantes con la curva LIBOR-forward; "
               "descuento con la curva OIS.")
