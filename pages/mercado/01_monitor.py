"""
01_monitor.py — Monitor de Quiebres de Mercado — TYASA BI
Detecta movimientos anómalos en variables globales y vincula noticias.
"""

import os, sys
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if _root not in sys.path:
    sys.path.insert(0, _root)

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
from config import COLORS, COLOR_SEQUENCE

from mercado_noticias.loaders import (
    load_variables_mercado,
    load_quiebres_activos,
    load_noticias,
    get_categorias_disponibles,
)
from mercado_noticias.analytics.detector import detectar_quiebres, resumen_quiebres
from mercado_noticias.analytics.noticias import (
    buscar_noticias_quiebre,
    buscar_noticias_actuales,
    buscar_noticias_multifuente,
    get_google_news_url,
)
from core.components.filters import sidebar_header
from core.components.kpi_cards import render_kpi_row, seccion_titulo

# ── Helper: panel de noticias reutilizable ────────────────────────────────────
def _render_panel_noticias(variable: str, color_txt: str, color_bg: str):
    """
    Panel de noticias con:
    - Pestañas de ventana temporal (7d / 14d / 30d)
    - Hasta 10 noticias por ventana
    - Botón directo a Google News
    - Fuente de la noticia visible
    """
    st.markdown("**📰 Noticias relacionadas a este mercado:**")

    col_tabs, col_gnews = st.columns([3, 1])
    with col_gnews:
        gnews_url = get_google_news_url(variable)
        st.markdown(
            f"<a href='{gnews_url}' target='_blank' style='"
            f"display:inline-block;padding:5px 10px;background:{color_txt};"
            f"color:white;border-radius:5px;font-size:11px;text-decoration:none;"
            f"font-weight:600;'>🔍 Más en Google News</a>",
            unsafe_allow_html=True
        )

    tab_7, tab_14, tab_30 = st.tabs(["Últimos 7 días", "Últimos 14 días", "Últimos 30 días"])

    def _render_noticias_lista(noticias: list[dict], c_txt: str, c_bg: str):
        if not noticias:
            st.caption("Sin noticias encontradas en este período.")
            return
        st.caption(f"{len(noticias)} artículo(s) encontrado(s)")
        for n in noticias:
            titulo = n.get("titulo", "") or ""
            desc   = (n.get("descripcion", "") or "")[:220]
            fuente = n.get("fuente", "") or ""
            url    = n.get("url", "") or ""
            fecha  = n.get("fecha_pub", "") or ""
            badge  = n.get("fuente_api", "")
            badge_color = "#1B3A5C" if badge == "Google News" else "#6B7280"
            st.markdown(
                f"""<div style='border-left:3px solid {c_txt};background:{c_bg};
                padding:9px 13px;border-radius:0 6px 6px 0;margin-bottom:7px;'>
                <div style='font-size:12px;font-weight:600;color:{c_txt};
                line-height:1.4;'>{titulo}</div>
                <div style='font-size:11px;color:#444;margin-top:4px;
                line-height:1.4;'>{desc}{'...' if desc else ''}</div>
                <div style='font-size:10px;color:#888;margin-top:5px;
                display:flex;gap:10px;align-items:center;flex-wrap:wrap;'>
                  <span>📅 {fecha}</span>
                  <span>📰 {fuente}</span>
                  <span style='background:{badge_color};color:white;padding:1px 5px;
                  border-radius:3px;font-size:9px;'>{badge}</span>
                  {'<a href="' + url + '" target="_blank" style="color:' + c_txt + ';font-weight:600;">Ver artículo →</a>' if url else ''}
                </div></div>""",
                unsafe_allow_html=True
            )

    with tab_7:
        with st.spinner("Buscando noticias..."):
            noticias_7 = buscar_noticias_multifuente(variable, ventana_dias=7, max_resultados=10)
        _render_noticias_lista(noticias_7, color_txt, color_bg)

    with tab_14:
        with st.spinner("Buscando noticias..."):
            noticias_14 = buscar_noticias_multifuente(variable, ventana_dias=14, max_resultados=12)
        _render_noticias_lista(noticias_14, color_txt, color_bg)

    with tab_30:
        with st.spinner("Buscando noticias..."):
            noticias_30 = buscar_noticias_multifuente(variable, ventana_dias=30, max_resultados=15)
        _render_noticias_lista(noticias_30, color_txt, color_bg)


