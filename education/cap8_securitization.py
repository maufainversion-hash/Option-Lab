"""
Hull Cap 8 · Securitization y la crisis de 2007-2008.

Mecánica de los ABS / MBS / CDOs, tranching (senior / mezzanine / equity),
waterfall de pérdidas y por qué los AAA fallaron en la crisis (correlación
de defaults subestimada).
"""
from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from ui.styling import output_card, info_box


def _waterfall_losses(
    pool_loss_rate: float,
    tranches: list[tuple[str, float, float]],  # (name, attach, detach) as fractions
) -> list[dict]:
    """
    Reparte el pool_loss_rate (fraction of pool defaulted) entre tranches según
    el waterfall: equity primero, luego mezzanine, finalmente senior.
    Cada tranche pierde lo que cae en su attach/detach range.
    """
    results = []
    for name, attach, detach in tranches:
        thickness = detach - attach
        if pool_loss_rate <= attach:
            tranche_loss_pct = 0.0
        elif pool_loss_rate >= detach:
            tranche_loss_pct = 1.0
        else:
            tranche_loss_pct = (pool_loss_rate - attach) / thickness
        results.append({
            "name": name, "attach": attach, "detach": detach,
            "thickness": thickness, "loss_pct": tranche_loss_pct,
        })
    return results


