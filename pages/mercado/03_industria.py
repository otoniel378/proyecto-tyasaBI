"""
03_industria.py — Monitor de la Industria Siderúrgica — TYASA BI
Mañanera presidencial · Noticias especializadas · Síntesis IA · Análisis de tendencias

DOM-STABLE: Cero componentes condicionales.
  - st.spinner eliminado → st.empty() con HTML de estado (cargando / resultado / vacío)
  - Todas las secciones de resultado usan 1 st.markdown / st.empty() fijo
  - st.chat_message loop eliminado → _render_chat_html() con burbujas HTML
"""
import os, sys
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if _root not in sys.path:
    sys.path.insert(0, _root)

import json
import datetime
from pathlib import Path

import streamlit as st
from config import COLORS
from mercado_noticias.analytics.noticias import buscar_noticias_industria, GRUPOS_INDUSTRIA
from mercado_noticias.analytics.ai_analysis import sintesis_industrial, _call_gemini_text
from mercado_noticias.analytics.mananera import analizar_mananera, MANANERA_CACHE_DIR, MANANERA_CACHE_DAYS
from core.components.filters import sidebar_header
from core.components.kpi_cards import seccion_titulo

# ── API key ───────────────────────────────────────────────────────────────────
try:
    _GEMINI_KEY = st.secrets["GEMINI_API_KEY"]
except Exception:
    _GEMINI_KEY = ""

# ── Paletas ───────────────────────────────────────────────────────────────────
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
# HELPERS — NOTICIAS
# ════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=1800, show_spinner=False)
def _noticias_grupo(grupo: str, max_r: int = 14) -> list[dict]:
    return buscar_noticias_industria(grupo, max_resultados=max_r)


def _filtrar_por_fecha(noticias: list[dict], desde: str, hasta: str) -> list[dict]:
    out = []
    for n in noticias:
        fp = (n.get("fecha_pub") or "")[:10]
        if not fp or (desde <= fp <= hasta):
            out.append(n)
    return out


def _render_news_card(n: dict, grupo: str) -> str:
    c_txt, c_bg = GRUPO_STYLE.get(grupo, ("#374151", "#F9FAFB"))
    titulo = (n.get("titulo", "") or "").strip()
    desc   = (n.get("descripcion", "") or "").strip()[:220]
    fuente = (n.get("fuente", "") or "").strip()
    url    = (n.get("url", "") or "").strip()
    fecha  = (n.get("fecha_pub", "") or "").strip()
    badge  = n.get("fuente_api", "")
    bc     = "#1B3A5C" if badge == "Google News" else "#6B7280"
    link   = (
        f'<a href="{url}" target="_blank" style="color:{c_txt};font-weight:700;'
        f'font-size:12px;text-decoration:none;">Leer artículo →</a>'
    ) if url else ""
    return (
        f"<div style='border:1px solid #E5E7EB;border-radius:10px;padding:16px;"
        f"background:white;box-shadow:0 1px 4px rgba(0,0,0,0.06);margin-bottom:12px;'>"
        f"<div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;'>"
        f"<span style='font-size:10px;font-weight:700;letter-spacing:0.06em;"
        f"background:{c_bg};color:{c_txt};padding:3px 10px;border-radius:20px;'>{grupo.upper()}</span>"
        f"<span style='font-size:11px;color:#9CA3AF;'>📅 {fecha}</span>"
        f"</div>"
        f"<div style='font-size:14px;font-weight:700;color:#111827;line-height:1.45;margin-bottom:8px;'>{titulo}</div>"
        f"<div style='font-size:12px;color:#6B7280;line-height:1.55;margin-bottom:12px;'>{desc}</div>"
        f"<div style='display:flex;justify-content:space-between;align-items:center;"
        f"padding-top:10px;border-top:1px solid #F3F4F6;'>"
        f"<span style='font-size:11px;color:#9CA3AF;display:flex;gap:6px;align-items:center;'>"
        f"📰 {fuente} "
        f"<span style='background:{bc};color:white;padding:1px 6px;border-radius:4px;font-size:9px;'>{badge}</span>"
        f"</span>"
        f"{link}"
        f"</div></div>"
    )


