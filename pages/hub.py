"""
hub.py — Pagina de bienvenida y vision general del proyecto TYASA BI.
Muestra el estado de cada area y sus modulos.
"""

import os
import sys
import streamlit as st

_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)

from config import COLORS, APP_NAME, APP_SUBTITLE, AREAS

# ---------------------------------------------------------------------------
# Encabezado
# ---------------------------------------------------------------------------
col_icon, col_title = st.columns([1, 6])
with col_icon:
    st.markdown("<div style='font-size:3rem;text-align:center;padding-top:8px;'>🏭</div>", unsafe_allow_html=True)
with col_title:
    st.markdown(
        f"""
        <h1 style='color:{COLORS["primary"]};margin-bottom:0;'>{APP_NAME}</h1>
        <p style='color:{COLORS["neutral"]};font-size:1.05rem;margin-top:4px;'>{APP_SUBTITLE}</p>
        """,
        unsafe_allow_html=True,
    )

st.divider()

st.markdown(
    f"<h3 style='color:{COLORS['primary']};'>Estado del Proyecto</h3>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='color:#6B7280;'>Selecciona un modulo en el menu lateral para comenzar el analisis.</p>",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Tarjetas por area
# ---------------------------------------------------------------------------

STATUS_BADGE = {
    "activo":        ("<span style='background:#E8F5E9;color:#2E7D32;padding:3px 10px;border-radius:12px;font-size:0.78rem;font-weight:600;'>✅ Activo</span>", "#2E7D32"),
    "en_desarrollo": ("<span style='background:#FFF3E0;color:#F57C00;padding:3px 10px;border-radius:12px;font-size:0.78rem;font-weight:600;'>🚧 En Desarrollo</span>", "#F57C00"),
    "proximo":       ("<span style='background:#F3F4F6;color:#6B7280;padding:3px 10px;border-radius:12px;font-size:0.78rem;font-weight:600;'>🔜 Proximo</span>", "#6B7280"),
}

# ── Aceros Planos ────────────────────────────────────────────────────────────
st.markdown(f"<h4 style='color:{COLORS['primary']};margin-top:24px;'>🔩 Aceros Planos</h4>", unsafe_allow_html=True)
col1, col2, col3 = st.columns(3)

subsecciones_ap = [
    ("negros",       "⚫ Aceros Negros",      "activo",        ["Resumen Ejecutivo", "Segmentacion Clientes", "Series de Tiempo", "Forecasting", "Mix de Productos"]),
    ("galvanizados", "✨ Aceros Galvanizados", "en_desarrollo", []),
    ("formados",     "🔧 Aceros Formados",    "en_desarrollo", []),
]

for col, (key, nombre, status, modulos) in zip([col1, col2, col3], subsecciones_ap):
    badge, border_color = STATUS_BADGE[status]
    modulos_html = "".join(
        f"<li style='font-size:0.82rem;color:{COLORS['text_light']};margin:2px 0;'>{m}</li>"
        for m in modulos
    ) if modulos else f"<li style='font-size:0.82rem;color:{COLORS['text_light']};font-style:italic;'>En construccion...</li>"

    with col:
        st.markdown(
            f"""
            <div style='
                background:{COLORS["surface"]};
                border:1px solid #E5E7EB;
                border-top:4px solid {border_color};
                border-radius:8px;
                padding:18px 16px;
                min-height:200px;
            '>
                <div style='font-size:1.1rem;font-weight:700;color:{COLORS["primary"]};margin-bottom:6px;'>{nombre}</div>
                {badge}
                <ul style='margin-top:12px;padding-left:18px;'>
                    {modulos_html}
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ── Otras areas ──────────────────────────────────────────────────────────────
st.markdown(f"<h4 style='color:{COLORS['primary']};margin-top:28px;'>Otras Areas</h4>", unsafe_allow_html=True)
col4, col5, _ = st.columns(3)

otras = [
    (col4, "📏 Aceros Largos",  "🔜 Proximo — Pendiente de desarrollo por el equipo responsable."),
    (col5, "🔑 Aceros SBQ",     "🔜 Proximo — Pendiente de desarrollo por el equipo responsable."),
]

for col, titulo, desc in otras:
    with col:
        st.markdown(
            f"""
            <div style='
                background:{COLORS["background"]};
                border:1px dashed #D1D5DB;
                border-radius:8px;
                padding:18px 16px;
                min-height:120px;
            '>
                <div style='font-size:1.1rem;font-weight:700;color:{COLORS["neutral"]};margin-bottom:8px;'>{titulo}</div>
                <p style='font-size:0.83rem;color:{COLORS["text_light"]};'>{desc}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.divider()
st.markdown(
    f"""
    <div style='text-align:center;color:{COLORS["text_light"]};font-size:0.82rem;'>
        TYASA BI — Plataforma de Inteligencia Comercial Multi-Area
        &nbsp;|&nbsp; Aceros Planos · Aceros Largos · Aceros SBQ
    </div>
    """,
    unsafe_allow_html=True,
)
