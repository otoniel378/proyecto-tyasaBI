"""
config.py — Configuracion global de TYASA BI.
Centraliza proyecto GCP, paleta de colores y parametros analiticos.
Arquitectura multi-area: Aceros Planos | Aceros Largos | Aceros SBQ
"""

import os

# ---------------------------------------------------------------------------
# Google Cloud / BigQuery
# ---------------------------------------------------------------------------
GCP_PROJECT_ID = "project-d0cf2519-d089-47d3-930"
BQ_DATASET     = "tyasa_bi"

# ---------------------------------------------------------------------------
# Areas del proyecto
# ---------------------------------------------------------------------------
AREAS = {
    "aceros_planos": {
        "nombre": "Aceros Planos",
        "icono":  "🔩",
        "responsable": "Otoniel",
        "subsecciones": {
            "castrip":      {"nombre": "CASTRIP",             "status": "activo",       "icono": "⚡"},
            "negros":       {"nombre": "Aceros Negros",       "status": "activo",       "icono": "⚫"},
            "galvanizados": {"nombre": "Aceros Galvanizados", "status": "en_desarrollo", "icono": "✨"},
            "formados":     {"nombre": "Aceros Formados",     "status": "en_desarrollo", "icono": "🔧"},
        },
    },
    "aceros_largos": {
        "nombre": "Aceros Largos",
        "icono":  "📏",
        "responsable": "Por definir",
        "subsecciones": {},
    },
    "aceros_sbq": {
        "nombre": "Aceros SBQ",
        "icono":  "🔑",
        "responsable": "Por definir",
        "subsecciones": {},
    },
}

# ---------------------------------------------------------------------------
# Rutas locales
# ---------------------------------------------------------------------------
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
EXPORTS_DIR = os.path.join(BASE_DIR, "exports")
ASSETS_DIR  = os.path.join(BASE_DIR, "assets")

# ---------------------------------------------------------------------------
# Metadata de la app
# ---------------------------------------------------------------------------
APP_NAME     = "TYASA BI"
APP_SUBTITLE = "Plataforma de Inteligencia Comercial"
APP_ICON     = "🏭"

# ---------------------------------------------------------------------------
# Paleta de colores — Tema ejecutivo claro (Power BI light)
# ---------------------------------------------------------------------------
COLORS = {
    "primary":    "#0078D4",   # Azul Microsoft — acciones, links
    "secondary":  "#1B3A5C",   # Azul oscuro
    "accent":     "#D83B01",   # Naranja Power BI
    "neutral":    "#605E5C",   # Gris texto secundario
    "background": "#F3F2F1",   # Fondo principal gris cálido
    "surface":    "#FFFFFF",   # Superficie tarjetas/paneles
    "surface2":   "#FAF9F8",   # Superficie secundaria
    "text":       "#252423",   # Texto principal casi negro
    "text_light": "#605E5C",   # Texto atenuado
    "success":    "#107C10",   # Verde Microsoft
    "warning":    "#D29200",   # Amarillo/naranja Microsoft
    "danger":     "#A80000",   # Rojo Microsoft
    "border":     "#EDEBE9",   # Borde gris claro
}

COLOR_SEQUENCE = [
    "#0078D4", "#D83B01", "#107C10", "#8764B8",
    "#D29200", "#00B294", "#A80000", "#2B88D8",
    "#498205", "#CA5010", "#5C2D91", "#004B50",
    "#FFB900", "#0062AF", "#4B1D52",
]

HEATMAP_COLORSCALE = [
    [0.0,  "#F3F2F1"],
    [0.20, "#C7E0F4"],
    [0.45, "#71AFE5"],
    [0.70, "#0078D4"],
    [1.0,  "#D83B01"],
]

# ---------------------------------------------------------------------------
# Parametros analiticos
# ---------------------------------------------------------------------------
FORECAST_HORIZON_DEFAULT = 6
FORECAST_HORIZON_MAX     = 24
MIN_PERIODS_FORECAST     = 12
PARETO_THRESHOLD_A       = 0.80
PARETO_THRESHOLD_B       = 0.95
