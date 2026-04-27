"""
app.py — Hub principal de TYASA BI.
Navegación: sidebar principal + subsecciones en área de contenido.
"""

import os
import sys
import streamlit as st

_root = os.path.dirname(os.path.abspath(__file__))
if _root not in sys.path:
    sys.path.insert(0, _root)

from config import APP_NAME, APP_SUBTITLE, APP_ICON, ASSETS_DIR

# ---------------------------------------------------------------------------
# Inicializar estado
# ---------------------------------------------------------------------------
if "nav_seccion" not in st.session_state:
    st.session_state.nav_seccion = "inicio"
if "nav_subseccion" not in st.session_state:
    st.session_state.nav_subseccion = "bienvenida"
if "nav_subcategoria" not in st.session_state:
    st.session_state.nav_subcategoria = "negros"

# ---------------------------------------------------------------------------
# Configuracion de pagina
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title=APP_NAME,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# CSS global
# ---------------------------------------------------------------------------
css_path = os.path.join(ASSETS_DIR, "style.css")
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# CSS navegación
# ---------------------------------------------------------------------------
st.markdown("""
<style>
.main-nav-btn {
    background-color: #FFFFFF !important;
    border: 2px solid #E5E7EB !important;
    border-radius: 10px !important;
    padding: 16px 20px !important;
    margin: 4px 0 !important;
    text-align: center !important;
    font-size: 1rem !important;
    font-weight: 600 !important;
    color: #374151 !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08) !important;
}
.main-nav-btn:hover {
    background-color: #EBF4FF !important;
    border-color: #1B3A5C !important;
    color: #1B3A5C !important;
}
.main-nav-btn.active {
    background-color: #1B3A5C !important;
    border-color: #1B3A5C !important;
    color: white !important;
}
.subsecciones-container {
    display: flex;
    gap: 4px;
    padding: 16px 0;
    border-bottom: 2px solid #1B3A5C;
    margin-bottom: 20px;
    flex-wrap: wrap;
}
.subseccion-tab {
    background-color: #F3F4F6 !important;
    border: 1px solid #E5E7EB !important;
    border-radius: 8px 8px 0 0 !important;
    padding: 12px 24px !important;
    font-size: 0.95rem !important;
    font-weight: 600 !important;
    color: #4B5563 !important;
    cursor: pointer;
    transition: all 0.15s ease !important;
}
.subseccion-tab:hover {
    background-color: #E5E7EB !important;
    color: #1B3A5C !important;
}
.subseccion-tab.active {
    background-color: #1B3A5C !important;
    border-color: #1B3A5C !important;
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Header estilo Power BI
# ---------------------------------------------------------------------------
st.markdown("""
<div style="background: linear-gradient(135deg, #1B3A5C 0%, #2C5282 100%); 
            padding: 20px 32px; 
            margin: -1rem -1rem 24px -1rem;
            border-radius: 0;
            display: flex;
            align-items: center;
            justify-content: space-between;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);">
    <div style="display: flex; align-items: center; gap: 16px;">
        <span style="font-size: 2.5rem;">🏭</span>
        <div>
            <h1 style="color: white; margin: 0; font-size: 1.5rem; font-weight: 700;">
                TYASA Business Intelligence
            </h1>
            <p style="color: rgba(255,255,255,0.85); margin: 4px 0 0 0; font-size: 0.9rem;">
                Plataforma de Inteligencia Comercial
            </p>
        </div>
    </div>
    <div style="color: rgba(255,255,255,0.7); font-size: 0.8rem;">
        📊 Powered by Streamlit & BigQuery
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Definición de secciones
# ---------------------------------------------------------------------------
SECCIONES = {
    "inicio": {"icon": "🏠", "label": "INICIO"},
    "aceros_planos": {"icon": "🔩", "label": "ACEROS PLANOS"},
    "aceros_largos": {"icon": "📏", "label": "ACEROS LARGOS"},
    "aceros_sbq": {"icon": "🔑", "label": "ACEROS SBQ"},
    "mercado": {"icon": "🌐", "label": "MERCADO GLOBAL"},
}

