"""
aceros_largos/loaders.py — Loaders de datos para Aceros Largos
Convierte los endpoints de tu FastAPI a funciones cacheadas para Streamlit
"""

import streamlit as st
from typing import Dict, List, Any
from datetime import datetime

# ---------------------------------------------------------------------------
# MOCK DATA — En producción, conectar a BigQuery o APIs externas
# ---------------------------------------------------------------------------

@st.cache_data(ttl=600)
def load_ticker_data() -> List[Dict[str, str]]:
    """Carga datos del ticker superior"""
    return [
        {"label": "Chatarra HMS", "value": "$3,380 MXN/ton", "color": "tertiary"},
        {"label": "USD/MXN", "value": "$17.82", "color": "white"},
        {"label": "Banxico Rate", "value": "7.00%", "color": "secondary"},
        {"label": "Construcción", "value": "-15.6% YoY", "color": "tertiary"},
        {"label": "Inv. Pública", "value": "$542 mil mdp", "color": "white"},
        {"label": "Arancel China", "value": "25-50%", "color": "tertiary"},
        {"label": "Expo MX→USA", "value": "-49%", "color": "tertiary"},
        {"label": "TYASA Laminador", "value": "$450 MDD inv.", "color": "secondary"},
        {"label": "CMIC 2026-29", "value": "+2.6% prom.", "color": "secondary"}
    ]

@st.cache_data(ttl=600)
def load_executive_summary() -> Dict[str, Any]:
    """Carga datos del resumen ejecutivo"""
    return {
        "ebitda": {
            "label": "EBITDA Mensual Est.",
            "value": "$10.8M",
            "trend": "-12.9% vs 2024",
            "trend_type": "down",
            "unit": "USD"
        },
        "margin": {
            "label": "Margen Operativo",
            "value": "14.2%",
            "trend": "-2.8 pp vs 2024",
            "trend_type": "down",
            "unit": "Crisis construcción"
        },
        "sales_trend": [
            {"mes": "Ago", "ventas": 94},
            {"mes": "Sep", "ventas": 87},
            {"mes": "Oct", "ventas": 82},
            {"mes": "Nov", "ventas": 71},
            {"mes": "Dic", "ventas": 76},
            {"mes": "Ene", "ventas": 80},
            {"mes": "Feb", "ventas": 83},
            {"mes": "Mar", "ventas": 88}
        ],
        "production_goals": [
            {"label": "Varilla Corrugada", "pct": 78, "color": "#ffb3ad", "text_color": "tertiary"},
            {"label": "Alambrón", "pct": 72, "color": "#ffb3ad", "text_color": "tertiary"},
            {"label": "Perfiles Estruct.", "pct": 88, "color": "#4edea3", "text_color": "secondary"}
        ],
        "regional_sales": [
            {"label": "Nacional (México)", "pct": 81, "color": "green"},
            {"label": "Exportación (USA)", "pct": 11, "color": "red"},
            {"label": "LATAM", "pct": 8, "color": "blue"}
        ]
    }

@st.cache_data(ttl=600)
def load_macro_data() -> Dict[str, Any]:
    """Carga datos macroeconómicos"""
    return {
        "interest_rate": {
            "label": "Tasa de Interés (Banxico)",
            "value": "7.00%",
            "trend": "Pausada 2026",
            "trend_type": "down",
            "unit": "Recorte Dic 2025"
        },
        "inflation": {
            "label": "Inflación Materiales (INPC)",
            "value": "3.93%",
            "trend": "-0.52 pp vs pico",
            "trend_type": "down",
            "unit": "Fin 2025"
        },
        "construction_trend": [
            {"mes": "Ene'25", "val": -4.1},
            {"mes": "Mar'25", "val": -5.8},
            {"mes": "May'25", "val": -6.3},
            {"mes": "Jul'25", "val": -8.5},
            {"mes": "Sep'25", "val": -7.2},
            {"mes": "Nov'25", "val": -15.6},
            {"mes": "Pron'26", "val": 2.6}
        ],
        "market_signals": [
            {"label": "Construcción residencial", "val": "-15.6% Nov'25", "impacto": "Alto"},
            {"label": "Inversión pública 2025", "val": "$542 mil mdp", "impacto": "Alto"},
            {"label": "Recorte inversión pública", "val": "-9.7% interan.", "impacto": "Alto"},
            {"label": "Tasa Banxico (dic 2025)", "val": "7.00%", "impacto": "Medio"},
            {"label": "Arancel China acero", "val": "25–50%", "impacto": "Alto"},
            {"label": "Expo México→USA", "val": "-49%", "impacto": "Alto"},
            {"label": "Nearshoring (oportunidad)", "val": "Activo 2026", "impacto": "Oport."}
        ]
    }

