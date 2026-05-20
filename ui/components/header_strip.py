"""Strip horizontal de tickers live al tope de cada page."""
from __future__ import annotations
import streamlit as st

from data.market_provider import get_quotes_batch
from data.tickers import HEADER_STRIP_TICKERS

LABELS = {
    "SPY": "S&P 500",
    "QQQ": "NASDAQ",
    "IWM": "RUSSELL",
    "^VIX": "VIX",
    "^TNX": "US 10Y",
    "GLD": "GOLD",
    "BTC-USD": "BTC",
}


def render_header_strip() -> None:
    """
    Renderea el strip con quotes en vivo.
    Si todos los quotes fallan, muestra un banner discreto en vez de N celdas vacías.
    """
    quotes = get_quotes_batch(tuple(HEADER_STRIP_TICKERS))
    valid = {k: v for k, v in quotes.items() if v is not None}

    if not valid:
        st.markdown(
            '<div class="ticker-strip-empty">'
            '⚠ Market data temporarily unavailable · yfinance throttled. '
            'Funcionalidad de pricing/educación intacta.'
            '</div>',
            unsafe_allow_html=True,
        )
        return

    cells = []
    for sym in HEADER_STRIP_TICKERS:
        q = quotes.get(sym)
        label = LABELS.get(sym, sym)
        if q is None:
            cells.append(
                f'<span class="ticker-cell">'
                f'<span class="symbol">{label}</span>'
                f'<span class="price" style="color:var(--text-muted);font-size:13px;">—</span>'
                f'</span>'
            )
            continue
        arrow = "▲" if q.is_up else "▼"
        cls = "pos" if q.is_up else "neg"
        cells.append(
            f'<span class="ticker-cell">'
            f'<span class="symbol">{label}</span>'
            f'<span class="price">{q.price:,.2f}</span>'
            f'<span class="delta {cls}">{arrow} {q.change_pct:+.2f}%</span>'
            f'</span>'
        )
    st.markdown(
        '<div class="ticker-strip">' + "".join(cells) + '</div>',
        unsafe_allow_html=True,
    )
