"""
01_monitor.py — Monitor de Quiebres de Mercado — TYASA BI
Alertas en tiempo real · Análisis IA · Chat · Explorar variable
"""
import os, sys
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if _root not in sys.path:
    sys.path.insert(0, _root)

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from config import COLORS

from mercado_noticias.loaders import load_variables_mercado, get_categorias_disponibles
from mercado_noticias.analytics.detector import detectar_quiebres_automatico
from mercado_noticias.analytics.noticias import (
    buscar_noticias_multifuente, get_google_news_url, QUERIES
)
from mercado_noticias.analytics.ai_analysis import (
    analizar_alerta, _call_gemini_text,
    _cache_key, _cache_load,
)
from core.components.filters import sidebar_header
from core.components.kpi_cards import render_kpi_row, seccion_titulo

# ── API key ───────────────────────────────────────────────────────────────────
try:
    _GEMINI_KEY = st.secrets["GEMINI_API_KEY"]
except Exception:
    _GEMINI_KEY = ""

# ── Paleta de severidad ───────────────────────────────────────────────────────
SEV_COLORS = {
    "Crítico":  ("#C0392B", "#FCEBEB"),
    "Alto":     ("#D68910", "#FAEEDA"),
    "Moderado": ("#185FA5", "#E6F1FB"),
}
SEV_ORDEN = {"Crítico": 4, "Alto": 3, "Moderado": 2, "Normal": 1}


# ════════════════════════════════════════════════════════════════════════════
# HELPERS (solo HTML puro — cero componentes Streamlit condicionales)
# ════════════════════════════════════════════════════════════════════════════

def _ai_html(result: dict | None, color_txt: str) -> str:
    """Convierte resultado de IA a HTML. Retorna '' si no hay resultado."""
    if not result:
        return ""
    D_ICO = {"Oferta":"🏭","Demanda":"📊","Geopolitica":"🌍","Macro":"🏦","Sectorial":"⚙️"}
    S_ICO = {"Alcista":"📈","Bajista":"📉","Neutral":"➡️"}
    C_COL = {"Alta":"#2E7D32","Media":"#D68910","Baja":"#C62828"}
    d  = result.get("driver_principal","—")
    s  = result.get("sentimiento","—")
    c  = result.get("confianza","—")
    ca = result.get("_cached", False)
    di = D_ICO.get(d,"🔍"); si = S_ICO.get(s,"➡️"); cc = C_COL.get(c,"#6B7280")
    cb = '<span style="background:#F3F4F6;color:#888;padding:2px 7px;border-radius:8px;font-size:10px;margin-left:4px;">💾</span>' if ca else ""
    err = result.get("_error","")
    eh  = f"<div style='color:#C62828;font-size:11px;margin-bottom:4px;'>⚠️ {err}</div>" if err else ""
    badges = (
        f"<div style='display:flex;gap:6px;flex-wrap:wrap;margin:8px 0;'>"
        f"<span style='background:#EEF2FF;color:#3730A3;padding:3px 8px;border-radius:20px;font-size:11px;font-weight:600;'>{di} {d}</span>"
        f"<span style='background:#F0FDF4;color:#166534;padding:3px 8px;border-radius:20px;font-size:11px;font-weight:600;'>{si} {s}</span>"
        f"<span style='background:#FFF7ED;color:{cc};padding:3px 8px;border-radius:20px;font-size:11px;font-weight:600;'>✓ {c}</span>"
        f"{cb}</div>"
    )
    puntos = result.get("puntos_clave",[])
    items  = "".join(
        f"<div style='border-left:3px solid {color_txt};padding:4px 10px;margin-bottom:4px;"
        f"font-size:12px;background:#FAFAFA;border-radius:0 4px 4px 0;'><b>{i}.</b> {p}</div>"
        for i, p in enumerate(puntos[:5], 1)
    ) if puntos else ""
    pkh = f"<b style='font-size:12px;'>Puntos clave:</b>{items}" if items else ""
    imp = result.get("impacto_tyasa","")
    imph = (
        f"<div style='background:#EFF6FF;border:1px solid #BFDBFE;border-radius:5px;"
        f"padding:8px 12px;margin-top:6px;font-size:12px;color:#1E40AF;'>"
        f"🏭 <b>Impacto TYASA:</b> {imp}</div>"
    ) if imp and imp != "—" else ""
    return (
        f"<div style='margin:8px 0;padding:10px;background:#F9FAFB;"
        f"border-radius:6px;border:1px solid #E5E7EB;'>{eh}{badges}{pkh}{imph}</div>"
    )


