"""
inegi_loader.py — Carga indicadores macroeconómicos desde la API del INEGI.

Indicadores clave para TYASA:
  - IGAE mensual (actividad industrial)
  - INPC (inflación)
  - Producción manufacturera
  - Inversión fija bruta
  - Exportaciones manufactureras

API: https://www.inegi.org.mx/app/api/indicadores/
Máximo 10 indicadores por request.
"""
from __future__ import annotations

import requests
import pandas as pd
import streamlit as st
from datetime import datetime

# ── IDs de indicadores INEGI ──────────────────────────────────────────────────
INDICADORES = {
    # Actividad económica
    "IGAE_TOTAL":          "493543",   # IGAE — índice general (base 2018=100)
    "IGAE_INDUSTRIA":      "493547",   # IGAE — actividades secundarias (industria)
    "IGAE_MANUFACTURA":    "493549",   # IGAE — industria manufacturera
    # Precios
    "INPC_GENERAL":        "216064",   # INPC general (base 2Q 2018=100)
    "INPC_ENERGIA":        "216082",   # INPC — energía
    # Producción
    "PROD_MANUFACT":       "444700",   # Producción manufacturera total (índice)
    "PROD_METALICA":       "444717",   # Fabricación de productos metálicos
    # Inversión y comercio
    "INVERSION_FIJA":      "581740",   # Inversión fija bruta (base 2013=100)
    "EXPORTACIONES_TOTAL": "158659",   # Exportaciones totales (MDD)
    "EXPORTACIONES_MANUF": "158681",   # Exportaciones manufactureras (MDD)
}

_BASE_URL = "https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml/INDICATOR"
_TOKEN = "8b02bc5f-f70e-4947-b5b6-e0e01a5c10f3"  # Token público demo INEGI


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fetch_serie(indicador_id: str, banco: str = "BIE") -> pd.DataFrame:
    url = f"{_BASE_URL}/{indicador_id}/es/0700/{banco}/false/json"
    params = {"token": _TOKEN}
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        series = data.get("Series", [])
        if not series:
            return pd.DataFrame()
        obs = series[0].get("OBSERVATIONS", [])
        rows = []
        for o in obs:
            val = o.get("OBS_VALUE")
            t = o.get("TIME_PERIOD", "")
            if val and t:
                try:
                    rows.append({"fecha": t, "valor": float(val)})
                except (ValueError, TypeError):
                    pass
        df = pd.DataFrame(rows)
        if not df.empty:
            df["fecha"] = pd.to_datetime(df["fecha"], format="%Y/%m", errors="coerce")
            df = df.dropna(subset=["fecha"]).sort_values("fecha").reset_index(drop=True)
        return df
    except Exception:
        return pd.DataFrame()


# ── API pública ───────────────────────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def load_indicadores_inegi(
    claves: list[str] | None = None,
    n_periodos: int = 36,
) -> dict[str, pd.DataFrame]:
    """
    Descarga las series especificadas por clave (claves de INDICADORES dict).
    Retorna dict {clave: DataFrame(fecha, valor)}.
    Si claves es None, descarga todos.
    """
    keys = claves or list(INDICADORES.keys())
    result: dict[str, pd.DataFrame] = {}
    for k in keys:
        ind_id = INDICADORES.get(k)
        if not ind_id:
            continue
        df = _fetch_serie(ind_id)
        if not df.empty and n_periodos > 0:
            df = df.tail(n_periodos).reset_index(drop=True)
        result[k] = df
    return result


def get_ultimo_valor(df: pd.DataFrame) -> tuple[float | None, str | None]:
    """Retorna (ultimo_valor, fecha_str) del DataFrame de serie."""
    if df.empty:
        return None, None
    row = df.iloc[-1]
    val = float(row["valor"])
    fecha = row["fecha"]
    fecha_str = fecha.strftime("%b %Y") if pd.notna(fecha) else ""
    return val, fecha_str


def calcular_var_mensual(df: pd.DataFrame) -> float | None:
    """Variación porcentual entre el último y penúltimo periodo."""
    if len(df) < 2:
        return None
    v1 = df.iloc[-1]["valor"]
    v0 = df.iloc[-2]["valor"]
    if v0 == 0:
        return None
    return (v1 - v0) / abs(v0) * 100


def calcular_var_anual(df: pd.DataFrame) -> float | None:
    """Variación porcentual entre el último periodo y el mismo mes del año anterior."""
    if len(df) < 13:
        return None
    v1 = df.iloc[-1]["valor"]
    v0 = df.iloc[-13]["valor"]
    if v0 == 0:
        return None
    return (v1 - v0) / abs(v0) * 100
