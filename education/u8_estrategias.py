"""
Unidad VIII · Estrategias multi-leg (Hull Cap 12).
"""
from __future__ import annotations

import numpy as np
import streamlit as st

from pricing.black_scholes import bs_price
from strategies import legs as L
from strategies.payoff import max_profit_loss, breakeven_points
from strategies.aggregator import net_greeks
from ui.charts.payoff_diagram import payoff_chart
from education import formulario


# ============================================================
# Guía práctica por estrategia: cuándo / quién / ejemplo / riesgo
# ============================================================
STRATEGY_CONTEXT: dict[str, dict[str, str]] = {
    "Long Call": {
        "compo": "1 long call",
        "cuando": "Esperás que el subyacente **suba fuerte** dentro del horizonte T. "
                  "Querés exposición direccional bullish con riesgo limitado al premium pagado.",
        "quien": "**Especulador bullish** con tesis concreta (earnings positivos, M&A, "
                 "noticias sectoriales). También usado por traders que quieren leverage "
                 "sin financiar la compra del activo entero.",
        "ejemplo": "Comprás call de **YPF strike $5.000** vencimiento a 60 días, premium $200. "
                   "Tenés tesis de que Vaca Muerta y nuevas concesiones empujan la acción a "
                   "$6.500. Si llega, ganás $1.500 − $200 = **$1.300 por acción** (650% sobre el premium). "
                   "Si no se mueve o baja, perdés los $200 y nada más.",
        "riesgo": "Time decay (theta) **come el premium todos los días**. Si el subyacente se "
                  "queda lateral hasta vencimiento, perdés el 100% del premium. La probabilidad de "
                  "ejercicio ITM (N(d₂)) suele ser 30-50% para calls OTM cortos.",
    },
    "Long Put": {
        "compo": "1 long put",
        "cuando": "Esperás que el subyacente **caiga fuerte**. Versión bearish del long call.",
        "quien": "**Especulador bearish** (tesis de caída por crisis sectorial, earnings malos, "
                 "factor macro adverso), o **hedger** que protege una posición long sin venderla.",
        "ejemplo": "Antes de elecciones inciertas en Argentina, comprás puts de **Galicia (GGAL) "
                   "strike $1.500** vencimiento 30 días, premium $80. Si gana el candidato "
                   "market-unfriendly y la acción cae a $1.000, ganás $500 − $80 = **$420 por acción**. "
                   "Versión hedge: tenés 10.000 acciones de Galicia y comprás puts para no tener que "
                   "venderlas.",
        "riesgo": "Igual que long call: theta come premium. Además, las acciones tienen drift positivo "
                  "esperado (r − q), así que estructuralmente los puts son más caros que los calls "
                  "(volatility skew lo amplifica todavía más).",
    },
    "Covered Call": {
        "compo": "1 long stock  +  1 short call  (K > spot)",
        "cuando": "Tenés stock long y esperás que se mueva **lateral o suba poco**. Estrategia de "
                  "**income generation** sobre posiciones existentes.",
        "quien": "**Holders de stock** que quieren generar yield extra sobre acciones que ya tienen. "
                 "Muy popular en wealth management para clientes que buscan renta sobre su portfolio.",
        "ejemplo": "Tenés 1.000 acciones de **Pampa Energía a $1.800**. Vendés 10 calls strike "
                   "$2.000 (OTM 11%) vencimiento mensual, cobrás $50 de premium cada uno = $500 total. "
                   "Si Pampa termina abajo de $2.000 → te quedás con los $500 (rentabilidad mensual ~2.8% "
                   "extra sobre el portfolio). Si supera $2.000 → te asignan, recibís $2.000 + $50 = "
                   "$2.050 por acción (todavía ganaste pero perdiste el upside por arriba).",
        "riesgo": "**Cap al upside**: si la acción se va a la luna, tu ganancia queda limitada en "
                  "K + premium. Es el opuesto al insurance — vos sos el que vende el seguro y cobrás "
                  "premium a cambio de aceptar la asignación.",
    },
    "Protective Put": {
        "compo": "1 long stock  +  1 long put  (K < spot)",
        "cuando": "Tenés stock long y querés un **seguro contra una caída fuerte**, sin vender la "
                  "posición.",
        "quien": "**Inversor long** que teme un evento de cola (crisis, earnings malos, decisión "
                 "regulatoria) pero no quiere salir del trade. También común en fondos que necesitan "
                 "limitar drawdown por mandato.",
        "ejemplo": "Tenés CEDEARs de **Tesla** comprados a USD 200, ahora valen USD 350. Querés proteger "
                   "las ganancias antes del próximo earnings sin vender. Comprás puts strike $320 a 45 "
                   "días, premium $8. Si Tesla baja a $250, el put compensa ($320 − $250 = $70). Si sube "
                   "o queda lateral, perdés solo los $8 del premium (costo del seguro).",
        "riesgo": "**Premium es costo permanente** (como pagar seguro de auto cada mes). En mercados "
                  "calmos pagás premium repetidamente sin que nunca se use el seguro. Para una posición "
                  "rolleada todo el año, el costo acumulado puede ser 5-10% del valor de la posición.",
    },
    "Bull Call Spread": {
        "compo": "1 long call K₁  +  1 short call K₂   (K₁ < K₂)",
        "cuando": "Esperás que el subyacente **suba moderado** (no x10). Querés bajar el costo del "
                  "long call aceptando un techo al profit.",
        "quien": "**Especulador moderadamente bullish** que tiene un price target concreto. Trader que "
                 "quiere mejorar el breakeven a costa de cap al upside.",
        "ejemplo": "Tesla cotiza a $300 y pensás que en 60 días estará en $340. Comprás call $310 "
                   "(premium $15) y vendés call $340 (premium $5). **Costo neto: $10**. Si termina "
                   "en $340 o más, ganás $30 − $10 = **$20 por contrato** (200% sobre el costo). Si "
                   "termina debajo de $310, perdés los $10.",
        "riesgo": "Si el subyacente sube **mucho más** que el strike alto, tu ganancia se cappea — "
                  "hubieras estado mejor con un long call simple. Trade-off clásico: menos costo a "
                  "cambio de menos upside.",
    },
    "Bear Put Spread": {
        "compo": "1 long put K₂  +  1 short put K₁   (K₁ < K₂)",
        "cuando": "Esperás que el subyacente **baje moderado**. Versión bearish del bull call spread.",
        "quien": "**Especulador moderadamente bearish** con price target. Igual que bull call pero al "
                 "revés.",
        "ejemplo": "Pensás que Mercado Libre va a corregir desde $1.500 a $1.300 después de un "
                   "earnings. Comprás put $1.450 (premium $30) y vendés put $1.300 (premium $10). "
                   "Costo neto $20. Si termina en $1.300 o menos, ganás $150 − $20 = **$130 por "
                   "contrato**. Si termina por arriba de $1.450, perdés los $20.",
        "riesgo": "Igual que bull call spread invertido: cap al downside profit. Si la acción colapsa "
                  "fuerte (ej. fraude contable, crash sectorial), hubieras ganado más con long put simple.",
    },
    "Long Straddle": {
        "compo": "1 long call  +  1 long put   (mismo strike K = spot, mismo vencimiento)",
        "cuando": "Esperás un **movimiento GRANDE pero NO sabés en qué dirección**. Apuesta de "
                  "volatilidad pura (long vega) para eventos binarios.",
        "quien": "**Especuladores de volatilidad** y traders pre-evento (earnings reports, decisiones "
                 "de FOMC, anuncios del BCRA, resultados electorales).",
        "ejemplo": "Una semana antes del earnings de **NVIDIA**, IV explota. Pero vos no sabés si va a "
                   "ser un beat masivo o un miss. Comprás call ATM y put ATM strike $500, premium "
                   "combinado $40. Si NVIDIA termina en $560 ganás $60 − $40 = $20. Si termina en $440 "
                   "ganás lo mismo. Si queda en $500, perdés los $40 (caso peor).",
        "riesgo": "**Caro**: pagás DOS premiums. Necesitás un movimiento grande para superar el "
                  "breakeven. **Vol crush** post-evento: si IV cae fuerte después del anuncio, perdés "
                  "vega aunque el direccional haya estado bien.",
    },
    "Long Strangle": {
        "compo": "1 long call K₂  +  1 long put K₁   (K₁ < spot < K₂, ambos OTM)",
        "cuando": "Igual setup que straddle pero querés **gastar menos premium**. Necesitás "
                  "movimiento aún mayor para ganar.",
        "quien": "**Especulador de vol** que quiere bajar el costo del straddle aceptando un "
                 "breakeven más lejano. Útil cuando esperás un movimiento muy grande pero no tanto "
                 "como justifica el straddle ATM.",
        "ejemplo": "Spot $500. Comprás call $530 (premium $8) y put $470 (premium $7), total $15 "
                   "(vs $40 del straddle ATM). Si termina entre $470 y $530, perdés todo. Pero si "
                   "termina en $560 o $440, ganás $30 − $15 = $15 (100% del premium).",
        "riesgo": "**Zona de pérdida más amplia** que el straddle. Si el subyacente queda entre los "
                  "dos strikes, perdés AMBOS premiums. Y necesitás un movimiento todavía mayor para "
                  "compensar.",
    },
    "Butterfly (calls)": {
        "compo": "1 long call K₁  +  2 short calls K₂  +  1 long call K₃   (K₁ < K₂ < K₃ equidistantes)",
        "cuando": "Tenés una tesis **muy precisa** sobre dónde va a terminar el spot al vencimiento. "
                  "Apuesta direccional + apuesta de baja vol simultánea.",
        "quien": "**Traders sofisticados** con vista pinpoint sobre el target. Common en mesas de "
                 "exotic options o trading de IV. También se usa para 'pin risk' alrededor de "
                 "strikes con alto open interest.",
        "ejemplo": "Pensás que el dólar Rofex cierra **exactamente en $1.200** al vencimiento de "
                   "fin de mes (porque hay mucho open interest ahí). Comprás 1 call $1.150, vendés "
                   "2 calls $1.200, comprás 1 call $1.250. Premium neto chico (~$10). Si cierra en "
                   "$1.200 → ganás $50 − $10 = **$40**. Fuera del rango, perdés los $10.",
        "riesgo": "**Probabilidad de profit es baja** (necesitás precisión). El profit máximo solo "
                  "ocurre en un punto exacto. Útil más como estrategia de risk-reward asimétrico que "
                  "como apuesta principal del portfolio.",
    },
    "Iron Condor": {
        "compo": "1 long put K₁  +  1 short put K₂  +  1 short call K₃  +  1 long call K₄   (K₁<K₂<spot<K₃<K₄)",
        "cuando": "Esperás que el subyacente se mantenga **LATERAL** en un rango definido. Apuesta de "
                  "baja volatilidad realizada vs alta IV implícita.",
        "quien": "**Theta sellers** que venden volatilidad sistemáticamente (income strategies de "
                 "fondos como JEPI, SVXY). Common en meses post-evento cuando IV está cara pero el "
                 "realised es bajo.",
        "ejemplo": "SPY cotiza a $500, IV alta post-FOMC. Vendés put $490 (premium $5), comprás put "
                   "$485 (premium $2), vendés call $510 (premium $4), comprás call $515 (premium $1). "
                   "Premium neto cobrado: $5 + $4 − $2 − $1 = **$6**. Si SPY queda entre $490 y $510 "
                   "al vencimiento, te quedás con los $6 (100% profit). Si se sale, máximo pierde "
                   "$5 − $6 = $1 (la diferencia de strikes menos el premium cobrado).",
        "riesgo": "**Risk-reward asimétrico** al revés: ganás poco frecuentemente y perdés "
                  "ocasionalmente más grande. Si el subyacente hace un movimiento brusco fuera del "
                  "rango (gap, crash, rally), la pérdida puede ser 5-10x el premium cobrado. Stop "
                  "loss disciplinado es crítico.",
    },
    "Collar": {
        "compo": "1 long stock  +  1 long put K_p  +  1 short call K_c   (K_p < spot < K_c)",
        "cuando": "Tenés stock long con **ganancia acumulada** y querés protegerla **sin pagar "
                  "premium**. Combina protective put con covered call para financiarlo.",
        "quien": "**Holders de stocks con ganancia significativa** (empleados con stock options "
                 "ya ITM, inversores que necesitan asegurar gains antes de cerrar el año fiscal).",
        "ejemplo": "Compraste **CEDEARs de Google a USD 100**, ahora valen USD 180. Querés protegerte "
                   "ante un crash pero no querés gastar premium. Vendés call strike $200 (cobrás $5) "
                   "y con esos $5 comprás put strike $160 (cuesta $5). **Costo neto: $0** (zero-cost "
                   "collar). Tu posición ahora tiene piso en $160 y techo en $200, sin haber gastado "
                   "nada en premium.",
        "riesgo": "**Limitás tu upside**. Si Google vuela a $300, tu ganancia queda capeada en $200. "
                  "Y si baja a $150, el put te protege pero hubieras estado mejor sin collar (porque "
                  "todavía no querías vender pero ahora estás forzado por la estructura).",
    },
}


