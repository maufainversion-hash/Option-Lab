"""
Visualizaciones de greeks.

Tres modos:
1. greek_vs_spot — 2D, una griega como función del spot (para T fijo).
2. greek_surface — 3D, una griega como función de (spot, tiempo al vencimiento).
3. all_greeks_panel — 2x3 panel con las 5 griegas en función del spot.
"""
from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from greeks.analytical import delta, gamma, vega, theta, rho
from pricing.black_scholes import OptionType

GREEK_FUNCTIONS = {
    "delta": delta,
    "gamma": gamma,
    "vega": vega,
    "theta": theta,
    "rho": rho,
}

GREEK_LABELS = {
    "delta": "Delta (∂V/∂S)",
    "gamma": "Gamma (∂²V/∂S²)",
    "vega": "Vega (∂V/∂σ)",
    "theta": "Theta (∂V/∂t por año)",
    "rho": "Rho (∂V/∂r)",
}


def _call_greek(name: str, S, K, T, r, sigma, q, option_type):
    """Call helper que maneja gamma/vega que no toman option_type."""
    func = GREEK_FUNCTIONS[name]
    if name in ("gamma", "vega"):
        return func(S, K, T, r, sigma, q)
    return func(S, K, T, r, sigma, q, option_type)


def greek_vs_spot(
    greek_name: str, K: float, T: float, r: float, sigma: float,
    q: float = 0.0, option_type: OptionType = "call",
    S_range: np.ndarray | None = None,
) -> go.Figure:
    """Plot 2D: una griega vs spot, manteniendo T fijo."""
    if S_range is None:
        S_range = np.linspace(K * 0.5, K * 1.5, 200)

    values = [_call_greek(greek_name, float(s), K, T, r, sigma, q, option_type) for s in S_range]

    color = "#26a69a" if option_type == "call" else "#ef5350"
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=S_range, y=values,
        line=dict(color=color, width=2.5),
        name=GREEK_LABELS[greek_name],
        hovertemplate="S=%{x:.2f}<br>" + greek_name + "=%{y:.4f}<extra></extra>",
    ))
    fig.add_vline(
        x=K, line=dict(color="white", width=1, dash="dot"),
        annotation_text=f"K=${K:.2f}", annotation_position="top",
    )
    fig.add_hline(y=0, line=dict(color="#888", width=1, dash="dot"))
    fig.update_layout(
        title=f"{GREEK_LABELS[greek_name]} — {option_type.title()}",
        xaxis_title="Spot S",
        yaxis_title=greek_name.title(),
        template="plotly_dark",
        height=400,
        margin=dict(l=10, r=10, t=50, b=10),
    )
    return fig


def greek_surface(
    greek_name: str, K: float, r: float, sigma: float,
    q: float = 0.0, option_type: OptionType = "call",
    S_min_pct: float = 0.5, S_max_pct: float = 1.5,
    T_min: float = 0.01, T_max: float = 1.0,
    n_S: int = 40, n_T: int = 40,
) -> go.Figure:
    """
    Superficie 3D: una griega como función de (S, T).

    Excelente para ver cómo gamma explota en ATM cerca del vencimiento,
    o cómo theta acelera, o el behavior de vega en distintos T.
    """
    S_grid = np.linspace(K * S_min_pct, K * S_max_pct, n_S)
    T_grid = np.linspace(T_min, T_max, n_T)
    S_mesh, T_mesh = np.meshgrid(S_grid, T_grid)

    Z = np.zeros_like(S_mesh)
    for i in range(n_T):
        for j in range(n_S):
            Z[i, j] = _call_greek(
                greek_name, float(S_mesh[i, j]), K, float(T_mesh[i, j]),
                r, sigma, q, option_type,
            )

    colorscale = "RdYlGn" if option_type == "call" else "RdYlGn_r"
    fig = go.Figure(data=[go.Surface(
        x=S_grid, y=T_grid, z=Z, colorscale=colorscale,
        hovertemplate="S=%{x:.2f}<br>T=%{y:.3f}<br>" + greek_name + "=%{z:.4f}<extra></extra>",
    )])
    fig.update_layout(
        title=f"{GREEK_LABELS[greek_name]} — superficie {option_type}",
        scene=dict(
            xaxis_title="Spot S",
            yaxis_title="Tiempo al vencimiento (años)",
            zaxis_title=greek_name.title(),
            xaxis=dict(backgroundcolor="rgb(20,20,30)"),
            yaxis=dict(backgroundcolor="rgb(20,20,30)"),
            zaxis=dict(backgroundcolor="rgb(20,20,30)"),
        ),
        template="plotly_dark",
        height=560,
        margin=dict(l=0, r=0, t=50, b=0),
    )
    return fig


def all_greeks_panel(
    K: float, T: float, r: float, sigma: float,
    q: float = 0.0, option_type: OptionType = "call",
    S_range: np.ndarray | None = None,
) -> go.Figure:
    """Panel 2x3 con las 5 griegas (la sexta celda queda con price)."""
    if S_range is None:
        S_range = np.linspace(K * 0.5, K * 1.5, 150)

    fig = make_subplots(
        rows=2, cols=3,
        subplot_titles=("Delta", "Gamma", "Vega", "Theta (por año)", "Rho", "Precio"),
        vertical_spacing=0.15, horizontal_spacing=0.08,
    )

    from pricing.black_scholes import bs_price
    color = "#26a69a" if option_type == "call" else "#ef5350"

    cells = [
        ("delta", 1, 1),
        ("gamma", 1, 2),
        ("vega", 1, 3),
        ("theta", 2, 1),
        ("rho", 2, 2),
    ]
    for name, row, col in cells:
        vals = [_call_greek(name, float(s), K, T, r, sigma, q, option_type) for s in S_range]
        fig.add_trace(
            go.Scatter(x=S_range, y=vals, line=dict(color=color, width=2), showlegend=False),
            row=row, col=col,
        )
        fig.add_vline(x=K, line=dict(color="white", width=1, dash="dot"), row=row, col=col)
        fig.add_hline(y=0, line=dict(color="#666", width=1, dash="dot"), row=row, col=col)

    # Sexta celda: precio
    prices = [bs_price(float(s), K, T, r, sigma, q, option_type) for s in S_range]
    fig.add_trace(
        go.Scatter(x=S_range, y=prices, line=dict(color="#ffa726", width=2), showlegend=False),
        row=2, col=3,
    )
    fig.add_vline(x=K, line=dict(color="white", width=1, dash="dot"), row=2, col=3)

    fig.update_layout(
        template="plotly_dark", height=620,
        title=f"Greeks Panel — {option_type.title()}  K={K:.2f}  T={T:.2f}y  σ={sigma:.0%}",
        margin=dict(l=10, r=10, t=80, b=10),
    )
    return fig
