"""
03_series_tiempo.py — Series de Tiempo — CASTRIP
"""
import os, sys
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if _root not in sys.path:
    sys.path.insert(0, _root)

import streamlit as st
from config import COLORS

from aceros_planos.castrip.loaders import (
    load_gold_demanda_mensual_total,
    load_gold_demanda_mensual_cliente,
    load_gold_demanda_mensual_producto,
)
from aceros_planos.negros.analytics.series_tiempo import (
    preparar_serie_mensual,
    calcular_variacion_mensual,
    calcular_volatilidad,
    construir_heatmap_mes_anio,
)
from core.components.kpi_cards import render_kpi_row, seccion_titulo
from core.components.filters import sidebar_header, filtro_rango_fechas, aplicar_filtro_fechas
from core.components.charts import linea_temporal, heatmap, yoy_comparison

if not st.session_state.get("_castrip_combined"):
    sidebar_header("CASTRIP", "⚡")
    fecha_inicio, fecha_fin = filtro_rango_fechas(key_prefix="cs_st")
else:
    fecha_inicio = st.session_state.get("_cs_fecha_inicio")
    fecha_fin = st.session_state.get("_cs_fecha_fin")

with st.spinner("Cargando series de tiempo..."):
    df_mensual    = load_gold_demanda_mensual_total()
    df_cli_mes    = load_gold_demanda_mensual_cliente()
    df_prod_mes   = load_gold_demanda_mensual_producto()

df_mensual_f = aplicar_filtro_fechas(df_mensual, fecha_inicio, fecha_fin, col="PERIODO")

st.markdown(
    f"<h2 style='color:{COLORS['text']};margin-bottom:0;'>📈 Series de Tiempo</h2>",
    unsafe_allow_html=True,
)
st.divider()

if df_mensual_f.empty:
    st.info("Sin datos en el periodo seleccionado.")
    st.stop()

serie = preparar_serie_mensual(df_mensual_f)
serie_var = calcular_variacion_mensual(serie)
mom_pct = serie_var["VAR_MOM_PCT"].iloc[-1] if not serie_var.empty and "VAR_MOM_PCT" in serie_var.columns else None
vol_df = calcular_volatilidad(serie)
cv_val = vol_df["CV"].iloc[0] if not vol_df.empty and "CV" in vol_df.columns else 0

render_kpi_row([
    {"label": "Últimas Ton.",    "value": serie["PESO_TON"].iloc[-1] if not serie.empty else 0, "suffix": " ton", "icon": "📦"},
    {"label": "Variación MoM",  "value": round(mom_pct, 1) if mom_pct is not None else "—", "suffix": "%", "icon": "📊",
     "delta": mom_pct, "delta_label": "vs mes anterior"},
    {"label": "Volatilidad CV", "value": round(cv_val, 1), "suffix": "%", "icon": "📐"},
])

seccion_titulo("Tendencia Mensual")
fig = linea_temporal(serie, "PERIODO", "PESO_TON",
                     titulo="Volumen mensual CASTRIP", y_label="Toneladas", show_area=True)
st.plotly_chart(fig, use_container_width=True)

tab_yoy, tab_hmap, tab_top_cli = st.tabs(["YoY", "Heatmap", "Top Clientes"])

with tab_yoy:
    if not df_mensual_f.empty and "ANIO" in df_mensual_f.columns and "MES" in df_mensual_f.columns:
        fig_yoy = yoy_comparison(df_mensual_f, x="MES", y="PESO_TON", anio_col="ANIO",
                                  titulo="Comparación año a año", y_label="Toneladas")
        st.plotly_chart(fig_yoy, use_container_width=True)

with tab_hmap:
    hmap_data = construir_heatmap_mes_anio(df_mensual_f)
    if not hmap_data.empty:
        fig = heatmap(hmap_data, titulo="Toneladas por mes y año")
        st.plotly_chart(fig, use_container_width=True)

with tab_top_cli:
    if not df_cli_mes.empty:
        top_clientes = (
            df_cli_mes.groupby("CLIENTE")["PESO_TON"].sum()
            .nlargest(5).index.tolist()
        )
        sel = st.multiselect("Clientes", top_clientes, default=top_clientes[:3], key="cs_st_cli")
        if sel:
            df_multi = df_cli_mes[df_cli_mes["CLIENTE"].isin(sel)]
            fig = linea_temporal(df_multi, x="PERIODO", y="PESO_TON", color="CLIENTE",
                                  titulo="Evolución por cliente", y_label="Toneladas")
            st.plotly_chart(fig, use_container_width=True)
