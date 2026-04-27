"""
00_mercado_global.py — Mercado Global integrado — TYASA BI
Vista unificada: Quiebres · Variables · INEGI · Siderúrgico · Mañanera · Chat
"""
import os, sys
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if _root not in sys.path:
    sys.path.insert(0, _root)

import streamlit as st
import datetime
from config import COLORS

# ── Claves API ────────────────────────────────────────────────────────────────
try:
    _GEMINI_KEY = st.secrets["GEMINI_API_KEY"]
except Exception:
    _GEMINI_KEY = ""

# ── Encabezado ────────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <div style='margin-bottom:16px;'>
        <h2 style='color:{COLORS["text"]};margin:0;font-size:1.5rem;'>🌐 Mercado Global</h2>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Tabs principales ──────────────────────────────────────────────────────────
tab_quiebres, tab_variables, tab_inegi, tab_siderurgico, tab_mananera = st.tabs([
    "📡 Quiebres",
    "📊 Variables",
    "🇲🇽 INEGI",
    "🏭 Siderúrgico",
    "🎙️ Mañanera",
])

# ════════════════════════════════════════════════════════════════════════════
# TAB 1 — Monitor de Quiebres
# ════════════════════════════════════════════════════════════════════════════
with tab_quiebres:
    try:
        from mercado_noticias.loaders import load_variables_mercado, get_categorias_disponibles
        from mercado_noticias.analytics.detector import detectar_quiebres_automatico
        from mercado_noticias.analytics.ai_analysis import analizar_alerta
        from core.components.kpi_cards import seccion_titulo

        df_vars = load_variables_mercado()

        if df_vars.empty:
            st.info("Sin datos de variables de mercado. Verifica la conexión a BigQuery.")
        else:
            categorias = get_categorias_disponibles()
            col_cat, col_sev = st.columns([3, 2])
            with col_cat:
                cat_sel = st.selectbox("Categoría", ["Todas"] + categorias, key="mg_cat")
            with col_sev:
                sev_sel = st.selectbox("Severidad mínima", ["Todas", "Crítico", "Alto", "Moderado"], key="mg_sev")

            df_f = df_vars if cat_sel == "Todas" else df_vars[df_vars["categoria"] == cat_sel]
            quiebres = detectar_quiebres_automatico(df_f)

            SEV_ORDEN = {"Crítico": 4, "Alto": 3, "Moderado": 2, "Normal": 1}
            SEV_COLORS = {
                "Crítico":  (COLORS["danger"],  "rgba(231,76,60,0.12)"),
                "Alto":     (COLORS["warning"], "rgba(243,156,18,0.12)"),
                "Moderado": (COLORS["primary"], "rgba(74,159,212,0.12)"),
            }
            if sev_sel != "Todas":
                quiebres = [q for q in quiebres if q.get("severidad") == sev_sel]

            quiebres = sorted(quiebres, key=lambda q: SEV_ORDEN.get(q.get("severidad",""), 0), reverse=True)

            seccion_titulo(f"Alertas detectadas ({len(quiebres)})")
            if not quiebres:
                st.success("Sin alertas de quiebres en el rango seleccionado.")
            else:
                for q in quiebres[:20]:
                    sev = q.get("severidad", "Moderado")
                    bc, bg = SEV_COLORS.get(sev, (COLORS["neutral"], COLORS["surface"]))
                    st.markdown(
                        f"""
                        <div style='background:{bg};border:1px solid {bc};border-left:4px solid {bc};
                                    border-radius:8px;padding:10px 14px;margin-bottom:6px;'>
                            <b style='color:{COLORS["text"]};'>{q.get("variable","")}</b>
                            <span style='float:right;color:{bc};font-size:0.75rem;font-weight:700;'>{sev}</span>
                            <br><span style='color:{COLORS["text_light"]};font-size:0.82rem;'>
                            {q.get("descripcion","")} · {q.get("fecha_quiebre","")}</span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
    except Exception as e:
        st.error(f"Error cargando quiebres: {e}")


# ════════════════════════════════════════════════════════════════════════════
# TAB 2 — Variables Globales
# ════════════════════════════════════════════════════════════════════════════
with tab_variables:
    try:
        from mercado_noticias.loaders import load_variables_mercado, get_categorias_disponibles
        from core.components.charts import linea_temporal, multi_axis_line
        import plotly.graph_objects as go

        df_vars = load_variables_mercado()
        if df_vars.empty:
            st.info("Sin datos de variables.")
        else:
            categorias_vars = sorted(df_vars["categoria"].dropna().unique().tolist())
            col_v1, col_v2 = st.columns([3, 2])
            with col_v1:
                cat_v = st.selectbox("Categoría", categorias_vars, key="mg_vars_cat")
            with col_v2:
                n_dias = st.selectbox("Periodo", [90, 180, 365, 730], index=1, key="mg_vars_d")

            variables = df_vars[df_vars["categoria"] == cat_v]["nombre"].unique().tolist() if cat_v else df_vars["nombre"].unique().tolist()
            var_sel = st.multiselect("Variables", variables, default=variables[:3], key="mg_vars_sel")

            if var_sel:
                fecha_corte = df_vars["fecha"].max() - datetime.timedelta(days=n_dias)
                df_plot = df_vars[
                    (df_vars["nombre"].isin(var_sel)) &
                    (df_vars["fecha"] >= fecha_corte)
                ]
                fig = go.Figure()
                palette = [COLORS["primary"], COLORS["accent"], COLORS["success"],
                           COLORS["warning"], COLORS["danger"]]
                for i, v in enumerate(var_sel):
                    dfv = df_plot[df_plot["nombre"] == v].sort_values("fecha")
                    fig.add_trace(go.Scatter(
                        x=dfv["fecha"], y=dfv["valor"], name=v,
                        mode="lines", line=dict(color=palette[i % len(palette)], width=2),
                    ))
                fig.update_layout(
                    paper_bgcolor=COLORS["surface"],
                    plot_bgcolor=COLORS["surface"],
                    font=dict(color=COLORS["text"], size=12),
                    margin=dict(l=40, r=20, t=30, b=40),
                    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=COLORS["text_light"])),
                    xaxis=dict(showgrid=False),
                    yaxis=dict(gridcolor=COLORS["border"]),
                    height=380,
                )
                st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Error cargando variables: {e}")


# ════════════════════════════════════════════════════════════════════════════
# TAB 3 — INEGI
# ════════════════════════════════════════════════════════════════════════════
with tab_inegi:
    try:
        from mercado_noticias.inegi_loader import (
            load_indicadores_inegi, get_ultimo_valor, calcular_var_mensual, calcular_var_anual,
            INDICADORES,
        )
        from core.components.kpi_cards import kpi_card_compact, kpi_card_with_sparkline
        from core.components.charts import linea_temporal

        _CLAVES_DISPLAY = [
            ("IGAE_INDUSTRIA",   "IGAE Industria",     ""),
            ("IGAE_MANUFACTURA", "Manufactura",        ""),
            ("INVERSION_FIJA",   "Inversión Fija",     ""),
            ("INPC_GENERAL",     "INPC General",       ""),
            ("EXPORTACIONES_MANUF", "Exportaciones Manuf.", " MDD"),
        ]

        with st.spinner("Consultando INEGI..."):
            claves = [c for c, _, _ in _CLAVES_DISPLAY]
            datos = load_indicadores_inegi(claves=claves)

        col_inegi = st.columns(len(_CLAVES_DISPLAY))
        for col, (clave, nombre, sufijo) in zip(col_inegi, _CLAVES_DISPLAY):
            df_ind = datos.get(clave, None)
            val, fecha = get_ultimo_valor(df_ind) if df_ind is not None and not df_ind.empty else (None, None)
            delta_m = calcular_var_mensual(df_ind) if df_ind is not None else None
            with col:
                if val is not None:
                    series_vals = df_ind["valor"].tail(24).tolist() if df_ind is not None else []
                    kpi_card_with_sparkline(
                        label=nombre,
                        value=f"{val:,.1f}{sufijo}",
                        series=series_vals,
                        delta=delta_m,
                        icon="📊",
                    )
                else:
                    kpi_card_compact(label=nombre, value="—", icon="📊")

        # Gráfica detalle
        clave_det = st.selectbox(
            "Ver detalle", [c for c, _, _ in _CLAVES_DISPLAY],
            format_func=lambda k: next((n for ck, n, _ in _CLAVES_DISPLAY if ck == k), k),
            key="mg_inegi_det",
        )
        df_det = datos.get(clave_det)
        if df_det is not None and not df_det.empty:
            import plotly.graph_objects as go
            fig = go.Figure(go.Scatter(
                x=df_det["fecha"], y=df_det["valor"], mode="lines+markers",
                line=dict(color=COLORS["primary"], width=2.5),
                marker=dict(size=4),
            ))
            fig.update_layout(
                paper_bgcolor=COLORS["surface"], plot_bgcolor=COLORS["surface"],
                font=dict(color=COLORS["text"]),
                margin=dict(l=40, r=20, t=30, b=40),
                xaxis=dict(showgrid=False),
                yaxis=dict(gridcolor=COLORS["border"]),
                height=300,
            )
            st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Error consultando INEGI: {e}")


# ════════════════════════════════════════════════════════════════════════════
# TAB 4 — Monitor Siderúrgico (noticias)
# ════════════════════════════════════════════════════════════════════════════
with tab_siderurgico:
    try:
        from mercado_noticias.analytics.noticias import (
            buscar_noticias_sector,
            GRUPOS_NACIONAL, GRUPOS_INTERNACIONAL,
            GRUPO_STYLE_NACIONAL, GRUPO_STYLE_INTERNACIONAL,
        )

        col_nac, col_int = st.columns(2)

        with col_nac:
            st.markdown(
                f"<div style='font-weight:700;color:{COLORS['text']};margin-bottom:8px;'>🇲🇽 Nacionales</div>",
                unsafe_allow_html=True,
            )
            grp_nac = st.selectbox("Grupo", list(GRUPOS_NACIONAL.keys()), key="mg_nac")
            if st.button("Buscar noticias 🇲🇽", key="mg_btn_nac"):
                with st.spinner("Buscando..."):
                    noticias = buscar_noticias_sector(grp_nac, max_resultados=8)
                st.session_state["mg_noticias_nac"] = noticias
            for n in st.session_state.get("mg_noticias_nac", [])[:8]:
                st.markdown(
                    f"<div style='background:{COLORS['surface']};border:1px solid {COLORS['border']};"
                    f"border-radius:6px;padding:10px 12px;margin-bottom:6px;'>"
                    f"<a href='{n.get('url','')}' target='_blank' style='color:{COLORS['primary']};font-weight:600;"
                    f"font-size:0.85rem;text-decoration:none;'>{n.get('titulo','')}</a>"
                    f"<br><span style='color:{COLORS['text_light']};font-size:0.75rem;'>"
                    f"{n.get('fuente','')} · {n.get('fecha','')}</span></div>",
                    unsafe_allow_html=True,
                )

        with col_int:
            st.markdown(
                f"<div style='font-weight:700;color:{COLORS['text']};margin-bottom:8px;'>🌐 Internacionales</div>",
                unsafe_allow_html=True,
            )
            grp_int = st.selectbox("Grupo", list(GRUPOS_INTERNACIONAL.keys()), key="mg_int")
            if st.button("Buscar noticias 🌐", key="mg_btn_int"):
                with st.spinner("Buscando..."):
                    noticias_i = buscar_noticias_sector(grp_int, max_resultados=8)
                st.session_state["mg_noticias_int"] = noticias_i
            for n in st.session_state.get("mg_noticias_int", [])[:8]:
                st.markdown(
                    f"<div style='background:{COLORS['surface']};border:1px solid {COLORS['border']};"
                    f"border-radius:6px;padding:10px 12px;margin-bottom:6px;'>"
                    f"<a href='{n.get('url','')}' target='_blank' style='color:{COLORS['primary']};font-weight:600;"
                    f"font-size:0.85rem;text-decoration:none;'>{n.get('titulo','')}</a>"
                    f"<br><span style='color:{COLORS['text_light']};font-size:0.75rem;'>"
                    f"{n.get('fuente','')} · {n.get('fecha','')}</span></div>",
                    unsafe_allow_html=True,
                )
    except Exception as e:
        st.error(f"Error cargando noticias: {e}")


# ════════════════════════════════════════════════════════════════════════════
# TAB 5 — Mañanera Presidencial IA
# ════════════════════════════════════════════════════════════════════════════
with tab_mananera:
    try:
        from mercado_noticias.analytics.mananera import (
            analizar_mananera, MANANERA_CACHE_DIR, MANANERA_CACHE_DAYS,
        )

        col_fecha, col_btn, col_frz = st.columns([3, 1, 1])
        with col_fecha:
            fecha_man = st.date_input(
                "Fecha", value=datetime.date.today(), max_value=datetime.date.today(),
                key="mg_man_fecha",
            )
        with col_btn:
            run_man = st.button("Analizar", key="mg_man_run", use_container_width=True)
        with col_frz:
            force_man = st.checkbox("Refrescar", key="mg_man_frz")

        if not _GEMINI_KEY:
            st.warning("GEMINI_API_KEY no configurada en secrets.toml")

        skey = f"mg_man_{fecha_man}"
        man_area = st.empty()

        if run_man and _GEMINI_KEY:
            man_area.markdown(
                f"<div style='background:{COLORS['surface']};border:1px solid {COLORS['border']};"
                f"border-radius:8px;padding:24px;text-align:center;color:{COLORS['text_light']};'>"
                f"⏳ Buscando video y transcripción...</div>",
                unsafe_allow_html=True,
            )
            st.session_state[skey] = analizar_mananera(
                api_key=_GEMINI_KEY,
                fecha=str(fecha_man),
                force_refresh=force_man,
            )
            st.rerun()

        result = st.session_state.get(skey)
        if result:
            err = result.get("_error")
            if err:
                man_area.markdown(
                    f"<div style='background:rgba(231,76,60,0.1);border:1px solid {COLORS['danger']};"
                    f"border-radius:8px;padding:16px;color:{COLORS['text']};'>⚠️ {err}</div>",
                    unsafe_allow_html=True,
                )
            elif result.get("tiene_contenido_relevante"):
                _PROD_STYLE = {
                    "Tubería OCTG":    ("#4A9FD4", "rgba(74,159,212,0.15)"),
                    "Tubería Mecánica": ("#2ECC71", "rgba(46,204,113,0.15)"),
                    "Perfiles":        ("#E05C2D", "rgba(224,92,45,0.15)"),
                    "SBQ":             ("#9B59B6", "rgba(155,89,182,0.15)"),
                    "Lámina Negra":    ("#F39C12", "rgba(243,156,18,0.15)"),
                    "Galvanizado":     ("#1ABC9C", "rgba(26,188,156,0.15)"),
                }
                resumen_items = "".join(
                    f"<li style='font-size:0.85rem;color:{COLORS['neutral']};margin-bottom:4px;'>{p}</li>"
                    for p in result.get("resumen_ejecutivo", [])
                )
                html_parts = [
                    f"<div style='background:{COLORS['surface']};border:1px solid {COLORS['border']};"
                    f"border-radius:10px;padding:20px;'>",
                    f"<div style='font-weight:700;font-size:1.05rem;color:{COLORS['text']};margin-bottom:10px;'>"
                    f"🎙️ Mañanera — {result.get('fecha','')}"
                    f"{'  <span style=\"font-size:0.72rem;background:rgba(74,159,212,0.15);color:#4A9FD4;padding:2px 8px;border-radius:10px;\">💾 caché</span>' if result.get('_cached') else ''}"
                    f"</div>",
                    f"<ul style='margin:0 0 12px 0;padding-left:18px;'>{resumen_items}</ul>",
                ]
                impactos = result.get("analisis_impacto", [])
                for imp in impactos:
                    tipo = imp.get("tipo", "")
                    impacto = imp.get("impacto", "")
                    dir_ = imp.get("direccion", "Neutral")
                    dir_color = COLORS["success"] if dir_ == "Positivo" else (COLORS["danger"] if dir_ == "Negativo" else COLORS["neutral"])
                    imp_color = COLORS["danger"] if impacto == "Alto" else (COLORS["warning"] if impacto == "Medio" else COLORS["primary"])
                    productos = imp.get("productos_afectados", [])
                    prod_tags = "".join(
                        f"<span style='background:{COLORS['surface2']};color:{COLORS['text']};padding:2px 8px;"
                        f"border-radius:10px;font-size:0.72rem;margin-right:4px;'>📦 {p}</span>"
                        for p in productos
                    )
                    html_parts.append(
                        f"<div style='background:{COLORS['surface2']};border:1px solid {COLORS['border']};"
                        f"border-left:3px solid {imp_color};border-radius:6px;padding:12px 14px;margin-bottom:8px;'>"
                        f"<div style='font-weight:700;color:{COLORS['text']};font-size:0.9rem;margin-bottom:4px;'>"
                        f"{imp.get('punto','')}"
                        f"<span style='float:right;color:{dir_color};font-size:0.78rem;'>{dir_} · {impacto}</span></div>"
                        f"<p style='color:{COLORS['neutral']};font-size:0.82rem;margin:4px 0;'>{imp.get('explicacion','')}</p>"
                        f"<div style='margin-top:6px;'>{prod_tags}</div>"
                        f"</div>"
                    )
                insight = result.get("insight_estrategico", "")
                rec = result.get("recomendacion", "")
                if insight:
                    html_parts.append(
                        f"<div style='background:rgba(74,159,212,0.08);border:1px solid rgba(74,159,212,0.3);"
                        f"border-radius:6px;padding:12px 14px;margin-top:8px;'>"
                        f"<span style='font-weight:700;color:{COLORS['primary']};'>💡 Insight:</span>"
                        f"<span style='color:{COLORS['neutral']};font-size:0.85rem;'> {insight}</span></div>"
                    )
                if rec:
                    html_parts.append(
                        f"<div style='background:rgba(224,92,45,0.08);border:1px solid rgba(224,92,45,0.3);"
                        f"border-radius:6px;padding:12px 14px;margin-top:8px;'>"
                        f"<span style='font-weight:700;color:{COLORS['accent']};'>⚡ Acción:</span>"
                        f"<span style='color:{COLORS['neutral']};font-size:0.85rem;'> {rec}</span></div>"
                    )
                html_parts.append("</div>")
                man_area.markdown("".join(html_parts), unsafe_allow_html=True)
            else:
                man_area.markdown(
                    f"<div style='background:{COLORS['surface']};border:1px solid {COLORS['border']};"
                    f"border-radius:8px;padding:16px;color:{COLORS['text_light']};'>"
                    f"Sin contenido relevante para la siderurgia en la conferencia del {result.get('fecha','')}.</div>",
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
        st.error(f"Error en módulo mañanera: {e}")
