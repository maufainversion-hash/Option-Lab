"""
Hub educativo. Selectbox de tema → render del módulo elegido.

Cubre el cronograma UADE IFD I (Hull Cap 1-19) en un solo entry point.
Cada tema vive en un módulo bajo education/ con su propia función render().
"""
from __future__ import annotations
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from education import (
    u1_futuros, u2_coberturas, u3_tasas_fras, u3_forward_pricing, u3_ir_futures,
    u4_swaps, u5_opciones_intro, u6_binomial, u7_index_fx, u8_estrategias,
    greeks_lab, cap8_securitization, cap9_ois,
)
from ui.styling import inject_premium_css
from ui.components.header_strip import render_header_strip


st.set_page_config(page_title="Educación — Options Lab", page_icon="📚",
                   layout="wide", initial_sidebar_state="collapsed")
inject_premium_css()
render_header_strip()


# Diccionario de temas: label visible → módulo con render()
TOPICS: dict[str, callable] = {
    "📖 Bienvenida (¿por dónde arranco?)": None,
    "U1 · Futuros y mecánica (Hull Cap 1-2)": u1_futuros.render,
    "U2 · Coberturas con futuros (Hull Cap 3)": u2_coberturas.render,
    "U3 · Tasas y FRAs (Hull Cap 4)": u3_tasas_fras.render,
    "U3 · Forward/Futures Pricing (Hull Cap 5)": u3_forward_pricing.render,
    "U3 · IR Futures (Hull Cap 6)": u3_ir_futures.render,
    "U4 · Swaps (Hull Cap 7)": u4_swaps.render,
    "Hull Cap 8 · Securitization": cap8_securitization.render,
    "Hull Cap 9 · OIS y colateral": cap9_ois.render,
    "U5 · Opciones intro y propiedades (Hull Cap 10-11)": u5_opciones_intro.render,
    "U6 · Valuación de opciones BSM/binomial (Hull Cap 13-15)": u6_binomial.render,
    "U7 · Index / FX / Futures Options (Hull Cap 17-18)": u7_index_fx.render,
    "U8 · Estrategias multi-leg (Hull Cap 12)": u8_estrategias.render,
    "Las griegas (Hull Cap 19)": greeks_lab.render,
}


# Header de la página
st.markdown(
    '<h1 style="margin:0;font-weight:600;">📚 Educación · Hull-driven</h1>'
    '<div style="color:var(--text-muted);font-size:13px;margin-bottom:18px;">'
    'Cronograma UADE IFD I completo. Elegí un tema del desplegable para cargar su contenido.'
    '</div>', unsafe_allow_html=True
)

# Selectbox prominente
selected = st.selectbox(
    "Elegí el tema",
    list(TOPICS.keys()),
    index=0,
    label_visibility="visible",
)

st.divider()


# Dispatcher
render_fn = TOPICS[selected]
if render_fn is None:
    # Bienvenida — landing default
    st.markdown(
        """
### Cómo está organizado

Este hub cubre **todo el cronograma UADE de Instrumentos Financieros Derivados I**,
mapeado contra los capítulos de Hull *Options, Futures and Other Derivatives*.
Cada tema del desplegable abre un módulo interactivo con explicación, fórmulas,
widgets y verificación contra los ejemplos canónicos del libro.

| Unidad UADE | Capítulos Hull | Foco |
|---|---|---|
| **Unidad I** | 1, 2 | Mecánica de futuros, mark-to-market, convergencia |
| **Unidad II** | 3 | Coberturas, hedge ratio óptimo, basis risk |
| **Unidad III** | 4, 5, 6 | Tasas y FRAs · Forward pricing · IR futures |
| **Unidad IV** | 7 | Swaps y par swap rate |
| **Unidad V** | 10, 11 | Opciones intro, los 6 factores, put-call parity |
| **Unidad VI** | 13, 14, 15 | Binomial, GBM, Black-Scholes-Merton |
| **Unidad VII** | 17, 18 | Index / FX (Garman-Kohlhagen) / Futures (Black) |
| **Unidad VIII** | 12 | Estrategias multi-leg |
| *Suplementos Hull* | 8, 9, 19 | Securitization · OIS · Griegas |

### Recomendado para el parcial

1. Si arrancás de cero: U1 → U2 → U3 (Tasas) → U4 → U5 → U6.
2. Si ya viste futuros y querés full opciones: U5 → U6 → U7 → U8 → Griegas.
3. Si buscás contexto histórico/práctico de mercado: Cap 8 (crisis 2008) y Cap 9 (OIS).

Cada módulo incluye **verificaciones contra Hull canon** marcadas con el sello
📘. Si los inputs default reproducen un ejemplo del libro, vas a ver ✓ verde.
"""
    )
else:
    render_fn()