# ── Sidebar ──────────────────────────────────────────────────────────────────
sidebar_header("Monitor de Mercado", "📡")

categorias = get_categorias_disponibles()
cat_sel = st.sidebar.selectbox(
    "Categoría",
    options=["Todas"] + categorias,
    key="mkt_cat"
)
sev_sel = st.sidebar.selectbox(
    "Severidad mínima",
    options=["Todas", "Crítico", "Alto", "Moderado"],
    key="mkt_sev"
)
umbral_sigma = st.sidebar.slider(
    "Sensibilidad (σ)",
    min_value=1.0, max_value=5.0, value=2.0, step=0.5,
    key="mkt_sigma"
)
st.sidebar.divider()
st.sidebar.caption(
    "**Detección automática** basada en prueba de Chow + z-score.\n\n"
    "σ = desviaciones estándar respecto a la media pre-evento.\n\n"
    "Datos actualizados diariamente desde BigQuery."
)

# ── Encabezado ────────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <h2 style='color:{COLORS["primary"]};margin-bottom:0;'>📡 Monitor de Quiebres de Mercado</h2>
    <p style='color:{COLORS["text_light"]};'>
        Variables siderúrgicas globales · Detección automática · Noticias vinculadas
    </p>
    """,
    unsafe_allow_html=True,
)
st.divider()

# ── Carga de datos ─────────────────────────────────────────────────────────
with st.spinner("Cargando datos de mercado..."):
    df_vars     = load_variables_mercado(dias=400)
    df_quiebres = load_quiebres_activos()

# ── Detección automática en tiempo real ────────────────────────────────────
from mercado_noticias.analytics.detector import detectar_quiebres_automatico

alertas_live = []
if not df_vars.empty:
    alertas_live = detectar_quiebres_automatico(
        df_vars, umbral_sigma=umbral_sigma
    )

# Combinar quiebres históricos de BQ con alertas live
df_filt = df_quiebres.copy() if not df_quiebres.empty else pd.DataFrame()
if not df_filt.empty:
    if cat_sel != "Todas":
        df_filt = df_filt[df_filt["categoria"] == cat_sel]
    if sev_sel != "Todas":
        orden = {"Crítico": 4, "Alto": 3, "Moderado": 2, "Normal": 1}
        nivel_min = orden.get(sev_sel, 1)
        df_filt = df_filt[df_filt["severidad"].map(orden).fillna(0) >= nivel_min]
    if umbral_sigma > 0:
        df_filt = df_filt[df_filt["sigma"].abs() >= umbral_sigma]

# Filtrar alertas live por categoría
alertas_filt = [
    a for a in alertas_live
    if cat_sel == "Todas" or a["categoria"] == cat_sel
]

# ── KPIs ───────────────────────────────────────────────────────────────────
n_total    = len(df_quiebres) if not df_quiebres.empty else 0
n_criticos = len(df_quiebres[df_quiebres["severidad"] == "Crítico"]) if not df_quiebres.empty else 0
n_live     = len(alertas_live)
max_cambio = df_quiebres["cambio_pct"].abs().max() if not df_quiebres.empty else 0

render_kpi_row([
    {"label": "Quiebres históricos",    "value": n_total,    "icon": "📚"},
    {"label": "Históricos críticos",    "value": n_criticos, "icon": "🔴"},
    {"label": "Alertas live (hoy)",     "value": n_live,     "icon": "⚡",
     "help_text": f"Variables que superan {umbral_sigma}σ en los últimos 5 días hábiles"},
    {"label": "Mayor cambio histórico", "value": round(max_cambio, 1), "suffix": "%", "icon": "📈"},
])
st.divider()

# ══════════════════════════════════════════════════════════════════════════
# SECCIÓN A — ALERTAS EN TIEMPO REAL
# ══════════════════════════════════════════════════════════════════════════
if alertas_filt:
    seccion_titulo(
        f"⚡ Alertas detectadas ahora ({len(alertas_filt)})",
        "Variables que muestran comportamiento anómalo en los últimos 5 días hábiles"
    )
    for alerta in alertas_filt[:10]:
        var      = alerta["variable"]
        sigma_a  = alerta["sigma_actual"]
        sev      = alerta["severidad"]
        cambio7  = alerta["cambio_7d_pct"]
        val_act  = alerta["valor_actual"]
        mu_base  = alerta["media_base"]
        tend     = alerta["tendencia"]
        cat      = alerta["categoria"]
        fecha_d  = alerta["fecha_deteccion"]

        SEV_COLORS = {
            "Crítico":  ("#C0392B", "#FCEBEB"),
            "Alto":     ("#D68910", "#FAEEDA"),
            "Moderado": ("#185FA5", "#E6F1FB"),
        }
        color_txt, color_bg = SEV_COLORS.get(sev, ("#6B7280", "#F3F4F6"))
        flecha = "↑" if tend == "sube" else "↓"

        with st.expander(
            f"**{var.replace('_',' ')}** — {flecha} {cambio7:+.1f}% (7d) · {sigma_a:+.2f}σ · {sev}",
            expanded=False
        ):
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Sigma actual",   f"{sigma_a:+.2f}σ")
            col2.metric("Cambio 7 días",  f"{cambio7:+.1f}%")
            col3.metric("Valor actual",   f"{val_act:,.2f}")
            col4.metric("Media base",     f"{mu_base:,.2f}")

            st.markdown(
                f"<div style='background:{color_bg};border-left:4px solid {color_txt};"
                f"border-radius:6px;padding:8px 14px;margin:6px 0;font-size:13px;'>"
                f"<b>Categoría:</b> {cat} &nbsp;|&nbsp; "
                f"<b>Última observación:</b> {pd.Timestamp(fecha_d).strftime('%d %b %Y')}"
                f"</div>",
                unsafe_allow_html=True
            )

            # Gráfica de la serie reciente
            df_var = df_vars[df_vars["nombre"] == var].sort_values("fecha")
            if not df_var.empty:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df_var["fecha"], y=df_var["valor"],
                    line=dict(color=COLORS["primary"], width=1.8),
                    hovertemplate="%{x|%d %b %Y}<br>%{y:,.2f}<extra></extra>",
                    name=var.replace("_", " ")
                ))
                # Banda de alerta (media ± umbral*std)
                std_val = df_var["valor"].std()
                fig.add_hrect(
                    y0=mu_base - umbral_sigma * std_val,
                    y1=mu_base + umbral_sigma * std_val,
                    fillcolor="rgba(27,58,92,0.07)", line_width=0,
                    annotation_text=f"Rango normal (±{umbral_sigma}σ)",
                    annotation_position="top left",
                    annotation_font_size=9,
                )
                fig.update_layout(
                    paper_bgcolor=COLORS["surface"],
                    plot_bgcolor=COLORS["background"],
                    font=dict(family="Inter, Arial, sans-serif",
                              color=COLORS["text"]),
                    margin=dict(l=40, r=20, t=30, b=40),
                    height=220, showlegend=False,
                    xaxis=dict(showgrid=False),
                    yaxis=dict(gridcolor="#E5E7EB"),
                )
                st.plotly_chart(fig, use_container_width=True)

            # ── Panel de noticias mejorado ─────────────────────────────────
            _render_panel_noticias(var, color_txt, color_bg)

    st.divider()
else:
    st.info(
        f"No hay alertas activas con el umbral de {umbral_sigma}σ. "
        "Reduce la sensibilidad en el sidebar para ver más variables."
    )

# ══════════════════════════════════════════════════════════════════════════
# SECCIÓN B — QUIEBRES HISTÓRICOS (eventos pasados documentados)
# ══════════════════════════════════════════════════════════════════════════
seccion_titulo(
    "📚 Quiebres históricos documentados",
    "Eventos pasados con quiebre estadístico confirmado · Haz clic para ver el detalle"
)

if df_filt.empty:
    st.info("No hay quiebres históricos con los filtros actuales.")
else:
    for _, row in df_filt.iterrows():
        var    = row.get("variable", "")
        sev    = row.get("severidad", "Normal")
        sigma  = row.get("sigma", 0) or 0
        cambio = row.get("cambio_pct", 0) or 0
        F_stat = row.get("F_stat", None)
        p_val  = row.get("p_value", None)
        m_pre  = row.get("media_pre", None)
        m_post = row.get("media_post", None)
        cat    = row.get("categoria", "")
        q_id   = row.get("id", "")
        fc     = row.get("fecha_corte", None)

        SEV_C = {
            "Crítico":     ("#C0392B", "#FCEBEB"),
            "Alto":        ("#D68910", "#FAEEDA"),
            "Moderado":    ("#185FA5", "#E6F1FB"),
            "Normal":      ("#6B7280", "#F3F4F6"),
            "Sin quiebre": ("#6B7280", "#F3F4F6"),
        }
        color_txt, color_bg = SEV_C.get(sev, ("#6B7280", "#F3F4F6"))
        chg_color = COLORS["danger"] if cambio > 0 else COLORS["success"]
        chg_str   = f"{cambio:+.1f}%"

        with st.expander(
            f"**{var.replace('_', ' ')}** — {chg_str} · {sigma:+.2f}σ · {sev} "
            f"· {'📅 ' + fc.strftime('%d %b %Y') if fc is not None else ''}",
            expanded=False
        ):
            col_a, col_b, col_c, col_d = st.columns(4)
            col_a.metric("Cambio %",  chg_str)
            col_b.metric("Sigma (σ)", f"{sigma:+.2f}σ")
            col_c.metric("F-stat",    f"F={F_stat:.1f}" if F_stat else "—")
            col_d.metric("p-value",   f"p={p_val:.4f}"  if p_val is not None else "—")

            if m_pre is not None and m_post is not None:
                st.markdown(
                    f"<div style='background:{color_bg};border-left:4px solid {color_txt};"
                    f"border-radius:6px;padding:8px 14px;margin:6px 0;font-size:13px;'>"
                    f"<b>Media pre:</b> {m_pre:,.2f} → "
                    f"<b style='color:{chg_color};'>Post: {m_post:,.2f} {chg_str}</b>"
                    f"&nbsp;|&nbsp;<b>Categoría:</b> {cat}"
                    f"</div>",
                    unsafe_allow_html=True
                )

            # Gráfica histórica
            df_var_h = df_vars[df_vars["nombre"] == var].sort_values("fecha") if not df_vars.empty else pd.DataFrame()
            if not df_var_h.empty and fc is not None:
                fc_ts = pd.Timestamp(fc)
                pre_s = df_var_h[df_var_h["fecha"] <  fc_ts]
                pos_s = df_var_h[df_var_h["fecha"] >= fc_ts]
                fig2  = go.Figure()
                if not pre_s.empty:
                    fig2.add_trace(go.Scatter(
                        x=pre_s["fecha"], y=pre_s["valor"],
                        line=dict(color=COLORS["primary"], width=1.5),
                        opacity=0.6, name="Pre-evento",
                    ))
                if not pos_s.empty:
                    fig2.add_trace(go.Scatter(
                        x=pos_s["fecha"], y=pos_s["valor"],
                        line=dict(color=COLORS["danger"], width=2.2),
                        name="Post-evento",
                    ))
                    fig2.add_vrect(
                        x0=str(fc_ts.date()),
                        x1=str(pos_s["fecha"].max().date()),
                        fillcolor="rgba(192,57,43,0.06)",
                        line_width=0,
                    )
                fig2.update_layout(
                    paper_bgcolor=COLORS["surface"],
                    plot_bgcolor=COLORS["background"],
                    font=dict(family="Inter", size=9, color=COLORS["text"]),
                    margin=dict(l=40, r=20, t=25, b=35),
                    height=220, showlegend=False,
                    xaxis=dict(showgrid=False),
                    yaxis=dict(gridcolor="#E5E7EB"),
                )
                st.plotly_chart(fig2, use_container_width=True)

            # ── Panel de noticias mejorado ─────────────────────────────────
            _render_panel_noticias(var, color_txt, color_bg)
