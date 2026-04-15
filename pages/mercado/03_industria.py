"""
03_industria.py — Monitor de la Industria Siderúrgica — TYASA BI
Noticias especializadas · Síntesis IA · Análisis de tendencias globales
"""
import os, sys
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if _root not in sys.path:
    sys.path.insert(0, _root)

import datetime
import streamlit as st
from config import COLORS
from mercado_noticias.analytics.noticias import buscar_noticias_industria, GRUPOS_INDUSTRIA
from mercado_noticias.analytics.ai_analysis import sintesis_industrial, _call_gemini_text
from core.components.filters import sidebar_header
from core.components.kpi_cards import seccion_titulo

# ── API key ───────────────────────────────────────────────────────────────────
try:
    _GEMINI_KEY = st.secrets["GEMINI_API_KEY"]
except Exception:
    _GEMINI_KEY = ""

# ── Paleta de grupos ──────────────────────────────────────────────────────────
GRUPO_STYLE: dict[str, tuple[str, str]] = {
    "Urgente":    ("#DC2626", "#FEE2E2"),
    "Tendencias": ("#059669", "#D1FAE5"),
    "Empresas":   ("#2563EB", "#DBEAFE"),
    "Insumos":    ("#D97706", "#FEF3C7"),
    "Tecnología": ("#7C3AED", "#EDE9FE"),
}
ALERTA_STYLE: dict[str, tuple[str, str]] = {
    "Alto":  ("#DC2626", "#FEE2E2"),
    "Medio": ("#D97706", "#FEF3C7"),
    "Bajo":  ("#059669", "#D1FAE5"),
}

# ════════════════════════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=1800, show_spinner=False)
def _noticias_grupo(grupo: str, max_r: int = 14) -> list[dict]:
    return buscar_noticias_industria(grupo, max_resultados=max_r)


def _filtrar_por_fecha(noticias: list[dict], desde: str, hasta: str) -> list[dict]:
    """Filtra por fecha_pub ('YYYY-MM-DD'). Mantiene artículos sin fecha."""
    out = []
    for n in noticias:
        fp = (n.get("fecha_pub") or "")[:10]
        if not fp or (desde <= fp <= hasta):
            out.append(n)
    return out


def _render_news_card(n: dict, grupo: str) -> str:
    """Card HTML estilo noticiero premium para la industria siderúrgica."""
    c_txt, c_bg = GRUPO_STYLE.get(grupo, ("#374151", "#F9FAFB"))
    titulo = (n.get("titulo", "") or "").strip()
    desc   = (n.get("descripcion", "") or "").strip()[:220]
    fuente = (n.get("fuente", "") or "").strip()
    url    = (n.get("url", "") or "").strip()
    fecha  = (n.get("fecha_pub", "") or "").strip()
    badge  = n.get("fuente_api", "")
    bc     = "#1B3A5C" if badge == "Google News" else "#6B7280"
    link   = (f'<a href="{url}" target="_blank" style="color:{c_txt};font-weight:700;'
              f'font-size:12px;text-decoration:none;">Leer artículo →</a>') if url else ""
    return (
        f"<div style='border:1px solid #E5E7EB;border-radius:10px;padding:16px;"
        f"background:white;box-shadow:0 1px 4px rgba(0,0,0,0.06);margin-bottom:12px;"
        f"transition:box-shadow 0.2s;'>"
        # Header: badge grupo + fecha
        f"<div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;'>"
        f"<span style='font-size:10px;font-weight:700;letter-spacing:0.06em;"
        f"background:{c_bg};color:{c_txt};padding:3px 10px;border-radius:20px;'>{grupo.upper()}</span>"
        f"<span style='font-size:11px;color:#9CA3AF;'>📅 {fecha}</span>"
        f"</div>"
        # Título
        f"<div style='font-size:14px;font-weight:700;color:#111827;line-height:1.45;"
        f"margin-bottom:8px;'>{titulo}</div>"
        # Descripción
        f"<div style='font-size:12px;color:#6B7280;line-height:1.55;margin-bottom:12px;'>{desc}</div>"
        # Footer: fuente + badge + link
        f"<div style='display:flex;justify-content:space-between;align-items:center;"
        f"padding-top:10px;border-top:1px solid #F3F4F6;'>"
        f"<span style='font-size:11px;color:#9CA3AF;display:flex;gap:6px;align-items:center;'>"
        f"📰 {fuente} "
        f"<span style='background:{bc};color:white;padding:1px 6px;border-radius:4px;font-size:9px;'>{badge}</span>"
        f"</span>"
        f"{link}"
        f"</div></div>"
    )


