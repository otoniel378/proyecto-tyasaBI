"""
castrip_main.py — CASTRIP (página principal del sidebar)
9 tabs internos: Alertas · Resumen · Segmentación · Series · Forecast · Mix · Clientes · Condición · Contexto
"""
import os, sys

_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)

import streamlit as st
from config import COLORS
from core.components.filters import sidebar_header, filtro_rango_fechas

# Signal to sub-pages that they are running inside the combined page
st.session_state["_castrip_combined"] = True

sidebar_header("Aceros Planos", "⚡")
fecha_inicio, fecha_fin = filtro_rango_fechas(key_prefix="cs_main")
st.session_state["_cs_fecha_inicio"] = fecha_inicio
st.session_state["_cs_fecha_fin"] = fecha_fin

st.markdown(
    f"<h2 style='color:{COLORS['text']};margin-bottom:4px;font-size:1.5rem;'>⚡ Aceros Planos — CASTRIP</h2>",
    unsafe_allow_html=True,
)

tabs = st.tabs([
    "⚡ Alertas",
    "📊 Resumen",
    "👥 Segmentación",
    "📈 Series",
    "🔮 Forecast",
    "🎯 Mix",
    "🤝 Clientes",
    "🌡️ Condición",
    "🌐 Contexto",
])

_cs_dir = os.path.join(os.path.dirname(__file__), "castrip")


def _run(filename: str) -> None:
    path = os.path.join(_cs_dir, filename)
    ns = {"__name__": "__main__", "__file__": path}
    exec(open(path, encoding="utf-8").read(), ns)  # noqa: S102


with tabs[0]:
    _run("00_alertas.py")

with tabs[1]:
    _run("01_resumen.py")

with tabs[2]:
    _run("02_segmentacion.py")

with tabs[3]:
    _run("03_series_tiempo.py")

with tabs[4]:
    _run("04_forecasting.py")

with tabs[5]:
    _run("05_mix_productos.py")

with tabs[6]:
    _run("06_clientes.py")

with tabs[7]:
    _run("07_condicion_mercado.py")

with tabs[8]:
    _run("08_mercado_contexto.py")
