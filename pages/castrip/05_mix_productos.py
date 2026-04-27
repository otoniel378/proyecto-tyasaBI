"""
05_mix_productos.py — Mix de Productos — CASTRIP
"""
import os, sys
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if _root not in sys.path:
    sys.path.insert(0, _root)

import streamlit as st
from config import COLORS

from aceros_planos.castrip.loaders import load_gold_cliente_producto, load_gold_demanda_producto
from aceros_planos.negros.analytics.mix_productos import (
    tabla_coocurrencia, participacion_por_familia,
)
from core.components.kpi_cards import seccion_titulo
from core.components.filters import sidebar_header
from core.components.charts import donut, barras_horizontales, treemap
from core.components.tables import tabla_ejecutiva

if not st.session_state.get("_castrip_combined"):
    sidebar_header("CASTRIP", "⚡")

with st.spinner("Cargando mix de productos..."):
    df_cli_prod = load_gold_cliente_producto()
    df_producto = load_gold_demanda_producto()

st.markdown(
    f"<h2 style='color:{COLORS['text']};margin-bottom:0;'>🎯 Mix de Productos</h2>",
    unsafe_allow_html=True,
)
st.divider()

if df_producto.empty:
    st.info("Sin datos CASTRIP disponibles.")
    st.stop()

col_donut, col_bars = st.columns(2)
with col_donut:
    seccion_titulo("Participación por Producto")
    top10 = df_producto.nlargest(10, "PESO_TON")
    fig = donut(top10, names="PRODUCTO_LIMPIO", values="PESO_TON", titulo="Mix de productos")
    st.plotly_chart(fig, use_container_width=True)

with col_bars:
    seccion_titulo("Volumen por Producto")
    fig = barras_horizontales(df_producto, x="PESO_TON", y="PRODUCTO_LIMPIO",
                               titulo="Top productos", x_label="Toneladas", max_items=15)
    st.plotly_chart(fig, use_container_width=True)

if not df_cli_prod.empty:
    seccion_titulo("Treemap Cliente × Producto")
    if "DIVISION" in df_cli_prod.columns:
        fig = treemap(df_cli_prod, path=["DIVISION", "PRODUCTO_LIMPIO"], values="PESO_TON",
                      titulo="Distribución por división y producto")
    else:
        fig = treemap(df_cli_prod, path=["PRODUCTO_LIMPIO", "CLIENTE"], values="PESO_TON",
                      titulo="Distribución por producto y cliente")
    st.plotly_chart(fig, use_container_width=True)

    seccion_titulo("Co-ocurrencia de Productos")
    cooc = tabla_coocurrencia(df_cli_prod)
    if not cooc.empty:
        tabla_ejecutiva(cooc.head(20), key="cs_mix_cooc")
