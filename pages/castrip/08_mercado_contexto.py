"""
08_mercado_contexto.py — Contexto de Mercado — CASTRIP
Noticias del sector, mañanera presidencial e indicadores INEGI relevantes.
"""
import os, sys
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if _root not in sys.path:
    sys.path.insert(0, _root)

import streamlit as st
import datetime
from config import COLORS

try:
    _GEMINI_KEY = st.secrets["GEMINI_API_KEY"]
except Exception:
    _GEMINI_KEY = ""

from core.components.kpi_cards import seccion_titulo
from core.components.filters import sidebar_header

if not st.session_state.get("_castrip_combined"):
    sidebar_header("CASTRIP", "⚡")

st.markdown(
    f"<h2 style='color:{COLORS['text']};margin-bottom:0;'>🌐 Contexto de Mercado</h2>",
    unsafe_allow_html=True,
)

tab_noticias, tab_mananera, tab_inegi = st.tabs(["📰 Noticias", "🎙️ Mañanera", "📊 INEGI"])

# ════════════════════════════════════════════════════════════════════════════
# TAB 1 — Noticias siderúrgicas
# ════════════════════════════════════════════════════════════════════════════
with tab_noticias:
    try:
        from mercado_noticias.analytics.noticias import (
            buscar_noticias_sector,
            GRUPOS_NACIONAL, GRUPOS_INTERNACIONAL,
        )
        col_ng, col_ig = st.columns(2)

        _GRUPOS_RELEVANTES_CASTRIP = {
            "Regulación": "Aranceles y regulación",
            "Energía": "Energía (CFE / Gas)",
            "Industria": "Industria y nearshoring",
            "Mercado Global": "Mercado global acero",
            "Materias Primas": "Materias primas",
            "Comercio": "Comercio internacional",
        }

        with col_ng:
            seccion_titulo("Nacionales")
            grp_nac = st.selectbox("Grupo", list(GRUPOS_NACIONAL.keys()), key="cs_ctx_nac")
            if st.button("Buscar 🇲🇽", key="cs_ctx_nac_btn"):
                with st.spinner("Buscando..."):
                    n_nac = buscar_noticias_sector(grp_nac, max_resultados=8)
                st.session_state["cs_ctx_noticias_nac"] = n_nac
            for n in st.session_state.get("cs_ctx_noticias_nac", [])[:8]:
                st.markdown(
                    f"<div style='background:{COLORS['surface']};border:1px solid {COLORS['border']};"
                    f"border-radius:6px;padding:10px 12px;margin-bottom:6px;'>"
                    f"<a href='{n.get('url','')}' target='_blank' style='color:{COLORS['primary']};"
                    f"font-weight:600;font-size:0.85rem;text-decoration:none;'>{n.get('titulo','')}</a>"
                    f"<br><span style='color:{COLORS['text_light']};font-size:0.75rem;'>"
                    f"{n.get('fuente','')} · {n.get('fecha','')}</span></div>",
                    unsafe_allow_html=True,
                )

        with col_ig:
            seccion_titulo("Internacionales")
            grp_int = st.selectbox("Grupo", list(GRUPOS_INTERNACIONAL.keys()), key="cs_ctx_int")
            if st.button("Buscar 🌐", key="cs_ctx_int_btn"):
                with st.spinner("Buscando..."):
                    n_int = buscar_noticias_sector(grp_int, max_resultados=8)
                st.session_state["cs_ctx_noticias_int"] = n_int
            for n in st.session_state.get("cs_ctx_noticias_int", [])[:8]:
                st.markdown(
                    f"<div style='background:{COLORS['surface']};border:1px solid {COLORS['border']};"
                    f"border-radius:6px;padding:10px 12px;margin-bottom:6px;'>"
                    f"<a href='{n.get('url','')}' target='_blank' style='color:{COLORS['primary']};"
                    f"font-weight:600;font-size:0.85rem;text-decoration:none;'>{n.get('titulo','')}</a>"
                    f"<br><span style='color:{COLORS['text_light']};font-size:0.75rem;'>"
                    f"{n.get('fuente','')} · {n.get('fecha','')}</span></div>",
                    unsafe_allow_html=True,
                )
    except Exception as e:
        st.error(f"Error: {e}")