# ════════════════════════════════════════════════════════════════════════════
# HELPERS — SÍNTESIS (HTML puro, sin componentes condicionales)
# ════════════════════════════════════════════════════════════════════════════

def _render_sintesis_full(result: dict | None, loading: bool = False) -> str:
    """Estado de la síntesis como HTML. Siempre 1 componente → DOM estable."""
    if loading:
        return (
            "<div style='background:#F0F9FF;border:1px solid #BAE6FD;border-radius:8px;"
            "padding:20px;color:#0369A1;font-size:13px;text-align:center;'>"
            "<div style='font-size:22px;margin-bottom:8px;'>⏳</div>"
            "<b>Generando síntesis industrial…</b><br>"
            "<span style='font-size:12px;color:#0284C7;'>"
            "Consultando noticias y analizando tendencias con IA.</span></div>"
        )
    if result is None:
        return (
            "<div style='background:#F0F9FF;border:1px solid #BAE6FD;border-radius:8px;"
            "padding:16px;color:#0369A1;font-size:13px;'>"
            "ℹ️ Haz clic en <b>▶ Generar síntesis</b> para obtener el resumen ejecutivo "
            "de la industria.</div>"
        )
    err = result.get("_error", "")
    if err:
        return (
            f"<div style='background:#FEF2F2;border:1px solid #FCA5A5;border-radius:8px;"
            f"padding:16px;color:#DC2626;font-size:13px;'>⚠️ {err}</div>"
        )
    nivel    = result.get("nivel_alerta", "—")
    nc_txt, nc_bg = ALERTA_STYLE.get(nivel, ("#6B7280", "#F3F4F6"))
    cached_s = result.get("_cached", False)
    cache_b  = (
        '<span style="background:#F3F4F6;color:#6B7280;padding:4px 10px;'
        'border-radius:20px;font-size:11px;">💾 Caché</span>'
    ) if cached_s else ""
    header = (
        f"<div style='display:flex;gap:10px;align-items:center;margin-bottom:14px;'>"
        f"<span style='background:{nc_bg};color:{nc_txt};padding:4px 14px;"
        f"border-radius:20px;font-size:12px;font-weight:700;'>Nivel de alerta: {nivel}</span>"
        f"{cache_b}</div>"
    )
    p_c = _sintesis_card("Impacto en Precios",  result.get("impacto_precios",""),  "#D97706","#FEF3C7","💰")
    m_c = _sintesis_card("Tendencias México",   result.get("tendencias_mexico",""),"#059669","#D1FAE5","🇲🇽")
    r_c = _sintesis_card("Riesgos Globales",    result.get("riesgos_globales",""), "#DC2626","#FEE2E2","⚠️")
    grid = (
        f"<div style='display:grid;grid-template-columns:repeat(3,1fr);gap:12px;'>"
        f"<div>{p_c}</div><div>{m_c}</div><div>{r_c}</div></div>"
    )
    rec = result.get("recomendacion","")
    rec_html = (
        f"<div style='background:#EFF6FF;border:1px solid #BFDBFE;border-radius:8px;"
        f"padding:12px 16px;margin-top:14px;font-size:13px;color:#1E40AF;'>"
        f"🏭 <b>Recomendación para TYASA:</b> {rec}</div>"
    ) if rec else ""
    return header + grid + rec_html


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
# HELPERS — MAÑANERA (HTML puro, sin componentes condicionales)
# ════════════════════════════════════════════════════════════════════════════

