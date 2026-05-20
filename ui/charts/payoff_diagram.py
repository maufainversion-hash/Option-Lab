"""
Diagrama de payoff con Plotly.

Visualiza payoff al vencimiento + opcionalmente P&L en tiempos intermedios.
Marca breakeven points, max profit, max loss y línea de spot actual.
"""
from __future__ import annotations

import numpy as np
import plotly.graph_objects as go

from strategies.legs import Strategy
from strategies.payoff import payoff_at_expiry, pnl_at_time, breakeven_points, max_profit_loss

# Paleta dark-friendly
COLOR_PROFIT = "#26a69a"  # verde
COLOR_LOSS = "#ef5350"    # rojo
COLOR_ZERO = "#888888"
COLOR_NOW = "#42a5f5"     # azul para P&L hoy
COLOR_EXPIRY = "#ffa726"  # naranja para P&L al vencimiento


def payoff_chart(
    strategy: Strategy,
    S_current: float,
    S_range: np.ndarray | None = None,
    sigma: float = 0.2,
    r: float = 0.05,
    q: float = 0.0,
    show_now: bool = True,
    title: str | None = None,
) -> go.Figure:
    """
    Diagrama de payoff de una estrategia.

    Eje X: precio del subyacente al vencimiento (o al momento de evaluar).
    Eje Y: P&L (profit and loss) — payoff menos premium pagado.

    Si show_now=True, también plotea el P&L con t=0 (hoy mismo) usando BS para
    mostrar el efecto de theta/vega antes del vencimiento.
    """
    if S_range is None:
        # Default: ±50% del spot actual con 200 puntos
        S_range = np.linspace(S_current * 0.5, S_current * 1.5, 200)

    payoff_exp = payoff_at_expiry(strategy, S_range)

    fig = go.Figure()

    # Sombrear área de ganancia/pérdida al vencimiento
    fig.add_trace(go.Scatter(
        x=S_range, y=payoff_exp,
        fill="tozeroy",
        fillcolor="rgba(38,166,154,0.15)",
        line=dict(color=COLOR_EXPIRY, width=2.5),
        name="P&L al vencimiento",
        hovertemplate="S=%{x:.2f}<br>P&L=%{y:.2f}<extra></extra>",
    ))

    # P&L hoy (vía BS) si pidieron
    if show_now:
        try:
            payoff_now = pnl_at_time(strategy, S_range, t=0.0, r=r, sigma=sigma, q=q)
            fig.add_trace(go.Scatter(
                x=S_range, y=payoff_now,
                line=dict(color=COLOR_NOW, width=2, dash="dash"),
                name="P&L hoy (BS)",
                hovertemplate="S=%{x:.2f}<br>P&L=%{y:.2f}<extra></extra>",
            ))
        except Exception:
            pass  # si BS falla en algún spot, igual mostramos el del vencimiento

    # Línea cero
    fig.add_hline(y=0, line=dict(color=COLOR_ZERO, width=1, dash="dot"))

    # Spot actual
    fig.add_vline(
        x=S_current,
        line=dict(color="white", width=1, dash="dot"),
        annotation_text=f"Spot ${S_current:.2f}",
        annotation_position="top right",
    )

    # Breakevens y max/min
    bes = breakeven_points(strategy, S_range)
    for be in bes:
        fig.add_vline(
            x=be,
            line=dict(color=COLOR_ZERO, width=1, dash="dashdot"),
            annotation_text=f"BE ${be:.2f}",
            annotation_position="bottom",
        )

    max_p, max_l = max_profit_loss(strategy, S_range)

    # Annotation de max profit / max loss (en S_range mostrado)
    annot_text = f"Máx profit: ${max_p:+.2f}<br>Máx loss: ${max_l:+.2f}"
    fig.add_annotation(
        xref="paper", yref="paper", x=0.02, y=0.98,
        text=annot_text, showarrow=False,
        font=dict(size=11, color="white"),
        bgcolor="rgba(0,0,0,0.5)", bordercolor=COLOR_ZERO, borderwidth=1,
        align="left",
    )

    fig.update_layout(
        title=title or strategy.name,
        xaxis_title="Precio del subyacente",
        yaxis_title="P&L ($)",
        template="plotly_dark",
        hovermode="x unified",
        height=460,
        margin=dict(l=10, r=10, t=50, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    return fig
