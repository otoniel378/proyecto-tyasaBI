"""
06_clientes.py — Inteligencia de Clientes — CASTRIP
Briefing de visita, frecuencia de compra, estacionalidad, cambio de mix por cliente.
"""
import os, sys
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if _root not in sys.path:
    sys.path.insert(0, _root)

import streamlit as st
from config import COLORS

from aceros_planos.castrip.loaders import (
    load_gold_demanda_cliente,
    load_gold_demanda_mensual_cliente,
    load_gold_cliente_producto,
)
from analytics.clientes import (
    calcular_frecuencia_compra,
    predecir_proximo_pedido,
    calcular_estacionalidad_cliente,
    generar_briefing_visita,
    detectar_cambio_mix_cliente,
)
from core.components.kpi_cards import seccion_titulo, kpi_card_compact, kpi_badge
from core.components.filters import sidebar_header
import plotly.graph_objects as go

if not st.session_state.get("_castrip_combined"):
    sidebar_header("CASTRIP", "⚡")

with st.spinner("Cargando datos de clientes..."):
    df_cliente    = load_gold_demanda_cliente()
    df_mensual_cli = load_gold_demanda_mensual_cliente()
    df_cli_prod   = load_gold_cliente_producto()

st.markdown(
    f"<h2 style='color:{COLORS['text']};margin-bottom:0;'>🤝 Inteligencia de Clientes</h2>",
    unsafe_allow_html=True,
)
st.divider()

if df_cliente.empty:
    st.info("Sin datos CASTRIP disponibles.")
    st.stop()

clientes = sorted(df_cliente["CLIENTE"].unique().tolist())
cliente_sel = st.selectbox("Cliente", clientes, key="cs_cli_sel")

st.divider()

# ── Briefing de visita ────────────────────────────────────────────────────────
seccion_titulo("Briefing de Visita")
briefing = generar_briefing_visita(df_mensual_cli, df_cli_prod, cliente_sel)

col1, col2, col3, col4 = st.columns(4)
with col1:
    kpi_card_compact("Compra últimos 6m", briefing.get("compra_total_6m", 0), suffix=" ton", icon="📦")
with col2:
    kpi_card_compact("Promedio mes", briefing.get("compra_promedio_mes", 0), suffix=" ton", icon="📊")
with col3:
    freq = briefing.get("freq_dias")
    kpi_card_compact("Freq. compra", f"{freq:.0f} días" if freq else "��", icon="🔄")
with col4:
    dias_sc = briefing.get("dias_sin_comprar")
    kpi_card_compact("Días sin comprar", dias_sc if dias_sc else "—", icon="⏰")

tendencia = briefing.get("tendencia", "")
if tendencia:
    t_variant = "success" if tendencia == "creciente" else "danger" if tendencia == "decreciente" else "neutral"
    t_pct = briefing.get("tendencia_pct", 0)
    st.markdown(
        f"Tendencia: {kpi_badge(f'{tendencia.capitalize()} ({t_pct:+.1f}%)', t_variant)}",
        unsafe_allow_html=True,
    )

top_prods = briefing.get("top_productos", [])
if top_prods:
    st.markdown(
        f"<div style='margin-top:8px;'>Top productos: "
        + "  ".join(kpi_badge(f"📦 {p['PRODUCTO_LIMPIO']} ({p['PESO_TON']:,.0f} ton)", "primary") for p in top_prods)
        + "</div>",
        unsafe_allow_html=True,
    )

st.divider()

# ── Próximo pedido estimado ───────────────────────────────────────────────────
seccion_titulo("Próximo Pedido Estimado")
proximo = predecir_proximo_pedido(df_mensual_cli, cliente_sel)
if proximo:
    dias = proximo.get("dias_para_pedido", 0)
    fecha_est = proximo.get("fecha_estimada", "—")
    alerta = proximo.get("alerta", False)
    variant = "danger" if alerta else "warning" if dias <= 7 else "success"
    msg = f"Vencido hace {abs(dias)} días" if alerta else f"En {dias} días ({fecha_est})"
    st.markdown(
        f"Fecha estimada: {kpi_badge(msg, variant)}",
        unsafe_allow_html=True,
    )
else:
    st.info("Sin suficiente historial para predecir próximo pedido.")

st.divider()

# ── Estacionalidad ────────────────────────────────────────────────────────────
seccion_titulo("Estacionalidad del Cliente")
estac = calcular_estacionalidad_cliente(df_mensual_cli, cliente_sel)
if not estac.empty:
    _MESES_ES = {1:"Ene",2:"Feb",3:"Mar",4:"Abr",5:"May",6:"Jun",
                 7:"Jul",8:"Ago",9:"Sep",10:"Oct",11:"Nov",12:"Dic"}
    fig = go.Figure(go.Bar(
        x=[_MESES_ES.get(m, str(m)) for m in estac.index],
        y=estac.values,
        marker_color=[COLORS["success"] if v >= 1 else COLORS["danger"] for v in estac.values],
        hovertemplate="Índice: %{y:.3f}<extra></extra>",
    ))
    fig.add_hline(y=1.0, line=dict(color=COLORS["text_light"], width=1.5, dash="dash"))
    fig.update_layout(
        paper_bgcolor=COLORS["surface"], plot_bgcolor=COLORS["surface"],
        font=dict(color=COLORS["text"]),
        xaxis=dict(showgrid=False),
        yaxis=dict(title="Índice (1.0 = promedio)", gridcolor=COLORS["border"]),
        margin=dict(l=40, r=20, t=30, b=40),
        height=280,
    )
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ── Cambio de mix ─────────────────────────────────────────────────────────────
seccion_titulo("Cambio de Mix de Productos")
df_mix = detectar_cambio_mix_cliente(df_mensual_cli, cliente_sel)
if not df_mix.empty:
    from core.components.tables import tabla_ejecutiva
    tabla_ejecutiva(
        df_mix.rename(columns={
            "PRODUCTO": "Producto",
            "SHARE_ACTUAL": "% Actual",
            "SHARE_HIST": "% Histórico",
            "DELTA_PP": "Δ pp",
        }),
        key="cs_cli_mix",
    )
else:
    st.info("Sin cambios significativos de mix detectados.")