_TIPO_STYLE: dict[str, tuple[str, str]] = {
    "Regulación":  ("#7C3AED", "#EDE9FE"),
    "Energía":     ("#D97706", "#FEF3C7"),
    "Demanda":     ("#2563EB", "#DBEAFE"),
    "Riesgo":      ("#DC2626", "#FEE2E2"),
    "Oportunidad": ("#059669", "#D1FAE5"),
}
_IMP_STYLE: dict[str, tuple[str, str]] = {
    "Alto":  ("#DC2626", "#FEE2E2"),
    "Medio": ("#D97706", "#FEF3C7"),
    "Bajo":  ("#059669", "#D1FAE5"),
}
_DIR_ICON  = {"Positivo": "↑", "Negativo": "↓", "Neutral": "→"}
_DIR_COLOR = {"Positivo": "#059669", "Negativo": "#DC2626", "Neutral": "#6B7280"}
_AREA_STYLE: dict[str, tuple[str, str]] = {
    "SBQ":           ("#1B3A5C", "#E8EFF6"),
    "Aceros Planos": ("#0F766E", "#CCFBF1"),
    "Aceros Largos": ("#4338CA", "#E0E7FF"),
}


def _render_mananera_full(result: dict | None, loading: bool = False) -> str:
    """
    Toda el área de resultados de la mañanera como HTML.
    loading=True → indicador animado en HTML.
    Siempre se llama con 1 st.empty() → árbol DOM estable.
    """
    if loading:
        return (
            "<div style='background:#F0F9FF;border:1px solid #BAE6FD;border-radius:8px;"
            "padding:24px;color:#0369A1;font-size:13px;text-align:center;'>"
            "<div style='font-size:28px;margin-bottom:10px;'>⏳</div>"
            "<b>Analizando la conferencia mañanera…</b><br>"
            "<span style='font-size:12px;color:#0284C7;'>"
            "Buscando el video en YouTube → obteniendo la transcripción → "
            "procesando con IA. Puede tardar entre 20 y 60 segundos.</span></div>"
        )
    if result is None:
        return (
            "<div style='background:#F0F9FF;border:1px solid #BAE6FD;border-radius:8px;"
            "padding:16px;color:#0369A1;font-size:13px;'>"
            "ℹ️ Haz clic en <b>▶ Analizar</b> para que la IA procese la conferencia "
            "presidencial y extraiga solo la información relevante para el sector acero."
            "</div>"
        )
    err = result.get("_error", "")
    is_live = result.get("_is_live", False)
    if err:
        vid_id = result.get("_video_id", "")
        yt = (
            f" &nbsp;<a href='https://www.youtube.com/watch?v={vid_id}' target='_blank'"
            f" style='color:#4A7BA7;font-size:11px;'>▶ Ver video</a>"
        ) if vid_id else ""
        live_badge = (
            "<span style='background:#FEF3C7;color:#92400E;padding:2px 8px;"
            "border-radius:10px;font-size:10px;font-weight:700;'>🔴 EN VIVO</span> "
        ) if is_live else ""
        return (
            f"<div style='background:#FEF2F2;border:1px solid #FCA5A5;border-radius:8px;"
            f"padding:16px;color:#DC2626;font-size:13px;'>"
            f"{live_badge}⚠️ {err}{yt}</div>"
        )
    if not result.get("tiene_contenido_relevante"):
        fecha  = result.get("fecha", "")
        vid_id = result.get("_video_id", "")
        yt = (
            f" &nbsp;<a href='https://www.youtube.com/watch?v={vid_id}' target='_blank'"
            f" style='color:#4A7BA7;font-size:11px;'>▶ Ver video</a>"
        ) if vid_id else ""
        return (
            f"<div style='background:#F0F9FF;border:1px solid #BAE6FD;border-radius:8px;"
            f"padding:16px;color:#0369A1;font-size:13px;'>"
            f"ℹ️ La conferencia del <b>{fecha}</b> no contiene información relevante "
            f"para la industria siderúrgica según el análisis de IA.{yt}</div>"
        )
    resumen  = result.get("resumen_ejecutivo", [])
    impactos = result.get("analisis_impacto", [])
    alertas  = result.get("alertas_criticas", [])
    insight  = result.get("insight_estrategico", "")
    rec      = result.get("recomendacion", "")
    cached   = result.get("_cached", False)
    vid_id   = result.get("_video_id", "")
    parts = []
    if resumen:
        parts.append(_man_resumen_html(resumen, cached, vid_id))
    if impactos:
        parts.append(_man_impacto_html(impactos))
    if alertas:
        parts.append(_man_alertas_html(alertas))
    ir = _man_insight_rec_html(insight, rec)
    if ir:
        parts.append(ir)
    return "".join(parts) or "<div></div>"


