from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from pricing.forwards import minimum_variance_hedge_ratio, equity_portfolio_hedge_contracts
from ui.styling import inject_premium_css
from ui.components.header_strip import render_header_strip

st.set_page_config(page_title="U2 — Coberturas", page_icon="🛡️", layout="wide",
                   initial_sidebar_state="collapsed")
inject_premium_css()
render_header_strip()

st.markdown(
    '<h1 style="margin:0;font-weight:600;">Unidad II · Coberturas con futuros</h1>'
    '<div style="color:var(--text-muted);font-size:13px;margin-bottom:20px;">'
    'Hull Cap 3. Hedge ratio óptimo, basis risk, cobertura de equity portfolios via beta.'
    '</div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["Hedge ratio óptimo", "Basis risk", "Hedge de equity portfolio"])

with tab1:
    st.markdown(r"""
**Hedge ratio de mínima varianza** (Hull 3.4):

$$h^* = \rho \cdot \frac{\sigma_S}{\sigma_F}$$

Donde σ_S es la desviación del cambio de precio spot, σ_F la del futuro, y ρ la correlación
entre ambos. Si la correlación es 1 y las vols iguales, h* = 1 (cobertura perfecta).
""")
    c1, c2, c3 = st.columns(3)
    sigma_s = c1.slider("σ del cambio en spot (Δ por período)", 0.001, 5.0, 0.65, 0.01)
    sigma_f = c2.slider("σ del cambio en futuro", 0.001, 5.0, 0.81, 0.01)
    rho = c3.slider("Correlación ρ", -1.0, 1.0, 0.928, 0.01)

    h_star = minimum_variance_hedge_ratio(sigma_s, sigma_f, rho)
    hedge_effectiveness = rho ** 2

    m1, m2 = st.columns(2)
    m1.metric("Hedge ratio óptimo h*", f"{h_star:.4f}")
    m2.metric("Hedge effectiveness", f"{hedge_effectiveness:.2%}",
              help="ρ² = porcentaje de varianza eliminado por el hedge")

    h_range = np.linspace(0, 2, 200)
    var_hedged = sigma_s**2 + (h_range**2) * sigma_f**2 - 2 * h_range * rho * sigma_s * sigma_f
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=h_range, y=var_hedged, mode="lines",
                             line=dict(color="#d4af37", width=2.5)))
    fig.add_vline(x=h_star, line=dict(color="#3fb950", dash="dash"),
                  annotation_text=f"h* = {h_star:.3f}")
    fig.update_layout(template="plotly_dark", height=380,
                      title="Varianza del portfolio hedgeado vs hedge ratio",
                      xaxis_title="h (hedge ratio)", yaxis_title="Var(ΔS - h·ΔF)",
                      margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("📖 Resumen / Hull pp. 56-62"):
        st.markdown(r"""
La derivación parte de minimizar Var(ΔS − h·ΔF) respecto de h. Derivando e igualando a cero:
$h^* = \text{Cov}(ΔS, ΔF) / \text{Var}(ΔF) = ρ \cdot σ_S / σ_F$.

La **hedge effectiveness** ρ² mide qué proporción de la varianza del cambio de precio
spot fue eliminada por el hedge. Si ρ = 1, eliminás todo. Si ρ = 0, no estás hedgeando nada.
""")

with tab2:
    st.markdown(r"""
**Basis = Spot − Futuro**. Cuando hedgeás un asset con un futuro que no es exactamente
sobre ese asset (ej: hedgear jet fuel con heating oil futures), te queda **basis risk**:
el spread spot-futuro al cerrar el hedge no es predecible.

Hull 3.1: el resultado de un hedge corto en un punto t₂ ≠ vencimiento es:
$$S_2 - F_1 = F_2 + (S_2 - F_2) = F_2 + b_2$$
""")

    b_init = st.slider("Basis inicial (cuando se entra al hedge)", -5.0, 5.0, 0.5, 0.1)
    b_end_low = st.slider("Basis al cerrar (low scenario)", -5.0, 5.0, -1.5, 0.1)
    b_end_high = st.slider("Basis al cerrar (high scenario)", -5.0, 5.0, 2.0, 0.1)

    c1, c2 = st.columns(2)
    c1.metric("Δ basis (low)", f"{b_end_low - b_init:+.2f}",
              help="Pérdida adicional para un short hedge si basis baja más de lo previsto")
    c2.metric("Δ basis (high)", f"{b_end_high - b_init:+.2f}")

    days = np.arange(60)
    rng = np.random.RandomState(11)
    basis_path_low = np.linspace(b_init, b_end_low, 60) + rng.normal(0, 0.15, 60)
    basis_path_high = np.linspace(b_init, b_end_high, 60) + rng.normal(0, 0.15, 60)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=days, y=basis_path_low, mode="lines", name="Escenario low",
                             line=dict(color="#f85149", width=2)))
    fig.add_trace(go.Scatter(x=days, y=basis_path_high, mode="lines", name="Escenario high",
                             line=dict(color="#3fb950", width=2)))
    fig.add_hline(y=b_init, line=dict(color="#d4af37", dash="dot"),
                  annotation_text="Basis inicial")
    fig.update_layout(template="plotly_dark", height=360, title="Path de la basis",
                      xaxis_title="Días", yaxis_title="Basis (S − F)",
                      margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.markdown(r"""
**Hedge de un portfolio de acciones con index futures** (Hull 3.5):

$$N^* = \beta \cdot \frac{V_A}{V_F}$$

Donde V_A es el valor del portfolio, V_F es el valor de un contrato futuro (precio × multiplicador),
y β es la beta del portfolio respecto al índice.
""")
    c1, c2, c3, c4 = st.columns(4)
    V_A = c1.number_input("Valor portfolio (USD)", min_value=10000.0, value=5_000_000.0, step=10000.0)
    beta = c2.number_input("Beta vs índice", min_value=-3.0, value=1.2, step=0.05)
    F = c3.number_input("Precio futuro S&P", min_value=100.0, value=5500.0, step=10.0)
    mult = c4.number_input("Multiplicador (E-mini = 50)", min_value=1.0, value=50.0, step=1.0)

    n_star = equity_portfolio_hedge_contracts(V_A, beta, F, mult)
    st.metric("Contratos a vender (N*)", f"{n_star:.1f}",
              help="Redondear al entero más cercano al ejecutar")

    st.markdown(r"""
**Cambiar la beta del portfolio.** Si tu β actual es β y querés llegar a β*:

$$N^* = (\beta^* - \beta) \cdot \frac{V_A}{V_F}$$

Si β* < β → vendés futuros (reducir exposición). Si β* > β → comprás futuros.
""")

    c5, c6 = st.columns(2)
    beta_target = c5.number_input("β target", min_value=0.0, value=0.5, step=0.05)
    n_change = (beta_target - beta) * V_A / (F * mult)
    c6.metric(f"Contratos para mover β de {beta:.2f} → {beta_target:.2f}",
              f"{n_change:+.1f}", help="Positivo = comprar; negativo = vender")
