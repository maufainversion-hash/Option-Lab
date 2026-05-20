"""Panel estilo broker para mostrar option chain real (calls | strike | puts)."""
from __future__ import annotations
import numpy as np
import pandas as pd
import streamlit as st


def render_chain_panel(calls: pd.DataFrame, puts: pd.DataFrame, spot: float) -> None:
    """
    Tabla estilo broker. Strike al medio, calls a la izquierda, puts a la derecha.
    Slider para acotar a ventana alrededor del spot (default ±15 strikes).
    """
    if calls.empty and puts.empty:
        st.warning("Sin datos de chain para este expiry.")
        return

    strikes = sorted(set(calls["strike"].tolist()) | set(puts["strike"].tolist()))
    rows = []
    for k in strikes:
        c = calls[calls["strike"] == k].iloc[0] if (calls["strike"] == k).any() else None
        p = puts[puts["strike"] == k].iloc[0] if (puts["strike"] == k).any() else None
        rows.append({
            "Call OI": int(c["openInterest"]) if c is not None else 0,
            "Call Vol": int(c["volume"]) if c is not None else 0,
            "Call IV": f"{c['impliedVolatility']*100:.1f}%" if c is not None and c["impliedVolatility"] > 0 else "—",
            "Call Bid": f"{c['bid']:.2f}" if c is not None else "—",
            "Call Ask": f"{c['ask']:.2f}" if c is not None else "—",
            "Strike": f"{k:.2f}",
            "Put Bid": f"{p['bid']:.2f}" if p is not None else "—",
            "Put Ask": f"{p['ask']:.2f}" if p is not None else "—",
            "Put IV": f"{p['impliedVolatility']*100:.1f}%" if p is not None and p["impliedVolatility"] > 0 else "—",
            "Put Vol": int(p["volume"]) if p is not None else 0,
            "Put OI": int(p["openInterest"]) if p is not None else 0,
            "_k": k,
        })
    df = pd.DataFrame(rows)

    atm_idx = int(np.argmin(np.abs(df["_k"].values - spot)))
    max_half = max(1, len(df) // 2)
    window = st.slider(
        "Strikes alrededor del spot",
        min_value=5, max_value=min(40, max_half), value=min(15, max_half), step=1,
    )
    lo = max(0, atm_idx - window)
    hi = min(len(df), atm_idx + window + 1)
    df_view = df.iloc[lo:hi].drop(columns=["_k"])

    st.dataframe(
        df_view,
        use_container_width=True,
        height=min(600, 38 * len(df_view) + 38),
        hide_index=True,
    )
