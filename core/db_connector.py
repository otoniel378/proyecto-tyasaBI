"""
db_connector.py — Conexion a BigQuery compartida entre todas las areas.
Todas las consultas van a project-d0cf2519-d089-47d3-930.tyasa_bi
"""

from google.cloud import bigquery
import pandas as pd
import streamlit as st

PROJECT_ID = "project-d0cf2519-d089-47d3-930"
DATASET    = "tyasa_bi"
FULL_DS    = f"{PROJECT_ID}.{DATASET}"


@st.cache_resource(show_spinner=False)
def get_bq_client() -> bigquery.Client:
    """Cliente BigQuery singleton por sesion de Streamlit."""
    return bigquery.Client(project=PROJECT_ID)


def run_query(sql: str) -> pd.DataFrame:
    """
    Ejecuta una consulta SQL en BigQuery y devuelve un DataFrame.

    Args:
        sql: sentencia SQL con nombres de tabla completamente calificados.

    Returns:
        pd.DataFrame con los resultados.
    """
    client = get_bq_client()
    try:
        return client.query(sql).to_dataframe()
    except Exception as e:
        raise RuntimeError(f"Error BigQuery:\n{sql}\n\nDetalle: {e}") from e


def list_tables() -> list[str]:
    """Devuelve la lista de tablas disponibles en el dataset."""
    client = get_bq_client()
    try:
        tables = client.list_tables(f"{PROJECT_ID}.{DATASET}")
        return [t.table_id for t in tables]
    except Exception:
        return []


def table_ref(table_name: str) -> str:
    """Devuelve la referencia completa de una tabla BigQuery."""
    return f"`{FULL_DS}.{table_name}`"
