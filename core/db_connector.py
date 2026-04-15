"""
db_connector.py — Conexion a BigQuery compartida entre todas las areas.
Todas las consultas van a project-d0cf2519-d089-47d3-930.tyasa_bi

Autenticacion (se intenta en este orden):
  1. secrets.toml [gcp_service_account] — JSON embebido (recomendado para equipos)
  2. secrets.toml GOOGLE_APPLICATION_CREDENTIALS — ruta al archivo JSON
  3. Variable de entorno GOOGLE_APPLICATION_CREDENTIALS
  4. Application Default Credentials (gcloud auth, Workload Identity, etc.)
"""

import os
import json
import tempfile

from google.cloud import bigquery
from google.oauth2 import service_account
import pandas as pd
import streamlit as st

PROJECT_ID = "project-d0cf2519-d089-47d3-930"
DATASET    = "tyasa_bi"
FULL_DS    = f"{PROJECT_ID}.{DATASET}"


def _build_credentials():
    """
    Construye credenciales GCP con fallback progresivo.
    Retorna (credentials, project_id) o (None, PROJECT_ID) para ADC.
    """
    # ── Método 1: JSON embebido en secrets.toml ────────────────────────────
    try:
        sa_info = dict(st.secrets["gcp_service_account"])
        creds = service_account.Credentials.from_service_account_info(
            sa_info,
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )
        return creds, sa_info.get("project_id", PROJECT_ID)
    except (KeyError, Exception):
        pass

    # ── Método 2: Ruta al JSON en secrets.toml ────────────────────────────
    try:
        cred_path = st.secrets.get("GOOGLE_APPLICATION_CREDENTIALS", "")
        if cred_path and os.path.isfile(cred_path):
            creds = service_account.Credentials.from_service_account_file(
                cred_path,
                scopes=["https://www.googleapis.com/auth/cloud-platform"],
            )
            return creds, PROJECT_ID
    except Exception:
        pass

    # ── Método 3: Variable de entorno del sistema ─────────────────────────
    env_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
    if env_path and os.path.isfile(env_path):
        try:
            creds = service_account.Credentials.from_service_account_file(
                env_path,
                scopes=["https://www.googleapis.com/auth/cloud-platform"],
            )
            return creds, PROJECT_ID
        except Exception:
            pass

    # ── Método 4: ADC (gcloud auth, Workload Identity, etc.) ─────────────
    return None, PROJECT_ID


@st.cache_resource(show_spinner=False)
def get_bq_client() -> bigquery.Client:
    """Cliente BigQuery singleton por sesion de Streamlit."""
    creds, project = _build_credentials()
    if creds:
        return bigquery.Client(project=project, credentials=creds)
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