# Subsecciones (pestañas horizontales en contenido)
SUBSECCIONES = {
    "inicio": {
        "bienvenida": ("🏠", "Bienvenida"),
    },
    "aceros_planos": {
        "negros": ("⚫", "Negros"),
        "galvanizados": ("✨", "Galvanizados"),
        "formados": ("🔧", "Formados"),
    },
    "aceros_largos": {
        "al_resumen": ("📊", "Resumen Ejecutivo"),
        "al_macro": ("🏦", "Macroeconomía"),
        "al_mercado": ("💹", "Mercado y Costos"),
        "al_operaciones": ("⚙️", "Operaciones"),
        "al_calidad": ("✅", "Calidad"),
    },
    "aceros_sbq": {
        "sbq_soon": ("⏳", "Próximamente"),
    },
    "mercado": {
        "mkt_monitor": ("📡", "Monitor de Quiebres"),
        "mkt_vars": ("🌐", "Variables Globales"),
        "mkt_industria": ("🏭", "Monitor Siderúrgico"),
        "mkt_inegi": ("📊", "Indicadores INEGI"),
    }
}

# Página base por sección + subcategoría
PAGINAS = {
    # INICIO
    "bienvenida": "pages.hub",
    
    # ACEROS PLANOS - Negros
    ("aceros_planos", "negros", "apn_resumen"): "pages.ap_negros.01_resumen",
    ("aceros_planos", "negros", "apn_seg"): "pages.ap_negros.02_segmentacion",
    ("aceros_planos", "negros", "apn_series"): "pages.ap_negros.03_series_tiempo",
    ("aceros_planos", "negros", "apn_forecast"): "pages.ap_negros.04_forecasting",
    ("aceros_planos", "negros", "apn_mix"): "pages.ap_negros.05_mix_productos",
    
    # ACEROS PLANOS - Galvanizados
    ("aceros_planos", "galvanizados", "coming"): "pages.ap_galvanizados.coming_soon",
    
    # ACEROS PLANOS - Formados  
    ("aceros_planos", "formados", "coming"): "pages.ap_formados.coming_soon",
    
    # ACEROS LARGOS
    "al_resumen": "pages.aceros_largos.01_resumen",
    "al_macro": "pages.aceros_largos.02_macroeconomia",
    "al_mercado": "pages.aceros_largos.03_mercado",
    "al_operaciones": "pages.aceros_largos.04_operaciones",
    "al_calidad": "pages.aceros_largos.05_calidad",
    
    # ACEROS SBQ
    "sbq_soon": "pages.aceros_sbq.coming_soon",
    
    # MERCADO
    "mkt_monitor": "pages.mercado.01_monitor",
    "mkt_vars": "pages.mercado.02_variables",
    "mkt_industria": "pages.mercado.03_industria",
    "mkt_inegi": "pages.mercado.04_indicadores",
}

# ---------------------------------------------------------------------------
# Navegación SIDEBAR
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 📍 Navegación")
    
    for seccion_id, seccion in SECCIONES.items():
        btn_type = "primary" if st.session_state.nav_seccion == seccion_id else "secondary"
        if st.button(f"{seccion['icon']} {seccion['label']}", use_container_width=True, type=btn_type, key=f"nav_{seccion_id}"):
            st.session_state.nav_seccion = seccion_id
            #Primera subsección
            first_sub = list(SUBSECCIONES[seccion_id].keys())[0]
            st.session_state.nav_subseccion = first_sub
            st.rerun()

# ---------------------------------------------------------------------------
# Subsecciones horizontales en área de contenido
# ---------------------------------------------------------------------------
seccion_actual = st.session_state.nav_seccion
subsecciones = SUBSECCIONES.get(seccion_actual, SUBSECCIONES["inicio"])

