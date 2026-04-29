"""
aceros_largos/loaders_new_data.py — Loaders for New BigQuery Data
Carga datos de las nuevas tablas INEGI y comercio acero desde BigQuery
"""

import re
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from core.db_connector import get_bq_client, table_ref

# ---------------------------------------------------------------------------
# CONFIGURACIÓN
# ---------------------------------------------------------------------------
CACHE_TTL = 600  # 10 minutes cache as per project standards

CONSTRUCCION_SEGMENT_CASE = """
CASE
    WHEN REGEXP_CONTAINS(LOWER(CONCAT(COALESCE(indicador, ''), ' ', COALESCE(descripcion, ''))), r'(^|[^0-9])236([^0-9]|$)|edificaci') THEN '236 Edificación'
    WHEN REGEXP_CONTAINS(LOWER(CONCAT(COALESCE(indicador, ''), ' ', COALESCE(descripcion, ''))), r'(^|[^0-9])237([^0-9]|$)|ingenier[ií]a civil|obras de ingenier') THEN '237 Obras de ingeniería civil'
    WHEN REGEXP_CONTAINS(LOWER(CONCAT(COALESCE(indicador, ''), ' ', COALESCE(descripcion, ''))), r'(^|[^0-9])238([^0-9]|$)|trabajos especializados') THEN '238 Trabajos especializados'
    WHEN REGEXP_CONTAINS(LOWER(CONCAT(COALESCE(indicador, ''), ' ', COALESCE(descripcion, ''))), r'(^|[^0-9])23([^0-9]|$)|construcci') THEN '23 Construcción total'
    ELSE NULL
END
"""


def _safe_to_datetime(df: pd.DataFrame, column: str = 'fecha') -> pd.DataFrame:
    if not df.empty and column in df.columns:
        df[column] = pd.to_datetime(df[column], errors='coerce')
        df = df.dropna(subset=[column])
    return df


def _choose_preferred_series(
    df: pd.DataFrame,
    description_col: str = 'descripcion',
    preferred_patterns: Optional[List[str]] = None,
) -> pd.DataFrame:
    """Selecciona UNA serie consistente para evitar mezclar conceptos/unidades."""
    if df.empty or description_col not in df.columns:
        return df

    preferred_patterns = preferred_patterns or []
    descriptions = [d for d in df[description_col].dropna().astype(str).unique().tolist() if d]
    if not descriptions:
        return df

    for pattern in preferred_patterns:
        matches = [d for d in descriptions if re.search(pattern, d, flags=re.IGNORECASE)]
        if matches:
            counts = (
                df[df[description_col].isin(matches)]
                .groupby(description_col)
                .size()
                .sort_values(ascending=False)
            )
            if not counts.empty:
                chosen = counts.index[0]
                return df[df[description_col] == chosen].copy()

    counts = df.groupby(description_col).size().sort_values(ascending=False)
    chosen = counts.index[0]
    return df[df[description_col] == chosen].copy()


def _calculate_delta(df: pd.DataFrame, value_col: str = 'valor', mode: str = 'pct_change') -> float:
    if df.empty or len(df) < 2 or value_col not in df.columns:
        return 0.0

    ordered = df.sort_values('fecha', ascending=False).reset_index(drop=True)
    latest = pd.to_numeric(ordered.loc[0, value_col], errors='coerce')
    previous = pd.to_numeric(ordered.loc[1, value_col], errors='coerce')
    if pd.isna(latest) or pd.isna(previous):
        return 0.0

    if mode == 'diff':
        return float(latest - previous)

    if previous == 0:
        return 0.0
    return float(((latest - previous) / previous) * 100)


def _annual_pct_change_from_index(df: pd.DataFrame, value_col: str = 'valor', periods: int = 12) -> float:
    """Convierte un índice mensual en variación anual porcentual."""
    if df.empty or len(df) <= periods or value_col not in df.columns:
        return 0.0

    ordered = df.sort_values('fecha', ascending=False).reset_index(drop=True)
    latest = pd.to_numeric(ordered.loc[0, value_col], errors='coerce')
    base = pd.to_numeric(ordered.loc[periods, value_col], errors='coerce')
    if pd.isna(latest) or pd.isna(base) or base == 0:
        return 0.0
    return float(((latest / base) - 1) * 100)


