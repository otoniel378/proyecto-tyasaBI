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
/* ══ SIDEBAR — Nav pills ══ */
[data-testid="stSidebar"] .stButton > button {
    background: #F1F5F9 !important; color: #475569 !important;
    border: 1.5px solid #DDE3EC !important; border-radius: 10px !important;
    padding: 9px 14px !important; margin: 3px 0 !important;
    text-align: left !important; font-size: 0.80rem !important;
    font-weight: 500 !important; width: 100% !important;
    box-shadow: none !important; transform: none !important;
    letter-spacing: 0.01em !important; transition: all 0.15s ease !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: #DBEAFE !important; color: #1E40AF !important;
    border-color: #93C5FD !important; box-shadow: 0 2px 6px rgba(59,130,246,0.15) !important;
}
[data-testid="stSidebar"] .stButton > button[kind="primary"] {
    background: #1B3A5C !important; color: #FFFFFF !important;
    border-color: #1B3A5C !important; font-weight: 700 !important;
    box-shadow: 0 2px 8px rgba(27,58,92,0.25) !important; border-radius: 10px !important;
}
[data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {
    background: #16304E !important; color: #FFFFFF !important; border-color: #16304E !important;
}

/* ══ TABS DE ÁREA Y MÓDULO ══ */
.block-container [data-testid="stHorizontalBlock"] [data-testid="stButton"] {
    width: 100% !important;
}
.block-container [data-testid="stHorizontalBlock"] [data-testid="stColumn"] > div {
    width: 100% !important;
}
.block-container [data-testid="stHorizontalBlock"] [data-testid="stColumn"] {
    display: flex !important; justify-content: center !important;
    align-items: center !important; padding: 5px 10px !important;
}
.block-container [data-testid="stHorizontalBlock"] [data-testid="stButton"] > button {
    width: 100% !important;
    height: 72px !important;
    min-height: 72px !important;
    border-radius: 50px !important;
    font-size: 1.05rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.025em !important;
    border-width: 2.5px !important;
    border-style: solid !important;
    transition: all 0.18s ease !important;
    box-shadow: none !important;
    transform: none !important;
    line-height: 1 !important;
}

/* ══ COLORES — Área tabs — usar SOLO + para no afectar módulos ══ */
[data-testid="stVerticalBlock"]:has(#area-tabs-marker) + [data-testid="stHorizontalBlock"]
  > [data-testid="stColumn"]:nth-child(1) button[kind="secondary"] {
    background: #EFF6FF !important; color: #1E40AF !important; border-color: #BFDBFE !important;
}
[data-testid="stVerticalBlock"]:has(#area-tabs-marker) + [data-testid="stHorizontalBlock"]
  > [data-testid="stColumn"]:nth-child(1) button[kind="primary"] {
    background: #1D4ED8 !important; color: #fff !important; border-color: #1D4ED8 !important;
    box-shadow: 0 6px 20px rgba(29,78,216,0.45) !important;
}
[data-testid="stVerticalBlock"]:has(#area-tabs-marker) + [data-testid="stHorizontalBlock"]
  > [data-testid="stColumn"]:nth-child(2) button[kind="secondary"] {
    background: #ECFDF5 !important; color: #065F46 !important; border-color: #6EE7B7 !important;
}
[data-testid="stVerticalBlock"]:has(#area-tabs-marker) + [data-testid="stHorizontalBlock"]
  > [data-testid="stColumn"]:nth-child(2) button[kind="primary"] {
    background: #059669 !important; color: #fff !important; border-color: #059669 !important;
    box-shadow: 0 6px 20px rgba(5,150,105,0.45) !important;
}
[data-testid="stVerticalBlock"]:has(#area-tabs-marker) + [data-testid="stHorizontalBlock"]
  > [data-testid="stColumn"]:nth-child(3) button[kind="secondary"] {
    background: #FFFBEB !important; color: #92400E !important; border-color: #FCD34D !important;
}
[data-testid="stVerticalBlock"]:has(#area-tabs-marker) + [data-testid="stHorizontalBlock"]
  > [data-testid="stColumn"]:nth-child(3) button[kind="primary"] {
    background: #D97706 !important; color: #fff !important; border-color: #D97706 !important;
    box-shadow: 0 6px 20px rgba(217,119,6,0.45) !important;
}

/* ══ COLORES — Module tabs (module-tabs-marker) ══ */
[data-testid="stVerticalBlock"]:has(#module-tabs-marker) ~ [data-testid="stHorizontalBlock"]
  button[kind="secondary"],
[data-testid="stVerticalBlock"]:has(#module-tabs-marker) + [data-testid="stHorizontalBlock"]
  button[kind="secondary"] {
    background: #EFF6FF !important; color: #1E40AF !important; border-color: #BFDBFE !important;
}
[data-testid="stVerticalBlock"]:has(#module-tabs-marker) ~ [data-testid="stHorizontalBlock"]
  button[kind="secondary"]:hover,
[data-testid="stVerticalBlock"]:has(#module-tabs-marker) + [data-testid="stHorizontalBlock"]
  button[kind="secondary"]:hover {
    background: #DBEAFE !important; box-shadow: 0 4px 14px rgba(59,130,246,0.28) !important;
    transform: translateY(-2px) !important;
}
[data-testid="stVerticalBlock"]:has(#module-tabs-marker) ~ [data-testid="stHorizontalBlock"]
  button[kind="primary"],
[data-testid="stVerticalBlock"]:has(#module-tabs-marker) + [data-testid="stHorizontalBlock"]
  button[kind="primary"] {
    background: #1B3A5C !important; color: #fff !important; border-color: #1B3A5C !important;
    box-shadow: 0 6px 18px rgba(27,58,92,0.42) !important;
}
[data-testid="stVerticalBlock"]:has(#module-tabs-marker) ~ [data-testid="stHorizontalBlock"]
  button[kind="primary"]:hover,
[data-testid="stVerticalBlock"]:has(#module-tabs-marker) + [data-testid="stHorizontalBlock"]
  button[kind="primary"]:hover {
    background: #16304E !important; transform: translateY(-2px) !important;
}

/* ══ Reducir altura para módulos (5 botones, más compactos) ══ */
[data-testid="stVerticalBlock"]:has(#module-tabs-marker) ~ [data-testid="stHorizontalBlock"]
  [data-testid="stButton"] > button,
[data-testid="stVerticalBlock"]:has(#module-tabs-marker) + [data-testid="stHorizontalBlock"]
  [data-testid="stButton"] > button {
    height: 60px !important;
    min-height: 60px !important;
    font-size: 0.88rem !important;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Header estilo Power BI
# ---------------------------------------------------------------------------
st.markdown("""
<div style="
    background:#1B3A5C;
    padding:10px 20px;
    margin:-0.4rem -0.9rem 14px -0.9rem;
    display:flex;align-items:center;justify-content:space-between;
">
    <div style="display:flex;align-items:center;gap:10px;">
        <span style="font-size:1.1rem;">🏭</span>
        <div>
            <div style="color:#FFFFFF;font-size:0.88rem;font-weight:700;
                        letter-spacing:0.01em;font-family:'Segoe UI',sans-serif;line-height:1.2;">
                TYASA Business Intelligence
            </div>
            <div style="color:rgba(255,255,255,0.55);font-size:0.62rem;font-weight:500;
                        letter-spacing:0.06em;text-transform:uppercase;">
                Plataforma de Inteligencia Comercial
            </div>
        </div>
    </div>
    <div style="display:flex;align-items:center;gap:12px;">
        <span style="color:rgba(255,255,255,0.35);font-size:0.62rem;font-weight:600;
                     letter-spacing:0.08em;text-transform:uppercase;">
            Streamlit · BigQuery · GCP
        </span>
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
        "negros": ("⚫", "Aceros Negros"),
        "galvanizados": ("✨", "Aceros Galvanizados"),
        "formados": ("🔧", "Aceros Formados"),
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
    st.markdown("<div style='margin-bottom:8px'></div>", unsafe_allow_html=True)
    
    for seccion_id, seccion in SECCIONES.items():
        btn_type = "primary" if st.session_state.nav_seccion == seccion_id else "secondary"
        if st.button(f"{seccion['icon']} {seccion['label']}", use_container_width=True, type=btn_type, key=f"nav_{seccion_id}"):
            st.session_state.nav_seccion = seccion_id
            first_sub = list(SUBSECCIONES[seccion_id].keys())[0]
            st.session_state.nav_subseccion = first_sub
            st.rerun()

# ---------------------------------------------------------------------------
# Subsecciones horizontales en área de contenido
# ---------------------------------------------------------------------------
seccion_actual = st.session_state.nav_seccion
subsecciones = SUBSECCIONES.get(seccion_actual, SUBSECCIONES["inicio"])

if len(subsecciones) > 1:
    st.markdown('<div id="area-tabs-marker" style="display:none"></div>', unsafe_allow_html=True)
    all_cols = st.columns([1] * len(subsecciones))
    tab_cols = all_cols
    for i, (sub_id, (icon, label)) in enumerate(subsecciones.items()):
        with tab_cols[i]:
            btn_type = "primary" if st.session_state.nav_subseccion == sub_id else "secondary"
            if st.button(f"{icon}  {label}", type=btn_type, key=f"tab_{sub_id}"):
                st.session_state.nav_subseccion = sub_id
                st.rerun()
    st.markdown("<div style='margin-bottom:12px'></div>", unsafe_allow_html=True)

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
        "apn_forecast": ("🔮", "Pronóstico"),
        "apn_mix": ("🎯", "Mix de Productos"),
    }

    st.markdown('<div id="module-tabs-marker" style="display:none"></div>', unsafe_allow_html=True)
    mod_all = st.columns([1] * len(MODULOS_NEGROS))
    mod_cols = mod_all
    for i, (mod_id, (icon, label)) in enumerate(MODULOS_NEGROS.items()):
        with mod_cols[i]:
            active = st.session_state.get("nav_modulo_planos") == mod_id
            btn_type = "primary" if active else "secondary"
            if st.button(f"{icon} {label}", type=btn_type, key=f"mod_{mod_id}"):
                st.session_state.nav_modulo_planos = mod_id
                st.rerun()
    st.markdown("<div style='margin-bottom:10px'></div>", unsafe_allow_html=True)

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