if len(subsecciones) > 1:
    st.markdown('<div class="subsecciones-container">', unsafe_allow_html=True)
    
    cols = st.columns(len(subsecciones))
    for i, (sub_id, (icon, label)) in enumerate(subsecciones.items()):
        with cols[i]:
            btn_type = "primary" if st.session_state.nav_subseccion == sub_id else "secondary"
            if st.button(f"{icon} {label}", type=btn_type, key=f"tab_{sub_id}"):
                st.session_state.nav_subseccion = sub_id
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Cargar página según sección
# ---------------------------------------------------------------------------
seccion = st.session_state.nav_seccion
subseccion = st.session_state.nav_subseccion
modulo = "pages.hub"

if seccion == "inicio":
    modulo = "pages.hub"

elif seccion == "aceros_planos":
    if subseccion == "negros":
        modulo_id = st.session_state.get("nav_modulo_planos", "apn_resumen")
        modulo = PAGINAS.get(("aceros_planos", "negros", modulo_id), "pages.ap_negros.01_resumen")
    elif subseccion == "galvanizados":
        modulo = "pages.ap_galvanizados.coming_soon"
    elif subseccion == "formados":
        modulo = "pages.ap_formados.coming_soon"

elif seccion == "aceros_largos":
    modulo = PAGINAS.get(subseccion, "pages.aceros_largos.01_resumen")

elif seccion == "aceros_sbq":
    modulo = "pages.aceros_sbq.coming_soon"

elif seccion == "mercado":
    modulo = PAGINAS.get(subseccion, "pages.mercado.01_monitor")

# ---------------------------------------------------------------------------
# Tabs para módulos dentro de ACEROS PLANOS
# ---------------------------------------------------------------------------
if seccion == "aceros_planos" and subseccion == "negros":
    MODULOS_NEGROS = {
        "apn_resumen": ("📊", "Resumen Ejecutivo"),
        "apn_seg": ("👥", "Segmentación"),
        "apn_series": ("📈", "Series de Tiempo"),
        "apn_forecast": ("🔮", "Forecasting"),
        "apn_mix": ("🎯", "Mix de Productos"),
    }
    
    st.markdown('<div class="subsecciones-container">', unsafe_allow_html=True)
    cols = st.columns(len(MODULOS_NEGROS))
    for i, (mod_id, (icon, label)) in enumerate(MODULOS_NEGROS.items()):
        with cols[i]:
            active = st.session_state.get("nav_modulo_planos") == mod_id
            btn_type = "primary" if active else "secondary"
            if st.button(f"{label}", type=btn_type, key=f"mod_{mod_id}"):
                st.session_state.nav_modulo_planos = mod_id
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Función para cargar página
# ---------------------------------------------------------------------------
def cargar_pagina(modulo):
    try:
        file_path = os.path.join(_root, modulo.replace(".", os.sep) + ".py")
        if os.path.exists(file_path):
            ns = {"__name__": "__main__", "__file__": file_path}
            exec(open(file_path, encoding="utf-8").read(), ns)
        else:
            st.error(f"Archivo no encontrado: {file_path}")
            renderizar_hub()
    except Exception as e:
        st.error(f"Error cargando {modulo}: {e}")
        renderizar_hub()

# ---------------------------------------------------------------------------
# Función para renderizar hub inline
# ---------------------------------------------------------------------------
def renderizar_hub():
    from config import COLORS, APP_NAME
    
    col1, col2 = st.columns([5, 1])
    with col1:
        st.markdown(
            f"<h2 style='color:{COLORS['primary']};margin-bottom:4px;'>Bienvenido a {APP_NAME}</h2>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<p style='color:#6B7280;'>Selecciona un módulo en el menú lateral.</p>",
            unsafe_allow_html=True,
        )

# ---------------------------------------------------------------------------
# Ejecutar página
# ---------------------------------------------------------------------------
cargar_pagina(modulo)