"""
Página de Monte Carlo / Wiener processes (Hull Cap 13).

4 tabs:
- Tab 1: Random walk → Wiener process (intuición discreta a continua)
- Tab 2: Movimiento Browniano geométrico (proceso del precio de la acción)
- Tab 3: Visualización de paths GBM (interactivo)
- Tab 4: Monte Carlo pricing + convergencia a Black-Scholes
"""
from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pricing.black_scholes import bs_price
from pricing.monte_carlo import (
    simulate_gbm_paths,
    mc_price_european,
    mc_convergence,
)


st.set_page_config(page_title="Monte Carlo — Options Lab", page_icon="🎲", layout="wide")

st.title("🎲 Monte Carlo y procesos de Wiener")
st.caption(
    "Hull Cap 13. De random walks a movimiento Browniano geométrico, paths simulados y "
    "pricing de opciones por Monte Carlo. Sirve como **modelo conceptual** detrás de BS y "
    "como **herramienta práctica** para opciones path-dependent (asiáticas, barreras, etc)."
)

tab_walk, tab_gbm, tab_paths, tab_mc = st.tabs([
    "1. Random walk → Wiener",
    "2. GBM del precio",
    "3. Paths simulados",
    "4. MC vs Black-Scholes",
])


# ============================================================
# TAB 1 — Random walk a Wiener process
# ============================================================
with tab_walk:
    st.header("Del random walk al proceso de Wiener")
    st.markdown(
        r"""
**Random walk discreto**: en cada paso de tiempo $\Delta t$, una variable $X$ se mueve
$+\sqrt{\Delta t}$ o $-\sqrt{\Delta t}$ con probabilidad 1/2 cada uno. Eso da:

- $E[\Delta X] = 0$
- $\text{Var}(\Delta X) = \Delta t$

Si achicamos $\Delta t \to 0$ y mantenemos el escalado $\sqrt{\Delta t}$, el límite es un
**proceso de Wiener** (o movimiento Browniano estándar) $W_t$ con estas tres propiedades
(Hull 13.1):

1. $W_0 = 0$.
2. Incrementos independientes: $W_t - W_s$ depende solo de $t-s$, no de la historia previa.
3. $W_t - W_s \sim \mathcal{N}(0, t-s)$.

En notación informal: $dW = \varepsilon \sqrt{dt}$, con $\varepsilon \sim \mathcal{N}(0,1)$.

**Markov**: el proceso no tiene memoria. Lo único que importa para el futuro es el valor
actual, no el camino. Esto encaja con la hipótesis débil de eficiencia de mercados (Hull §13.1).
"""
    )

    st.subheader("Random walk discreto — convergencia a Wiener")
    c1, c2, c3 = st.columns(3)
    n_steps_rw = c1.slider("Pasos por trayectoria", 50, 2000, 500, 50, key="rw_steps")
    n_paths_rw = c2.slider("Trayectorias a dibujar", 5, 100, 30, 5, key="rw_paths")
    seed_rw = c3.number_input("Seed", value=42, step=1, key="rw_seed")

    rng = np.random.default_rng(int(seed_rw))
    dt = 1.0 / n_steps_rw
    # ±sqrt(dt) por paso
    steps_arr = rng.choice([-1, 1], size=(n_paths_rw, n_steps_rw)) * np.sqrt(dt)
    walks = np.cumsum(steps_arr, axis=1)
    walks = np.hstack([np.zeros((n_paths_rw, 1)), walks])   # W_0 = 0
    t_grid = np.linspace(0, 1, n_steps_rw + 1)

    fig = go.Figure()
    for i in range(n_paths_rw):
        fig.add_trace(go.Scatter(
            x=t_grid, y=walks[i], mode="lines",
            line=dict(width=1), opacity=0.4, showlegend=False,
        ))
    # Banda teórica ±1.96·√t
    fig.add_trace(go.Scatter(
        x=t_grid, y=1.96 * np.sqrt(t_grid), mode="lines",
        line=dict(color="#ffa726", width=2, dash="dash"),
        name="±1.96·√t (CI 95% teórico)",
    ))
    fig.add_trace(go.Scatter(
        x=t_grid, y=-1.96 * np.sqrt(t_grid), mode="lines",
        line=dict(color="#ffa726", width=2, dash="dash"),
        showlegend=False,
    ))
    fig.update_layout(
        title=f"{n_paths_rw} random walks (Δt = 1/{n_steps_rw})",
        xaxis_title="t",
        yaxis_title="W_t",
        template="plotly_dark",
        height=420,
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown(
        r"""
**¿Por qué $\sqrt{\Delta t}$ y no $\Delta t$?** Si fuera $\Delta t$, la varianza acumulada
después de $n$ pasos sería $n \cdot (\Delta t)^2 = T \cdot \Delta t \to 0$, y el proceso colapsa.
Con $\sqrt{\Delta t}$, la varianza es $n \cdot \Delta t = T$, finita en el límite.

> Ese escalado raíz cuadrada es **el truco entero** del cálculo estocástico: hace que
> $(dW)^2 = dt$ en lugar de $0$, lo que sostiene Itô's lemma.
"""
    )

    with st.expander("📖 Wiener generalizado y proceso de Itô (Hull 13.2–13.3)"):
        st.markdown(
            r"""
**Wiener generalizado**: agrega drift $a$ y vol $b$ constantes:

$$
dX = a\, dt + b\, dW
$$

$X_t \sim \mathcal{N}(X_0 + a t,\ b^2 t)$. Drift y diffusion son **constantes**.

**Proceso de Itô**: drift y vol pueden depender de $X$ y $t$:

$$
dX = a(X, t)\, dt + b(X, t)\, dW
$$

GBM es un caso especial: $a(S, t) = \mu S$ y $b(S, t) = \sigma S$ — ambos proporcionales
a $S$, lo que asegura que $S$ nunca cruce 0.
"""
        )


# ============================================================
# TAB 2 — GBM del precio
# ============================================================
with tab_gbm:
    st.header("Movimiento Browniano geométrico para el precio")
    st.markdown(
        r"""
Hull 13.5 propone el modelo del precio de una acción:

$$
\boxed{\,dS = \mu S\, dt + \sigma S\, dW\,}
$$

Es decir, **retornos** instantáneos $dS/S$ siguen un Wiener generalizado con drift $\mu$ y
vol $\sigma$. Aplicando Itô (Hull 13.6) a $\ln S$:

$$
d(\ln S) = \left(\mu - \tfrac{1}{2}\sigma^2\right) dt + \sigma\, dW
$$

Integrando de $0$ a $T$:

$$
\ln S_T \sim \mathcal{N}\!\left(\ln S_0 + \left(\mu - \tfrac{1}{2}\sigma^2\right)T,\ \sigma^2 T\right)
$$

O sea, $S_T$ es **log-normal**. Solución cerrada:

$$
S_T = S_0 \cdot \exp\!\left( \left(\mu - \tfrac{1}{2}\sigma^2\right)T + \sigma\sqrt{T}\,Z \right),\quad Z \sim \mathcal{N}(0,1)
$$

**Momentos analíticos**:

- $E[S_T] = S_0 \cdot e^{\mu T}$
- $\text{Var}(S_T) = S_0^2 \cdot e^{2\mu T} \cdot (e^{\sigma^2 T} - 1)$
"""
    )

    st.subheader("Distribución de $S_T$ — log-normal vs simulación")
    c1, c2, c3, c4 = st.columns(4)
    S0_g = c1.number_input("S₀", min_value=1.0, value=100.0, step=1.0, key="gbm_S0")
    mu_g = c2.slider("μ (drift anual)", -0.20, 0.50, 0.10, 0.01, key="gbm_mu")
    sigma_g = c3.slider("σ (vol anual)", 0.05, 1.0, 0.30, 0.01, key="gbm_sigma")
    T_g = c4.slider("T (años)", 0.1, 5.0, 1.0, 0.1, key="gbm_T")

    paths_hist = simulate_gbm_paths(S0_g, mu_g, sigma_g, T_g,
                                    steps=1, n_paths=20_000, seed=123)
    ST = paths_hist[:, -1]
    mean_analytical = S0_g * np.exp(mu_g * T_g)
    var_analytical = (S0_g ** 2) * np.exp(2 * mu_g * T_g) * (np.exp(sigma_g ** 2 * T_g) - 1)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("E[S_T] analítico", f"${mean_analytical:.2f}")
    m2.metric("E[S_T] simulado", f"${ST.mean():.2f}")
    m3.metric("σ[S_T] analítico", f"${np.sqrt(var_analytical):.2f}")
    m4.metric("σ[S_T] simulado", f"${ST.std(ddof=1):.2f}")

    # Histograma + densidad log-normal teórica
    x_grid = np.linspace(ST.min(), ST.max(), 400)
    # Log-normal: si Y = ln(X) ~ N(m, s²), entonces f_X(x) = (1/(x·s·√2π)) · exp(-(ln x - m)² / (2 s²))
    m_log = np.log(S0_g) + (mu_g - 0.5 * sigma_g ** 2) * T_g
    s_log = sigma_g * np.sqrt(T_g)
    pdf = (1.0 / (x_grid * s_log * np.sqrt(2 * np.pi))) * np.exp(-((np.log(x_grid) - m_log) ** 2) / (2 * s_log ** 2))

    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=ST, nbinsx=80, histnorm="probability density",
        name="Simulación", marker=dict(color="#26a69a"), opacity=0.6,
    ))
    fig.add_trace(go.Scatter(
        x=x_grid, y=pdf, mode="lines",
        name="Log-normal teórica",
        line=dict(color="#ffa726", width=3),
    ))
    fig.add_vline(x=S0_g, line=dict(color="#90caf9", width=2, dash="dot"),
                  annotation_text=f"S₀={S0_g:.0f}", annotation_position="top")
    fig.add_vline(x=mean_analytical, line=dict(color="#ef5350", width=2, dash="dash"),
                  annotation_text=f"E[S_T]={mean_analytical:.1f}", annotation_position="top")
    fig.update_layout(
        title=f"Distribución de S_T después de T={T_g:.2f} años (20k paths)",
        xaxis_title="S_T",
        yaxis_title="densidad",
        template="plotly_dark",
        height=420,
        bargap=0.02,
    )
    st.plotly_chart(fig, use_container_width=True)

    st.info(
        "💡 Nota: la densidad log-normal es **asimétrica** — cola derecha más pesada. "
        "Esto refleja que un activo puede multiplicarse muchas veces pero solo puede caer "
        "hasta 0. Por eso $E[S_T] > $ mediana de $S_T$."
    )

    with st.expander("📖 ¿Por qué μ no aparece en el precio de la opción?"):
        st.markdown(
            r"""
La famosa "trampa" de BS: el drift real $\mu$ del activo **NO aparece** en la fórmula del
precio de la opción. Sí aparece en la distribución de $S_T$ bajo la **medida física** $\mathbb{P}$,
pero cuando hacemos el hedging perfecto del Cap 14, todo termina valuándose bajo la
**medida risk-neutral** $\mathbb{Q}$ donde el drift es $r - q$.

Por eso para **pricing** usamos $\mu = r - q$ en la simulación, y para **forecasting** real
(qué tan probable es ganar dinero comprando esta opción) podríamos usar un μ distinto. Son
preguntas diferentes.
"""
        )


