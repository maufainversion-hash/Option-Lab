# Options Lab AR 📊

Laboratorio personal de opciones construido en Python + Streamlit. Tiene dos partes:

1. **Educación** — Recorrido interactivo basado en Hull, *Options, Futures and Other Derivatives*. Cubre Cap 1, 9, 10, 11 y 18.
2. **Mercado AR** *(próximamente)* — Chains reales de BYMA, IV surface, scanner.

Pricing engine validado contra Hull Ejemplo 14.6 (S=42, K=40, T=0.5, r=10%, σ=20%) → Call=4.7594, Put=0.8086.

## Quickstart

```bash
git clone https://github.com/maufaferreyra-alt/Option-Lab.git
cd Option-Lab
pip install -r requirements.txt
streamlit run app.py
```

App abre en `http://localhost:8501`.

> **Deploy público**: el repo está pensado para Streamlit Community Cloud — entrypoint
> `app.py` en la raíz, deps en `requirements.txt`. Conectar el repo en
> [share.streamlit.io](https://share.streamlit.io) y deployar.

## Tests

```bash
pytest tests/ -v
```

Se deben pasar todos. Anclados a Hull para tener verificación numérica externa.

## Estructura

```
Option-Lab/
├── app.py                          # Landing (entrypoint Streamlit)
├── pages/
│   ├── 1_📚_Education.py           # 4 tabs (Hull Cap 1, 9, 10, 11, 18)
│   └── 2_🎲_Monte_Carlo.py         # 4 tabs (Hull Cap 13: Wiener, GBM, paths, MC)
├── pricing/
│   ├── black_scholes.py            # BS analítico
│   ├── binomial.py                 # CRR + Leisen-Reimer
│   ├── monte_carlo.py              # GBM paths + MC pricer + antithetic
│   └── implied_vol.py              # IV via Brent
├── greeks/
│   ├── analytical.py               # closed-form
│   └── numerical.py                # bump-and-reprice (validación)
├── strategies/
│   ├── legs.py                     # 11 estrategias clásicas (Hull Cap 11)
│   ├── payoff.py                   # P&L engine
│   └── aggregator.py               # net greeks
├── education/
│   ├── parity.py                   # put-call parity + implied rate
│   └── bounds.py                   # cotas de no-arbitraje (Hull Cap 10)
├── ui/
│   └── charts/
│       ├── payoff_diagram.py       # diagram de payoff con annotations
│       └── greeks_visualizer.py    # greeks 2D + 3D surfaces
├── tests/                          # 6 suites, anclados a Hull Cap 14.6
└── requirements.txt
```

## Hull → Module Map

| Hull Cap | Tema | Módulo en la app |
|---|---|---|
| 1 | Introducción a derivados | Tab 1 de Education |
| 9 | Mechanics of options markets | Tab 1 (terminología, payoffs) |
| 10 | Properties of stock options | Tab 2 (parity + bounds) |
| 11 | Trading strategies | Tab 3 (11 estrategias interactivas) |
| 12 | Binomial trees | Tab 4 (convergencia CRR + LR) |
| 13 | Wiener processes / GBM | Página Monte Carlo (4 tabs) |
| 14 | Black-Scholes-Merton | Pricing engine + sliders en Tab 4 |
| 18 | Greeks | Tab 4 (panel 2x3 + surface 3D) |
| 21 | Monte Carlo simulation | Página Monte Carlo (Tab 4) |

## Roadmap

**Hechos en Bloque 1** (este commit):
- ✅ Pricing core: BS + Binomial + IV inversion
- ✅ Greeks analíticos + numéricos
- ✅ Strategy engine (11 estrategias clásicas)
- ✅ Education page con 4 tabs interactivos
- ✅ Tests anclados a Hull

**Hechos en Bloque 2:**
- ✅ Cap 13: Wiener processes + GBM (página Monte Carlo, 4 tabs)
- ✅ Pricing engine MC: paths GBM, MC europeo con antithetic, convergencia a BS
- ✅ Tests MC anclados a Hull 14.6 + verificación de momentos analíticos

**Próximos bloques:**
- ⏳ Cap 14: derivación BS step-by-step (educativo)
- ⏳ Cap 19: Volatility smile
- ⏳ Data layer AR: PyOBD para chains BYMA, tasa AR
- ⏳ AR Chains page con IV surface real
- ⏳ AI Scanner (Gemini sobre chains)

## Decisiones técnicas

- **Binomial: CRR + Leisen-Reimer.** LR converge mucho más rápido y monotónicamente, ideal para mostrar la convergencia a BS en pocos pasos. CRR queda como referencia clásica de Hull.
- **IV via Brent's method.** Más robusto que Newton-Raphson para chains AR donde los quotes son ruidosos (bid/ask wide, OI bajo) y Vega ≈ 0 hace divergir Newton.
- **Greeks analíticas + numéricas en paralelo.** Las numéricas no se usan en producción — están como validación cruzada de las analíticas en los tests.
- **Greeks en `theta`: por año.** Multiplicar por 1/365 para "theta per día calendario" (la convención de la mayoría de los brokers).
- **Strategies en `payoff.py`: vectorizadas con NumPy.** Para no tener overhead Python en loops sobre 200+ spots.

## Referencia

Hull, J.C. *Options, Futures and Other Derivatives*, 11th ed. Pearson, 2021.

## Licencia

Proyecto personal de uso propio.