def _news_card_html(n: dict, c_txt: str, c_bg: str) -> str:
    titulo = (n.get("titulo","") or "")
    desc   = (n.get("descripcion","") or "")[:200]
    fuente = (n.get("fuente","") or "")
    url    = (n.get("url","") or "")
    fecha  = (n.get("fecha_pub","") or "")
    badge  = n.get("fuente_api","")
    bc     = "#1B3A5C" if badge == "Google News" else "#6B7280"
    link   = (f'<a href="{url}" target="_blank" style="color:{c_txt};font-weight:600;'
              f'font-size:11px;text-decoration:none;">Ver →</a>') if url else ""
    return (
        f"<div style='border-left:3px solid {c_txt};background:{c_bg};"
        f"padding:8px 12px;border-radius:0 5px 5px 0;margin-bottom:6px;'>"
        f"<div style='font-size:12px;font-weight:600;color:{c_txt};line-height:1.4;'>{titulo}</div>"
        f"<div style='font-size:11px;color:#444;margin-top:3px;line-height:1.4;'>{desc}</div>"
        f"<div style='font-size:10px;color:#888;margin-top:4px;display:flex;gap:8px;"
        f"flex-wrap:wrap;align-items:center;'>"
        f"📅 {fecha} · 📰 {fuente} "
        f"<span style='background:{bc};color:white;padding:1px 5px;border-radius:3px;"
        f"font-size:9px;'>{badge}</span> {link}</div></div>"
    )


# ════════════════════════════════════════════════════════════════════════════
# COMPONENTES REUTILIZABLES (componentes Streamlit estables)
# ════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=900, show_spinner=False)
def _noticias_var_cached(variable: str, max_r: int = 10) -> list[dict]:
    """Caché 15 min por variable. Evita llamadas HTTP repetidas en cada rerender."""
    return buscar_noticias_multifuente(variable, ventana_dias=7, max_resultados=max_r)


def _render_ai_inline(var: str, sigma_a: float, cambio7: float,
                       val_act: float, mu_base: float, tend: str,
                       color_txt: str):
    """
    AI inline dentro del expander.
    Exactamente 1 st.button + 1 st.markdown — árbol DOM estable.
    Sin st.spinner, sin condicionales de árbol.
    """
    if not _GEMINI_KEY:
        return
    skey = f"ai_{var}_{round(sigma_a, 1)}"
    if st.button("🤖 Análisis IA", key=f"aibtn_{var}"):
        nots = _noticias_var_cached(variable=var)
        st.session_state[skey] = analizar_alerta(
            variable=var, sigma=sigma_a, cambio7=cambio7,
            valor=val_act, media_base=mu_base, tendencia=tend,
            noticias=nots, api_key=_GEMINI_KEY,
            scrape_articles=False, force_refresh=False,
        )
    result = st.session_state.get(skey)
    if result is None:
        disk = _cache_load(_cache_key(var, sigma_a))
        if disk:
            disk["_cached"] = True
            st.session_state[skey] = disk
            result = disk
    st.markdown(_ai_html(result, color_txt), unsafe_allow_html=True)


def _render_noticias_tabs(variable: str, color_txt: str, color_bg: str):
    """Noticias últimos 7 días (sin tabs — una sola llamada HTTP cacheada)."""
    col_t, col_g = st.columns([3, 1])
    with col_g:
        st.markdown(
            f"<a href='{get_google_news_url(variable)}' target='_blank' style='"
            f"display:inline-block;padding:5px 10px;background:{color_txt};color:white;"
            f"border-radius:5px;font-size:11px;text-decoration:none;font-weight:600;'>"
            f"🔍 Google News</a>",
            unsafe_allow_html=True
        )
    nots = _noticias_var_cached(variable)
    if not nots:
        st.caption("Sin noticias en los últimos 7 días.")
        return
    st.caption(f"{len(nots)} artículo(s) · últimos 7 días")
    html = "".join(_news_card_html(n, color_txt, color_bg) for n in nots)
    st.markdown(html, unsafe_allow_html=True)


