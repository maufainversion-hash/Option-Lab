"""CSS premium para Options Lab — Inter + JetBrains Mono + gold accent."""
from __future__ import annotations
import streamlit as st

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
    --bg: #0e1117;
    --surface: #161b22;
    --surface-2: #1c2128;
    --border: #30363d;
    --border-strong: #484f58;
    --text: #e6edf3;
    --text-muted: #8b949e;
    --text-dim: #6e7681;
    --accent: #d4af37;
    --accent-soft: rgba(212, 175, 55, 0.10);
    --positive: #3fb950;
    --negative: #f85149;
    --info: #58a6ff;
}

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

h1, h2, h3, h4 { letter-spacing: -0.4px; }

/* Hero / inline stats strip — chip-style numbers */
.stat-chip {
    display: inline-flex;
    align-items: baseline;
    gap: 6px;
    padding: 6px 12px;
    border-right: 1px solid var(--border);
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px;
}
.stat-chip:last-child { border-right: none; }
.stat-chip .v {
    color: var(--accent);
    font-weight: 600;
    font-size: 15px;
}
.stat-chip .k {
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.4px;
    font-size: 10px;
}

/* Streamlit metric tweaks — smaller, refined */
[data-testid="stMetricValue"] {
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 600 !important;
    font-size: 22px !important;
    color: var(--text) !important;
    line-height: 1.2;
}
[data-testid="stMetricLabel"] {
    font-size: 10px !important;
    color: var(--text-muted) !important;
    text-transform: uppercase;
    letter-spacing: 0.6px;
}
[data-testid="stMetricDelta"] {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 12px !important;
}

/* Premium cards */
.premium-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 16px 18px;
    margin-bottom: 8px;
    transition: all 0.15s ease;
}
.premium-card:hover {
    border-color: var(--accent);
    background: var(--surface-2);
}

/* Navigation cards via st.page_link styling */
[data-testid="stPageLink"] {
    display: block !important;
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    padding: 18px 20px !important;
    margin: 0 !important;
    text-decoration: none !important;
    transition: all 0.15s ease !important;
    width: 100% !important;
}
[data-testid="stPageLink"]:hover {
    border-color: var(--accent) !important;
    background: var(--surface-2) !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}
[data-testid="stPageLink"] p,
[data-testid="stPageLink"] span,
[data-testid="stPageLink"] div {
    color: var(--text) !important;
    font-size: 15px !important;
    font-weight: 600 !important;
    margin: 0 !important;
}
[data-testid="stPageLink"]::after {
    content: "→";
    float: right;
    color: var(--accent);
    font-size: 16px;
    transition: transform 0.15s ease;
}
[data-testid="stPageLink"]:hover::after {
    transform: translateX(4px);
}

/* Header strip — ticker cells */
.ticker-strip {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0;
    margin-bottom: 18px;
    overflow-x: auto;
    white-space: nowrap;
    display: flex;
    align-items: center;
}
.ticker-strip-empty {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 10px 14px;
    margin-bottom: 18px;
    color: var(--text-muted);
    font-size: 12px;
    font-family: 'JetBrains Mono', monospace;
}
.ticker-cell {
    display: inline-flex;
    align-items: baseline;
    gap: 6px;
    padding: 10px 16px;
    border-right: 1px solid var(--border);
    font-family: 'JetBrains Mono', monospace;
    flex-shrink: 0;
}
.ticker-cell:last-child { border-right: none; }
.ticker-cell .symbol {
    color: var(--text-muted);
    font-size: 10px;
    letter-spacing: 0.6px;
    text-transform: uppercase;
}
.ticker-cell .price {
    color: var(--text);
    font-size: 14px;
    font-weight: 600;
}
.ticker-cell .delta {
    font-size: 11px;
    font-weight: 500;
}
.ticker-cell .delta.pos { color: var(--positive); }
.ticker-cell .delta.neg { color: var(--negative); }

/* Universe chips */
.universe-strip {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 14px 16px;
    margin: 8px 0 16px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    line-height: 1.9;
}
.universe-strip .cat-label {
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    font-size: 10px;
    margin-right: 8px;
}
.universe-strip .chip {
    display: inline-block;
    padding: 2px 8px;
    margin: 0 3px 2px 0;
    background: var(--surface-2);
    border: 1px solid var(--border);
    border-radius: 4px;
    color: var(--text);
    font-size: 11px;
    font-weight: 500;
    transition: border-color 0.15s ease;
}
.universe-strip .chip:hover {
    border-color: var(--accent);
}

/* Section labels (small uppercase) */
.section-label {
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.7px;
    font-size: 10px;
    font-weight: 600;
    margin-bottom: 6px;
}

