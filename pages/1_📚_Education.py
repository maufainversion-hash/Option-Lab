"""
Hub educativo. Dos selectboxes en cascada (Bloque + Tema) que dispatchean al
módulo elegido bajo education/.

Cubre el cronograma UADE IFD I (Hull Cap 1-19) en un solo entry point.
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
    greeks_lab, cap8_securitization, cap9_ois, formulario,
)
from ui.styling import inject_premium_css
from ui.components.header_strip import render_header_strip


st.set_page_config(page_title="Educación — Options Lab", page_icon="📚",
                   layout="wide", initial_sidebar_state="collapsed")
inject_premium_css()
render_header_strip()


# Estructura en 2 niveles: Bloque → {Tema: render_fn}
SECTIONS: dict[str, dict[str, callable]] = {
    "📖 Bienvenida": {
        "Cómo está organizado este hub": None,  # None → renderiza la landing
    },
    "📘 Forwards, tasas y swaps (Cap 1-7)": {
        "U1 · Futuros y mecánica (Cap 1-2)": u1_futuros.render,
        "U2 · Coberturas con futuros (Cap 3)": u2_coberturas.render,
        "U3 · Tasas y FRAs (Cap 4)": u3_tasas_fras.render,
        "U3 · Forward/Futures Pricing (Cap 5)": u3_forward_pricing.render,
        "U3 · IR Futures (Cap 6)": u3_ir_futures.render,
        "U4 · Swaps (Cap 7)": u4_swaps.render,
    },
    "📗 Opciones (Cap 10-15, 17-19)": {
        "U5 · Intro y propiedades (Cap 10-11)": u5_opciones_intro.render,
        "U6 · Valuación BSM/binomial (Cap 13-15)": u6_binomial.render,
        "U7 · Index / FX / Futures Options (Cap 17-18)": u7_index_fx.render,
        "U8 · Estrategias multi-leg (Cap 12)": u8_estrategias.render,
        "Las griegas (Cap 19)": greeks_lab.render,
    },
    "📙 Suplementos Hull (Cap 8-9)": {
        "Cap 8 · Securitization y crisis 2008": cap8_securitization.render,
        "Cap 9 · OIS y colateral": cap9_ois.render,
    },
    "📐 Formulario (machete completo)": {
        "Todas las fórmulas del curso": formulario.render,
    },
}


# Header de la página
st.markdown(
    '<h1 style="margin:0;font-weight:600;">📚 Educación · Hull-driven</h1>'
    '<div style="color:var(--text-muted);font-size:13px;margin-bottom:18px;">'
    'Cronograma UADE IFD I completo. Elegí un bloque y después el tema específico.'
    '</div>', unsafe_allow_html=True
)

# Dos selectboxes en cascada (cada uno con pocos items → no se trunca)
col_block, col_topic = st.columns([1, 2])
section_name = col_block.selectbox(
    "Bloque",
    list(SECTIONS.keys()),
    index=0,
)
topic_name = col_topic.selectbox(
    "Tema",
    list(SECTIONS[section_name].keys()),
    index=0,
)

st.divider()


# Dispatcher
render_fn = SECTIONS[section_name][topic_name]
if render_fn is None:
    st.markdown(
        """
### Cómo está organizado

Este hub cubre **todo el cronograma UADE de Instrumentos Financieros Derivados I**,
mapeado contra los capítulos de Hull *Options, Futures and Other Derivatives*.
Cada tema abre un módulo interactivo con explicación, fórmulas, widgets y
verificación contra los ejemplos canónicos del libro.

| Bloque | Capítulos Hull | Foco |
|---|---|---|
| **Forwards, tasas y swaps** | 1-7 | Mecánica de futuros · coberturas · tasas/FRAs · forward pricing · IR futures · swaps |
| **Opciones** | 10-15, 17-19 | Intro y propiedades · BSM/binomial · Index/FX/Futures · estrategias · griegas |
| **Suplementos Hull** | 8, 9 | Securitization (crisis 2008) · OIS y colateral post-crisis |

### Recomendado para el parcial

1. Si arrancás de cero: U1 → U2 → U3 (Tasas) → U4 → U5 → U6.
2. Si ya viste futuros y querés full opciones: U5 → U6 → U7 → U8 → Griegas.
3. Si buscás contexto de mercado: Cap 8 (crisis 2008) y Cap 9 (OIS).

Cada módulo incluye **verificaciones contra Hull canon** marcadas con el sello
📘. Si los inputs default reproducen un ejemplo del libro, vas a ver ✓ verde.
"""
    )
else:
    render_fn()
