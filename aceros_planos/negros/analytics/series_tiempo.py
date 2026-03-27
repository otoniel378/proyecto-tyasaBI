"""
series_tiempo.py — Analisis de series de tiempo de demanda.
Calcula variaciones, volatilidad, heatmaps y rankings de estabilidad.
"""

import pandas as pd
import numpy as np


def preparar_serie_mensual(df_mensual: pd.DataFrame) -> pd.DataFrame:
    if df_mensual.empty or "PERIODO" not in df_mensual.columns:
        return pd.DataFrame()

    df = df_mensual.copy().sort_values("PERIODO").reset_index(drop=True)

    if "ANIO" not in df.columns:
        df["ANIO"] = df["PERIODO"].dt.year
    if "MES" not in df.columns:
        df["MES"] = df["PERIODO"].dt.month

    df["ANIO"] = df["ANIO"].astype(int)
    df["MES"]  = df["MES"].astype(int)
    return df


def calcular_variacion_mensual(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    df = df.copy()
    df["VAR_MOM"]     = df["PESO_TON"].diff()
    df["VAR_MOM_PCT"] = (df["PESO_TON"].pct_change() * 100).round(1)
    return df


def calcular_volatilidad(df: pd.DataFrame, col_dim: str | None = None, col_val: str = "PESO_TON") -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    if col_dim and col_dim in df.columns:
        grupos = df.groupby(col_dim)[col_val]
        result = grupos.agg(MEDIA="mean", STD="std", N="count").reset_index()
        result.columns = ["DIMENSION", "MEDIA", "STD", "N"]
    else:
        result = pd.DataFrame([{
            "DIMENSION": "Global",
            "MEDIA": df[col_val].mean(),
            "STD":   df[col_val].std(),
            "N":     len(df),
        }])

    result["CV"] = (result["STD"] / result["MEDIA"] * 100).round(1).fillna(0)
    result = result.sort_values("CV").reset_index(drop=True)
    result["ESTABILIDAD"] = result["CV"].apply(_clasificar_estabilidad)
    return result


def _clasificar_estabilidad(cv: float) -> str:
    if cv < 20:
        return "Alta"
    elif cv < 40:
        return "Media"
    return "Baja"


def construir_heatmap_mes_anio(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "ANIO" not in df.columns or "MES" not in df.columns:
        return pd.DataFrame()

    pivot = df.pivot_table(
        index="MES", columns="ANIO",
        values="PESO_TON", aggfunc="sum", fill_value=0,
    )
    pivot.index = [_nombre_mes(m) for m in pivot.index]
    return pivot


def _nombre_mes(mes: int) -> str:
    nombres = {
        1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr",
        5: "May", 6: "Jun", 7: "Jul", 8: "Ago",
        9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic",
    }
    return nombres.get(mes, str(mes))


def ranking_estabilidad(
    df_cliente_producto: pd.DataFrame | None = None,
    df_mensual: pd.DataFrame | None = None,
    col_dim: str = "PRODUCTO_LIMPIO",
    col_val: str = "PESO_TON",
) -> pd.DataFrame:
    df_input = df_cliente_producto if df_cliente_producto is not None else df_mensual
    if df_input is None or df_input.empty:
        return pd.DataFrame()
    return calcular_volatilidad(df_input, col_dim=col_dim if col_dim in df_input.columns else None, col_val=col_val)


def top_afectados_variacion(
    df: pd.DataFrame,
    col_dim: str,
    col_periodo: str = "PERIODO",
    col_val: str = "PESO_TON",
    n: int = 10,
) -> pd.DataFrame:
    if df.empty or col_dim not in df.columns or col_periodo not in df.columns:
        return pd.DataFrame()

    df = df.copy()
    df[col_periodo] = pd.to_datetime(df[col_periodo], errors="coerce")
    periodos = sorted(df[col_periodo].dropna().unique())
    if len(periodos) < 2:
        return pd.DataFrame()

    p_actual   = periodos[-1]
    p_anterior = periodos[-2]

    mes_a = df[df[col_periodo] == p_actual].groupby(col_dim)[col_val].sum()
    mes_p = df[df[col_periodo] == p_anterior].groupby(col_dim)[col_val].sum()

    merged = pd.DataFrame({"ACTUAL": mes_a, "ANTERIOR": mes_p}).fillna(0).reset_index()
    merged.columns = ["DIMENSION", "ACTUAL", "ANTERIOR"]
    merged["VAR_ABS"] = (merged["ACTUAL"] - merged["ANTERIOR"]).round(1)
    denom = merged["ANTERIOR"].replace(0, float("nan"))
    merged["VAR_PCT"] = ((merged["VAR_ABS"] / denom) * 100).round(1)

    merged = merged.reindex(merged["VAR_ABS"].abs().sort_values(ascending=False).index)
    return merged.head(n).reset_index(drop=True)


def serie_por_dimension(
    df: pd.DataFrame,
    col_dim: str,
    col_periodo: str = "PERIODO",
    col_val: str = "PESO_TON",
) -> pd.DataFrame:
    if df.empty or col_periodo not in df.columns:
        return pd.DataFrame()

    return (
        df.groupby([col_periodo, col_dim], as_index=False)[col_val]
        .sum()
        .sort_values([col_periodo, col_dim])
        .reset_index(drop=True)
    )