/* Tabs styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 0;
    border-bottom: 1px solid var(--border);
}
.stTabs [data-baseweb="tab"] {
    background: transparent;
    border: none;
    padding: 10px 18px;
    font-size: 13px;
    color: var(--text-muted);
}
.stTabs [aria-selected="true"] {
    color: var(--accent) !important;
    border-bottom: 2px solid var(--accent) !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: var(--surface);
    border-right: 1px solid var(--border);
}

/* Caption (small print) */
.stCaption, [data-testid="stCaptionContainer"] {
    color: var(--text-dim) !important;
    font-size: 11px !important;
}

/* Code / mono helpers */
code, .mono {
    font-family: 'JetBrains Mono', monospace !important;
}

/* Hide hamburger en producción */
#MainMenu, footer { visibility: hidden; }
</style>
"""


def inject_premium_css() -> None:
    """Inyecta el CSS custom. Llamar al tope de cada page después de set_page_config."""
    st.markdown(_CSS, unsafe_allow_html=True)


def output_card(label: str, value: str, *, hint: str = "", color: str = "accent",
                width_pct: int = 100) -> str:
    """
    Devuelve HTML de una card de output monospace.
    color: 'accent' (gold), 'positive' (verde), 'negative' (rojo), 'info' (azul), 'muted'.
    Usar con st.markdown(..., unsafe_allow_html=True), o componer varias en una row.
    """
    color_map = {
        "accent": "var(--accent)", "positive": "var(--positive)",
        "negative": "var(--negative)", "info": "var(--info)", "muted": "var(--text-muted)",
    }
    c = color_map.get(color, "var(--accent)")
    hint_html = (f'<div style="color:var(--text-muted);font-size:10px;'
                 f'margin-top:4px;">{hint}</div>') if hint else ""
    return (
        f'<div class="premium-card" style="width:{width_pct}%;">'
        f'<div style="color:var(--text-muted);font-size:11px;'
        f'text-transform:uppercase;letter-spacing:0.5px;">{label}</div>'
        f'<div style="font-family:JetBrains Mono;color:{c};font-size:22px;'
        f'font-weight:600;margin-top:4px;">{value}</div>'
        f'{hint_html}</div>'
    )


def info_box(text: str, *, kind: str = "info") -> None:
    """
    Box informativo más bonito que st.info default.
    kind: 'info' (azul), 'success' (verde), 'warning' (amarillo), 'hull' (gold, Hull ref).
    """
    border_map = {"info": "#58a6ff", "success": "#3fb950",
                  "warning": "#d29922", "hull": "#d4af37"}
    bg_map = {"info": "rgba(88,166,255,0.08)", "success": "rgba(63,185,80,0.08)",
              "warning": "rgba(210,153,34,0.08)", "hull": "rgba(212,175,55,0.10)"}
    border = border_map.get(kind, "#58a6ff")
    bg = bg_map.get(kind, "rgba(88,166,255,0.08)")
    icon = {"info": "ℹ", "success": "✓", "warning": "⚠", "hull": "📘"}.get(kind, "ℹ")
    st.markdown(
        f'<div style="border-left:3px solid {border}; background:{bg}; '
        f'padding:10px 14px; border-radius:4px; margin:8px 0; font-size:13px;">'
        f'<b>{icon}</b>  {text}</div>',
        unsafe_allow_html=True,
    )


def hull_check(expected: float, calculated: float, *, label: str,
               tolerance: float = 0.005, units: str = "") -> None:
    """
    Muestra una row con: Hull esperado | tu cálculo | ✓ o ✗.
    Usa tolerancia relativa si abs(expected) > 1, absoluta sino.
    """
    rel_tol = tolerance if abs(expected) > 1 else 0
    abs_tol = tolerance if abs(expected) <= 1 else 0
    matches = abs(calculated - expected) <= max(abs_tol, abs(expected) * rel_tol)
    check_icon = "✓" if matches else "✗"
    check_color = "#3fb950" if matches else "#f85149"
    st.markdown(
        f'<div style="border:1px solid var(--border); background:rgba(212,175,55,0.06); '
        f'border-radius:6px; padding:10px 14px; margin:8px 0; '
        f'display:flex; justify-content:space-between; align-items:center; font-family:JetBrains Mono;">'
        f'<span style="color:var(--text-muted);font-size:11px;">{label}</span>'
        f'<span>Hull: <b style="color:var(--accent);">{expected}{units}</b> '
        f'&nbsp;|&nbsp; Calc: <b style="color:var(--text);">{calculated:.4f}{units}</b> '
        f'&nbsp;<span style="color:{check_color};font-size:18px;font-weight:700;">{check_icon}</span></span>'
        f'</div>', unsafe_allow_html=True,
    )
