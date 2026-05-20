"""
Market Lab — Options on real US tickers (yfinance).

3 tabs:
- Option Chain  : tabla estilo broker (calls | strike | puts) acotada a ventana ATM
- Strategy Builder : armás estrategia con strikes del chain real; greeks via BS sobre IV
- Smile / Skew  : IV vs strike (calls + puts) del expiry seleccionado
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from datetime import datetime, timezone

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data.market_provider import (
    get_quote, get_options_expirations, get_option_chain,
    time_to_expiry_years, risk_free_rate,
)
from data.tickers import UNIVERSE
from strategies.legs import Strategy, Leg
from strategies.payoff import breakeven_points, max_profit_loss
from strategies.aggregator import net_greeks
from ui.components.header_strip import render_header_strip
from ui.components.option_chain_panel import render_chain_panel
from ui.charts.payoff_diagram import payoff_chart
from ui.styling import inject_premium_css

st.set_page_config(page_title="Market Lab — Options Lab", page_icon="📈", layout="wide",
                   initial_sidebar_state="collapsed")
inject_premium_css()
render_header_strip()

st.markdown(
    '<h1 style="margin:0;font-weight:600;">Market Lab</h1>'
    '<div style="color:var(--text-muted);font-size:13px;margin-bottom:20px;">'
    'Chains reales de yfinance · greeks recalculadas con tu engine · strategy builder sobre quotes reales.'
    '</div>',
    unsafe_allow_html=True,
)

# ============================================================
# Ticker + spot
# ============================================================
sc1, sc2, sc3 = st.columns([2, 1, 1])
universe_symbols = [t.symbol for t in UNIVERSE]
selected = sc1.selectbox("Underlying", universe_symbols, index=0, key="mkt_ticker")
custom = sc2.text_input("o ticker libre", value="", placeholder="ej. PLTR")
symbol = custom.strip().upper() if custom.strip() else selected

q = get_quote(symbol)
if q is None:
    st.markdown(
        f'<div style="background:var(--surface);border:1px solid var(--border);'
        f'border-radius:8px;padding:18px 22px;margin:12px 0 18px;">'
        f'<div style="color:var(--negative);font-size:14px;font-weight:600;margin-bottom:6px;">'
        f'⚠ No se pudo cargar quote de <span class="mono">{symbol}</span></div>'
        f'<div style="color:var(--text-muted);font-size:12px;line-height:1.6;">'
        f'Causa más probable: Yahoo está throttling las IPs de Streamlit Cloud. '
        f'El resto de la app sigue funcionando — Education y Monte Carlo no dependen '
        f'de yfinance. Podés también probar otro ticker (algunos tienen mejor disponibilidad).'
        f'</div></div>',
        unsafe_allow_html=True,
    )
    rc1, rc2 = st.columns([1, 4])
    if rc1.button("↻ Reintentar", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    rc2.page_link("app.py", label="← Volver al landing")
    st.stop()

# Cards de spot
m1, m2, m3, m4 = st.columns(4)
m1.metric("Spot", f"${q.price:,.2f}", f"{q.change:+.2f} ({q.change_pct:+.2f}%)")
m2.metric("Cierre anterior", f"${q.prev_close:,.2f}")
m3.metric("Volumen", f"{q.volume:,}")
r = risk_free_rate()
m4.metric("Risk-free (^TNX)", f"{r*100:.2f}%")

# Expiry
expirations = get_options_expirations(symbol)
if not expirations:
    st.warning(f"{symbol} no tiene options chains disponibles en yfinance.")
    st.stop()

expiry = sc3.selectbox("Expiry", expirations, index=0)
T = time_to_expiry_years(expiry)
st.caption(
    f"T = {T:.4f} años ({T*365:.0f} días) · r = {r*100:.2f}% · "
    f"data delay ≈ 15 min · last update {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}"
)

chain = get_option_chain(symbol, expiry)
if chain is None:
    st.warning("Chain vacío para este expiry.")
    st.stop()

# ============================================================
# Tabs
# ============================================================
tab_chain, tab_strat, tab_smile = st.tabs([
    "Option Chain", "Strategy Builder (real)", "Smile / Skew"
])

# ---------------- Option Chain ----------------
with tab_chain:
    render_chain_panel(chain["calls"], chain["puts"], q.price)

# ---------------- Strategy Builder ----------------
def _row_for(df: pd.DataFrame, K: float) -> pd.Series | None:
    sub = df[df["strike"] == K]
    return sub.iloc[0] if not sub.empty else None


def _atm_index(strikes: list[float], spot: float) -> int:
    return min(range(len(strikes)), key=lambda i: abs(strikes[i] - spot))


with tab_strat:
    st.markdown(
        "Elegí strikes del chain real. P&L y greeks se calculan con BS sobre "
        "el IV de cada quote."
    )

    all_strikes = sorted(set(chain["calls"]["strike"].tolist())
                         | set(chain["puts"]["strike"].tolist()))
    atm = _atm_index(all_strikes, q.price)

    sb1, sb2, sb3, sb4 = st.columns(4)
    strat_type = sb1.selectbox("Estrategia", [
        "Long Call", "Long Put",
        "Bull Call Spread", "Bear Put Spread",
        "Long Straddle", "Long Strangle",
        "Iron Condor",
    ])

    legs: list[Leg] = []
    leg_ivs: list[float] = []

    if strat_type == "Long Call":
        K = sb2.selectbox("Strike", all_strikes, index=atm, format_func=lambda x: f"{x:.2f}")
        row = _row_for(chain["calls"], K)
        if row is None or row["mid"] <= 0:
            st.warning("No hay call líquida para este strike."); st.stop()
        legs = [Leg("call", 1.0, K, T, float(row["mid"]))]
        leg_ivs = [float(row["impliedVolatility"])]
        sb3.metric("Premium mid", f"${row['mid']:.2f}")
        sb4.metric("IV", f"{row['impliedVolatility']*100:.1f}%")

    elif strat_type == "Long Put":
        K = sb2.selectbox("Strike", all_strikes, index=atm, format_func=lambda x: f"{x:.2f}")
        row = _row_for(chain["puts"], K)
        if row is None or row["mid"] <= 0:
            st.warning("No hay put líquida para este strike."); st.stop()
        legs = [Leg("put", 1.0, K, T, float(row["mid"]))]
        leg_ivs = [float(row["impliedVolatility"])]
        sb3.metric("Premium mid", f"${row['mid']:.2f}")
        sb4.metric("IV", f"{row['impliedVolatility']*100:.1f}%")

    elif strat_type == "Bull Call Spread":
        K_low = sb2.selectbox("K_low (long)", all_strikes,
                              index=max(0, atm - 2), format_func=lambda x: f"{x:.2f}")
        K_high = sb3.selectbox("K_high (short)", all_strikes,
                               index=min(len(all_strikes) - 1, atm + 2),
                               format_func=lambda x: f"{x:.2f}")
        if K_low >= K_high:
            st.warning("K_low debe ser < K_high"); st.stop()
        rl, rh = _row_for(chain["calls"], K_low), _row_for(chain["calls"], K_high)
        if rl is None or rh is None:
            st.warning("Strike faltante en el chain."); st.stop()
        legs = [
            Leg("call", 1.0, K_low, T, float(rl["mid"])),
            Leg("call", -1.0, K_high, T, float(rh["mid"])),
        ]
        leg_ivs = [float(rl["impliedVolatility"]), float(rh["impliedVolatility"])]
        sb4.metric("Costo neto", f"${(rl['mid'] - rh['mid']):+.2f}")

    elif strat_type == "Bear Put Spread":
        K_low = sb2.selectbox("K_low (short)", all_strikes,
                              index=max(0, atm - 2), format_func=lambda x: f"{x:.2f}")
        K_high = sb3.selectbox("K_high (long)", all_strikes,
                               index=min(len(all_strikes) - 1, atm + 2),
                               format_func=lambda x: f"{x:.2f}")
        if K_low >= K_high:
            st.warning("K_low debe ser < K_high"); st.stop()
        rl, rh = _row_for(chain["puts"], K_low), _row_for(chain["puts"], K_high)
        if rl is None or rh is None:
            st.warning("Strike faltante en el chain."); st.stop()
        legs = [
            Leg("put", 1.0, K_high, T, float(rh["mid"])),
            Leg("put", -1.0, K_low, T, float(rl["mid"])),
        ]
        leg_ivs = [float(rh["impliedVolatility"]), float(rl["impliedVolatility"])]
        sb4.metric("Costo neto", f"${(rh['mid'] - rl['mid']):+.2f}")

    elif strat_type == "Long Straddle":
        K = sb2.selectbox("Strike (ATM)", all_strikes, index=atm,
                          format_func=lambda x: f"{x:.2f}")
        rc, rp = _row_for(chain["calls"], K), _row_for(chain["puts"], K)
        if rc is None or rp is None:
            st.warning("Falta call o put para este strike."); st.stop()
        legs = [
            Leg("call", 1.0, K, T, float(rc["mid"])),
            Leg("put", 1.0, K, T, float(rp["mid"])),
        ]
        leg_ivs = [float(rc["impliedVolatility"]), float(rp["impliedVolatility"])]
        sb3.metric("Costo total", f"${rc['mid'] + rp['mid']:.2f}")
        sb4.metric("IV promedio", f"{np.mean(leg_ivs)*100:.1f}%")

    elif strat_type == "Long Strangle":
        K_put = sb2.selectbox("Strike Put (OTM)", all_strikes,
                              index=max(0, atm - 3), format_func=lambda x: f"{x:.2f}")
        K_call = sb3.selectbox("Strike Call (OTM)", all_strikes,
                               index=min(len(all_strikes) - 1, atm + 3),
                               format_func=lambda x: f"{x:.2f}")
        if K_put >= K_call:
            st.warning("K_put debe ser < K_call"); st.stop()
        rp, rc = _row_for(chain["puts"], K_put), _row_for(chain["calls"], K_call)
        if rp is None or rc is None:
            st.warning("Strike faltante en chain."); st.stop()
        legs = [
            Leg("put", 1.0, K_put, T, float(rp["mid"])),
            Leg("call", 1.0, K_call, T, float(rc["mid"])),
        ]
        leg_ivs = [float(rp["impliedVolatility"]), float(rc["impliedVolatility"])]
        sb4.metric("Costo total", f"${rp['mid'] + rc['mid']:.2f}")

    elif strat_type == "Iron Condor":
        st.markdown(
            '<div style="color:var(--text-muted);font-size:12px;">'
            'Estructura: short put + long put OTM-er ⊕ short call + long call OTM-er.'
            '</div>', unsafe_allow_html=True,
        )
        ic1, ic2, ic3, ic4 = st.columns(4)
        K_pl = ic1.selectbox("Put long", all_strikes, index=max(0, atm - 5),
                             format_func=lambda x: f"{x:.2f}", key="ic_pl")
        K_ps = ic2.selectbox("Put short", all_strikes, index=max(0, atm - 2),
                             format_func=lambda x: f"{x:.2f}", key="ic_ps")
        K_cs = ic3.selectbox("Call short", all_strikes,
                             index=min(len(all_strikes) - 1, atm + 2),
                             format_func=lambda x: f"{x:.2f}", key="ic_cs")
        K_cl = ic4.selectbox("Call long", all_strikes,
                             index=min(len(all_strikes) - 1, atm + 5),
                             format_func=lambda x: f"{x:.2f}", key="ic_cl")
        if not (K_pl < K_ps < K_cs < K_cl):
            st.warning("Strikes desordenados. Necesito K_pl < K_ps < K_cs < K_cl"); st.stop()
        rpl = _row_for(chain["puts"], K_pl); rps = _row_for(chain["puts"], K_ps)
        rcs = _row_for(chain["calls"], K_cs); rcl = _row_for(chain["calls"], K_cl)
        if any(x is None for x in (rpl, rps, rcs, rcl)):
            st.warning("Alguno de los strikes no existe en el chain."); st.stop()
        legs = [
            Leg("put", 1.0, K_pl, T, float(rpl["mid"])),
            Leg("put", -1.0, K_ps, T, float(rps["mid"])),
            Leg("call", -1.0, K_cs, T, float(rcs["mid"])),
            Leg("call", 1.0, K_cl, T, float(rcl["mid"])),
        ]
        leg_ivs = [float(rpl["impliedVolatility"]), float(rps["impliedVolatility"]),
                   float(rcs["impliedVolatility"]), float(rcl["impliedVolatility"])]

    if not legs:
        st.info("Configurá la estrategia arriba.")
        st.stop()

    # IV promedio para BS (en charts y greeks). Fallback 25% si no hay IVs válidos.
    valid_ivs = [iv for iv in leg_ivs if iv > 0]
    iv_avg = float(np.mean(valid_ivs)) if valid_ivs else 0.25

    strat = Strategy(name=strat_type, legs=legs)

    # Chart
    S_range = np.linspace(q.price * 0.7, q.price * 1.3, 200)
    fig = payoff_chart(strat, S_current=q.price, S_range=S_range,
                       sigma=iv_avg, r=r, q=0.0, show_now=True)
    st.plotly_chart(fig, use_container_width=True)

    # Métricas
    max_p, max_l = max_profit_loss(strat, S_range)
    bes = breakeven_points(strat, S_range)
    mm1, mm2, mm3, mm4 = st.columns(4)
    mm1.metric("Premium neto", f"${strat.net_premium():+.2f}",
               help="Positivo = debit. Negativo = credit.")
    mm2.metric("Máx profit (en rango)", f"${max_p:+.2f}")
    mm3.metric("Máx loss", f"${max_l:+.2f}")
    mm4.metric("Breakevens", ", ".join(f"${be:.2f}" for be in bes) if bes else "—")

    # Net greeks
    st.markdown("##### Greeks netas del combo (en spot actual)")
    ng = net_greeks(strat, q.price, 0.0, r, iv_avg, 0.0)
    gg1, gg2, gg3, gg4, gg5 = st.columns(5)
    gg1.metric("Δ Delta", f"{ng['delta']:+.4f}")
    gg2.metric("Γ Gamma", f"{ng['gamma']:+.4f}")
    gg3.metric("ν Vega", f"{ng['vega']:+.2f}")
    gg4.metric("Θ Theta/año", f"{ng['theta']:+.2f}")
    gg5.metric("ρ Rho", f"{ng['rho']:+.2f}")

    st.caption(
        f"IV usada para BS/greeks: **{iv_avg*100:.1f}%** (promedio de las patas). "
        "Esto es la IV implícita observada en el chain; cuando vendés vega quedás corto "
        "esta IV."
    )

# ---------------- Smile / Skew ----------------
with tab_smile:
    cc = chain["calls"][(chain["calls"]["valid"]) & (chain["calls"]["impliedVolatility"] > 0)]
    pp = chain["puts"][(chain["puts"]["valid"]) & (chain["puts"]["impliedVolatility"] > 0)]

    if cc.empty and pp.empty:
        st.warning("Sin quotes válidos para construir el smile (todos con bid=0 o spreads anchos).")
    else:
        fig = go.Figure()
        if not cc.empty:
            fig.add_trace(go.Scatter(
                x=cc["strike"], y=cc["impliedVolatility"] * 100,
                mode="markers+lines", name="Calls",
                line=dict(color="#3fb950", width=2), marker=dict(size=6),
            ))
        if not pp.empty:
            fig.add_trace(go.Scatter(
                x=pp["strike"], y=pp["impliedVolatility"] * 100,
                mode="markers+lines", name="Puts",
                line=dict(color="#f85149", width=2), marker=dict(size=6),
            ))
        fig.add_vline(x=q.price, line=dict(color="#d4af37", dash="dot"),
                      annotation_text=f"Spot ${q.price:.2f}",
                      annotation_position="top")
        fig.update_layout(
            title=f"{symbol} · IV vs Strike · expiry {expiry}",
            xaxis_title="Strike", yaxis_title="IV (%)",
            template="plotly_dark", height=480,
            hovermode="x unified", margin=dict(l=10, r=10, t=50, b=10),
        )
        st.plotly_chart(fig, use_container_width=True)

        st.caption(
            "Lo que ves es el **smile/skew real**. En equity US, los puts suelen tener IV "
            "más alta que los calls equidistantes (skew negativo): el mercado cobra más por "
            "seguro a la baja. Hull Cap 19 explica por qué."
        )