@st.cache_data(ttl=600)
def load_market_data() -> Dict[str, Any]:
    """Carga datos de mercado y costos"""
    return {
        "usd_mxn": {
            "label": "USD / MXN Spot",
            "value": "$17.82",
            "trend": "+1.64%",
            "trend_type": "up",
            "unit": "Depreciación MXN"
        },
        "scrap_price": {
            "label": "Chatarra / Scrap (Platts)",
            "value": "$3,380",
            "trend": "-2.1% vs mes ant.",
            "trend_type": "down",
            "unit": "MXN / Ton  ·  Dic 2025"
        }
    }

@st.cache_data(ttl=600)
def load_operations_data() -> Dict[str, Any]:
    """Carga datos de operaciones e inventario"""
    return {
        "production": {
            "label": "Producción Diaria",
            "value": "1,850",
            "trend": "-3.1% vs plan",
            "trend_type": "down",
            "unit": "MT / Día"
        },
        "scrap_stock": {
            "label": "Chatarra en Stock",
            "value": "48,200",
            "trend": "+6.8% acumulación",
            "trend_type": "up",
            "unit": "MT · Presión costo"
        },
        "equipment_status": [
            {"name": "Horno de Arco Eléctrico (EAF)", "status": "Operativo", "color": "secondary"},
            {"name": "Tren de Laminación (existente)", "status": "Operativo", "color": "secondary"},
            {"name": "Nuevo Laminador ($450 MDD)", "status": "En instalación", "color": "primary"},
            {"name": "Planta de Oxígeno", "status": "Mantenimiento", "color": "tertiary"}
        ],
        "inventory": [
            {"name": "Varilla", "mt": 18750, "max": 25000, "color": "#ffb3ad", "pct": 75},
            {"name": "Alambrón", "mt": 10400, "max": 15000, "color": "#ffb3ad", "pct": 69},
            {"name": "Perfiles", "mt": 4150, "max": 12000, "color": "#4edea3", "pct": 35}
        ]
    }

@st.cache_data(ttl=600)
def load_quality_data() -> Dict[str, Any]:
    """Carga datos de calidad y certificaciones"""
    return {
        "quality_index": {
            "label": "Índice de Calidad",
            "value": "99.85%",
            "trend": "+0.05% vs Q3",
            "trend_type": "up",
            "unit": "% Aprobación lotes"
        },
        "certs_count": {
            "label": "Certificaciones Activas",
            "value": "12",
            "trend": "Todas vigentes",
            "trend_type": "up",
            "unit": "Normas sísmicas incl."
        },
        "tests": [
            {"test": "Pruebas de Tensión", "result": "100% Aprobado", "ok": True},
            {"test": "Análisis Químico", "result": "100% Aprobado", "ok": True},
            {"test": "Doblado en Frío", "result": "100% Aprobado", "ok": True},
            {"test": "Resistencia Sísmica", "result": "100% Aprobado", "ok": True},
            {"test": "Geometría y Resalles", "result": "99.7% Aprob.", "ok": True}
        ],
        "certifications": [
            {"name": "ISO 9001:2015", "desc": "Gestión de Calidad", "active": True},
            {"name": "ISO 14001:2015", "desc": "Gestión Ambiental", "active": True},
            {"name": "NMX-B-457-CANACERO", "desc": "Varilla Corrugada Nacional", "active": True},
            {"name": "ASTM A615 Gr.60", "desc": "Exportación USA", "active": True},
            {"name": "NTC-2017 Sísmica (CDMX)", "desc": "Resistencia Antisísmica", "active": True},
            {"name": "ISO 45001:2018", "desc": "Seguridad Ocupacional", "active": True}
        ]
    }

# ---------------------------------------------------------------------------
# UTILS
# ---------------------------------------------------------------------------

def get_last_update() -> str:
    """Retorna timestamp de última actualización"""
    return datetime.now().strftime("%Y-%m-%d · %H:%M CST")

def get_data_sources() -> List[str]:
    """Retorna las fuentes de datos"""
    return ["Bloomberg & Platts API", "CANACERO", "INEGI"]