def _man_resumen_html(puntos: list[str], cached: bool, video_id: str) -> str:
    cached_badge = (
        "<span style='background:#F3F4F6;color:#6B7280;padding:2px 8px;"
        "border-radius:10px;font-size:10px;'>💾 Caché</span>"
    ) if cached else (
        "<span style='background:#D1FAE5;color:#065F46;padding:2px 8px;"
        "border-radius:10px;font-size:10px;'>✓ Nuevo</span>"
    )
    yt_link = (
        f"<a href='https://www.youtube.com/watch?v={video_id}' target='_blank' "
        f"style='font-size:10px;color:#4A7BA7;text-decoration:none;'>▶ Ver video</a>"
    ) if video_id else ""
    items = "".join(f"<li style='margin-bottom:5px;'>{p}</li>" for p in puntos)
    return (
        f"<div style='background:#F0F4F8;border-left:4px solid #1B3A5C;"
        f"border-radius:0 10px 10px 0;padding:16px 20px;margin-bottom:16px;'>"
        f"<div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;'>"
        f"<span style='font-size:12px;font-weight:800;letter-spacing:0.06em;color:#1B3A5C;'>"
        f"📋 RESUMEN EJECUTIVO</span>"
        f"<span style='display:flex;gap:8px;align-items:center;'>{cached_badge} {yt_link}</span>"
        f"</div>"
        f"<ol style='margin:0;padding-left:18px;font-size:13px;color:#374151;line-height:1.75;'>"
        f"{items}</ol></div>"
    )


def _man_impacto_html(items: list[dict]) -> str:
    if not items:
        return ""
    cards = []
    for item in items:
        tipo  = item.get("tipo", "")
        imp   = item.get("impacto", "")
        dire  = item.get("direccion", "")
        areas = item.get("areas_afectadas", [])
        punto = item.get("punto", "")
        expl  = item.get("explicacion", "")
        tc, tb = _TIPO_STYLE.get(tipo, ("#6B7280", "#F3F4F6"))
        ic, ib = _IMP_STYLE.get(imp,  ("#6B7280", "#F3F4F6"))
        dc     = _DIR_COLOR.get(dire, "#6B7280")
        di     = _DIR_ICON.get(dire, "→")
        area_tags = "".join(
            f"<span style='background:{_AREA_STYLE.get(a, ('#6B7280','#F3F4F6'))[1]};"
            f"color:{_AREA_STYLE.get(a, ('#6B7280','#F3F4F6'))[0]};"
            f"padding:1px 7px;border-radius:10px;font-size:10px;font-weight:600;'>{a}</span>"
            for a in areas
        )
        cards.append(
            f"<div style='border:1px solid #E5E7EB;border-radius:10px;padding:14px;"
            f"background:white;box-shadow:0 1px 3px rgba(0,0,0,0.06);'>"
            f"<div style='font-size:12px;font-weight:700;color:#111827;margin-bottom:10px;"
            f"line-height:1.4;'>{punto}</div>"
            f"<div style='display:flex;gap:5px;flex-wrap:wrap;margin-bottom:8px;'>"
            f"<span style='background:{tb};color:{tc};padding:2px 8px;border-radius:10px;"
            f"font-size:10px;font-weight:700;'>{tipo}</span>"
            f"<span style='background:{ib};color:{ic};padding:2px 8px;border-radius:10px;"
            f"font-size:10px;font-weight:700;'>⚡ {imp}</span>"
            f"<span style='background:#F9FAFB;color:{dc};padding:2px 8px;border-radius:10px;"
            f"font-size:10px;font-weight:700;border:1px solid #E5E7EB;'>{di} {dire}</span>"
            f"</div>"
            f"<div style='display:flex;gap:4px;flex-wrap:wrap;margin-bottom:8px;'>{area_tags}</div>"
            f"<div style='font-size:12px;color:#6B7280;line-height:1.55;'>{expl}</div>"
            f"</div>"
        )
    grid = "".join(f"<div>{c}</div>" for c in cards)
    return (
        f"<div style='margin-bottom:6px;'>"
        f"<span style='font-size:12px;font-weight:800;letter-spacing:0.06em;"
        f"color:#1B3A5C;'>🔍 ANÁLISIS DE IMPACTO</span></div>"
        f"<div style='display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));"
        f"gap:12px;margin-bottom:16px;'>{grid}</div>"
    )


