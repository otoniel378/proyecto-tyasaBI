"""
app.py — Hub principal TYASA BI.
Navegación plana: 5 elementos en sidebar (Inicio · Mercado Global · CASTRIP · Aceros Largos · SBQ)
"""

import os
import sys
import streamlit as st

_root = os.path.dirname(os.path.abspath(__file__))
if _root not in sys.path:
    sys.path.insert(0, _root)

from config import APP_NAME, APP_SUBTITLE, APP_ICON, ASSETS_DIR

st.set_page_config(
    page_title=APP_NAME,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": f"**{APP_NAME}** — {APP_SUBTITLE}"},
)

# ── CSS global ────────────────────────────────────────────────────────────────
css_path = os.path.join(ASSETS_DIR, "style.css")
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ── Páginas (5 items planos — sin sub-grupos en sidebar) ──────────────────────
hub      = st.Page("pages/hub.py",              title="Inicio",         icon="🏠", default=True)
mercado  = st.Page("pages/mercado_main.py",     title="Mercado Global", icon="🌐", url_path="mercado")
castrip  = st.Page("pages/castrip_main.py",     title="Aceros Planos",  icon="⚡", url_path="aceros_planos")
largos   = st.Page("pages/aceros_largos_main.py", title="Aceros Largos", icon="📏", url_path="aceros_largos")
sbq      = st.Page("pages/aceros_sbq/coming_soon.py", title="Aceros SBQ", icon="🔑", url_path="aceros_sbq")

pg = st.navigation([hub, mercado, castrip, largos, sbq])
pg.run()
