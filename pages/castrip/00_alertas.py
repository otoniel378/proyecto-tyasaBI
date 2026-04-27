"""
00_alertas.py — Panel de Alertas Comerciales — CASTRIP
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
    load_gold_cliente_producto,
)
from analytics.alertas import (
    detectar_clientes_en_fuga,
    detectar_enfriamiento,
    calcular_proyeccion_cierre_mes,
    detectar_anomalias_volumen,
)
from core.components.kpi_cards import seccion_titulo, kpi_card_compact
from core.components.alertas_panel import render_anomalia_card, render_termometro_mes, render_semaforo_area
from core.components.filters import sidebar_header

if not st.session_state.get("_castrip_combined"):
    sidebar_header("CASTRIP", "⚡")

st.markdown(
    f"<h2 style='color:{COLORS['text']};margin:0 0 16px 0;'>⚡ Alertas Comerciales</h2>",
    unsafe_allow_html=True,
)

# ── Carga de datos ────────────────────���───────────────────────────────────────
with st.spinner("Cargando datos CASTRIP..."):
    df_mensual = load_gold_demanda_mensual_total()
    df_mensual_cli = load_gold_demanda_mensual_cliente()
    df_cli_prod = load_gold_cliente_producto()

if df_mensual.empty:
    st.info("Sin datos CASTRIP disponibles. Verifica la conexión a BigQuery.")
    st.stop()

# ── Proyección de cierre del mes ──────────────────────────────────────────────
seccion_titulo("Proyección de Cierre del Mes")
proyeccion = calcular_proyeccion_cierre_mes(df_mensual)
if proyeccion:
    render_termometro_mes(
        real=proyeccion.get("acumulado_real", 0),
        objetivo=proyeccion.get("objetivo", 0),
        label=f"Cierre {proyeccion.get('mes_actual', '')}",
        sufijo=" ton",
        dias_restantes=proyeccion.get("dias_restantes"),
    )
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        kpi_card_compact("Acumulado real", proyeccion["acumulado_real"], suffix=" ton", icon="📦")
    with col2:
        kpi_card_compact("Proyección", proyeccion["proyeccion_fin_mes"], suffix=" ton", icon="🔮")
    with col3:
        kpi_card_compact("% del objetivo", proyeccion["pct_objetivo"], suffix="%", icon="🎯")
    with col4:
        kpi_card_compact("Promedio 12m", proyeccion["promedio_12m"], suffix=" ton", icon="📊")

st.divider()

# ── Alertas de clientes en fuga ───────────────────────────────────────────────
seccion_titulo("Clientes en Fuga (últimos 3 meses)")
if not df_mensual_cli.empty:
    df_fuga = detectar_clientes_en_fuga(df_mensual_cli, n_meses_ventana=3, umbral_caida_pct=30)
    if df_fuga.empty:
        st.success("Sin alertas de fuga detectadas.")
    else:
        for _, row in df_fuga.head(10).iterrows():
            render_anomalia_card(
                titulo=row["CLIENTE"],
                descripcion=f"Volumen promedio cayó de {row['PROMEDIO_ANTERIOR']:.1f} a {row['PROMEDIO_RECIENTE']:.1f} ton/mes",
                severidad=row["SEVERIDAD"],
                tipo="Fuga",
                delta_pct=row["CAIDA_PCT"],
            )
else:
    st.info("Sin datos de clientes disponibles.")

st.divider()

# ── Anomalías en volumen total ────────────────────────────��───────────────────
seccion_titulo("Anomalías en Volumen Mensual")
anomalias = detectar_anomalias_volumen(df_mensual)
if anomalias.empty:
    st.success("Sin anomalías estadísticas detectadas en el periodo.")
else:
    for _, row in anomalias.iterrows():
        tipo_ico = "📈" if row["TIPO"] == "pico" else "📉"
        render_anomalia_card(
            titulo=f"{tipo_ico} {row['PERIODO'].strftime('%B %Y') if hasattr(row['PERIODO'], 'strftime') else str(row['PERIODO'])}",
            descripcion=f"Volumen: {row['PESO_TON']:,.1f} ton · Z-score: {row['Z_SCORE']:.2f} · Media móvil: {row['MEDIA_MOV']:,.1f} ton",
            severidad="alta" if abs(row["Z_SCORE"]) > 3 else "media",
            tipo=row["TIPO"].capitalize(),
        )
