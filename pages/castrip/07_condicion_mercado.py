"""
07_condicion_mercado.py — Condición de Mercado — CASTRIP
Índice compuesto, ventanas de oportunidad, correlaciones con ventas.
"""
import os, sys
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if _root not in sys.path:
    sys.path.insert(0, _root)

import streamlit as st
from config import COLORS

from aceros_planos.castrip.loaders import load_gold_demanda_mensual_total
from mercado_noticias.loaders import load_variables_mercado
from mercado_noticias.inegi_loader import load_indicadores_inegi
from analytics.condicion_mercado import (
    calcular_indice_condicion,
    detectar_ventanas_oportunidad,
    calcular_correlaciones_lag,
)
from core.components.kpi_cards import seccion_titulo, kpi_card_compact
from core.components.filters import sidebar_header
import plotly.graph_objects as go

if not st.session_state.get("_castrip_combined"):
    sidebar_header("CASTRIP", "⚡")

st.markdown(
    f"<h2 style='color:{COLORS['text']};margin-bottom:0;'>🌡️ Condición de Mercado</h2>",
    unsafe_allow_html=True,
)
st.divider()

# ── Carga de datos ────────────────────────────────────────────────────────────
with st.spinner("Cargando datos de mercado..."):
    df_ventas = load_gold_demanda_mensual_total()
    df_vars   = load_variables_mercado()

# Construir series_dict desde variables de mercado + INEGI
series_dict: dict = {}

if not df_vars.empty and "VARIABLE" in df_vars.columns:
    for var in df_vars["VARIABLE"].unique():
        dv = df_vars[df_vars["VARIABLE"] == var][["FECHA", "VALOR"]].rename(
            columns={"FECHA": "fecha", "VALOR": "valor"}
        )
        series_dict[var] = dv

with st.spinner("Consultando INEGI..."):
    inegi_claves = ["IGAE_INDUSTRIA", "IGAE_MANUFACTURA", "INVERSION_FIJA",
                    "INPC_GENERAL", "USD_MXN"]
    try:
        inegi_data = load_indicadores_inegi(claves=inegi_claves)
        series_dict.update(inegi_data)
    except Exception:
        pass

if not series_dict:
    st.info("Sin datos de variables de mercado disponibles.")
    st.stop()

# ── Índice de condición ───────────────────────────────────────────────────────
seccion_titulo("Índice de Condición de Mercado")

with st.spinner("Calculando índice..."):
    df_indice = calcular_indice_condicion(series_dict)

if df_indice.empty:
    st.info("Insuficientes variables para calcular el índice.")
else:
    ultimo_indice = df_indice["INDICE"].iloc[-1] if not df_indice.empty else 50
    color_ind = COLORS["success"] if ultimo_indice >= 65 else (COLORS["danger"] if ultimo_indice <= 35 else COLORS["warning"])
    estado_ind = "Favorable" if ultimo_indice >= 65 else "Desfavorable" if ultimo_indice <= 35 else "Neutral"

    col1, col2, col3 = st.columns(3)
    with col1:
        kpi_card_compact("Índice actual", round(ultimo_indice, 1), suffix="/100", icon="🌡️", accent=color_ind)
    with col2:
        var_m = df_indice["INDICE"].diff().iloc[-1] if len(df_indice) > 1 else 0
        kpi_card_compact("Variación mensual", round(float(var_m), 1), suffix=" pts", icon="📊")
    with col3:
        kpi_card_compact("Estado", estado_ind, icon="🎯", accent=color_ind)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_indice["fecha"], y=df_indice["INDICE"],
        mode="lines", name="Índice",
        line=dict(color=COLORS["primary"], width=2.5),
        fill="tozeroy", fillcolor="rgba(74,159,212,0.08)",
    ))
    fig.add_hrect(y0=65, y1=100, fillcolor="rgba(46,204,113,0.06)",
                  line_width=0, annotation_text="Favorable", annotation_position="top right",
                  annotation=dict(font=dict(color=COLORS["success"], size=11)))
    fig.add_hrect(y0=0, y1=35, fillcolor="rgba(231,76,60,0.06)",
                  line_width=0, annotation_text="Desfavorable", annotation_position="bottom right",
                  annotation=dict(font=dict(color=COLORS["danger"], size=11)))
    fig.update_layout(
        paper_bgcolor=COLORS["surface"], plot_bgcolor=COLORS["surface"],
        font=dict(color=COLORS["text"]),
        xaxis=dict(showgrid=False),
        yaxis=dict(title="Índice (0-100)", range=[0, 100], gridcolor=COLORS["border"]),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        margin=dict(l=40, r=20, t=30, b=40),
        height=320,
    )
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ── Ventanas de oportunidad ──────────────────────────────────────────���────
    seccion_titulo("Ventanas de Oportunidad / Riesgo")
    ventanas = detectar_ventanas_oportunidad(df_indice)
    if ventanas.empty:
        st.info("Sin ventanas significativas detectadas.")
    else:
        for _, v in ventanas.iterrows():
            tipo = v["tipo"]
            color = COLORS["success"] if tipo == "oportunidad" else COLORS["danger"]
            bg = "rgba(46,204,113,0.1)" if tipo == "oportunidad" else "rgba(231,76,60,0.1)"
            ico = "🟢" if tipo == "oportunidad" else "🔴"
            fecha_i = v["fecha_inicio"].strftime("%b %Y") if hasattr(v["fecha_inicio"], "strftime") else str(v["fecha_inicio"])
            fecha_f = v["fecha_fin"].strftime("%b %Y") if hasattr(v["fecha_fin"], "strftime") else str(v["fecha_fin"])
            st.markdown(
                f"<div style='background:{bg};border:1px solid {color};border-radius:6px;"
                f"padding:10px 14px;margin-bottom:6px;'>"
                f"<b style='color:{COLORS['text']};'>{ico} {tipo.capitalize()}</b>"
                f"<span style='float:right;color:{COLORS['text_light']};font-size:0.8rem;'>{v['duracion_meses']} meses</span>"
                f"<br><span style='color:{COLORS['neutral']};font-size:0.83rem;'>"
                f"{fecha_i} → {fecha_f} · Índice medio: {v['indice_medio']:.1f}</span></div>",
                unsafe_allow_html=True,
            )

# ── Correlaciones con ventas ──────────────────────────────────────────────────
if not df_ventas.empty and series_dict:
    st.divider()
    seccion_titulo("Correlaciones con Ventas CASTRIP (lag 0-6m)")

    if st.button("Calcular correlaciones", key="cs_cm_corr"):
        with st.spinner("Calculando..."):
            df_corr = calcular_correlaciones_lag(df_ventas, series_dict, max_lag=6)
        st.session_state["cs_cm_corr_df"] = df_corr

    df_corr = st.session_state.get("cs_cm_corr_df")
    if df_corr is not None and not df_corr.empty:
        # Mostrar top correlaciones por lag=0
        top_corr = (
            df_corr[df_corr["lag"] == 0]
            .sort_values("correlacion", key=abs, ascending=False)
            .head(10)
        )
        from core.components.tables import tabla_ejecutiva
        tabla_ejecutiva(
            top_corr.rename(columns={"variable": "Variable", "lag": "Lag", "correlacion": "Correlación", "p_value": "p-valor"}),
            key="cs_cm_corr_tbl",
        )