@st.cache_data(ttl=CACHE_TTL)
def load_banxico_series(table_name: str, limit_months: int = 24) -> pd.DataFrame:
    """Carga una serie simple de Banxico para KPIs robustos."""
    try:
        client = get_bq_client()
        ref = table_ref(table_name)
        query = f"""
        SELECT fecha, valor, indicador
        FROM {ref}
        WHERE fecha >= DATE_SUB(CURRENT_DATE(), INTERVAL {limit_months} MONTH)
        ORDER BY fecha DESC
        """
        df = client.query(query).to_dataframe()
        return _safe_to_datetime(df)
    except Exception:
        return pd.DataFrame()

# ---------------------------------------------------------------------------
# INEGI LOADERS
# ---------------------------------------------------------------------------

@st.cache_data(ttl=CACHE_TTL)
def load_inegi_inpc_data(limit_months: int = 24) -> pd.DataFrame:
    """
    Carga datos de INPC desde gold_inegi_manual_inpc
    
    Args:
        limit_months: Número de meses hacia atrás desde hoy
    
    Returns:
        DataFrame con datos de INPC
    """
    try:
        client = get_bq_client()
        ref = table_ref('gold_inegi_manual_inpc')
        
        query = f"""
        SELECT 
            fecha,
            periodo,
            valor,
            concepto,
            descripcion,
            fecha_procesamiento
        FROM {ref}
        WHERE fecha >= DATE_SUB(CURRENT_DATE(), INTERVAL {limit_months} MONTH)
        ORDER BY fecha DESC, concepto
        """
        
        df = client.query(query).to_dataframe()
        
        # Clean and process data
        if not df.empty:
            df['fecha'] = pd.to_datetime(df['fecha'])
            df['concepto_clean'] = df['concepto'].str.replace('Índice nacional de precios al consumidor (mensual), Resumen, Subíndices subyacente y complementarios, ', '')
        
        return df
        
    except Exception as e:
        st.warning(f"Error cargando datos INPC: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=CACHE_TTL)
def load_inegi_construccion_data(limit_months: int = 24) -> pd.DataFrame:
    """
    Carga datos del sector construcción desde gold_inegi_manual_construccion
    
    Args:
        limit_months: Número de meses hacia atrás desde hoy
    
    Returns:
        DataFrame con datos de construcción
    """
    try:
        df = load_inegi_construccion_segmented(limit_months)
        if df.empty:
            return df

        total_construccion = df[df['segmento'] == '23 Construcción total'].copy()
        if total_construccion.empty:
            return df

        total_construccion = _choose_preferred_series(
            total_construccion,
            preferred_patterns=[r'variaci[oó]n porcentual anual', r'variaci[oó]n porcentual respecto al mismo mes', r'índice de volumen físico']
        )
        return total_construccion.sort_values('fecha', ascending=False)
        
    except Exception as e:
        st.warning(f"Error cargando datos construcción: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=CACHE_TTL)
def load_inegi_construccion_segmented(limit_months: int = 24) -> pd.DataFrame:
    """Carga y clasifica construcción INEGI en 23/236/237/238."""
    try:
        client = get_bq_client()
        ref = table_ref('gold_inegi_manual_construccion')

        query = f"""
        SELECT *
        FROM (
            SELECT
                fecha,
                periodo,
                valor,
                indicador,
                descripcion,
                {CONSTRUCCION_SEGMENT_CASE} AS segmento
            FROM {ref}
            WHERE fecha >= DATE_SUB(CURRENT_DATE(), INTERVAL {limit_months} MONTH)
        )
        WHERE segmento IS NOT NULL
        ORDER BY fecha DESC
        """

        df = client.query(query).to_dataframe()
        if not df.empty:
            df = _safe_to_datetime(df)
        return df
    except Exception as e:
        st.warning(f"Error cargando construcción segmentada: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=CACHE_TTL)
def load_internal_demand_aceros_largos(limit_months: int = 24) -> pd.DataFrame:
    """Demanda interna mensual de Aceros Largos desde tabla curada."""
    try:
        client = get_bq_client()
        ref = table_ref('gold_demanda_mensual')

        query = f"""
        SELECT
            DATE(PERIODO) AS fecha,
            SUM(PESO_TON) AS peso_ton,
            SUM(N_CLIENTES) AS n_clientes,
            SUM(N_EMBARQUES) AS n_embarques
        FROM {ref}
        WHERE DATE(PERIODO) >= DATE_SUB(CURRENT_DATE(), INTERVAL {limit_months} MONTH)
          AND (
            UPPER(AREA) = 'LARGOS'
            OR REGEXP_CONTAINS(UPPER(COALESCE(DIVISION, '')), r'LARG')
          )
        GROUP BY DATE(PERIODO)
        ORDER BY fecha DESC
        """

        df = client.query(query).to_dataframe()
        if not df.empty:
            df['fecha'] = pd.to_datetime(df['fecha'])
        return df
    except Exception as e:
        st.warning(f"Error cargando demanda interna de aceros largos: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=CACHE_TTL)
def load_macro_market_series(limit_months: int = 24) -> pd.DataFrame:
    """Carga USD/MXN desde variables curadas.

    Importante: no inferir tipo de cambio con regex amplio sobre cualquier texto
    que contenga "USD" o "MXN". La tabla de mercado incluye series financieras
    con unidades distintas; mezclarlas produce valores imposibles.
    Sólo se acepta una serie explícita de tipo de cambio y valores razonables.
    """
    try:
        client = get_bq_client()
        ref = table_ref('gold_variables_mercado')

        query = f"""
        SELECT *
        FROM (
            SELECT
                fecha,
                ticker,
                nombre,
                categoria,
                valor,
                'usd_mxn' AS serie
            FROM {ref}
            WHERE fecha >= DATE_SUB(CURRENT_DATE(), INTERVAL {limit_months} MONTH)
              AND (
                UPPER(COALESCE(ticker, '')) IN ('MXN=X', 'USDMXN=X')
                OR REGEXP_CONTAINS(LOWER(COALESCE(nombre, '')), r'(usd/mxn|d[oó]lar.*peso|peso.*d[oó]lar|tipo de cambio)')
              )
              AND SAFE_CAST(valor AS FLOAT64) BETWEEN 10 AND 30
        )
        ORDER BY fecha DESC
        """

        df = client.query(query).to_dataframe()
        if not df.empty:
            df = _safe_to_datetime(df)
            df['valor'] = pd.to_numeric(df['valor'], errors='coerce')
        return df
    except Exception as e:
        st.warning(f"Error cargando series de mercado macro: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=CACHE_TTL)
def load_inegi_pib_data(limit_quarters: int = 8) -> pd.DataFrame:
    """
    Carga datos de PIB desde gold_inegi_manual_pib
    
    Args:
        limit_quarters: Número de trimestres hacia atrás desde hoy
    
    Returns:
        DataFrame con datos de PIB
    """
    try:
        client = get_bq_client()
        ref = table_ref('gold_inegi_manual_pib')
        
        query = f"""
        SELECT 
            fecha,
            periodo,
            valor,
            indicador,
            descripcion,
            fecha_procesamiento
        FROM {ref}
        WHERE fecha >= DATE_SUB(CURRENT_DATE(), INTERVAL {limit_quarters * 3} MONTH)
        AND frecuencia = 'trimestral'
        ORDER BY fecha DESC
        """
        
        df = client.query(query).to_dataframe()
        
        # Clean and process data
        if not df.empty:
            df['fecha'] = pd.to_datetime(df['fecha'])
        
        return df
        
    except Exception as e:
        st.warning(f"Error cargando datos PIB: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=CACHE_TTL)
def load_inegi_manufactura_data(limit_months: int = 24) -> pd.DataFrame:
    """
    Carga datos del sector manufacturero desde gold_inegi_manual_manufactura
    
    Args:
        limit_months: Número de meses hacia atrás desde hoy
    
    Returns:
        DataFrame con datos de manufactura
    """
    try:
        client = get_bq_client()
        ref = table_ref('gold_inegi_manual_manufactura')
        
        query = f"""
        SELECT 
            fecha,
            periodo,
            valor,
            indicador,
            descripcion,
            fecha_procesamiento
        FROM {ref}
        WHERE fecha >= DATE_SUB(CURRENT_DATE(), INTERVAL {limit_months} MONTH)
        ORDER BY fecha DESC
        """
        
        df = client.query(query).to_dataframe()
        
        # Clean and process data
        if not df.empty:
            df['fecha'] = pd.to_datetime(df['fecha'])
        
        return df
        
    except Exception as e:
        st.warning(f"Error cargando datos manufactura: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=CACHE_TTL)
def load_inegi_mineria_data(limit_months: int = 24) -> pd.DataFrame:
    """
    Carga datos del sector minería desde gold_inegi_manual_mineria
    
    Args:
        limit_months: Número de meses hacia atrás desde hoy
    
    Returns:
        DataFrame con datos de minería
    """
    try:
        client = get_bq_client()
        ref = table_ref('gold_inegi_manual_mineria')
        
        query = f"""
        SELECT 
            fecha,
            periodo,
            valor,
            indicador,
            descripcion,
            fecha_procesamiento
        FROM {ref}
        WHERE fecha >= DATE_SUB(CURRENT_DATE(), INTERVAL {limit_months} MONTH)
        ORDER BY fecha DESC
        """
        
        df = client.query(query).to_dataframe()
        
        # Clean and process data
        if not df.empty:
            df['fecha'] = pd.to_datetime(df['fecha'])
        
        return df
        
    except Exception as e:
        st.warning(f"Error cargando datos minería: {e}")
        return pd.DataFrame()

# ---------------------------------------------------------------------------
# COMERCIO ACERO LOADERS
# ---------------------------------------------------------------------------

@st.cache_data(ttl=CACHE_TTL)
def load_comercio_acero_summary(limit_months: int = 12) -> Dict[str, Any]:
    """
    Carga resumen del comercio de acero desde tyasa_bronce_comercio_acero
    
    Args:
        limit_months: Número de meses hacia atrás desde hoy
    
    Returns:
        Dictionary con resumen de importaciones y exportaciones
    """
    try:
        client = get_bq_client()
        ref = table_ref('tyasa_bronce_comercio_acero')
        
        # Summary by operation type
        query = f"""
        SELECT 
            tipo_operacion,
            COUNT(*) as operaciones,
            SUM(volumen) as volumen_total_ton,
            AVG(volumen) as volumen_promedio_ton,
            COUNT(DISTINCT pais) as paises_distintos,
            COUNT(DISTINCT producto) as productos_distintos
        FROM {ref}
        WHERE fecha >= DATE_SUB(CURRENT_DATE(), INTERVAL {limit_months} MONTH)
        AND volumen IS NOT NULL
        AND (UPPER(COALESCE(familia, '')) = 'LARGOS' OR UPPER(COALESCE(producto, '')) LIKE '%VARILLA%' OR UPPER(COALESCE(producto, '')) LIKE '%ALAMBR%' OR UPPER(COALESCE(producto, '')) LIKE '%PERFIL%' OR UPPER(COALESCE(producto, '')) LIKE '%BARRA%')
        AND UPPER(COALESCE(producto, '')) NOT LIKE '%INOXIDABLE%'
        AND UPPER(COALESCE(producto, '')) NOT LIKE '%RIEL%'
        AND UPPER(COALESCE(producto, '')) NOT LIKE '%NINGUNO%'
        GROUP BY tipo_operacion
        """
        
        summary_df = client.query(query).to_dataframe()
        
        # Process results
        result = {}
        for _, row in summary_df.iterrows():
            tipo = row['tipo_operacion'].lower()
            result[tipo] = {
                'operaciones': row['operaciones'],
                'volumen_total_ton': row['volumen_total_ton'],
                'volumen_promedio_ton': row['volumen_promedio_ton'],
                'paises_distintos': row['paises_distintos'],
                'productos_distintos': row['productos_distintos']
            }
        
        return result
        
    except Exception as e:
        st.warning(f"Error cargando resumen comercio acero: {e}")
        return {}

@st.cache_data(ttl=CACHE_TTL)
def load_comercio_acero_top_countries(operation_type: str = 'all', limit: int = 10) -> pd.DataFrame:
    """
    Carga principales países en el comercio de acero
    
    Args:
        operation_type: 'IMPORTACION', 'EXPORTACION', o 'all'
        limit: Número de países a retornar
    
    Returns:
        DataFrame con top países por volumen
    """
    try:
        client = get_bq_client()
        ref = table_ref('tyasa_bronce_comercio_acero')
        
        # Build WHERE clause
        where_clause = "WHERE volumen IS NOT NULL AND pais IS NOT NULL AND (UPPER(COALESCE(familia, '')) = 'LARGOS' OR UPPER(COALESCE(producto, '')) LIKE '%VARILLA%' OR UPPER(COALESCE(producto, '')) LIKE '%ALAMBR%' OR UPPER(COALESCE(producto, '')) LIKE '%PERFIL%' OR UPPER(COALESCE(producto, '')) LIKE '%BARRA%') AND UPPER(COALESCE(producto, '')) NOT LIKE '%INOXIDABLE%' AND UPPER(COALESCE(producto, '')) NOT LIKE '%RIEL%' AND UPPER(COALESCE(producto, '')) NOT LIKE '%NINGUNO%'"
        if operation_type != 'all':
            where_clause += f" AND tipo_operacion = '{operation_type}'"
        
        query = f"""
        SELECT 
            pais,
            tipo_operacion,
            COUNT(*) as operaciones,
            SUM(volumen) as volumen_total_ton,
            AVG(volumen) as volumen_promedio_ton
        FROM {ref}
        {where_clause}
        GROUP BY pais, tipo_operacion
        ORDER BY volumen_total_ton DESC
        LIMIT {limit}
        """
        
        df = client.query(query).to_dataframe()
        return df
        
    except Exception as e:
        st.warning(f"Error cargando top países comercio acero: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=CACHE_TTL)
def load_comercio_acero_top_products(operation_type: str = 'all', limit: int = 10) -> pd.DataFrame:
    """
    Carga principales productos en el comercio de acero
    
    Args:
        operation_type: 'IMPORTACION', 'EXPORTACION', o 'all'
        limit: Número de productos a retornar
    
    Returns:
        DataFrame con top productos por volumen
    """
    try:
        client = get_bq_client()
        ref = table_ref('tyasa_bronce_comercio_acero')
        
        # Build WHERE clause
        where_clause = "WHERE volumen IS NOT NULL AND producto IS NOT NULL AND (UPPER(COALESCE(familia, '')) = 'LARGOS' OR UPPER(COALESCE(producto, '')) LIKE '%VARILLA%' OR UPPER(COALESCE(producto, '')) LIKE '%ALAMBR%' OR UPPER(COALESCE(producto, '')) LIKE '%PERFIL%' OR UPPER(COALESCE(producto, '')) LIKE '%BARRA%') AND UPPER(COALESCE(producto, '')) NOT LIKE '%INOXIDABLE%' AND UPPER(COALESCE(producto, '')) NOT LIKE '%RIEL%' AND UPPER(COALESCE(producto, '')) NOT LIKE '%NINGUNO%'"
        if operation_type != 'all':
            where_clause += f" AND tipo_operacion = '{operation_type}'"
        
        query = f"""
        SELECT 
            producto,
            tipo_operacion,
            COUNT(*) as operaciones,
            SUM(volumen) as volumen_total_ton,
            AVG(volumen) as volumen_promedio_ton
        FROM {ref}
        {where_clause}
        GROUP BY producto, tipo_operacion
        ORDER BY volumen_total_ton DESC
        LIMIT {limit}
        """
        
        df = client.query(query).to_dataframe()
        return df
        
    except Exception as e:
        st.warning(f"Error cargando top productos comercio acero: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=CACHE_TTL)
def load_comercio_acero_time_series(limit_months: int = 24) -> pd.DataFrame:
    """
    Carga serie temporal del comercio de acero
    
    Args:
        limit_months: Número de meses hacia atrás desde hoy
    
    Returns:
        DataFrame con serie temporal mensual
    """
    try:
        client = get_bq_client()
        ref = table_ref('tyasa_bronce_comercio_acero')
        
        query = f"""
        SELECT 
            DATE_TRUNC(fecha, MONTH) as mes,
            tipo_operacion,
            SUM(volumen) as volumen_mensual_ton,
            COUNT(*) as operaciones_mensual,
            COUNT(DISTINCT pais) as paises_mensual
        FROM {ref}
        WHERE fecha >= DATE_SUB(CURRENT_DATE(), INTERVAL {limit_months} MONTH)
        AND volumen IS NOT NULL
        AND (UPPER(COALESCE(familia, '')) = 'LARGOS' OR UPPER(COALESCE(producto, '')) LIKE '%VARILLA%' OR UPPER(COALESCE(producto, '')) LIKE '%ALAMBR%' OR UPPER(COALESCE(producto, '')) LIKE '%PERFIL%' OR UPPER(COALESCE(producto, '')) LIKE '%BARRA%')
        AND UPPER(COALESCE(producto, '')) NOT LIKE '%INOXIDABLE%'
        AND UPPER(COALESCE(producto, '')) NOT LIKE '%RIEL%'
        AND UPPER(COALESCE(producto, '')) NOT LIKE '%NINGUNO%'
        GROUP BY DATE_TRUNC(fecha, MONTH), tipo_operacion
        ORDER BY mes DESC, tipo_operacion
        """
        
        df = client.query(query).to_dataframe()
        
        # Clean and process data
        if not df.empty:
            df['mes'] = pd.to_datetime(df['mes'])
        
        return df
        
    except Exception as e:
        st.warning(f"Error cargando serie temporal comercio acero: {e}")
        return pd.DataFrame()

# ---------------------------------------------------------------------------
# UTILITY FUNCTIONS
# ---------------------------------------------------------------------------

def calculate_trend_pct(df: pd.DataFrame, value_col: str = 'valor', periods: int = 1) -> float:
    """
    Calcula variación porcentual entre periodos
    
    Args:
        df: DataFrame con datos ordenados por fecha
        value_col: Nombre de la columna con valores
        periods: Número de periodos para comparar
    
    Returns:
        Variación porcentual
    """
    if df.empty or len(df) < periods + 1:
        return 0.0
    
    latest = df.iloc[0][value_col]  # Asume DataFrame ordenado DESC
    previous = df.iloc[periods][value_col]
    
    if previous != 0 and pd.notna(latest) and pd.notna(previous):
        return ((latest - previous) / previous) * 100
    
    return 0.0

def get_latest_value(df: pd.DataFrame, value_col: str = 'valor'):
    """
    Obtiene el último valor de una serie
    
    Args:
        df: DataFrame con datos ordenados por fecha
        value_col: Nombre de la columna con valores
    
    Returns:
        Último valor o None
    """
    if df.empty:
        return None
    
    return df.iloc[0][value_col] if pd.notna(df.iloc[0][value_col]) else None

@st.cache_data(ttl=CACHE_TTL)
def load_macro_kpis_summary() -> Dict[str, Any]:
    """
    Carga KPIs macro consolidados para dashboards
    
    Returns:
        Dictionary con KPIs principales
    """
    try:
        # Load data from different sources
        inpc_df = load_inegi_inpc_data(18)
        construccion_df = load_inegi_construccion_data(18)
        construccion_segmented_df = load_inegi_construccion_segmented(18)
        pib_df = load_inegi_pib_data(12)
        internal_demand_df = load_internal_demand_aceros_largos(12)
        macro_market_df = load_macro_market_series(12)
        
        # Calculate KPIs
        kpis = {}
        
        # INPC KPI
        if not inpc_df.empty:
            general_inpc = _choose_preferred_series(
                inpc_df,
                description_col='concepto',
                preferred_patterns=[r'precios al consumidor \(inpc\)$', r'precios al consumidor.*\(inpc\)', r'inpc']
            )
            inflation_yoy = _annual_pct_change_from_index(general_inpc)
            prev_inflation_yoy = _annual_pct_change_from_index(general_inpc.iloc[1:].copy()) if len(general_inpc) > 13 else 0.0
            kpis['inpc'] = {
                'valor': inflation_yoy,
                'tendencia_pct': inflation_yoy - prev_inflation_yoy,
                'ultima_fecha': general_inpc.iloc[0]['fecha'] if not general_inpc.empty else None
            }
        
        # Construction activity KPI
        if not construccion_segmented_df.empty:
            total_construccion = construccion_segmented_df[
                construccion_segmented_df['segmento'] == '23 Construcción total'
            ].copy()
            total_construccion = _choose_preferred_series(
                total_construccion,
                preferred_patterns=[r'variaci[oó]n porcentual anual', r'variaci[oó]n porcentual respecto al mismo mes', r'índice de volumen físico']
            )
            latest_construccion = get_latest_value(total_construccion)
            trend_construccion = _calculate_delta(
                total_construccion,
                mode='diff' if total_construccion['descripcion'].astype(str).str.contains('variaci', case=False, na=False).any() else 'pct_change'
            )
            kpis['construccion'] = {
                'valor': latest_construccion,
                'tendencia_pct': trend_construccion,
                'ultima_fecha': total_construccion.iloc[0]['fecha'] if not total_construccion.empty else None
            }
        
        # GDP KPI (if available)
        if not pib_df.empty:
            pib_total = _choose_preferred_series(
                pib_df,
                preferred_patterns=[r'variaci[oó]n porcentual anual.*producto interno bruto', r'producto interno bruto', r'b\.1bp---producto interno bruto']
            )
            latest_pib = get_latest_value(pib_total)
            trend_pib = _calculate_delta(
                pib_total,
                mode='diff' if pib_total['descripcion'].astype(str).str.contains('variaci', case=False, na=False).any() else 'pct_change'
            )
            kpis['pib'] = {
                'valor': latest_pib,
                'tendencia_pct': trend_pib,
                'ultima_fecha': pib_total.iloc[0]['fecha'] if not pib_total.empty else None
                 }

        # Internal demand KPI (if available)
        if not internal_demand_df.empty:
            latest_demanda = get_latest_value(internal_demand_df, 'peso_ton')
            trend_demanda = calculate_trend_pct(internal_demand_df, 'peso_ton')
            kpis['demanda_interna'] = {
                'valor': latest_demanda,
                'tendencia_pct': trend_demanda,
                'ultima_fecha': internal_demand_df.iloc[0]['fecha']
            }

        # USD/MXN KPI (if available). TIIE is intentionally excluded until a
        # reliable Banxico source is loaded for this module.
        if not macro_market_df.empty:
            for serie_key in ['usd_mxn']:
                serie_df = macro_market_df[macro_market_df['serie'] == serie_key]
                if not serie_df.empty:
                    kpis[serie_key] = {
                        'valor': get_latest_value(serie_df),
                        'tendencia_pct': calculate_trend_pct(serie_df),
                        'ultima_fecha': serie_df.iloc[0]['fecha']
                    }
        
        return kpis
        
    except Exception as e:
        st.warning(f"Error cargando KPIs macro: {e}")
        return {}

def get_last_update() -> str:
    """Retorna timestamp de última actualización"""
    return datetime.now().strftime("%Y-%m-%d · %H:%M CST")

def get_data_sources() -> List[str]:
    """Retorna las fuentes de datos"""
    return [
        "INEGI Manual - Índices y Estadísticas", 
        "Monitor Comercio Acero México",
        "BigQuery - Datos procesados",
        "TYASA BI Platform"
    ]
