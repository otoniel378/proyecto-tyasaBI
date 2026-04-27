"""
aceros_largos_main.py — Aceros Largos (página principal del sidebar)
Contiene las 5 pestañas de Aceros Largos en tabs internos.
"""
import os, sys

_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)

import streamlit as st
from config import COLORS

st.markdown(
    f"<h2 style='color:{COLORS['text']};margin-bottom:4px;font-size:1.5rem;'>📏 Aceros Largos</h2>",
    unsafe_allow_html=True,
)

tabs = st.tabs([
    "📊 Resumen",
    "🏦 Macroeconomía",
    "💹 Mercado",
    "⚙️ Operaciones",
    "✅ Calidad",
])

_al_dir = os.path.join(os.path.dirname(__file__), "aceros_largos")


def _run(filename: str) -> None:
    path = os.path.join(_al_dir, filename)
    ns = {"__name__": "__main__", "__file__": path}
    exec(open(path, encoding="utf-8").read(), ns)  # noqa: S102


with tabs[0]:
    _run("01_resumen.py")

with tabs[1]:
    _run("02_macroeconomia.py")

with tabs[2]:
    _run("03_mercado.py")

with tabs[3]:
    _run("04_operaciones.py")

with tabs[4]:
    _run("05_calidad.py")