# ════════════════════════════════════════════════════════════════════════════
# TAB 2 — Mañanera
# ════════════════════════════════════════════════════════════════════════════
with tab_mananera:
    try:
        from mercado_noticias.analytics.mananera import analizar_mananera

        col_f, col_b = st.columns([3, 1])
        with col_f:
            fecha_man = st.date_input("Fecha", value=datetime.date.today(),
                                      max_value=datetime.date.today(), key="cs_ctx_man_f")
        with col_b:
            run_man = st.button("Analizar", key="cs_ctx_man_run", use_container_width=True)

        if not _GEMINI_KEY:
            st.warning("GEMINI_API_KEY no configurada.")

        skey_man = f"cs_man_{fecha_man}"
        man_area = st.empty()

        if run_man and _GEMINI_KEY:
            man_area.markdown(
                f"<div style='background:{COLORS['surface']};border:1px solid {COLORS['border']};"
                f"border-radius:8px;padding:24px;text-align:center;color:{COLORS['text_light']};'>"
                f"⏳ Buscando y analizando...</div>",
                unsafe_allow_html=True,
            )
            st.session_state[skey_man] = analizar_mananera(
                api_key=_GEMINI_KEY, fecha=str(fecha_man),
            )
            st.rerun()

        result = st.session_state.get(skey_man)
        if result:
            err = result.get("_error")
            if err:
                man_area.markdown(
                    f"<div style='background:rgba(231,76,60,0.1);border:1px solid {COLORS['danger']};"
                    f"border-radius:8px;padding:16px;color:{COLORS['text']};'>⚠️ {err}</div>",
                    unsafe_allow_html=True,
                )
            elif result.get("tiene_contenido_relevante"):
                resumen = result.get("resumen_ejecutivo", [])
                items_html = "".join(
                    f"<li style='color:{COLORS['neutral']};font-size:0.85rem;margin-bottom:4px;'>{p}</li>"
                    for p in resumen
                )
                rec = result.get("recomendacion", "")
                rec_html = (
                    f"<div style='background:rgba(216,59,1,0.08);border:1px solid rgba(216,59,1,0.3);"
                    f"border-radius:6px;padding:10px;margin-top:8px;'>"
                    f"<b style='color:{COLORS['accent']};'>⚡ Acción: </b>"
                    f"<span style='color:{COLORS['neutral']};font-size:0.85rem;'>{rec}</span></div>"
                ) if rec else ""
                man_area.markdown(
                    f"<div style='background:{COLORS['surface']};border:1px solid {COLORS['border']};"
                    f"border-radius:10px;padding:20px;'>"
                    f"<b style='color:{COLORS['text']};'>Mañanera {result.get('fecha','')}</b>"
                    f"<ul style='margin:10px 0;padding-left:18px;'>{items_html}</ul>"
                    f"{rec_html}"
                    f"</div>",
                    unsafe_allow_html=True,
                )
            else:
                man_area.markdown(
                    f"<div style='background:{COLORS['surface']};border:1px solid {COLORS['border']};"
                    f"border-radius:8px;padding:16px;color:{COLORS['text_light']};'>"
                    f"Sin contenido relevante para la siderurgia en {result.get('fecha','')}.</div>",
                    unsafe_allow_html=True,
                )
        else:
            man_area.markdown(
                f"<div style='background:{COLORS['surface']};border:1px solid {COLORS['border']};"
                f"border-radius:8px;padding:24px;text-align:center;color:{COLORS['text_light']};'>"
                f"Selecciona fecha y presiona <b>Analizar</b></div>",
                unsafe_allow_html=True,
            )
    except Exception as e:
        st.error(f"Error en mañanera: {e}")


# ════════════════════════════════════════════════════════════════════════════
# TAB 3 — INEGI
# ════════════════════════════════════════════════════════════════════════════
with tab_inegi:
    try:
        from mercado_noticias.inegi_loader import (
            load_indicadores_inegi, get_ultimo_valor, calcular_var_mensual,
        )
        from core.components.kpi_cards import kpi_card_compact

        _INEGI_DISPLAY = [
            ("IGAE_INDUSTRIA",    "IGAE Industria"),
            ("IGAE_MANUFACTURA",  "Manufactura"),
            ("INVERSION_FIJA",    "Inversión Fija"),
            ("INPC_GENERAL",      "Inflación"),
            ("EXPORTACIONES_MANUF","Expo. Manuf."),
        ]

        with st.spinner("Consultando INEGI..."):
            inegi_dat = load_indicadores_inegi(claves=[k for k, _ in _INEGI_DISPLAY])

        cols_inegi = st.columns(len(_INEGI_DISPLAY))
        for col, (clave, nombre) in zip(cols_inegi, _INEGI_DISPLAY):
            df_i = inegi_dat.get(clave)
            val, fecha_s = get_ultimo_valor(df_i) if df_i is not None and not df_i.empty else (None, None)
            delta_m = calcular_var_mensual(df_i) if df_i is not None else None
            with col:
                if val is not None:
                    kpi_card_compact(
                        label=nombre,
                        value=f"{val:,.1f}",
                        delta=delta_m,
                        icon="📊",
                    )
                else:
                    kpi_card_compact(label=nombre, value="Sin datos", icon="📊")
    except Exception as e:
        st.error(f"Error consultando INEGI: {e}")