# ============================================================
# TAB 3 — Paths visualizados
# ============================================================
with tab_paths:
    st.header("Paths de GBM — visualización interactiva")
    st.markdown(
        "Cada línea es una posible trayectoria del precio bajo GBM. Sirve para construir "
        "intuición: **cuánto puede variar el activo** y **cuánto vale cada cuantil**."
    )

    c1, c2, c3, c4, c5 = st.columns(5)
    S0_p = c1.number_input("S₀", value=100.0, step=1.0, key="paths_S0")
    mu_p = c2.slider("μ", -0.20, 0.50, 0.08, 0.01, key="paths_mu")
    sigma_p = c3.slider("σ", 0.05, 1.0, 0.25, 0.01, key="paths_sigma")
    T_p = c4.slider("T (años)", 0.1, 3.0, 1.0, 0.1, key="paths_T")
    steps_p = c5.slider("Pasos (resolución)", 20, 252, 100, 1, key="paths_steps")

    c6, c7 = st.columns(2)
    n_paths_p = c6.slider("Paths a dibujar", 10, 500, 100, 10, key="paths_n")
    seed_p = c7.number_input("Seed", value=7, step=1, key="paths_seed")

    paths = simulate_gbm_paths(S0_p, mu_p, sigma_p, T_p,
                               steps=steps_p, n_paths=n_paths_p, seed=int(seed_p))
    t_grid = np.linspace(0, T_p, steps_p + 1)

    # Cuantiles de la distribución analítica log-normal a cada t
    # log S_t ~ N(log S0 + (μ - σ²/2)t, σ² t)
    t_pos = t_grid[1:]   # evitar t=0 (var=0)
    m_log = np.log(S0_p) + (mu_p - 0.5 * sigma_p ** 2) * t_pos
    s_log = sigma_p * np.sqrt(t_pos)
    q05 = np.exp(m_log - 1.645 * s_log)
    q95 = np.exp(m_log + 1.645 * s_log)
    median = np.exp(m_log)

    fig = go.Figure()
    # Paths
    for i in range(n_paths_p):
        fig.add_trace(go.Scatter(
            x=t_grid, y=paths[i], mode="lines",
            line=dict(width=1), opacity=0.25, showlegend=False,
        ))
    # Cuantiles teóricos
    fig.add_trace(go.Scatter(
        x=t_pos, y=q05, mode="lines",
        line=dict(color="#ffa726", width=2, dash="dash"),
        name="Cuantil 5%",
    ))
    fig.add_trace(go.Scatter(
        x=t_pos, y=median, mode="lines",
        line=dict(color="#ef5350", width=2),
        name="Mediana",
    ))
    fig.add_trace(go.Scatter(
        x=t_pos, y=q95, mode="lines",
        line=dict(color="#ffa726", width=2, dash="dash"),
        name="Cuantil 95%",
    ))
    fig.update_layout(
        title=f"{n_paths_p} paths GBM (σ={sigma_p:.2f}, μ={mu_p:.2f}, T={T_p:.2f})",
        xaxis_title="t (años)",
        yaxis_title="S_t",
        template="plotly_dark",
        height=500,
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)

    # Estadísticas terminales
    ST = paths[:, -1]
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Min S_T", f"${ST.min():.2f}")
    s2.metric("P(S_T < S₀)", f"{(ST < S0_p).mean():.1%}")
    s3.metric("P(S_T > 1.5·S₀)", f"{(ST > 1.5 * S0_p).mean():.1%}")
    s4.metric("Max S_T", f"${ST.max():.2f}")


