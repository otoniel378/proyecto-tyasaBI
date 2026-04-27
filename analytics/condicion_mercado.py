"""
condicion_mercado.py — Índice de condición de mercado y ventanas de oportunidad.

Combina variables macroeconómicas y de mercado para generar un índice
compuesto que caracteriza el entorno comercial de TYASA.

Funciones:
  calcular_indice_condicion      — Índice 0–100 basado en variables ponderadas
  detectar_ventanas_oportunidad  — Periodos donde el índice supera umbral
  calcular_correlaciones_lag     — Correlaciones rezagadas entre variables y ventas
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Sequence


# ── Índice de condición de mercado ────────────────────────────────────────────

# Pesos de cada variable en el índice (deben sumar ~1)
_PESOS_DEFAULT: dict[str, float] = {
    "IGAE_INDUSTRIA":   0.20,  # Actividad industrial
    "IGAE_MANUFACTURA": 0.15,  # Manufactura
    "INVERSION_FIJA":   0.15,  # Inversión
    "USD_MXN":          0.15,  # Tipo de cambio (inverso: peso fuerte = +)
    "Brent_USD":        0.10,  # Petróleo (demanda OCTG)
    "ETF_Mexico":       0.10,  # Confianza México
    "INPC_GENERAL":     0.15,  # Inflación (inverso)
}


def calcular_indice_condicion(
    series_dict: dict[str, pd.DataFrame],
    pesos: dict[str, float] | None = None,
    ventana_norm: int = 24,
) -> pd.DataFrame:
    """
    Calcula el índice de condición de mercado mensual.

    series_dict: {variable_name: DataFrame(fecha, valor)} — las variables del modelo
    pesos: pesos de cada variable (default = _PESOS_DEFAULT)
    ventana_norm: número de meses para normalizar (min-max rolling)

    Retorna DataFrame con: fecha, INDICE (0-100), y una columna por variable normalizada
    """
    _pesos = pesos or _PESOS_DEFAULT
    variables_usadas = [v for v in _pesos if v in series_dict and not series_dict[v].empty]
    if not variables_usadas:
        return pd.DataFrame()

    dfs = []
    for v in variables_usadas:
        df = series_dict[v].copy()
        df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
        df = df.dropna(subset=["fecha"]).set_index("fecha")[["valor"]].rename(columns={"valor": v})
        dfs.append(df.resample("MS").last())

    combined = pd.concat(dfs, axis=1).sort_index().dropna(how="all")

    # Invertir variables donde mayor valor = peor condición
    _invertidas = {"USD_MXN", "INPC_GENERAL"}
    for v in _invertidas:
        if v in combined.columns:
            combined[v] = combined[v] * -1

    # Normalización min-max rolling
    normed = pd.DataFrame(index=combined.index)
    for v in variables_usadas:
        if v not in combined.columns:
            continue
        rolling_min = combined[v].rolling(ventana_norm, min_periods=3).min()
        rolling_max = combined[v].rolling(ventana_norm, min_periods=3).max()
        rng = (rolling_max - rolling_min).replace(0, np.nan)
        normed[f"{v}_norm"] = ((combined[v] - rolling_min) / rng * 100).clip(0, 100)

    # Índice ponderado
    total_peso = sum(_pesos[v] for v in variables_usadas)
    indice = pd.Series(0.0, index=normed.index)
    for v in variables_usadas:
        col = f"{v}_norm"
        if col in normed.columns:
            indice += normed[col].fillna(50) * (_pesos[v] / total_peso)

    result = normed.copy()
    result.insert(0, "INDICE", indice.round(1))
    return result.dropna(subset=["INDICE"]).reset_index()


# ── Ventanas de oportunidad ───────────────────────────────────────────────────

def detectar_ventanas_oportunidad(
    df_indice: pd.DataFrame,
    umbral_alto: float = 65.0,
    umbral_bajo: float = 35.0,
    min_duracion_meses: int = 2,
) -> pd.DataFrame:
    """
    Identifica periodos consecutivos donde el índice supera umbral_alto
    o cae por debajo de umbral_bajo.

    df_indice: salida de calcular_indice_condicion (columnas: fecha, INDICE)
    Retorna DataFrame con: fecha_inicio, fecha_fin, duracion_meses, tipo (oportunidad|riesgo), indice_medio
    """
    if df_indice.empty or "INDICE" not in df_indice.columns:
        return pd.DataFrame()

    df = df_indice.copy()
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    df = df.dropna(subset=["fecha"]).sort_values("fecha").reset_index(drop=True)

    ventanas = []
    in_window = False
    start_idx = 0
    tipo_actual = ""

    for i, row in df.iterrows():
        v = row["INDICE"]
        if not in_window:
            if v >= umbral_alto:
                in_window, tipo_actual, start_idx = True, "oportunidad", i
            elif v <= umbral_bajo:
                in_window, tipo_actual, start_idx = True, "riesgo", i
        else:
            condition_holds = (tipo_actual == "oportunidad" and v >= umbral_alto) or \
                              (tipo_actual == "riesgo" and v <= umbral_bajo)
            if not condition_holds or i == len(df) - 1:
                end_idx = i - 1 if not condition_holds else i
                duracion = end_idx - start_idx + 1
                if duracion >= min_duracion_meses:
                    ventanas.append({
                        "fecha_inicio": df.loc[start_idx, "fecha"],
                        "fecha_fin": df.loc[end_idx, "fecha"],
                        "duracion_meses": duracion,
                        "tipo": tipo_actual,
                        "indice_medio": round(df.loc[start_idx:end_idx, "INDICE"].mean(), 1),
                    })
                in_window = False
                if not condition_holds:
                    if v >= umbral_alto:
                        in_window, tipo_actual, start_idx = True, "oportunidad", i
                    elif v <= umbral_bajo:
                        in_window, tipo_actual, start_idx = True, "riesgo", i

    if not ventanas:
        return pd.DataFrame(columns=["fecha_inicio", "fecha_fin", "duracion_meses", "tipo", "indice_medio"])
    return pd.DataFrame(ventanas)


# ── Correlaciones rezagadas ───────────────────────────────────────────────────

def calcular_correlaciones_lag(
    df_ventas_mensual: pd.DataFrame,
    series_dict: dict[str, pd.DataFrame],
    max_lag: int = 6,
    min_obs: int = 18,
) -> pd.DataFrame:
    """
    Calcula correlaciones de Pearson entre cada variable de series_dict
    y el volumen de ventas con rezagos de 0 a max_lag meses.

    df_ventas_mensual: columnas PERIODO, PESO_TON (serie total)
    series_dict: {variable: DataFrame(fecha, valor)}
    Retorna DataFrame con: variable, lag, correlacion, p_value (approx)
    """
    if df_ventas_mensual.empty:
        return pd.DataFrame()

    ventas = df_ventas_mensual.copy()
    ventas["PERIODO"] = pd.to_datetime(ventas["PERIODO"], errors="coerce")
    ventas = ventas.dropna(subset=["PERIODO"]).groupby("PERIODO")["PESO_TON"].sum()
    ventas = ventas.resample("MS").sum()

    results = []
    for var_name, df_var in series_dict.items():
        if df_var.empty or "valor" not in df_var.columns:
            continue
        dv = df_var.copy()
        dv["fecha"] = pd.to_datetime(dv.get("fecha", dv.get("PERIODO")), errors="coerce")
        dv = dv.dropna(subset=["fecha"]).set_index("fecha")["valor"]
        dv = dv.resample("MS").last()

        combined = pd.concat({"ventas": ventas, "variable": dv}, axis=1).dropna()
        if len(combined) < min_obs:
            continue

        for lag in range(0, max_lag + 1):
            shifted = combined["variable"].shift(lag)
            pair = pd.concat({"v": combined["ventas"], "x": shifted}, axis=1).dropna()
            if len(pair) < min_obs:
                continue
            corr = pair["v"].corr(pair["x"])
            n = len(pair)
            # t-statistic approx p-value
            t = corr * np.sqrt(n - 2) / np.sqrt(1 - corr**2) if abs(corr) < 1 else np.inf
            from scipy import stats as _stats  # local import
            try:
                p_val = 2 * (1 - _stats.t.cdf(abs(t), df=n - 2))
            except Exception:
                p_val = np.nan
            results.append({
                "variable": var_name,
                "lag": lag,
                "correlacion": round(corr, 3),
                "p_value": round(p_val, 4) if not np.isnan(p_val) else None,
            })

    if not results:
        return pd.DataFrame(columns=["variable", "lag", "correlacion", "p_value"])
    return pd.DataFrame(results).sort_values(["variable", "lag"]).reset_index(drop=True)
