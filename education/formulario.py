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
