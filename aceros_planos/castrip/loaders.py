"""
loaders.py — Funciones de carga desde BigQuery para CASTRIP (Aceros Planos).
Reutiliza la misma estructura de gold_tables que aceros_negros,
filtrando por AREA = 'CASTRIP'.
"""

import pandas as pd
import streamlit as st
from core.db_connector import run_query, table_ref

T_SILVER   = table_ref("silver_ventas_limpias")
T_CLIENTE  = table_ref("gold_demanda_cliente")
T_PRODUCTO = table_ref("gold_demanda_producto")
T_MENSUAL  = table_ref("gold_demanda_mensual")
T_CLI_PROD = table_ref("gold_cliente_producto")
T_PROCESO  = table_ref("gold_demanda_proceso")

AREA_FILTER = "CASTRIP"


@st.cache_data(ttl=600, show_spinner="Cargando demanda por cliente...")
def load_gold_demanda_cliente() -> pd.DataFrame:
    sql = f"""
        SELECT CLIENTE, AREA, DIVISION,
               PESO_TON, N_EMBARQUES,
               PRIMERA_COMPRA, ULTIMA_COMPRA
        FROM {T_CLIENTE}
        WHERE AREA = '{AREA_FILTER}'
    """
    df = run_query(sql)
    if not df.empty:
        df["PESO_TON"] = pd.to_numeric(df["PESO_TON"], errors="coerce").fillna(0)
    return df


@st.cache_data(ttl=600, show_spinner="Cargando demanda por producto...")
def load_gold_demanda_producto() -> pd.DataFrame:
    sql = f"""
        SELECT PRODUCTO_LIMPIO, AREA, DIVISION,
               PESO_TON, N_CLIENTES
        FROM {T_PRODUCTO}
        WHERE AREA = '{AREA_FILTER}'
    """
    df = run_query(sql)
    if not df.empty:
        df["PESO_TON"] = pd.to_numeric(df["PESO_TON"], errors="coerce").fillna(0)
    return df


@st.cache_data(ttl=600, show_spinner="Cargando serie mensual total...")
def load_gold_demanda_mensual_total() -> pd.DataFrame:
    sql = f"""
        SELECT PERIODO, ANIO, MES,
               SUM(PESO_TON)   AS PESO_TON,
               SUM(N_CLIENTES) AS N_CLIENTES,
               SUM(N_EMBARQUES) AS N_EMBARQUES
        FROM {T_MENSUAL}
        WHERE AREA = '{AREA_FILTER}'
        GROUP BY PERIODO, ANIO, MES
        ORDER BY PERIODO
    """
    df = run_query(sql)
    if not df.empty:
        df["PESO_TON"] = pd.to_numeric(df["PESO_TON"], errors="coerce").fillna(0)
        df["PERIODO"] = pd.to_datetime(df["PERIODO"], errors="coerce")
    return df


@st.cache_data(ttl=600, show_spinner="Cargando serie mensual por cliente...")
def load_gold_demanda_mensual_cliente() -> pd.DataFrame:
    sql = f"""
        SELECT PERIODO, CLIENTE, SUM(PESO_TON) AS PESO_TON
        FROM {T_SILVER}
        WHERE AREA = '{AREA_FILTER}'
        GROUP BY PERIODO, CLIENTE
        ORDER BY PERIODO, CLIENTE
    """
    df = run_query(sql)
    if not df.empty:
        df["PESO_TON"] = pd.to_numeric(df["PESO_TON"], errors="coerce").fillna(0)
        df["PERIODO"] = pd.to_datetime(df["PERIODO"], errors="coerce")
    return df


@st.cache_data(ttl=600, show_spinner="Cargando serie mensual por producto...")
def load_gold_demanda_mensual_producto() -> pd.DataFrame:
    sql = f"""
        SELECT PERIODO, ANIO, MES, PRODUCTO_LIMPIO,
               PESO_TON, N_CLIENTES
        FROM {T_MENSUAL}
        WHERE AREA = '{AREA_FILTER}'
        ORDER BY PERIODO, PRODUCTO_LIMPIO
    """
    df = run_query(sql)
    if not df.empty:
        df["PESO_TON"] = pd.to_numeric(df["PESO_TON"], errors="coerce").fillna(0)
        df["PERIODO"] = pd.to_datetime(df["PERIODO"], errors="coerce")
    return df


@st.cache_data(ttl=600, show_spinner="Cargando matriz cliente × producto...")
def load_gold_cliente_producto() -> pd.DataFrame:
    sql = f"""
        SELECT CLIENTE, PRODUCTO_LIMPIO, AREA, DIVISION,
               PESO_TON, N_EMBARQUES
        FROM {T_CLI_PROD}
        WHERE AREA = '{AREA_FILTER}'
    """
    df = run_query(sql)
    if not df.empty:
        df["PESO_TON"] = pd.to_numeric(df["PESO_TON"], errors="coerce").fillna(0)
    return df


@st.cache_data(ttl=600, show_spinner="Cargando ventas detalladas...")
def load_silver_ventas(n_meses: int = 24) -> pd.DataFrame:
    sql = f"""
        SELECT CLIENTE, PRODUCTO_LIMPIO, AREA, DIVISION,
               PERIODO, ANIO, MES,
               PESO_TON, N_EMBARQUES
        FROM {T_SILVER}
        WHERE AREA = '{AREA_FILTER}'
          AND PERIODO >= DATE_SUB(CURRENT_DATE(), INTERVAL {n_meses} MONTH)
        ORDER BY PERIODO DESC, CLIENTE
    """
    df = run_query(sql)
    if not df.empty:
        df["PESO_TON"] = pd.to_numeric(df["PESO_TON"], errors="coerce").fillna(0)
        df["PERIODO"] = pd.to_datetime(df["PERIODO"], errors="coerce")
    return df
