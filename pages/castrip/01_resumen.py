"""
01_resumen.py — Resumen Ejecutivo — CASTRIP
"""
import os, sys
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if _root not in sys.path:
    sys.path.insert(0, _root)

import streamlit as st
from config import COLORS

from aceros_planos.castrip.loaders import (
    load_gold_demanda_cliente,
    load_gold_demanda_producto,
    load_gold_demanda_mensual_total,
)
from aceros_planos.negros.analytics.kpis import calcular_kpis_resumen, calcular_top_n, calcular_participacion
from aceros_planos.negros.analytics.series_tiempo import preparar_serie_mensual, construir_heatmap_mes_anio
from core.components.kpi_cards import render_kpi_row, seccion_titulo
from core.components.filters import sidebar_header, filtro_rango_fechas, aplicar_filtro_fechas
from core.components.charts import linea_temporal, barras_horizontales, donut, heatmap
from core.components.tables import tabla_ejecutiva

if not st.session_state.get("_castrip_combined"):
    sidebar_header("CASTRIP", "⚡")
    fecha_inicio, fecha_fin = filtro_rango_fechas(key_prefix="cs_re")
else:
    fecha_inicio = st.session_state.get("_cs_fecha_inicio")
    fecha_fin = st.session_state.get("_cs_fecha_fin")

with st.spinner("Cargando datos CASTRIP..."):
    df_cliente  = load_gold_demanda_cliente()
    df_producto = load_gold_demanda_producto()
    df_mensual  = load_gold_demanda_mensual_total()

df_mensual_f = aplicar_filtro_fechas(df_mensual, fecha_inicio, fecha_fin, col="PERIODO")

st.markdown(
    f"<h2 style='color:{COLORS['text']};margin-bottom:0;'>📊 Resumen Ejecutivo</h2>",
    unsafe_allow_html=True,
)
st.divider()

if df_cliente.empty and df_producto.empty:
    st.info("Sin datos CASTRIP disponibles. Verifica la conexión a BigQuery.")
    st.stop()

kpis_data = calcular_kpis_resumen(df_cliente, df_producto, df_mensual_f)

render_kpi_row([
    {"label": "Volumen Total",    "value": kpis_data.peso_total,     "suffix": " ton", "icon": "📦"},
    {"label": "Clientes Activos", "value": kpis_data.n_clientes,     "icon": "👥"},
    {"label": "Productos",        "value": kpis_data.n_productos,    "icon": "🔩"},
    {"label": "Ticket Promedio",  "value": kpis_data.ticket_promedio,"suffix": " ton", "icon": "🎯"},
])

st.divider()

seccion_titulo("Tendencia Mensual")
if not df_mensual_f.empty:
    df_serie = preparar_serie_mensual(df_mensual_f)
    if not df_serie.empty:
        fig = linea_temporal(df_serie, "PERIODO", "PESO_TON",
                             titulo="Volumen mensual CASTRIP", y_label="Toneladas", show_area=True)
        st.plotly_chart(fig, use_container_width=True)

col_prod, col_cli = st.columns(2)

with col_prod:
    seccion_titulo("Top Productos")
    top_prod = calcular_top_n(df_producto, col="PRODUCTO_LIMPIO", n=10)
    if not top_prod.empty:
        fig = barras_horizontales(top_prod, x="PESO_TON", y="PRODUCTO_LIMPIO",
                                  titulo="Por volumen", x_label="Toneladas")
        st.plotly_chart(fig, use_container_width=True)

with col_cli:
    seccion_titulo("Top Clientes")
    top_cli = calcular_top_n(df_cliente, col="CLIENTE", n=10)
    if not top_cli.empty:
        fig = barras_horizontales(top_cli, x="PESO_TON", y="CLIENTE",
                                  titulo="Por volumen", x_label="Toneladas")
        st.plotly_chart(fig, use_container_width=True)

seccion_titulo("Heatmap Mensual")
hmap_data = construir_heatmap_mes_anio(df_mensual_f)
if not hmap_data.empty:
    fig = heatmap(hmap_data, titulo="Toneladas por mes y año")
    st.plotly_chart(fig, use_container_width=True)