def _sintesis_card(titulo: str, texto: str, c_txt: str, c_bg: str, icon: str) -> str:
    return (
        f"<div style='background:{c_bg};border:1px solid {c_txt}33;border-radius:10px;"
        f"padding:16px;height:100%;min-height:120px;'>"
        f"<div style='font-size:11px;font-weight:800;letter-spacing:0.07em;color:{c_txt};"
        f"margin-bottom:10px;'>{icon} {titulo.upper()}</div>"
        f"<div style='font-size:13px;color:#374151;line-height:1.6;'>{texto}</div>"
        f"</div>"
    )


# ════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════════════════════════
sidebar_header("Industria Siderúrgica", "🏭")
st.sidebar.caption(
    "Noticias especializadas del sector acero México y global.\n\n"
    "Fuentes: Google News · worldsteel · CANACERO · reportacero\n\n"
    "Caché de noticias: 30 min · Síntesis IA: 24 h"
)

# ════════════════════════════════════════════════════════════════════════════
# HEADER
# ════════════════════════════════════════════════════════════════════════════
st.markdown(
    f"<h2 style='color:{COLORS['primary']};margin-bottom:0;'>🏭 Monitor de la Industria Siderúrgica</h2>"
    f"<p style='color:#6B7280;'>Noticias especializadas en tiempo real · Síntesis IA · "
    f"Tendencias México y global</p>",
    unsafe_allow_html=True,
)
st.divider()

# ════════════════════════════════════════════════════════════════════════════
# SECCIÓN A — SÍNTESIS INDUSTRIAL IA
# ════════════════════════════════════════════════════════════════════════════
seccion_titulo(
    "🤖 Síntesis Industrial",
    "Resumen ejecutivo generado por IA con las noticias más recientes del sector"
)

col_btn_s, col_frz_s, col_info_s = st.columns([1, 1, 3])
with col_btn_s:
    run_sint = st.button("▶ Generar síntesis", key="sint_run")
with col_frz_s:
    frz_sint = st.checkbox("Regenerar", key="sint_frz", value=False)
with col_info_s:
    st.caption("Análisis de Impacto en Precios · Tendencias México · Riesgos Globales · Caché 24 h")

if run_sint and _GEMINI_KEY:
    with st.spinner("Consultando noticias y generando síntesis..."):
        noticias_todos = {g: _noticias_grupo(g, 8) for g in GRUPOS_INDUSTRIA}
        sint = sintesis_industrial(noticias_todos, _GEMINI_KEY, force_refresh=frz_sint)
    st.session_state["sint_result"] = sint
elif run_sint and not _GEMINI_KEY:
    st.warning("Configura GEMINI_API_KEY en .streamlit/secrets.toml")

sint_result = st.session_state.get("sint_result")
if sint_result:
    nivel = sint_result.get("nivel_alerta", "—")
    nc_txt, nc_bg = ALERTA_STYLE.get(nivel, ("#6B7280", "#F3F4F6"))
    cached_s = sint_result.get("_cached", False)

    st.markdown(
        f"<div style='display:flex;gap:10px;align-items:center;margin-bottom:14px;'>"
        f"<span style='background:{nc_bg};color:{nc_txt};padding:4px 14px;border-radius:20px;"
        f"font-size:12px;font-weight:700;'>Nivel de alerta: {nivel}</span>"
        f"{'<span style=\"background:#F3F4F6;color:#6B7280;padding:4px 10px;border-radius:20px;font-size:11px;\">💾 Caché</span>' if cached_s else ''}"
        f"</div>",
        unsafe_allow_html=True
    )

    col_p, col_m, col_r = st.columns(3)
    with col_p:
        st.markdown(
            _sintesis_card("Impacto en Precios",
                           sint_result.get("impacto_precios",""),
                           "#D97706", "#FEF3C7", "💰"),
            unsafe_allow_html=True
        )
    with col_m:
        st.markdown(
            _sintesis_card("Tendencias México",
                           sint_result.get("tendencias_mexico",""),
                           "#059669", "#D1FAE5", "🇲🇽"),
            unsafe_allow_html=True
        )
    with col_r:
        st.markdown(
            _sintesis_card("Riesgos Globales",
                           sint_result.get("riesgos_globales",""),
                           "#DC2626", "#FEE2E2", "⚠️"),
            unsafe_allow_html=True
        )

    rec = sint_result.get("recomendacion","")
    if rec:
        st.markdown(
            f"<div style='background:#EFF6FF;border:1px solid #BFDBFE;border-radius:8px;"
            f"padding:12px 16px;margin-top:14px;font-size:13px;color:#1E40AF;'>"
            f"🏭 <b>Recomendación para TYASA:</b> {rec}</div>",
            unsafe_allow_html=True
        )