def _render_chart(df_vars: pd.DataFrame, var: str,
                  mu_base: float, umbral_sigma: float, color: str = "#1B3A5C"):
    df_var = df_vars[df_vars["nombre"] == var].sort_values("fecha")
    if df_var.empty:
        return
    std_val = df_var["valor"].std()
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_var["fecha"], y=df_var["valor"],
        line=dict(color=color, width=1.8),
        hovertemplate="%{x|%d %b %Y}<br>%{y:,.2f}<extra></extra>",
        name=var.replace("_", " ")
    ))
    fig.add_hrect(
        y0=mu_base - umbral_sigma * std_val,
        y1=mu_base + umbral_sigma * std_val,
        fillcolor="rgba(27,58,92,0.07)", line_width=0,
        annotation_text=f"Rango normal (±{umbral_sigma}σ)",
        annotation_position="top left", annotation_font_size=9,
    )
    fig.update_layout(
        paper_bgcolor=COLORS["surface"], plot_bgcolor=COLORS["background"],
        font=dict(family="Inter, Arial, sans-serif", color=COLORS["text"]),
        margin=dict(l=40, r=20, t=30, b=40),
        height=220, showlegend=False,
        xaxis=dict(showgrid=False), yaxis=dict(gridcolor="#E5E7EB"),
    )
    st.plotly_chart(fig, use_container_width=True)


# ════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════════════════════════
sidebar_header("Monitor de Mercado", "📡")
categorias    = get_categorias_disponibles()
cat_sel       = st.sidebar.selectbox("Categoría", ["Todas"] + categorias, key="mkt_cat")
sev_sel       = st.sidebar.selectbox("Severidad mínima", ["Todas","Crítico","Alto","Moderado"], key="mkt_sev")
umbral_sigma  = st.sidebar.slider("Sensibilidad (σ)", 1.0, 5.0, 2.0, 0.5, key="mkt_sigma")
st.sidebar.divider()
st.sidebar.caption(
    "Detección automática z-score respecto a la media pre-evento.\n\n"
    "Datos actualizados diariamente desde BigQuery."
)

# ════════════════════════════════════════════════════════════════════════════
# HEADER
# ════════════════════════════════════════════════════════════════════════════
st.markdown(
    f"<h2 style='color:{COLORS['primary']};margin-bottom:0;'>📡 Monitor de Quiebres de Mercado</h2>"
    f"<p style='color:#6B7280;'>Variables siderúrgicas globales · Detección automática · "
    f"Noticias vinculadas · Análisis IA</p>",
    unsafe_allow_html=True,
)
st.divider()

# ════════════════════════════════════════════════════════════════════════════
# DATA
# ════════════════════════════════════════════════════════════════════════════
with st.spinner("Cargando datos de mercado..."):
    df_vars = load_variables_mercado(dias=400)

alertas_live: list[dict] = []
if not df_vars.empty:
    alertas_live = detectar_quiebres_automatico(df_vars, umbral_sigma=umbral_sigma)

nivel_min = SEV_ORDEN.get(sev_sel, 1) if sev_sel != "Todas" else 0
alertas_filt = [
    a for a in alertas_live
    if (cat_sel == "Todas" or a["categoria"] == cat_sel)
    and SEV_ORDEN.get(a["severidad"], 1) >= nivel_min
]

# ── KPIs ───────────────────────────────────────────────────────────────────
n_crit = sum(1 for a in alertas_live if a["severidad"] == "Crítico")
n_alto = sum(1 for a in alertas_live if a["severidad"] == "Alto")
n_mod  = sum(1 for a in alertas_live if a["severidad"] == "Moderado")
render_kpi_row([
    {"label": "Alertas activas",    "value": len(alertas_live), "icon": "⚡",
     "help_text": f"Variables superando {umbral_sigma}σ en los últimos 5 días hábiles"},
    {"label": "Críticas",           "value": n_crit,            "icon": "🔴"},
    {"label": "Altas",              "value": n_alto,            "icon": "🟠"},
    {"label": "Moderadas",          "value": n_mod,             "icon": "🟡"},
])
st.divider()

