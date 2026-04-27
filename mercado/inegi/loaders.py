"""
loaders.py — Funciones de carga para indicadores INEGI desde BigQuery.
"""

import pandas as pd
import streamlit as st
from core.db_connector import run_query, table_ref

T_INDICADORES = table_ref("gold_indicadores_inegi")

INDICADORES_CONFIG = {
    # GRUPO 1: IMAI - Actividad Industrial
    "736414": "IMAI_Construccion_Total",
    "736476": "IMAI_MetalicasBasicas_331",
    "736475": "IMAI_HierroAcero_3311",
    "736481": "IMAI_ProductosMetalicos_332",
    "736491": "IMAI_MaquinariaEquipo_333",
    "736418": "IMAI_Manufactureras_Total",
    "736407": "IMAI_ActividadIndustrial_Total",
    "736526": "IMAI_EquipoTransporte_336",
    "736594": "IMAI_Construccion_2",
    "736533": "IMAI_MetalicasBasicas_2",
    
    # GRUPO 2: EMIM + ENEC + EMEC
    "910468": "EMIM_VolFisico_Desest_Indice",
    "910470": "EMIM_VolFisico_Desest_VarAnual",
    "720332": "ENEC_ValorProd_Total",
    "720334": "ENEC_ValorProd_Edificacion",
    "720340": "ENEC_ValorProd_Transporte_Urb",
    "718504": "EMEC_Ingresos_ComercioMayor_43",
    "718506": "EMEC_Ingresos_ComercioMenor_46",
    
    # GRUPO 3: IGAE + Balanza Comercial
    "737173": "IGAE_Secundario_IndiceVolFisico",
    "737149": "IGAE_Secundario_VarAnual",
    "133094": "BC_Siderurgia_Importaciones",
    "133031": "BC_Siderurgia_Exportaciones",
    
    # GRUPO 4: INPP - Precios al Productor
    "910503": "INPP_Manufactura_3133",
    "910502": "INPP_Construccion_23",
    "910501": "INPP_Energia_22",
    "910500": "INPP_Mineria_SinPetroleo",
    "910499": "INPP_Mineria_ConPetroleo",
    
    # GRUPO 5: INPC - Precios al Consumidor
    "909294": "INPC_Energeticos",
    "910396": "INPC_Total",
    
    # GRUPO 6: IFB - Formacion Bruta de Capital Fijo
    "910398": "IFB_Total",
    "910393": "IFB_Construccion",
    "741034": "IFB_MaquinariaEquipo_Total",
    "741030": "IFB_MaquinariaEquipo_Importado",
"741025": "IFB_MaquinariaEquipo_Nacional",
}


@st.cache_data(ttl=3600, show_spinner="Cargando indicadores INEGI...")
def load_todos_indicadores() -> pd.DataFrame:
    """Carga todos los indicadores disponibles."""
    sql = f"""
        SELECT Clave, Nombre, Fecha, Valor
        FROM {T_INDICADORES}
        ORDER BY Clave, Fecha DESC
    """
    return run_query(sql)


@st.cache_data(ttl=3600, show_spinner="Cargando indicador...")
def load_indicador(clave: str) -> pd.DataFrame:
    """Carga un indicador específico por clave."""
    sql = f"""
        SELECT Fecha, Valor, Nombre
        FROM {T_INDICADORES}
        WHERE Clave = '{clave}'
        ORDER BY Fecha DESC
        LIMIT 500
    """
    df = run_query(sql)
    if not df.empty:
        if "Fecha" in df.columns:
            df["Fecha"] = pd.to_datetime(df["Fecha"], format="%Y-%m", errors="coerce")
    return df


@st.cache_data(ttl=3600)
def load_indicadores_por_grupo(grupo: str) -> pd.DataFrame:
    """Carga indicadores por grupo."""
    clves = [c for c, n in INDICADORES_CONFIG.items() if grupo.upper() in n.upper()]
    if not clves:
        return pd.DataFrame()
    
    sql = f"""
        SELECT Clave, Nombre, Fecha, Valor
        FROM {T_INDICADORES}
        WHERE Clave IN ({','.join([f"'{c}'" for c in clves])})
        ORDER BY Clave, Fecha DESC
    """
    return run_query(sql)


@st.cache_data(ttl=3600)
def load_serie(clave: str, periodos: int = 24) -> pd.DataFrame:
    """Carga últimos N periodos de un indicador."""
    sql = f"""
        SELECT Fecha, Valor
        FROM {T_INDICADORES}
        WHERE Clave = '{clave}'
        ORDER BY Fecha DESC
        LIMIT {periodos}
    """
    df = run_query(sql)
    if not df.empty:
        if "Fecha" in df.columns:
            df["Fecha"] = pd.to_datetime(df["Fecha"], format="%Y-%m", errors="coerce")
            df = df.sort_values("Fecha")
    return df