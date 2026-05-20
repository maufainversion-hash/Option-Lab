"""Options Lab — landing dashboard (trading-pro hybrid)."""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from ui.styling import inject_premium_css
from ui.components.header_strip import render_header_strip
from data.tickers import UNIVERSE

st.set_page_config(
    page_title="Options Lab",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_premium_css()
render_header_strip()

# ============================================================
# Hero — título + tagline inline
# ============================================================
st.markdown(
    '<div style="display:flex;justify-content:space-between;align-items:baseline;'
    'margin-bottom:6px;">'
    '<h1 style="margin:0;font-weight:600;font-size:32px;">Options Lab</h1>'
    '<span style="color:var(--text-muted);font-size:13px;font-family:JetBrains Mono;">'
    'hull-driven · live chains · personal use</span>'
    '</div>',
    unsafe_allow_html=True,
)

# Stats strip horizontal (chips compactos)
st.markdown(
    '<div class="universe-strip" style="margin-bottom:24px;">'
    f'<span class="stat-chip"><span class="k">tickers</span><span class="v">{len(UNIVERSE)}</span></span>'
    '<span class="stat-chip"><span class="k">models</span><span class="v">4</span></span>'
    '<span class="stat-chip"><span class="k">greeks</span><span class="v">5</span></span>'
    '<span class="stat-chip"><span class="k">strategies</span><span class="v">11</span></span>'
    '<span class="stat-chip"><span class="k">tests</span><span class="v">96</span></span>'
    '</div>',
    unsafe_allow_html=True,
)

# ============================================================
# Navegación — clickeable de verdad via st.page_link
# ============================================================
st.markdown('<div class="section-label">Navegación</div>', unsafe_allow_html=True)

nav1, nav2, nav3 = st.columns(3, gap="small")
with nav1:
    st.page_link(
        "pages/1_📚_Education.py",
        label="📚 Education",
        help="Hull Cap 1, 9, 10, 11, 18 — parcial prep con widgets interactivos",
    )
    st.markdown(
        '<div style="color:var(--text-muted);font-size:12px;padding:8px 4px 0;line-height:1.5;">'
        'Conceptos, parity, estrategias multi-leg, griegas, convergencia binomial → BS.'
        '</div>', unsafe_allow_html=True,
    )

with nav2:
    st.page_link(
        "pages/2_📈_Market_Lab.py",
        label="📈 Market Lab",
        help="Chains reales de yfinance · greeks calculadas · strategy builder real",
    )
    st.markdown(
        '<div style="color:var(--text-muted);font-size:12px;padding:8px 4px 0;line-height:1.5;">'
        'Chain real, strategy builder sobre quotes vivos, smile/skew observado.'
        '</div>', unsafe_allow_html=True,
    )

with nav3:
    st.page_link(
        "pages/3_🎲_Monte_Carlo.py",
        label="🎲 Monte Carlo",
        help="Hull Cap 13 — Wiener processes, GBM, simulación con convergencia a BS",
    )
    st.markdown(
        '<div style="color:var(--text-muted);font-size:12px;padding:8px 4px 0;line-height:1.5;">'
        'Wiener processes, paths GBM, pricing por simulación con bandas CI95.'
        '</div>', unsafe_allow_html=True,
    )

st.markdown('<div style="height:24px;"></div>', unsafe_allow_html=True)

# ============================================================
# Universo — strip condensado con chips
# ============================================================
st.markdown('<div class="section-label">Universo · 25 tickers US líquidos</div>',
            unsafe_allow_html=True)

by_cat: dict[str, list] = {}
for t in UNIVERSE:
    by_cat.setdefault(t.category, []).append(t)

# Orden custom para que pegue visualmente
cat_order = ["index", "tech", "financials", "consumer", "energy", "commodity"]
rows = []
for cat in cat_order:
    if cat not in by_cat:
        continue
    chips = "".join(f'<span class="chip">{t.symbol}</span>' for t in by_cat[cat])
    rows.append(
        f'<div style="display:flex;align-items:baseline;margin-bottom:4px;">'
        f'<span class="cat-label" style="min-width:90px;display:inline-block;">{cat}</span>'
        f'<span>{chips}</span>'
        f'</div>'
    )

st.markdown(
    '<div class="universe-strip">' + "".join(rows) + '</div>',
    unsafe_allow_html=True,
)

# ============================================================
# Pricing engine footer (info técnica resumida)
# ============================================================
ec1, ec2, ec3 = st.columns(3)
with ec1:
    st.markdown(
        '<div class="premium-card">'
        '<div class="section-label">Pricing engine</div>'
        '<div style="font-family:JetBrains Mono;font-size:12px;color:var(--text);'
        'line-height:1.8;margin-top:6px;">'
        '• Black-Scholes-Merton<br>'
        '• Binomial CRR + Leisen-Reimer<br>'
        '• Monte Carlo (antithetic)<br>'
        '• Implied vol vía Brent'
        '</div></div>',
        unsafe_allow_html=True,
    )
with ec2:
    st.markdown(
        '<div class="premium-card">'
        '<div class="section-label">Validación</div>'
        '<div style="font-family:JetBrains Mono;font-size:12px;color:var(--text);'
        'line-height:1.8;margin-top:6px;">'
        '• Hull Ej 14.6 anchored<br>'
        '• 96 tests verdes<br>'
        '• Greeks: cerrado vs numérico<br>'
        '• MC converge ±0.05 a BS'
        '</div></div>',
        unsafe_allow_html=True,
    )
with ec3:
    st.markdown(
        '<div class="premium-card">'
        '<div class="section-label">Data</div>'
        '<div style="font-family:JetBrains Mono;font-size:12px;color:var(--text);'
        'line-height:1.8;margin-top:6px;">'
        '• yfinance (delay ~15 min)<br>'
        '• Cache: prices 60s · chains 5m<br>'
        '• ^TNX → tasa risk-free<br>'
        '• Sanity gates: bid&gt;0, spread&lt;50%'
        '</div></div>',
        unsafe_allow_html=True,
    )

st.markdown(
    '<div style="margin-top:24px;color:var(--text-dim);font-size:11px;'
    'font-family:JetBrains Mono;">'
    'Hull, J.C. <i>Options, Futures and Other Derivatives</i> · '
    'github.com/maufaferreyra-alt/Option-Lab'
    '</div>',
    unsafe_allow_html=True,
)