def _man_alertas_html(alertas: list[str]) -> str:
    if not alertas:
        return ""
    items = "".join(f"<li style='margin-bottom:4px;'>{a}</li>" for a in alertas)
    return (
        f"<div style='background:#FEF2F2;border:1px solid #FCA5A5;border-radius:8px;"
        f"padding:14px 18px;margin-bottom:16px;'>"
        f"<div style='font-size:12px;font-weight:800;color:#DC2626;margin-bottom:8px;'>"
        f"⚠️ ALERTAS CRÍTICAS</div>"
        f"<ul style='margin:0;padding-left:18px;font-size:12px;color:#991B1B;"
        f"line-height:1.65;'>{items}</ul></div>"
    )


def _man_insight_rec_html(insight: str, rec: str) -> str:
    if not insight and not rec:
        return ""
    col_ins = (
        f"<div style='background:#EFF6FF;border:1px solid #BFDBFE;border-radius:8px;padding:14px 16px;'>"
        f"<div style='font-size:12px;font-weight:800;color:#1D4ED8;margin-bottom:8px;'>"
        f"💡 INSIGHT ESTRATÉGICO</div>"
        f"<div style='font-size:13px;color:#1E40AF;line-height:1.65;'>{insight}</div></div>"
    ) if insight else ""
    col_rec = (
        f"<div style='background:#F0FDF4;border:1px solid #86EFAC;border-radius:8px;padding:14px 16px;'>"
        f"<div style='font-size:12px;font-weight:800;color:#15803D;margin-bottom:8px;'>"
        f"🎯 RECOMENDACIÓN PARA TYASA</div>"
        f"<div style='font-size:13px;color:#166534;line-height:1.65;'>{rec}</div></div>"
    ) if rec else ""
    cols = "".join(f"<div>{c}</div>" for c in [col_ins, col_rec] if c)
    n = sum(1 for c in [col_ins, col_rec] if c)
    return (
        f"<div style='display:grid;grid-template-columns:repeat({n},1fr);"
        f"gap:12px;margin-top:4px;'>{cols}</div>"
    )


# ════════════════════════════════════════════════════════════════════════════
# HELPERS — CHAT (HTML puro, sin st.chat_message en loop)
# ════════════════════════════════════════════════════════════════════════════

