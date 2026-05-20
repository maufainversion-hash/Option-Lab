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

    tab0, tab1, tab2, tab3, tab4 = st.tabs([
        "Qué son y para qué sirven",
        "Forward vs Futuro",
        "Mark-to-Market",
        "Convergencia spot-futuro",
        "Especulación y Apalancamiento",
    ])

    with tab0:
        st.header("Fundamentos — derivados, futuros y los actores del mercado")

        st.markdown(r"""
### 1 · ¿Qué es un derivado?

Un **derivado** es un instrumento financiero cuyo **valor deriva** del precio de
otro activo, llamado **subyacente**. No es el activo en sí: es un contrato cuyo
P&L depende de lo que le pase a ese activo.

El subyacente puede ser cualquier cosa cuyo precio se pueda medir: acciones,
índices bursátiles, commodities (oil, oro, soja), divisas, tasas de interés,
bonos, electricidad, eventos climáticos, créditos, hasta volatilidad misma.

**Las 4 grandes familias de derivados** (Hull Cap 1):

| Familia | Qué es | Ejemplo típico |
|---|---|---|
| **Forwards** | Acuerdo bilateral para comprar/vender en T a precio K | Importador fija USD/ARS a 90 días |
| **Futuros** | Forward estandarizado y listado en exchange | Dólar futuro en MATBA Rofex |
| **Opciones** | Derecho (no obligación) de comprar/vender a K | Call sobre GGAL en BYMA |
| **Swaps** | Intercambio periódico de flujos entre 2 partes | IR swap fijo vs LIBOR |

---

### 2 · ¿Qué es un futuro específicamente?

Un **contrato futuro** es un acuerdo **estandarizado** para comprar (long) o
vender (short) una cantidad fija de un activo subyacente, a un **precio acordado
hoy**, con entrega en una **fecha futura específica**.

**Las 5 propiedades que definen un futuro:**

1. **Estandarización total**: el exchange define todo — tamaño del contrato
   (ej. 100 oz de oro), vencimiento (ej. 3er viernes del mes), calidad del
   subyacente, lugar de entrega. Vos solo elegís precio y cantidad de contratos.
2. **Negociación en exchange**: cotiza en mercado centralizado (CME, ICE,
   MATBA Rofex). Liquidez transparente, precios públicos.
3. **Clearing house como contraparte**: la cámara compensadora se interpone
   entre comprador y vendedor. Vos no le debés al otro lado del trade, le debés
   a la cámara. Esto elimina counterparty risk individual.
4. **Mark-to-market diario**: tu posición se revalúa cada día, las ganancias/
   pérdidas se acreditan/debitan en tu cuenta de margen. Si tu balance cae
   bajo el *maintenance level*, recibís un **margin call**.
5. **Liquidación**: la mayoría se cierra antes del vencimiento por **offset**
   (tomás la posición opuesta). Las que llegan a vencimiento se liquidan por
   **physical delivery** (commodities) o **cash settlement** (índices, tasas).

> **Forward vs Futuro en una frase**: el forward es un acuerdo bilateral hecho
> a medida; el futuro es un forward estandarizado que cotiza en bolsa, con
> margen diario y clearing house en el medio.

---

### 3 · ¿Para qué sirven los derivados?

Cuatro funciones económicas centrales (Hull Cap 1):

**(a) Gestión de riesgo (hedging)**

Transferir riesgo de quien no lo quiere a quien sí. Un exportador agro tiene
exposición natural al precio de la soja: si baja, pierde. Si vende futuros
de soja, transfiere ese riesgo al mercado a cambio de **certeza**. Cuando la
soja baje, la pérdida del físico se compensa con la ganancia del futuro short.

**(b) Especulación**

Tomar posiciones direccionales con **eficiencia de capital**. Un hedge fund
que cree que el oro va a subir compra futuros: con un margen del ~10% del
notional, controla la exposición completa. Si acierta, el ROI sobre el margen
es enorme; si se equivoca, también.

**(c) Arbitraje**

Explotar ineficiencias de precio entre mercados. Si el futuro de oro está
demasiado caro respecto al spot (F₀ > S₀·e^{rT} más costos), un arbitrajista
compra spot, vende futuro, y se queda con la diferencia *risk-free*. La acción
de los arbitrajistas presiona los precios hasta que la oportunidad desaparece.

**(d) Descubrimiento de precios**

Los precios de futuros agregan las expectativas de miles de participantes.
El futuro de dólar a 90 días en MATBA Rofex no es solo un precio: es la
mejor estimación pública de qué va a pasar con el FX. Bancos centrales,
empresas y traders los miran para tomar decisiones.

---

### 4 · Los 3 tipos de inversores

Hull divide a los participantes en tres categorías por motivación:
""")

        invest_df = pd.DataFrame({
            "Tipo": ["**Hedger**", "**Especulador**", "**Arbitrajista**"],
            "Motivación": [
                "Reducir un riesgo que YA tiene",
                "Tomar riesgo NUEVO apostando a una dirección",
                "Capturar mispricing risk-free",
            ],
            "Ejemplo argentino típico": [
                "Exportador agro short futuro de soja para fijar el precio de venta",
                "Trader compra dólar futuro porque cree que el peso se va a devaluar",
                "Arbitra CCL vs MEP cuando se abre el spread",
            ],
            "Trade-off": [
                "Renuncia al upside a cambio de certeza",
                "Alto leverage = alto retorno o alta pérdida",
                "Requiere capital, velocidad y bajos costos",
            ],
        })
        st.dataframe(invest_df, hide_index=True, use_container_width=True)

        st.markdown(r"""
**Ejemplos concretos por tipo:**

**Hedger** — *Aerolínea cubriendo combustible*
- Tiene gastos de jet fuel garantizados.
- Compra futuros de crudo (cross-hedge porque no hay futuro líquido de jet fuel).
- Si el petróleo sube → su combustible sube, pero la ganancia del futuro lo compensa.
- Si el petróleo baja → su combustible baja, pero pierde en el futuro. Resultado: **costo fijado**.

**Especulador** — *Hedge fund con tesis macro sobre el peso*
- Cree que en 6 meses ARS va a estar más débil vs USD.
- Compra dólar futuro Rofex con margen ~10%.
- Si acierta: la ganancia del futuro sobre el margen es 5x-10x el movimiento %.
- Si erra: pierde 5x-10x. Margin calls posibles si la posición se mueve en contra.

**Arbitrajista** — *Trading desk de banco haciendo cash & carry*
- Detecta que el futuro de oro a 6 meses cotiza por encima del fair value (S₀·e^{rT}).
- Compra oro spot, vende futuro, financia la posición.
- Al vencimiento entrega el oro, cobra el strike, devuelve el préstamo.
- Profit risk-free = F₀ − S₀·e^{rT} (asumiendo costos pequeños).

---

### 5 · Mercados principales

**Global:**
- **CME Group** (Chicago Mercantile Exchange): el más grande del mundo. Agrupa
  CME (índices, FX, tasas), CBOT (granos, treasuries), NYMEX (energía), COMEX (metales).
- **ICE** (Intercontinental Exchange): energía (Brent), commodities, equity índices.
- **Eurex**: derivados europeos, bonos, equity.
- **HKEX, JPX**: Asia.

**Argentina:**
- **MATBA Rofex** (Mercado a Término de Buenos Aires + Rofex fusión 2018):
  futuros de **dólar Rofex**, commodities agro (soja, maíz, trigo), tasas Badlar.
- **MAE** (Mercado Abierto Electrónico): bonos, FX, repo.
- **BYMA** (Bolsas y Mercados Argentinos): equity, opciones sobre acciones líderes.

**Regulación**: en USA la **CFTC** (futuros) + **SEC** (securities). En Argentina
la **CNV** (Comisión Nacional de Valores) supervisa todos los mercados y el
**BCRA** regula el mercado FX.

---

### 6 · Tamaño y riesgos del mercado

El mercado **global de derivados** tiene un **notional outstanding** de ~$700
trillones (BIS 2024), aproximadamente **7 veces el PIB mundial**. Pero ojo: el
notional sobreestima la exposición real. El **gross market value** (lo que
realmente vale el portfolio si se cerrara hoy) es mucho menor, ~$20T.

**Riesgos asociados:**

| Riesgo | Qué es | Mitigación |
|---|---|---|
| **Market risk** | Pérdida por movimiento del subyacente | Diversificación, stop-loss |
| **Counterparty risk** | Que la otra parte no pague | Clearing house, colateral diario |
| **Liquidity risk** | No poder cerrar a precio razonable | Operar mercados profundos |
| **Model risk** | Tu modelo de valuación está mal | Validación independiente, stress tests |
| **Operational risk** | Errores humanos / sistemas | Controles, reconciliaciones |
| **Systemic risk** | Crisis afecta a todos a la vez | Regulación, requisitos de capital |
""")

        with st.expander("📖 Historia breve de los derivados"):
            st.markdown(r"""
**Siglo XVII Japón** — mercados de arroz en Dojima son los primeros futuros
modernos. Los samurai recibían su salario en arroz y vendían contratos a término
para fijar el valor monetario.

**1848 — CBOT (Chicago Board of Trade)** — el primer exchange de futuros
moderno. Inicialmente centrado en granos del Midwest. Estandariza contratos
y crea la cámara compensadora.

**1972 — Futuros de divisas** — colapso de Bretton Woods (oro/dólar fijo)
genera la necesidad de hedgear FX. CME crea el International Monetary Market.

**1973 — Opciones listadas + Black-Scholes** — CBOE (Chicago Board Options
Exchange) abre como primer mercado de opciones listadas. Mismo año, Fischer
Black, Myron Scholes y Robert Merton publican el modelo BSM.

**1980s-90s — Explosión de derivados OTC** — swaps de tasas, currency swaps,
exotic options. Mercado en crecimiento exponencial.

**2008 — Crisis subprime** — los CDOs y credit derivatives detonan la crisis
financiera global. Bear Stearns, Lehman, AIG. La opacidad del mercado OTC
queda al descubierto.

**Post-2010 — Reformas** — Dodd-Frank (USA), EMIR (Europa). Centralización
del clearing OTC, reporting obligatorio, márgenes para non-cleared trades.

**Hoy** — el mercado de derivados es ~$700T notional. La mayor parte sigue
siendo OTC (swaps de tasas IBOR/OIS) pero el ecosistema regulatorio post-2010
hizo el sistema sustancialmente más robusto que en 2008.
""")

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