# ============================================================
# TAB 4 — MC vs Black-Scholes
# ============================================================
with tab_mc:
    st.header("Pricing por Monte Carlo y convergencia a Black-Scholes")
    st.markdown(
        r"""
Para una opción europea no necesitamos las trayectorias, solo $S_T$. Bajo medida
risk-neutral $\mathbb{Q}$ con drift $r - q$:

$$
C_0 = e^{-rT} \cdot \mathbb{E}^{\mathbb{Q}}\!\left[ \max(S_T - K,\ 0) \right]
$$

El estimador MC con $N$ samples es:

$$
\hat C_0 = e^{-rT} \cdot \frac{1}{N} \sum_{i=1}^{N} \max(S_T^{(i)} - K,\ 0)
$$

Error estándar: $\text{SE} = \frac{\sigma_{\text{payoff}}}{\sqrt{N}}$. Es decir, para
**reducir el error a la mitad necesitás 4× los paths** — convergencia lentísima
$O(1/\sqrt{N})$.

**Antithetic variates**: por cada $Z$ que sampleás, usás también $-Z$. Como $g(Z)$ y $g(-Z)$
están negativamente correlacionados (para payoffs monótonos), el promedio del par tiene
menos varianza que dos samples independientes.
"""
    )

    c1, c2, c3, c4 = st.columns(4)
    S_mc = c1.number_input("S", value=42.0, step=1.0, key="mc_S")
    K_mc = c2.number_input("K", value=40.0, step=1.0, key="mc_K")
    T_mc = c3.slider("T", 0.05, 2.0, 0.5, 0.05, key="mc_T")
    sigma_mc = c4.slider("σ", 0.05, 1.0, 0.20, 0.01, key="mc_sigma")

    c5, c6, c7, c8 = st.columns(4)
    r_mc = c5.slider("r", 0.0, 0.30, 0.10, 0.005, key="mc_r")
    q_mc = c6.slider("q", 0.0, 0.20, 0.0, 0.005, key="mc_q")
    opt_mc = c7.radio("Tipo", ["call", "put"], horizontal=True, key="mc_type")
    antithetic_mc = c8.checkbox("Antithetic", value=True, key="mc_anti")

    n_paths_mc = st.slider("N (paths)", 1_000, 500_000, 50_000, 1_000, key="mc_n")
    seed_mc = st.number_input("Seed", value=2024, step=1, key="mc_seed")

    bs_ref = bs_price(S_mc, K_mc, T_mc, r_mc, sigma_mc, q_mc, opt_mc)
    result = mc_price_european(S_mc, K_mc, T_mc, r_mc, sigma_mc, q_mc, opt_mc,
                               n_paths=n_paths_mc, antithetic=antithetic_mc,
                               seed=int(seed_mc))

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Precio MC", f"${result['price']:.4f}")
    m2.metric("Black-Scholes", f"${bs_ref:.4f}")
    m3.metric("Diferencia", f"${result['price'] - bs_ref:+.4f}")
    m4.metric("Std error", f"${result['stderr']:.4f}",
              help="±1.96·SE es el intervalo de confianza 95%.")

    ci_contains_bs = result["ci95_lo"] <= bs_ref <= result["ci95_hi"]
    if ci_contains_bs:
        st.success(
            f"✅ El CI95 [{result['ci95_lo']:.4f}, {result['ci95_hi']:.4f}] contiene al precio BS exacto."
        )
    else:
        st.warning(
            f"⚠️ El CI95 [{result['ci95_lo']:.4f}, {result['ci95_hi']:.4f}] **no** contiene a BS. "
            "Esperable ~5% de las veces por puro chance, o señal de pocos paths."
        )

    st.subheader("Convergencia: precio MC vs N paths")
    n_grid = [500, 1_000, 2_500, 5_000, 10_000, 25_000, 50_000, 100_000, 250_000]
    conv = mc_convergence(S_mc, K_mc, T_mc, r_mc, sigma_mc, q_mc, opt_mc,
                          n_values=n_grid, antithetic=antithetic_mc, seed=int(seed_mc))

    fig = make_subplots(rows=1, cols=2, subplot_titles=(
        "Precio MC y CI95 vs BS",
        "Standard error vs N (log-log)",
    ))
    fig.add_trace(go.Scatter(
        x=conv["n"], y=conv["price"], mode="lines+markers",
        name="Precio MC", line=dict(color="#26a69a", width=2),
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=conv["n"], y=conv["ci95_hi"], mode="lines",
        line=dict(color="#26a69a", width=1, dash="dot"), name="CI95",
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=conv["n"], y=conv["ci95_lo"], mode="lines",
        line=dict(color="#26a69a", width=1, dash="dot"),
        fill="tonexty", fillcolor="rgba(38,166,154,0.15)", showlegend=False,
    ), row=1, col=1)
    fig.add_hline(y=bs_ref, line=dict(color="#ffa726", width=2, dash="dash"),
                  annotation_text=f"BS = ${bs_ref:.4f}", annotation_position="right",
                  row=1, col=1)
    # log-log de stderr y referencia 1/√N
    se0 = conv["stderr"][0]
    n0 = conv["n"][0]
    ref_slope = [se0 * np.sqrt(n0 / n) for n in conv["n"]]
    fig.add_trace(go.Scatter(
        x=conv["n"], y=conv["stderr"], mode="lines+markers",
        name="SE empírico", line=dict(color="#ef5350", width=2),
    ), row=1, col=2)
    fig.add_trace(go.Scatter(
        x=conv["n"], y=ref_slope, mode="lines",
        name="∝ 1/√N (teórico)", line=dict(color="#ffa726", width=2, dash="dash"),
    ), row=1, col=2)
    fig.update_xaxes(type="log", row=1, col=1)
    fig.update_xaxes(type="log", row=1, col=2, title_text="N (paths)")
    fig.update_yaxes(type="log", row=1, col=2, title_text="Standard error")
    fig.update_layout(template="plotly_dark", height=440, hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown(
        """
**Cosas para observar:**

1. **Convergencia lenta**: para bajar el SE de 0.05 a 0.005 necesitás ~100× más paths.
2. **Antithetic** desplaza la curva de SE hacia abajo — se ve directamente en el log-log.
3. **El CI95 se angosta como 1/√N**. Si fijás un objetivo de precisión $\\varepsilon$,
   necesitás $N \\propto 1/\\varepsilon^2$.

**¿Cuándo usar MC en lugar de BS?** Cuando el payoff es **path-dependent**: opciones
asiáticas (promedio del path), barreras (knock-in/knock-out), lookback, etc. Para esos
casos no hay closed-form y MC es el camino más natural.
"""
    )