def render() -> None:
    st.markdown(
        '<h1 style="margin:0;font-weight:600;">Unidad VIII · Estrategias multi-leg</h1>'
        '<div style="color:var(--text-muted);font-size:13px;margin-bottom:20px;">'
        'Hull Cap 12. Bull/bear spreads, straddle, strangle, butterfly, iron condor.'
        '</div>', unsafe_allow_html=True)

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
    # Guía práctica de la estrategia seleccionada
    # ============================================================
    if strat_name in STRATEGY_CONTEXT:
        ctx = STRATEGY_CONTEXT[strat_name]
        st.markdown("---")
        st.subheader(f"📚 {strat_name} — guía práctica")

        # Composición — patas del combo en notación compacta
        st.markdown(
            f'<div class="premium-card" style="border-left:3px solid var(--accent);'
            f'background:rgba(212,175,55,0.06); margin-bottom:16px;">'
            f'<div style="color:var(--text-muted);font-size:11px;'
            f'text-transform:uppercase;letter-spacing:0.5px;">🧱 Composición</div>'
            f'<div style="font-family:JetBrains Mono;color:var(--text);font-size:15px;'
            f'font-weight:500;margin-top:6px;">{ctx["compo"]}</div></div>',
            unsafe_allow_html=True,
        )

        cc1, cc2 = st.columns(2)
        with cc1:
            st.markdown(
                f'<div class="premium-card" style="border-left:3px solid var(--accent);">'
                f'<div style="color:var(--accent);font-weight:600;font-size:14px;">'
                f'🎯 Cuándo se usa</div>'
                f'<div style="color:var(--text);font-size:13px;margin-top:8px;line-height:1.6;">'
                f'{ctx["cuando"]}</div></div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div class="premium-card" style="border-left:3px solid var(--info);">'
                f'<div style="color:var(--info);font-weight:600;font-size:14px;">'
                f'👤 Quién la usa</div>'
                f'<div style="color:var(--text);font-size:13px;margin-top:8px;line-height:1.6;">'
                f'{ctx["quien"]}</div></div>',
                unsafe_allow_html=True,
            )
        with cc2:
            st.markdown(
                f'<div class="premium-card" style="border-left:3px solid var(--positive);">'
                f'<div style="color:var(--positive);font-weight:600;font-size:14px;">'
                f'🌎 Ejemplo real</div>'
                f'<div style="color:var(--text);font-size:13px;margin-top:8px;line-height:1.6;">'
                f'{ctx["ejemplo"]}</div></div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div class="premium-card" style="border-left:3px solid var(--negative);">'
                f'<div style="color:var(--negative);font-weight:600;font-size:14px;">'
                f'⚠️ Riesgo principal</div>'
                f'<div style="color:var(--text);font-size:13px;margin-top:8px;line-height:1.6;">'
                f'{ctx["riesgo"]}</div></div>',
                unsafe_allow_html=True,
            )

    st.markdown("---")
    formulario.cap12()