else:
    st.info("Haz clic en **▶ Generar síntesis** para obtener el resumen ejecutivo de la industria.")

st.divider()

# ════════════════════════════════════════════════════════════════════════════
# SECCIÓN B — NOTICIAS POR GRUPO (Tabs)
# ════════════════════════════════════════════════════════════════════════════
seccion_titulo(
    "📰 Noticias de la Industria",
    "Resultados en tiempo real desde Google News · Organizados por tema"
)

# ── Controles de fecha y actualización ───────────────────────────────────────
hoy       = datetime.date.today()
hace_30d  = hoy - datetime.timedelta(days=30)

col_rng, col_act = st.columns([3, 1])
with col_rng:
    rango = st.date_input(
        "Rango de fechas",
        value=(hoy - datetime.timedelta(days=7), hoy),
        min_value=hace_30d,
        max_value=hoy,
        key="ind_fecha_rango",
        format="DD/MM/YYYY",
    )
with col_act:
    st.markdown("<div style='padding-top:22px;'></div>", unsafe_allow_html=True)
    if st.button("🔄 Actualizar noticiero", key="ind_refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# Parsear rango seleccionado
if isinstance(rango, (list, tuple)) and len(rango) == 2:
    fecha_desde, fecha_hasta = str(rango[0]), str(rango[1])
else:
    fecha_desde = str(hoy - datetime.timedelta(days=7))
    fecha_hasta = str(hoy)

st.caption(f"Mostrando noticias del **{fecha_desde}** al **{fecha_hasta}**")

grupos_list = list(GRUPOS_INDUSTRIA.keys())
tabs = st.tabs([
    f"{'🔴' if g=='Urgente' else '🟢' if g=='Tendencias' else '🔵' if g=='Empresas' else '🟡' if g=='Insumos' else '🟣'} {g}"
    for g in grupos_list
])

for tab, grupo in zip(tabs, grupos_list):
    with tab:
        with st.spinner(f"Cargando noticias de {grupo}..."):
            noticias_raw = _noticias_grupo(grupo, 20)

        noticias_g = _filtrar_por_fecha(noticias_raw, fecha_desde, fecha_hasta)

        if not noticias_g:
            st.info(f"Sin noticias para el grupo **{grupo}** en el rango seleccionado.")
            continue

        st.caption(f"{len(noticias_g)} artículo(s) en el período")

        # Grid de 2 columnas
        col_a, col_b = st.columns(2)
        for i, n in enumerate(noticias_g):
            target = col_a if i % 2 == 0 else col_b
            with target:
                st.markdown(_render_news_card(n, grupo), unsafe_allow_html=True)

st.divider()

# ════════════════════════════════════════════════════════════════════════════
# SECCIÓN C — CHAT SOBRE LA INDUSTRIA
# ════════════════════════════════════════════════════════════════════════════
if _GEMINI_KEY:
    seccion_titulo(
        "💬 Chat con el Analista Siderúrgico",
        "Haz preguntas sobre tendencias, precios, empresas o riesgos del sector acero"
    )

    CHAT_KEY_IND = "chat_industria_msgs"
    if CHAT_KEY_IND not in st.session_state:
        st.session_state[CHAT_KEY_IND] = []

    msgs_ind = st.session_state[CHAT_KEY_IND]

    with st.container(height=340):
        if not msgs_ind:
            st.markdown(
                "<div style='text-align:center;color:#9CA3AF;padding:40px;font-size:13px;'>"
                "Escribe una pregunta sobre la industria siderúrgica para comenzar.</div>",
                unsafe_allow_html=True
            )
        for msg in msgs_ind:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    prompt_ind = st.chat_input(
        "Pregunta sobre la industria siderúrgica...",
        key="chat_input_industria"
    )
    if prompt_ind:
        msgs_ind.append({"role": "user", "content": prompt_ind})
        hist_txt = "\n".join(
            f"{'Analista' if m['role']=='assistant' else 'Usuario'}: {m['content']}"
            for m in msgs_ind[:-1]
        )
        full_prompt_ind = (
            "Contexto: Analista de la industria siderúrgica para TYASA México.\n\n"
            f"{'Conversación previa:\n' + hist_txt + chr(10) if hist_txt else ''}"
            f"Usuario: {prompt_ind}"
        )
        resp_ind = _call_gemini_text(full_prompt_ind, _GEMINI_KEY)
        msgs_ind.append({"role": "assistant", "content": resp_ind})
        st.session_state[CHAT_KEY_IND] = msgs_ind
        st.rerun()

    if st.button("🗑 Limpiar conversación", key="chat_ind_clear"):
        st.session_state[CHAT_KEY_IND] = []
        st.rerun()
