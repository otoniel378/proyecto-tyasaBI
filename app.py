"""
app.py — Hub principal de TYASA BI.
Punto de entrada unico con navegacion multi-area via st.navigation().
Arquitectura: Aceros Planos | Aceros Largos | Aceros SBQ
"""

import os
import sys
import streamlit as st

# Asegurar que el directorio raiz esta en el path
_root = os.path.dirname(os.path.abspath(__file__))
if _root not in sys.path:
    sys.path.insert(0, _root)

from config import APP_NAME, APP_SUBTITLE, APP_ICON, ASSETS_DIR

# ---------------------------------------------------------------------------
# Configuracion de pagina (debe ser el primer comando Streamlit)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title=APP_NAME,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": f"**{APP_NAME}** — {APP_SUBTITLE}",
    },
)

# ---------------------------------------------------------------------------
# CSS global
# ---------------------------------------------------------------------------
css_path = os.path.join(ASSETS_DIR, "style.css")
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Definicion de paginas
# ---------------------------------------------------------------------------

# Hub de bienvenida
hub = st.Page("pages/hub.py", title="Inicio", icon="🏠", default=True)

# ── Aceros Planos — Negros (COMPLETADO) ──────────────────────────────────
apn_resumen  = st.Page("pages/ap_negros/01_resumen.py",          title="Resumen Ejecutivo",     icon="📊", url_path="apn_resumen")
apn_seg      = st.Page("pages/ap_negros/02_segmentacion.py",      title="Segmentacion Clientes", icon="👥")
apn_series   = st.Page("pages/ap_negros/03_series_tiempo.py",     title="Series de Tiempo",      icon="📈")
apn_forecast = st.Page("pages/ap_negros/04_forecasting.py",       title="Forecasting",           icon="🔮")
apn_mix      = st.Page("pages/ap_negros/05_mix_productos.py",     title="Mix de Productos",      icon="🎯")

# ── Aceros Planos — Galvanizados (EN DESARROLLO) ─────────────────────────
apg_soon = st.Page("pages/ap_galvanizados/coming_soon.py", title="Aceros Galvanizados", icon="✨", url_path="ap_galvanizados")

# ── Aceros Planos — Formados (EN DESARROLLO) ─────────────────────────────
apf_soon = st.Page("pages/ap_formados/coming_soon.py", title="Aceros Formados", icon="🔧", url_path="ap_formados")

# ── Aceros Largos (COMPLETADO) ──────────────────────────────────────────
al_resumen    = st.Page("pages/aceros_largos/01_resumen.py",        title="Resumen Ejecutivo",     icon="📊", url_path="al_resumen")
al_macro      = st.Page("pages/aceros_largos/02_macroeconomia.py",  title="Macroeconomía",         icon="🏦")  
al_mercado    = st.Page("pages/aceros_largos/03_mercado.py",        title="Mercado y Costos",      icon="💹")
al_operaciones = st.Page("pages/aceros_largos/04_operaciones.py",   title="Operaciones",           icon="⚙️")
al_calidad    = st.Page("pages/aceros_largos/05_calidad.py",        title="Calidad",               icon="✅")

# ── Aceros SBQ (PROXIMO) ─────────────────────────────────────────────────
sbq_soon = st.Page("pages/aceros_sbq/coming_soon.py", title="Aceros SBQ", icon="🔑", url_path="aceros_sbq")

# ── Mercado Global (NUEVO) ────────────────────────────────────────────────
mkt_monitor   = st.Page("pages/mercado/01_monitor.py",   title="Monitor de Quiebres",    icon="📡")
mkt_vars      = st.Page("pages/mercado/02_variables.py", title="Variables Globales",      icon="🌐")
mkt_industria = st.Page("pages/mercado/03_industria.py", title="Monitor Siderúrgico",     icon="🏭")

# ---------------------------------------------------------------------------
# Navegacion estructurada por area
# ---------------------------------------------------------------------------
pg = st.navigation({
    "Inicio": [hub],
    "Aceros Planos — Negros": [apn_resumen, apn_seg, apn_series, apn_forecast, apn_mix],
    "Aceros Planos — Galvanizados": [apg_soon],
    "Aceros Planos — Formados": [apf_soon],
    "Aceros Largos": [al_resumen, al_macro, al_mercado, al_operaciones, al_calidad],
    "Aceros SBQ": [sbq_soon],
    "Mercado Global": [mkt_monitor, mkt_vars, mkt_industria],
})
pg.run()