def _render_chat_html(msgs: list[dict], has_key: bool) -> str:
    """Historial del chat como burbujas HTML. 1 st.empty() → DOM estable."""
    if not has_key:
        return (
            "<div style='background:#FEF3C7;border:1px solid #FCD34D;border-radius:8px;"
            "padding:16px;color:#92400E;font-size:13px;'>"
            "⚙️ Configura <b>GEMINI_API_KEY</b> en <code>.streamlit/secrets.toml</code> "
            "para usar el chat con el analista.</div>"
        )
    if not msgs:
        return (
            "<div style='background:#F9FAFB;border:1px solid #E5E7EB;border-radius:8px;"
            "padding:36px 24px;text-align:center;color:#9CA3AF;font-size:13px;'>"
            "💬 Escribe una pregunta sobre la industria siderúrgica para comenzar."
            "</div>"
        )
    bubbles = []
    for m in msgs:
        content = (m.get("content") or "").replace("<", "&lt;").replace(">", "&gt;")
        if m.get("role") == "user":
            bubbles.append(
                f"<div style='display:flex;justify-content:flex-end;margin-bottom:10px;'>"
                f"<div style='background:#1B3A5C;color:white;border-radius:18px 18px 4px 18px;"
                f"padding:10px 16px;max-width:76%;font-size:13px;line-height:1.55;'>"
                f"{content}</div></div>"
            )
        else:
            bubbles.append(
                f"<div style='display:flex;justify-content:flex-start;margin-bottom:10px;'>"
                f"<div style='background:#F0F4F8;color:#374151;border-radius:18px 18px 18px 4px;"
                f"padding:10px 16px;max-width:76%;font-size:13px;line-height:1.55;'>"
                f"🤖 {content}</div></div>"
            )
    return (
        "<div style='background:white;border:1px solid #E5E7EB;border-radius:8px;"
        "padding:16px 20px;max-height:340px;overflow-y:auto;'>"
        + "".join(bubbles)
        + "</div>"
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
# SECCIÓN 0 — ANALISTA DE LA MAÑANERA PRESIDENCIAL
# DOM: st.columns(4) + st.empty() siempre presentes — cero condicionales
# ════════════════════════════════════════════════════════════════════════════
seccion_titulo(
    "🇲🇽 Analista de la Mañanera Presidencial",
    "Extrae automáticamente de la conferencia diaria solo lo relevante para la industria siderúrgica"
)

hoy_man = datetime.date.today()
col_fman, col_bman, col_frzman, col_infoman = st.columns([2, 1, 1, 3])
with col_fman:
    fecha_man = st.date_input(
        "Fecha de la conferencia",
        value=hoy_man,
        min_value=hoy_man - datetime.timedelta(days=MANANERA_CACHE_DAYS),
        max_value=hoy_man,
        key="man_fecha",
        format="DD/MM/YYYY",
    )
with col_bman:
    st.markdown("<div style='padding-top:22px;'></div>", unsafe_allow_html=True)
    run_man = st.button("▶ Analizar", key="man_run", use_container_width=True)
with col_frzman:
    st.markdown("<div style='padding-top:22px;'></div>", unsafe_allow_html=True)
    frz_man = st.checkbox("Regenerar", key="man_frz", value=False)
with col_infoman:
    st.caption(
        "Busca en YouTube la conferencia (en vivo o grabada) → obtiene la transcripción → "
        "filtra con IA solo información de acero, energía, aranceles e infraestructura · "
        "Caché 3 días"
    )

fecha_man_str = str(fecha_man)
skey_man = f"mananera_{fecha_man_str}"

# Auto-cargar desde disco si hay caché para la fecha seleccionada
if skey_man not in st.session_state:
    cache_path_man = MANANERA_CACHE_DIR / f"{fecha_man_str}.json"
    if cache_path_man.exists():
        try:
            with open(cache_path_man, encoding="utf-8") as _f:
                _d = json.load(_f)
                _d["_cached"] = True
                st.session_state[skey_man] = _d
        except Exception:
            pass

# st.empty() fijo → actualizado con HTML de carga, resultado o vacío (sin spinner)
man_area = st.empty()

if run_man and _GEMINI_KEY:
    # Mostrar loading inmediatamente, luego reemplazar con resultado
    man_area.markdown(_render_mananera_full(None, loading=True), unsafe_allow_html=True)
    st.session_state[skey_man] = analizar_mananera(_GEMINI_KEY, fecha_man_str, force_refresh=frz_man)
elif run_man:
    st.session_state[skey_man] = {
        "tiene_contenido_relevante": False,
        "_error": "Configura GEMINI_API_KEY en .streamlit/secrets.toml",
    }

man_area.markdown(
    _render_mananera_full(st.session_state.get(skey_man)),
    unsafe_allow_html=True,
)

st.divider()

# ════════════════════════════════════════════════════════════════════════════
# SECCIÓN A — SÍNTESIS INDUSTRIAL IA
# DOM: st.columns(3) + st.empty() siempre presentes — cero condicionales
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

sint_area = st.empty()

if run_sint and _GEMINI_KEY:
    sint_area.markdown(_render_sintesis_full(None, loading=True), unsafe_allow_html=True)
    noticias_todos = {g: _noticias_grupo(g, 8) for g in GRUPOS_INDUSTRIA}
    sint = sintesis_industrial(noticias_todos, _GEMINI_KEY, force_refresh=frz_sint)
    st.session_state["sint_result"] = sint
elif run_sint:
    st.session_state["sint_result"] = {"_error": "Configura GEMINI_API_KEY en .streamlit/secrets.toml"}

sint_area.markdown(
    _render_sintesis_full(st.session_state.get("sint_result")),
    unsafe_allow_html=True,
)

st.divider()

# ════════════════════════════════════════════════════════════════════════════
# SECCIÓN B — NOTICIAS POR GRUPO (Tabs)
# DOM: st.tabs() + 1 st.markdown por tab — siempre estable
# ════════════════════════════════════════════════════════════════════════════
seccion_titulo(
    "📰 Noticias de la Industria",
    "Resultados en tiempo real desde Google News · Organizados por tema"
)

hoy      = datetime.date.today()
hace_30d = hoy - datetime.timedelta(days=30)

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
        noticias_raw = _noticias_grupo(grupo, 20)
        noticias_g   = _filtrar_por_fecha(noticias_raw, fecha_desde, fecha_hasta)
        if not noticias_g:
            html_tab = (
                f"<div style='color:#9CA3AF;padding:24px 0;text-align:center;"
                f"font-size:13px;'>Sin noticias para <b>{grupo}</b> "
                f"en el rango seleccionado.</div>"
            )
        else:
            caption = (
                f"<div style='font-size:11px;color:#6B7280;margin-bottom:10px;'>"
                f"{len(noticias_g)} artículo(s) en el período</div>"
            )
            cards = "".join(f"<div>{_render_news_card(n, grupo)}</div>" for n in noticias_g)
            html_tab = (
                caption
                + f"<div style='display:grid;grid-template-columns:repeat(2,1fr);gap:12px;'>{cards}</div>"
            )
        st.markdown(html_tab, unsafe_allow_html=True)

st.divider()

# ════════════════════════════════════════════════════════════════════════════
# SECCIÓN C — CHAT SOBRE LA INDUSTRIA
# DOM: 1 st.empty() + st.chat_input + st.button — sin st.chat_message en loop
# ════════════════════════════════════════════════════════════════════════════
seccion_titulo(
    "💬 Chat con el Analista Siderúrgico",
    "Haz preguntas sobre tendencias, precios, empresas o riesgos del sector acero"
)

CHAT_KEY_IND = "chat_industria_msgs"
if CHAT_KEY_IND not in st.session_state:
    st.session_state[CHAT_KEY_IND] = []

msgs_ind = st.session_state[CHAT_KEY_IND]

chat_area = st.empty()
chat_area.markdown(_render_chat_html(msgs_ind, bool(_GEMINI_KEY)), unsafe_allow_html=True)

prompt_ind = st.chat_input(
    "Pregunta sobre la industria siderúrgica...",
    key="chat_input_industria"
)
if prompt_ind and _GEMINI_KEY:
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