# ════════════════════════════════════════════════════════════════════════════
# SECCIÓN A — ALERTAS EN TIEMPO REAL
# ════════════════════════════════════════════════════════════════════════════
if alertas_filt:
    seccion_titulo(
        f"⚡ Alertas detectadas ({len(alertas_filt)})",
        "Variables con comportamiento anómalo en los últimos 5 días hábiles"
    )
    for alerta in alertas_filt[:10]:
        var     = alerta["variable"]
        sigma_a = alerta["sigma_actual"]
        sev     = alerta["severidad"]
        cambio7 = alerta["cambio_7d_pct"]
        val_act = alerta["valor_actual"]
        mu_base = alerta["media_base"]
        tend    = alerta["tendencia"]
        cat     = alerta["categoria"]
        fecha_d = alerta["fecha_deteccion"]

        color_txt, color_bg = SEV_COLORS.get(sev, ("#6B7280", "#F3F4F6"))
        flecha = "↑" if tend == "sube" else "↓"
        sev_badge = f"<span style='background:{color_txt};color:white;padding:2px 8px;border-radius:12px;font-size:11px;font-weight:700;'>{sev}</span>"

        with st.expander(
            f"**{var.replace('_',' ')}** — {flecha} {cambio7:+.1f}% (7d) · {sigma_a:+.2f}σ · {sev}",
            expanded=False
        ):
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Sigma actual",  f"{sigma_a:+.2f}σ")
            col2.metric("Cambio 7 días", f"{cambio7:+.1f}%")
            col3.metric("Valor actual",  f"{val_act:,.2f}")
            col4.metric("Media base",    f"{mu_base:,.2f}")

            st.markdown(
                f"<div style='background:{color_bg};border-left:4px solid {color_txt};"
                f"border-radius:6px;padding:8px 14px;margin:6px 0;font-size:13px;'>"
                f"<b>Categoría:</b> {cat} &nbsp;|&nbsp; "
                f"<b>Última observación:</b> {pd.Timestamp(fecha_d).strftime('%d %b %Y')}"
                f"</div>",
                unsafe_allow_html=True
            )

            # Gráfica
            _render_chart(df_vars, var, mu_base, umbral_sigma, color_txt)

            # ── AI inline (1 button + 1 markdown — DOM estable) ───────────
            if sev in ("Crítico", "Alto"):
                st.markdown(
                    f"<div style='border-top:1px solid #E5E7EB;margin:10px 0 6px;'></div>",
                    unsafe_allow_html=True
                )
                col_ai, col_chat = st.columns([1, 1])
                with col_ai:
                    _render_ai_inline(var, sigma_a, cambio7, val_act, mu_base, tend, color_txt)
                with col_chat:
                    if st.button("💬 Preguntar al analista", key=f"chat_open_{var}"):
                        st.session_state["chat_var"] = var
                        st.session_state["chat_alerta"] = alerta
                        if f"chat_msgs_{var}" not in st.session_state:
                            st.session_state[f"chat_msgs_{var}"] = []

            # Noticias
            st.markdown("**📰 Noticias relacionadas:**")
            _render_noticias_tabs(var, color_txt, color_bg)

    st.divider()

else:
    st.info(
        f"No hay alertas activas con umbral {umbral_sigma}σ. "
        "Reduce la sensibilidad en el sidebar para ver más variables."
    )
    st.divider()


# ════════════════════════════════════════════════════════════════════════════
# SECCIÓN B — EXPLORAR VARIABLE
# Permite ver tendencia, noticias y análisis IA de cualquier variable
# sin necesidad de que esté en alerta
# ════════════════════════════════════════════════════════════════════════════
seccion_titulo(
    "🔍 Explorar Variable de Mercado",
    "Selecciona cualquier variable para ver su tendencia, noticias y análisis IA"
)

all_vars   = sorted(QUERIES.keys())
var_expl   = st.selectbox("Variable", all_vars, key="expl_var",
                           format_func=lambda v: v.replace("_", " "))

df_expl    = df_vars[df_vars["nombre"] == var_expl].sort_values("fecha") if not df_vars.empty else pd.DataFrame()
color_expl = COLORS["primary"]

if not df_expl.empty:
    mu_expl = float(df_expl["valor"].iloc[:-45].mean()) if len(df_expl) > 50 else float(df_expl["valor"].mean())
    val_expl = float(df_expl["valor"].iloc[-1])
    sigma_expl_val = float(
        (df_expl["valor"].iloc[-5:].mean() - mu_expl) / (df_expl["valor"].iloc[:-45].std() + 1e-9)
    ) if len(df_expl) > 50 else 0.0
    cambio_expl = float(
        (df_expl["valor"].iloc[-1] / df_expl["valor"].iloc[-8] - 1) * 100
    ) if len(df_expl) >= 8 else 0.0

    col_e1, col_e2, col_e3 = st.columns(3)
    col_e1.metric("Valor actual",    f"{val_expl:,.2f}")
    col_e2.metric("Cambio 7 días",   f"{cambio_expl:+.1f}%")
    col_e3.metric("Sigma vs base",   f"{sigma_expl_val:+.2f}σ")

    _render_chart(df_expl.assign(nombre=var_expl), var_expl, mu_expl, umbral_sigma, color_expl)
else:
    mu_expl       = 0.0
    sigma_expl_val = 0.0
    cambio_expl   = 0.0
    st.info("Sin datos para esta variable.")

