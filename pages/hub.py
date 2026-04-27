"""
hub.py — Landing page TYASA BI — Tema ejecutivo oscuro.
"""
import os, sys
import streamlit as st

_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)

from config import COLORS, APP_NAME, APP_SUBTITLE

# ── Encabezado ────────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <div style='padding:32px 0 24px 0;'>
        <div style='font-size:2.8rem;font-weight:800;color:{COLORS["text"]};letter-spacing:-0.02em;
                    line-height:1.1;'>
            🏭 {APP_NAME}
        </div>
        <div style='color:{COLORS["text_light"]};font-size:1.05rem;margin-top:6px;'>
            {APP_SUBTITLE}
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.divider()

# ── Grid de áreas ─────────────────────────────────────────────────────────────
def _area_card(
    titulo: str,
    icono: str,
    descripcion: str,
    modulos: list[str],
    status: str = "activo",
    accent: str | None = None,
) -> str:
    STATUS_STYLES = {
        "activo":        (COLORS["success"], "rgba(16,124,16,0.08)",   "✅ Activo"),
        "en_desarrollo": (COLORS["warning"], "rgba(210,146,0,0.10)",   "🚧 En desarrollo"),
        "proximo":       (COLORS["neutral"], "rgba(96,94,92,0.08)",    "🔜 Próximo"),
    }
    sc, sb, st_label = STATUS_STYLES.get(status, STATUS_STYLES["proximo"])
    border_top = accent or sc

    mods_html = "".join(
        f"<li style='color:{COLORS['text_light']};font-size:0.8rem;margin:3px 0;'>{m}</li>"
        for m in modulos
    ) if modulos else (
        f"<li style='color:{COLORS['text_light']};font-size:0.8rem;font-style:italic;'>En construcción...</li>"
    )

    return f"""
    <div style='
        background:{COLORS["surface"]};
        border:1px solid {COLORS["border"]};
        border-top:4px solid {border_top};
        border-radius:10px;
        padding:20px 18px;
        min-height:220px;
        display:flex;
        flex-direction:column;
    '>
        <div style='font-size:1.8rem;margin-bottom:6px;'>{icono}</div>
        <div style='font-size:1.1rem;font-weight:700;color:{COLORS["text"]};margin-bottom:6px;'>{titulo}</div>
        <span style='display:inline-block;background:{sb};color:{sc};padding:2px 10px;
                     border-radius:12px;font-size:0.72rem;font-weight:600;margin-bottom:10px;'>
            {st_label}
        </span>
        <p style='color:{COLORS["text_light"]};font-size:0.8rem;margin-bottom:8px;'>{descripcion}</p>
        <ul style='margin:0;padding-left:16px;flex:1;'>
            {mods_html}
        </ul>
    </div>
    """


col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(
        _area_card(
            "Mercado Global", "🌐",
            "Variables macroeconómicas, quiebres estructurales, noticias IA, mañanera.",
            ["Mercado Global integrado", "Monitor de Quiebres", "Variables 31 series", "Monitor Siderúrgico"],
            "activo", COLORS["primary"],
        ),
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        _area_card(
            "Aceros Planos", "⚡",
            "CASTRIP: alertas, analytics comerciales e inteligencia de clientes.",
            ["00 Alertas", "01–05 Analytics", "06 Clientes IA", "07 Condición Mercado", "08 Contexto"],
            "activo", COLORS["accent"],
        ),
        unsafe_allow_html=True,
    )

with col3:
    st.markdown(
        _area_card(
            "Aceros Largos", "📏",
            "Perfiles estructurales, varilla, ángulos y canales: resumen, macro, mercado.",
            ["Resumen Ejecutivo", "Macroeconomía", "Mercado y Costos", "Operaciones", "Calidad"],
            "activo", COLORS["success"],
        ),
        unsafe_allow_html=True,
    )

with col4:
    st.markdown(
        _area_card(
            "Aceros SBQ", "🔑",
            "Special Bar Quality para autopartes y maquinaria.",
            [],
            "proximo", COLORS["neutral"],
        ),
        unsafe_allow_html=True,
    )

st.divider()

# ── KPIs de estado rápido ─────────────────────────────────────────────────────
col_k1, col_k2, col_k3, col_k4 = st.columns(4)

_kpis = [
    (col_k1, "🌐",  "Mercado Global", "Activo",   COLORS["primary"]),
    (col_k2, "⚡",  "Aceros Planos",  "CASTRIP", COLORS["accent"]),
    (col_k3, "📏",  "Aceros Largos",  "5 módulos", COLORS["success"]),
    (col_k4, "🔑",  "SBQ",            "Próximo",   COLORS["neutral"]),
]

for col, icon, label, val, color in _kpis:
    with col:
        st.markdown(
            f"""
            <div style='
                background:{COLORS["surface"]};
                border:1px solid {COLORS["border"]};
                border-left:4px solid {color};
                border-radius:8px;
                padding:14px 16px;
                text-align:center;
            '>
                <div style='font-size:1.5rem;'>{icon}</div>
                <div style='color:{COLORS["text_light"]};font-size:0.72rem;font-weight:600;
                            text-transform:uppercase;letter-spacing:0.05em;margin:4px 0 2px 0;'>
                    {label}
                </div>
                <div style='color:{color};font-size:1rem;font-weight:700;'>{val}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.markdown(
    f"""
    <div style='text-align:center;color:{COLORS["text_light"]};font-size:0.78rem;padding:8px 0;'>
        TYASA BI — Plataforma de Inteligencia Comercial
        &nbsp;·&nbsp; Mercado Global · CASTRIP · Aceros Largos · SBQ
    </div>
    """,
    unsafe_allow_html=True,
)
