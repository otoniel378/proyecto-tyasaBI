"""
04_forecasting.py — Forecasting — CASTRIP
"""
import os, sys
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if _root not in sys.path:
    sys.path.insert(0, _root)

import streamlit as st
from config import COLORS, FORECAST_HORIZON_DEFAULT, FORECAST_HORIZON_MAX

from aceros_planos.castrip.loaders import load_gold_demanda_mensual_total
from aceros_planos.negros.analytics.series_tiempo import preparar_serie_mensual
from aceros_planos.negros.analytics.forecasting import generar_forecast
from core.components.kpi_cards import render_kpi_row, seccion_titulo
from core.components.filters import sidebar_header, filtro_rango_fechas, aplicar_filtro_fechas
import plotly.graph_objects as go

if not st.session_state.get("_castrip_combined"):
    sidebar_header("CASTRIP", "⚡")
    fecha_inicio, fecha_fin = filtro_rango_fechas(key_prefix="cs_fc")
else:
    fecha_inicio = st.session_state.get("_cs_fecha_inicio")
    fecha_fin = st.session_state.get("_cs_fecha_fin")

with st.spinner("Cargando datos para forecasting..."):
    df_mensual = load_gold_demanda_mensual_total()

df_mensual_f = aplicar_filtro_fechas(df_mensual, fecha_inicio, fecha_fin, col="PERIODO")

st.markdown(
    f"<h2 style='color:{COLORS['text']};margin-bottom:0;'>🔮 Forecasting</h2>",
    unsafe_allow_html=True,
)
st.divider()

if df_mensual_f.empty:
    st.info("Sin datos en el periodo seleccionado.")
    st.stop()

serie = preparar_serie_mensual(df_mensual_f)

_MODELOS = ["auto", "ets", "sarima", "xgb", "naive"]

col_mod, col_hor = st.columns(2)
with col_mod:
    modelo = st.selectbox("Modelo", _MODELOS, key="cs_fc_mod")
with col_hor:
    horizonte = st.slider("Horizonte (meses)", 1, FORECAST_HORIZON_MAX,
                          FORECAST_HORIZON_DEFAULT, key="cs_fc_hor")

if st.button("Generar pronóstico", key="cs_fc_run"):
    with st.spinner("Calculando..."):
        result = generar_forecast(serie, horizonte=horizonte, modelo=modelo)
    st.session_state["cs_fc_result"] = result

result = st.session_state.get("cs_fc_result")
if result:
    if result.error_msg:
        st.error(result.error_msg)
        st.stop()
    fc_df = result.forecast
    metricas = result.metricas
    mejor_modelo = result.modelo

    seccion_titulo(f"Pronóstico — {mejor_modelo}")
    cols = st.columns(4)
    for i, (k, v) in enumerate(list(metricas.items())[:4]):
        with cols[i]:
            from core.components.kpi_cards import kpi_card_compact
            kpi_card_compact(label=k, value=round(v, 2) if isinstance(v, float) else v, icon="📊")

    if fc_df is not None and not fc_df.empty:
        fig = go.Figure()
        hist = fc_df[fc_df["yhat_lower"].isna()]
        fc   = fc_df[fc_df["yhat_lower"].notna()]
        if not hist.empty:
            fig.add_trace(go.Scatter(
                x=hist["ds"], y=hist["yhat"], name="Histórico",
                line=dict(color=COLORS["primary"], width=2), mode="lines",
            ))
        if not fc.empty:
            fig.add_trace(go.Scatter(
                x=fc["ds"], y=fc["yhat"], name="Pronóstico",
                line=dict(color=COLORS["accent"], width=2.5, dash="dot"),
                mode="lines+markers", marker=dict(size=6),
            ))
            fig.add_trace(go.Scatter(
                x=list(fc["ds"]) + list(fc["ds"][::-1]),
                y=list(fc["yhat_upper"]) + list(fc["yhat_lower"][::-1]),
                fill="toself",
                fillcolor="rgba(216,59,1,0.1)",
                line=dict(color="rgba(0,0,0,0)"),
                name="Intervalo",
                showlegend=True,
            ))
        fig.update_layout(
            paper_bgcolor=COLORS["surface"], plot_bgcolor=COLORS["surface"],
            font=dict(color=COLORS["text"]),
            xaxis=dict(showgrid=False),
            yaxis=dict(title="Toneladas", gridcolor=COLORS["border"]),
            legend=dict(bgcolor="rgba(0,0,0,0)"),
            margin=dict(l=40, r=20, t=40, b=40),
            height=380,
        )
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Selecciona parámetros y presiona **Generar pronóstico** para comenzar.")
