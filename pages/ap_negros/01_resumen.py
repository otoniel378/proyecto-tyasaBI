"""
01_resumen.py — Resumen Ejecutivo — Aceros Planos Negros.
Vision 360: KPIs, tendencia mensual, participacion por producto, top clientes y top productos.
"""

import os, sys

_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if _root not in sys.path:
    sys.path.insert(0, _root)

import streamlit as st
import pandas as pd
from config import APP_NAME, COLORS

from aceros_planos.negros.loaders import (
    load_gold_demanda_cliente,
    load_gold_demanda_producto,
    load_gold_demanda_mensual,
    load_gold_demanda_mensual_total,
)
from aceros_planos.negros.analytics.kpis import calcular_kpis_resumen, calcular_top_n, calcular_participacion
from aceros_planos.negros.analytics.series_tiempo import preparar_serie_mensual, construir_heatmap_mes_anio
from core.components.kpi_cards import render_kpi_row, seccion_titulo
from core.components.filters import sidebar_header, filtro_rango_fechas, aplicar_filtro_fechas
from core.components.charts import linea_temporal, barras_horizontales, donut, heatmap, treemap
from core.components.tables import tabla_ejecutiva

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
sidebar_header("Filtros", "📊")
fecha_inicio, fecha_fin = filtro_rango_fechas(key_prefix="re")

# ---------------------------------------------------------------------------
# Carga de datos
# ---------------------------------------------------------------------------
with st.spinner("Cargando datos..."):
    df_cliente  = load_gold_demanda_cliente()
    df_producto = load_gold_demanda_producto()
    df_mensual  = load_gold_demanda_mensual_total()

df_mensual_f = aplicar_filtro_fechas(df_mensual, fecha_inicio, fecha_fin, col="PERIODO")

# ---------------------------------------------------------------------------
# Encabezado
# ---------------------------------------------------------------------------
st.markdown(
    f"""
    <h2 style='color:{COLORS["primary"]};margin-bottom:0;'>📊 Resumen Ejecutivo</h2>
    <p style='color:{COLORS["text_light"]};'>Aceros Planos Negros — Demanda historica</p>
    """,
    unsafe_allow_html=True,
)
st.divider()

# ---------------------------------------------------------------------------
# KPIs principales
# ---------------------------------------------------------------------------
kpis_data = calcular_kpis_resumen(df_cliente, df_producto, df_mensual_f)

render_kpi_row([
    {"label": "Toneladas Totales",     "value": kpis_data.toneladas_totales, "suffix": " ton",  "icon": "⚖️",
     "help_text": "Suma total de toneladas en el periodo seleccionado."},
    {"label": "Clientes Activos",      "value": kpis_data.clientes_activos,  "icon": "👥",
     "help_text": "Numero de clientes con al menos un embarque."},
    {"label": "Productos Activos",     "value": kpis_data.productos_activos, "icon": "🔩",
     "help_text": "Numero de productos unicos vendidos."},
    {"label": "Ticket Prom. / Cliente","value": kpis_data.ticket_promedio,   "suffix": " ton",  "icon": "📦",
     "delta": kpis_data.variacion_mom, "delta_label": "vs mes anterior",
     "help_text": "Toneladas promedio por cliente activo."},
])

st.markdown("")
col1, col2 = st.columns(2)
with col1:
    st.metric("Top cliente",  kpis_data.top_cliente  or "—")
with col2:
    st.metric("Top producto", kpis_data.top_producto or "—")

st.divider()

# ---------------------------------------------------------------------------
# Tendencia mensual
# ---------------------------------------------------------------------------
seccion_titulo("Tendencia Mensual de Demanda", "Serie de toneladas por mes")

if df_mensual_f.empty:
    st.warning("Sin datos para el periodo seleccionado.")
else:
    serie = preparar_serie_mensual(df_mensual_f)
    fig_linea = linea_temporal(serie, x="PERIODO", y="PESO_TON", titulo="Toneladas mensuales", show_area=True)
    st.plotly_chart(fig_linea, use_container_width=True)

# ---------------------------------------------------------------------------
# Participacion por producto y Heatmap
# ---------------------------------------------------------------------------
col_a, col_b = st.columns([3, 2])

with col_a:
    seccion_titulo("Participacion por Producto", "Distribucion del volumen")
    df_part = calcular_participacion(df_producto, "PRODUCTO_LIMPIO")
    if not df_part.empty:
        fig_treemap = treemap(df_part, path=["PRODUCTO_LIMPIO"], values="PESO_TON",
                              titulo="Treemap — Toneladas por producto")
        st.plotly_chart(fig_treemap, use_container_width=True)

with col_b:
    seccion_titulo("Mix Donut", "")
    if not df_part.empty:
        fig_donut = donut(df_part.head(8), names="PRODUCTO_LIMPIO", values="PESO_TON", titulo="")
        st.plotly_chart(fig_donut, use_container_width=True)

# ---------------------------------------------------------------------------
# Heatmap Mes x Anio
# ---------------------------------------------------------------------------
seccion_titulo("Heatmap Mes x Anio", "Intensidad de demanda por periodo")

if not df_mensual_f.empty:
    serie_heat = preparar_serie_mensual(df_mensual_f)
    if "ANIO" in serie_heat.columns:
        pivot = construir_heatmap_mes_anio(serie_heat)
        if not pivot.empty:
            fig_heat = heatmap(pivot, titulo="Toneladas por Mes y Anio", x_label="Anio", y_label="Mes")
            st.plotly_chart(fig_heat, use_container_width=True)

# ---------------------------------------------------------------------------
# Top 10 Clientes y Top 10 Productos
# ---------------------------------------------------------------------------
col_c, col_d = st.columns(2)

with col_c:
    seccion_titulo("Top 10 Clientes", "Por volumen de toneladas")
    top_clientes = calcular_top_n(df_cliente, "CLIENTE", n=10)
    if not top_clientes.empty:
        fig_cli = barras_horizontales(top_clientes, x="PESO_TON", y="CLIENTE", x_label="Toneladas")
        st.plotly_chart(fig_cli, use_container_width=True)

with col_d:
    seccion_titulo("Top 10 Productos", "Por volumen de toneladas")
    top_prod = calcular_top_n(df_producto, "PRODUCTO_LIMPIO", n=10)
    if not top_prod.empty:
        fig_prod = barras_horizontales(top_prod, x="PESO_TON", y="PRODUCTO_LIMPIO", x_label="Toneladas")
        st.plotly_chart(fig_prod, use_container_width=True)

# ---------------------------------------------------------------------------
# Tabla resumen
# ---------------------------------------------------------------------------
st.divider()
seccion_titulo("Tabla Resumen por Cliente", "Descargable en Excel")

df_resumen = df_cliente.copy() if not df_cliente.empty else pd.DataFrame()
if not df_resumen.empty:
    tabla_ejecutiva(df_resumen.sort_values("PESO_TON", ascending=False),
                    col_formatos={"PESO_TON": "{:,.1f}"}, key="resumen_clientes")
