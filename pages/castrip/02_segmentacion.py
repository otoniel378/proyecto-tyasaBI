"""
02_segmentacion.py — Segmentación de Clientes — CASTRIP
"""
import os, sys
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if _root not in sys.path:
    sys.path.insert(0, _root)

import streamlit as st
from config import COLORS

from aceros_planos.castrip.loaders import load_gold_demanda_cliente, load_gold_demanda_mensual_cliente
from aceros_planos.negros.analytics.segmentacion import (
    clasificar_abc, calcular_concentracion_hhi, resumen_abc,
)
from core.components.kpi_cards import render_kpi_row, seccion_titulo, kpi_card_compact
from core.components.filters import sidebar_header, filtro_rango_fechas, aplicar_filtro_fechas
from core.components.charts import pareto, barras_horizontales, scatter
from core.components.tables import tabla_ejecutiva

if not st.session_state.get("_castrip_combined"):
    sidebar_header("CASTRIP", "⚡")
    fecha_inicio, fecha_fin = filtro_rango_fechas(key_prefix="cs_seg")
else:
    fecha_inicio = st.session_state.get("_cs_fecha_inicio")
    fecha_fin = st.session_state.get("_cs_fecha_fin")

with st.spinner("Cargando segmentación CASTRIP..."):
    df_cliente = load_gold_demanda_cliente()
    df_mensual_cli = load_gold_demanda_mensual_cliente()

st.markdown(
    f"<h2 style='color:{COLORS['text']};margin-bottom:0;'>👥 Segmentación de Clientes</h2>",
    unsafe_allow_html=True,
)
st.divider()

if df_cliente.empty:
    st.info("Sin datos CASTRIP disponibles.")
    st.stop()

df_abc = clasificar_abc(df_cliente)

n_a = len(df_abc[df_abc["CLASE"] == "A"])
n_b = len(df_abc[df_abc["CLASE"] == "B"])
n_c = len(df_abc[df_abc["CLASE"] == "C"])
hhi = calcular_concentracion_hhi(df_abc)

render_kpi_row([
    {"label": "Clientes A (Pareto 80%)", "value": n_a,   "icon": "🥇"},
    {"label": "Clientes B",              "value": n_b,   "icon": "🥈"},
    {"label": "Clientes C",              "value": n_c,   "icon": "🥉"},
    {"label": "HHI Concentración",       "value": round(hhi, 1), "icon": "📊"},
])

st.divider()

seccion_titulo("Análisis Pareto")
fig = pareto(df_abc, x="CLIENTE", y="PESO_TON", titulo="Pareto de clientes por volumen", max_items=25)
st.plotly_chart(fig, use_container_width=True)

seccion_titulo("Tabla de Segmentación ABC")
tabla_ejecutiva(
    df_abc[["CLIENTE","PESO_TON","PCT","PCT_ACUM","CLASE"]].rename(columns={
        "PESO_TON": "Toneladas", "PCT": "% Vol", "PCT_ACUM": "% Acum.", "CLASE": "Segmento"
    }),
    key="cs_seg_tabla",
)