# AI para variable explorada — fuera de expander/loop → DOM estable
if _GEMINI_KEY:
    skey_expl = f"ai_{var_expl}_{round(sigma_expl_val, 1)}"
    col_btn_e, col_frz_e = st.columns([1, 2])
    with col_btn_e:
        run_expl = st.button("🤖 Análisis IA", key="expl_ai_btn")
    with col_frz_e:
        frz_expl = st.checkbox("Regenerar (ignorar caché)", key="expl_ai_chk")
    if run_expl:
        nots_expl = _noticias_var_cached(var_expl)
        st.session_state[skey_expl] = analizar_alerta(
            variable=var_expl, sigma=sigma_expl_val, cambio7=cambio_expl,
            valor=val_expl if not df_expl.empty else 0.0,
            media_base=mu_expl, tendencia="sube" if cambio_expl > 0 else "baja",
            noticias=nots_expl, api_key=_GEMINI_KEY,
            scrape_articles=False, force_refresh=frz_expl,
        )
    res_expl = st.session_state.get(skey_expl) or _cache_load(_cache_key(var_expl, sigma_expl_val))
    st.markdown(_ai_html(res_expl, color_expl), unsafe_allow_html=True)

st.markdown("**📰 Noticias:**")
_render_noticias_tabs(var_expl, color_expl, "#EBF5FB")
st.divider()


# ════════════════════════════════════════════════════════════════════════════
# SECCIÓN C — CHAT CON EL ANALISTA
# Se activa al pulsar "💬 Preguntar" en cualquier alerta.
# Colocado aquí (fuera de loops/expanders) para evitar el NotFoundError.
# ════════════════════════════════════════════════════════════════════════════
chat_var    = st.session_state.get("chat_var")
chat_alerta = st.session_state.get("chat_alerta", {})

if chat_var and _GEMINI_KEY:
    color_chat, bg_chat = SEV_COLORS.get(
        chat_alerta.get("severidad","Moderado"), ("#185FA5","#E6F1FB")
    )
    seccion_titulo(
        f"💬 Chat · {chat_var.replace('_',' ')}",
        f"Conversa con el analista de IA sobre esta alerta · {chat_alerta.get('severidad','')} "
        f"({chat_alerta.get('sigma_actual', 0):+.2f}σ)"
    )

    chat_key = f"chat_msgs_{chat_var}"
    if chat_key not in st.session_state:
        st.session_state[chat_key] = []

    # Contexto de la alerta para el LLM
    _ctx = (
        f"Variable: {chat_var.replace('_',' ')} | Sigma: {chat_alerta.get('sigma_actual',0):+.2f}σ "
        f"({chat_alerta.get('severidad','')}) | Cambio 7d: {chat_alerta.get('cambio_7d_pct',0):+.1f}% | "
        f"Valor: {chat_alerta.get('valor_actual',0):,.2f} | Base: {chat_alerta.get('media_base',0):,.2f} | "
        f"Tendencia: {chat_alerta.get('tendencia','')}"
    )

    # Mostrar historial
    messages = st.session_state[chat_key]
    with st.container(height=380):
        if not messages:
            st.markdown(
                f"<div style='text-align:center;color:#9CA3AF;padding:40px;font-size:13px;'>"
                f"Escribe una pregunta sobre <b>{chat_var.replace('_',' ')}</b> "
                f"para iniciar la conversación.</div>",
                unsafe_allow_html=True
            )
        for msg in messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # Input de chat (inline — no floating)
    prompt = st.chat_input(
        f"Pregunta sobre {chat_var.replace('_',' ')}...",
        key=f"chat_input_{chat_var}"
    )
    if prompt:
        messages.append({"role": "user", "content": prompt})
        # Construir prompt con contexto + historial
        hist_txt = "\n".join(
            f"{'Analista' if m['role']=='assistant' else 'Usuario'}: {m['content']}"
            for m in messages[:-1]
        )
        full_prompt = (
            f"Contexto de alerta: {_ctx}\n\n"
            f"{'Conversación previa:\n' + hist_txt if hist_txt else ''}\n\n"
            f"Usuario: {prompt}"
        )
        resp_txt = _call_gemini_text(full_prompt, _GEMINI_KEY)
        messages.append({"role": "assistant", "content": resp_txt})
        st.session_state[chat_key] = messages
        st.rerun()

    if st.button("🗑 Limpiar conversación", key="chat_clear"):
        st.session_state[chat_key] = []
        st.session_state["chat_var"] = None
        st.rerun()