def render() -> None:
    st.markdown(
        '<h1 style="margin:0;font-weight:600;">Hull Cap 8 · Securitization</h1>'
        '<div style="color:var(--text-muted);font-size:13px;margin-bottom:20px;">'
        'ABS, MBS, CDOs, tranching, waterfall y la crisis 2008.'
        '</div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs([
        "Mecánica de ABS/MBS", "Waterfall calculator", "Crisis 2008"
    ])

    with tab1:
        st.header("¿Qué es securitización?")
        st.markdown(r"""
**Securitización** = empaquetar un pool de activos (hipotecas, auto loans, credit
cards, corporate loans) en un vehículo (SPV) que emite **bonos** respaldados por
los cashflows del pool.

**Cadena clásica de hipotecas (MBS)**:

```
Borrower → Originator (banco) → Pool (SPV) → Tranches (AAA/AA/.../Equity) → Inversores
```

**Por qué se hace:**
1. El originador **off-loads** el riesgo (vende el pool al SPV, sale del balance).
2. El SPV puede emitir bonos AAA porque la **estructura de tranches** convierte un
   pool de calidad media en un instrumento senior de calidad alta.
3. El comprador AAA (fondos de pensión, bancos centrales) consigue yield extra
   vs Treasuries con (aparentemente) el mismo rating.

**Tranching** — el corazón del invento. Las pérdidas del pool van impactando los
tranches **de abajo hacia arriba**:

| Tranche | Attach | Detach | Thickness | Rating típico |
|---|---|---|---|---|
| Equity (first-loss) | 0% | 3% | 3% | NR |
| Mezzanine BBB | 3% | 7% | 4% | BBB |
| Mezzanine A | 7% | 12% | 5% | A |
| Senior AAA | 12% | 100% | 88% | AAA |
""")
        st.subheader("Visualización del stack de tranches")
        tranches_viz = [
            ("Equity (NR)", 0.0, 0.03, "#f85149"),
            ("Mezz BBB", 0.03, 0.07, "#ffa198"),
            ("Mezz A", 0.07, 0.12, "#d29922"),
            ("Senior AAA", 0.12, 1.0, "#3fb950"),
        ]
        fig = go.Figure()
        for name, attach, detach, color in tranches_viz:
            fig.add_trace(go.Bar(
                x=["Capital structure"], y=[(detach - attach) * 100],
                base=attach * 100, marker_color=color,
                name=f"{name} ({attach*100:.0f}-{detach*100:.0f}%)",
                text=f"{name}<br>{(detach-attach)*100:.0f}%",
                textposition="inside", insidetextanchor="middle",
            ))
        fig.update_layout(template="plotly_dark", barmode="stack", height=420,
                          title="Stack de capital de un CDO típico (% del pool)",
                          margin=dict(l=10, r=10, t=40, b=10),
                          yaxis=dict(range=[0, 100], title="% del pool"),
                          showlegend=True,
                          legend=dict(orientation="v", x=1.02, y=1))
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.header("Waterfall de pérdidas — calculator")
        st.markdown("""
Movés el **pool loss rate** y mirás cuánto pierde cada tranche. Las pérdidas
suben de abajo hacia arriba: hasta que el equity no esté wiped-out, el AAA no
sufre nada.
""")
        c1, c2 = st.columns([2, 1])
        with c1:
            pool_loss = st.slider("Pool loss rate (% defaulted)",
                                  min_value=0.0, max_value=30.0, value=8.0, step=0.5,
                                  format="%.1f%%")
        with c2:
            scenario = st.selectbox("Preset", [
                "Custom", "Boom (0% loss)", "Normal cycle (3%)",
                "Recession (8%)", "Crisis 2008 (20%)"
            ])
        preset_map = {"Boom (0% loss)": 0.0, "Normal cycle (3%)": 3.0,
                      "Recession (8%)": 8.0, "Crisis 2008 (20%)": 20.0}
        if scenario in preset_map:
            pool_loss = preset_map[scenario]
            st.caption(f"Override por preset: {pool_loss:.1f}%")

        tranches = [
            ("Equity (NR)", 0.0, 0.03),
            ("Mezzanine BBB", 0.03, 0.07),
            ("Mezzanine A", 0.07, 0.12),
            ("Senior AAA", 0.12, 1.0),
        ]
        results = _waterfall_losses(pool_loss / 100, tranches)

        st.subheader("Pérdida por tranche")
        cols = st.columns(4)
        colors = ["negative", "negative", "info", "positive"]
        for col, r, c in zip(cols, results, colors):
            loss_pct = r["loss_pct"] * 100
            actual_color = "negative" if loss_pct > 50 else ("info" if loss_pct > 0 else "positive")
            col.markdown(output_card(
                r["name"], f"{loss_pct:.1f}%",
                hint=f"Attach {r['attach']*100:.0f}%–{r['detach']*100:.0f}%",
                color=actual_color,
            ), unsafe_allow_html=True)

        # Bar chart de pérdidas vs tamaño de tranche
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=[r["name"] for r in results],
            y=[r["thickness"] * 100 for r in results],
            name="Tamaño del tranche",
            marker_color="rgba(212,175,55,0.3)",
            text=[f"{r['thickness']*100:.0f}%" for r in results],
            textposition="outside",
        ))
        fig.add_trace(go.Bar(
            x=[r["name"] for r in results],
            y=[r["thickness"] * r["loss_pct"] * 100 for r in results],
            name="Pérdida absoluta (% del pool)",
            marker_color="#f85149",
            text=[f"{r['thickness']*r['loss_pct']*100:.1f}%" for r in results],
            textposition="outside",
        ))
        fig.update_layout(template="plotly_dark", barmode="overlay", height=380,
                          title="Tamaño vs pérdida absorbida (cada tranche, % del pool total)",
                          margin=dict(l=10, r=10, t=40, b=10),
                          legend=dict(orientation="h", yanchor="bottom", y=1.02))
        st.plotly_chart(fig, use_container_width=True)

        info_box("Notá cómo en 'Crisis 2008 (20%)' el equity está wiped, el BBB y A "
                 "también, y hasta el AAA empieza a sufrir (~9% loss). Pre-crisis, "
                 "los modelos asumían que el AAA jamás sufriría — la realidad fue otra.",
                 kind="warning")

    with tab3:
        st.header("¿Qué falló en 2008?")
        st.markdown(r"""
La crisis subprime fue un **cluster fuck de assumption failures**. Las cuatro grandes:

**1. Originación predatoria** — los originadores (Countrywide, IndyMac, etc.)
emitían **NINJA loans** ("No Income, No Job, no Assets"): hipotecas con doc
fraudulenta, teaser rates 2-3 años y luego reset.

**2. Modelos de correlación rotos** — los CDOs se ratearon asumiendo
correlación baja entre defaults de hipotecas en distintas regiones. La copula
gaussiana de Li (2000) fue el modelo standard. Cuando la correlación se dispara
en una crisis sistémica, **todas las hipotecas defaultean juntas** y el AAA pierde.

**3. CDO² (CDO al cuadrado)** — empaquetar tranches mezzanine de varios CDOs en
un nuevo CDO. Suena absurdo, lo era. Concentraba todo el riesgo de cola en el
tope de la estructura.

**4. Conflict of interest en ratings** — las agencias (S&P, Moody's, Fitch)
cobraban al emisor. Si no daban AAA, el emisor iba a la competencia. **Race to
the bottom**.

### El timing canónico

| Fecha | Evento |
|---|---|
| 2003-2006 | Boom hipotecario, originación masiva subprime |
| 2007 Feb | HSBC anuncia $10B losses en US subprime |
| 2007 Jun | Bear Stearns hedge funds colapsan |
| 2008 Mar | Bear Stearns rescatado por JPMorgan |
| 2008 Sep 7 | Fannie/Freddie nacionalizados |
| 2008 Sep 15 | **Lehman Brothers quiebra** |
| 2008 Sep 16 | AIG rescatado ($85B inicial) |
| 2008 Oct | TARP ($700B) firmado |

### Lecciones que sobreviven en el curriculum

- **Tail correlation matters more than average correlation.** El modelo Li
  funcionaba "en promedio", colapsaba en cola.
- **Liquidez ≠ valor.** El AAA-MBS era "líquido" hasta que dejó de serlo. Mark-
  to-market en ese contexto es problemático.
- **Hard-to-value tranches están al final del waterfall.** Si tu equity está
  ya wiped, el mezzanine es un binary bet.
- **Ratings ≠ riesgo.** Una calificación AAA significa "el emisor cumplió los
  criterios del modelo del rater", no "este bono va a pagar".
""")

        st.subheader("Simulación: efecto de la correlación en el tail loss")
        st.markdown(
            "Si la correlación entre defaults sube, la **probabilidad de un tail "
            "event** (pool loss > 10%) crece dramáticamente. Aquí simulamos un pool "
            "de 100 hipotecas con probabilidad de default individual de 5%, bajo "
            "distintas correlaciones (vía cópula gaussiana simplificada de un factor)."
        )
        n_loans = 100
        p_default = 0.05
        n_sims = 5000
        rho_vals = [0.0, 0.1, 0.3, 0.6]
        rng = np.random.default_rng(42)
        from scipy.stats import norm as _norm
        threshold = _norm.ppf(p_default)

        fig = go.Figure()
        colors_rho = ["#3fb950", "#d4af37", "#d29922", "#f85149"]
        for rho, color in zip(rho_vals, colors_rho):
            # 1-factor gaussian copula
            M = rng.standard_normal((n_sims, 1))  # systemic factor
            eps = rng.standard_normal((n_sims, n_loans))
            X = np.sqrt(rho) * M + np.sqrt(1 - rho) * eps
            defaults = (X < threshold).sum(axis=1)
            loss_rates = defaults / n_loans
            fig.add_trace(go.Histogram(
                x=loss_rates * 100, nbinsx=40, histnorm="probability",
                name=f"ρ = {rho:.1f}", marker_color=color, opacity=0.5,
            ))
        fig.update_layout(template="plotly_dark", barmode="overlay", height=420,
                          title="Distribución del pool loss rate bajo distintas correlaciones",
                          xaxis_title="Pool loss rate (%)", yaxis_title="Probabilidad",
                          margin=dict(l=10, r=10, t=40, b=10),
                          legend=dict(orientation="h", yanchor="bottom", y=1.02))
        st.plotly_chart(fig, use_container_width=True)

        info_box("Con <b>ρ=0</b> (independencia, lo que asumían los modelos pre-2008) "
                 "la cola es muy delgada — pool losses &gt; 15% son casi imposibles. "
                 "Con <b>ρ=0.6</b> (lo que pasó en realidad) la cola se engorda y losses "
                 "del 30-50% son escenarios plausibles.", kind="hull")
