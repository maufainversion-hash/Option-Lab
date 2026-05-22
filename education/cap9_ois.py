"""
Hull Cap 9 · OIS rates y colateral.

Por qué se descuenta con OIS y no con LIBOR. LIBOR-OIS spread como termómetro
de stress. Multi-curve framework: una curva para descontar, otra para forecast
de cashflows flotantes.
"""
from __future__ import annotations

from math import exp

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from ui.styling import output_card, info_box, hull_check
from education import formulario


def render() -> None:
    st.markdown(
        '<h1 style="margin:0;font-weight:600;">Hull Cap 9 · OIS y colateral</h1>'
        '<div style="color:var(--text-muted);font-size:13px;margin-bottom:20px;">'
        'Por qué OIS para descontar, LIBOR-OIS spread, multi-curve framework.'
        '</div>', unsafe_allow_html=True)

    tab1, tab2, tab3, tab_f = st.tabs([
        "Por qué OIS para descontar",
        "LIBOR-OIS spread",
        "Multi-curve framework",
        "📐 Fórmulas",
    ])

    # ============================================================
    # TAB 1 — Por qué OIS para descontar
    # ============================================================
    with tab1:
        st.header("OIS vs LIBOR — el cambio post-crisis")
        st.markdown(r"""
**Pre-2008**, todo el mundo descontaba derivados con la **curva LIBOR**. Después
de la crisis, quedó claro que LIBOR tiene **credit risk** del panel bancario
(banks reporting → si un banco está en problemas, su LIBOR submission no es
"risk-free"). Las contrapartes con colateral diario (CSA) miran otra cosa.

**OIS** (Overnight Index Swap) = swap donde una pata paga **floating overnight
rate compoundeada** (Fed Funds en USD, EONIA → €STR en EUR). Como es overnight,
prácticamente no hay credit risk: el rate refleja la política monetaria, no la
salud bancaria.

### Por qué OIS para colateral

Cuando un derivado está **colateralizado** (la mayoría del mercado interbancario):
- El colateral genera **OIS** (es cash diario en una cuenta).
- El "costo de financiar" la posición = OIS.
- Por no-arbitraje: el derivado se descuenta con la curva que paga el colateral.

**Conclusión post-crisis (~2010 en adelante):**
> Derivados colateralizados → descontar con **OIS**.
> Derivados sin colateral (corporates) → descontar con tasa de funding propia del banco.
""")
        st.subheader("Comparación: NPV de un cashflow bajo OIS vs LIBOR")
        c1, c2, c3 = st.columns(3)
        cf = c1.number_input("Cashflow nominal", value=1_000_000.0, step=10000.0)
        T_cf = c2.number_input("T (años)", value=5.0, step=0.5)
        ois_rate = c3.number_input("OIS rate (cc)", value=0.030, step=0.005, format="%.4f")

        c4, c5 = st.columns(2)
        spread_bps = c4.slider("LIBOR-OIS spread (bps)", 0, 300, 25, 5)
        libor_rate = ois_rate + spread_bps / 10000
        c5.markdown(output_card("LIBOR rate (cc)", f"{libor_rate*100:.4f}%",
                                hint=f"OIS + {spread_bps} bps", color="info"),
                    unsafe_allow_html=True)

        pv_ois = cf * exp(-ois_rate * T_cf)
        pv_libor = cf * exp(-libor_rate * T_cf)
        diff = pv_ois - pv_libor

        st.subheader("PVs comparados")
        cc = st.columns(3)
        cc[0].markdown(output_card("PV bajo OIS (correcto)", f"${pv_ois:,.0f}",
                                    color="positive"), unsafe_allow_html=True)
        cc[1].markdown(output_card("PV bajo LIBOR (pre-2008)", f"${pv_libor:,.0f}",
                                    color="negative"), unsafe_allow_html=True)
        cc[2].markdown(output_card("Δ por descontar mal", f"${diff:+,.0f}",
                                    hint=f"{(diff/pv_libor)*100:+.2f}%",
                                    color="muted"), unsafe_allow_html=True)

        info_box("Para un swap de 5 años con notional 1MM y spread LIBOR-OIS de 25 bps, "
                 "elegir mal la curva de descuento te puede valuar el derivado mal "
                 "por ~$12K. En portafolios grandes (bancos, hedge funds) eso se vuelve "
                 "millones de USD en P&L mal calculado.", kind="hull")

    # ============================================================
    # TAB 2 — LIBOR-OIS spread
    # ============================================================
    with tab2:
        st.header("LIBOR-OIS spread como termómetro de stress")
        st.markdown(r"""
El **spread LIBOR-OIS** es un indicador clásico de stress en el sistema bancario
interbancario. En tiempos normales: 5-15 bps. En crisis: explota.

| Período | LIBOR-OIS típico | Comentario |
|---|---|---|
| 2003-2007 | 5-10 bps | Mercado tranquilo, banks se prestan entre sí sin friction |
| 2007 Aug | 50-90 bps | BNP Paribas suspende 3 funds — inicio crisis |
| 2008 Oct | 350+ bps | Post-Lehman, banks no se prestan entre sí, panic |
| 2009-2019 | 10-20 bps | Steady state post-crisis con QE |
| 2020 Mar | 130 bps | COVID liquidity squeeze (breve) |
| 2021+ | LIBOR phasing out → SOFR/€STR/SONIA |

### Por qué el spread se mueve

- **Credit risk** de los panel banks: si la probabilidad de default de un banco
  promedio sube, el LIBOR (que es **unsecured lending** entre banks) sube.
- **Liquidity premium**: si los banks acumulan cash defensivamente y no se prestan,
  el LIBOR repunta aún sin cambio en credit fundamentals.
- **OIS** se mueve con la **política monetaria** (Fed funds target, expectations).
  Es mucho más estable.
""")
        st.subheader("Simulación histórica simplificada del spread")
        np.random.seed(42)
        days = np.arange(0, 365 * 6)
        base = 12 + 2 * np.sin(days / 100)
        # crisis spike at year ~1.5 (Aug 2007), year ~3 (Sept 2008), year ~5 (COVID)
        spike_2007 = 70 * np.exp(-((days - 365 * 1.5) / 80) ** 2)
        spike_2008 = 340 * np.exp(-((days - 365 * 3) / 120) ** 2)
        spike_2020 = 110 * np.exp(-((days - 365 * 5) / 50) ** 2)
        noise = np.random.normal(0, 3, len(days))
        spread = np.maximum(0, base + spike_2007 + spike_2008 + spike_2020 + noise)
        years = days / 365

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=years, y=spread, mode="lines",
            line=dict(color="#d4af37", width=1.8),
            fill="tozeroy", fillcolor="rgba(212,175,55,0.15)",
            name="LIBOR-OIS spread",
        ))
        fig.add_hline(y=20, line=dict(color="#3fb950", dash="dot"),
                      annotation_text="Normal (≤20 bps)")
        fig.add_hline(y=100, line=dict(color="#f85149", dash="dash"),
                      annotation_text="Stress (≥100 bps)")
        fig.add_annotation(x=1.5, y=120, text="BNP halt<br>(Aug 2007)",
                           showarrow=True, arrowhead=2, font=dict(color="#ffa198"))
        fig.add_annotation(x=3.0, y=340, text="Lehman<br>(Sep 2008)",
                           showarrow=True, arrowhead=2, font=dict(color="#f85149"))
        fig.add_annotation(x=5.0, y=130, text="COVID<br>(Mar 2020)",
                           showarrow=True, arrowhead=2, font=dict(color="#ffa198"))
        fig.update_layout(template="plotly_dark", height=420,
                          title="LIBOR-OIS spread (estilizado, 6 años post-2007)",
                          xaxis_title="Años desde el inicio del período",
                          yaxis_title="Spread (bps)",
                          margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig, use_container_width=True)

        info_box("LIBOR está siendo retirado (cessation 2023-2024 según moneda). "
                 "Lo reemplazan rates 'casi risk-free': <b>SOFR</b> (USD), <b>€STR</b> (EUR), "
                 "<b>SONIA</b> (GBP), <b>TONA</b> (JPY). Todos son overnight, alineados al "
                 "spirit de OIS.", kind="info")

    # ============================================================
    # TAB 3 — Multi-curve framework
    # ============================================================
    with tab3:
        st.header("Multi-curve framework — descuento ≠ forecast")
        st.markdown(r"""
La gran insight post-2010: **la curva que usás para descontar NO tiene que ser
la misma que usás para forecasear cashflows flotantes.**

### El framework moderno (simplified)

Para valuar un swap LIBOR/fixed con colateral:

1. **Descontás** todos los cashflows con la curva **OIS** (porque el colateral
   paga OIS).
2. **Forecaseás** los cashflows flotantes (LIBOR a recibir/pagar en cada reset)
   con la **curva LIBOR-forward** (independiente).

**Pre-2008** (single-curve world): ambas eran la misma curva LIBOR. Esto
funcionaba porque LIBOR-OIS era tan chico que daba lo mismo.

**Post-2008** (multi-curve world): hay que mantener **una curva de descuento
por moneda × tipo de colateral** (USD/OIS, EUR/€STR, etc.) y **una curva de
forecast por benchmark** (3M LIBOR, 6M LIBOR, etc.).

### Ejemplo numérico
""")
        st.subheader("Swap simple bajo multi-curve")
        c1, c2 = st.columns(2)
        notional = c1.number_input("Notional", value=10_000_000.0, step=100000.0)
        T_swap = c2.number_input("Plazo total (años)", value=5.0, step=0.5)

        c3, c4 = st.columns(2)
        ois_curve = c3.number_input("OIS flat (cc)", value=0.030, step=0.005, format="%.4f")
        libor_curve = c4.number_input("LIBOR-forward flat (cc)", value=0.035, step=0.005, format="%.4f")

        fixed_rate = st.slider("Fixed rate del swap", 0.01, 0.10, 0.034, 0.001, format="%.3f")
        freq = st.selectbox("Frequencia de pago (años)", [0.25, 0.5, 1.0], index=1)

        payment_times = [freq * i for i in range(1, int(T_swap / freq) + 1)]

        # Bajo multi-curve: descontamos con OIS, forecaseamos floating con LIBOR
        b_fix = sum(notional * fixed_rate * freq * exp(-ois_curve * t) for t in payment_times) \
                + notional * exp(-ois_curve * payment_times[-1])
        # Floating leg: cada pago floating es notional * libor * freq, pero al final también devuelve notional
        b_flt = sum(notional * libor_curve * freq * exp(-ois_curve * t) for t in payment_times) \
                + notional * exp(-ois_curve * payment_times[-1])
        v_multi = b_fix - b_flt

        # Bajo single-curve LIBOR (pre-2008): descontamos todo con LIBOR
        b_fix_old = sum(notional * fixed_rate * freq * exp(-libor_curve * t) for t in payment_times) \
                    + notional * exp(-libor_curve * payment_times[-1])
        b_flt_old = notional  # under single-curve, floating leg always vale el notional al inicio
        v_single = b_fix_old - b_flt_old

        st.subheader("Valuación bajo cada framework")
        cc = st.columns(2)
        v_color_m = "positive" if v_multi >= 0 else "negative"
        v_color_s = "positive" if v_single >= 0 else "negative"
        cc[0].markdown(output_card(
            "V swap (multi-curve, post-2008)", f"${v_multi:+,.0f}",
            hint="OIS para descuento + LIBOR para forecast", color=v_color_m,
        ), unsafe_allow_html=True)
        cc[1].markdown(output_card(
            "V swap (single-curve LIBOR, pre-2008)", f"${v_single:+,.0f}",
            hint="LIBOR para todo (la convención vieja)", color=v_color_s,
        ), unsafe_allow_html=True)
        st.markdown(output_card(
            "Diferencia", f"${v_multi - v_single:+,.0f}",
            hint="El error que cometés si descontás con la curva equivocada",
            color="muted",
        ), unsafe_allow_html=True)

        info_box("La diferencia entre las dos valuaciones crece con el plazo y con el "
                 "LIBOR-OIS spread. En portfolios de billones de notional como los de un "
                 "dealer mayor, descontar con la curva equivocada se traduce en P&L "
                 "incorrecto del orden de cientos de millones.", kind="hull")

    with tab_f:
        formulario.cap9()
