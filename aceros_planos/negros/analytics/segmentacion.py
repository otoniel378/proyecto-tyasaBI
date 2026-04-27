"""
segmentacion.py — Analisis de segmentacion y clasificacion de clientes.
Implementa Pareto, clasificacion ABC, concentracion y diversificacion.
"""

import pandas as pd
import numpy as np
from config import PARETO_THRESHOLD_A, PARETO_THRESHOLD_B


def clasificar_abc(df_cliente: pd.DataFrame, col_cliente: str = "CLIENTE", col_val: str = "PESO_TON") -> pd.DataFrame:
    if df_cliente.empty:
        return pd.DataFrame()

    agg = (
        df_cliente[[col_cliente, col_val]]
        .groupby(col_cliente, as_index=False)[col_val]
        .sum()
        .sort_values(col_val, ascending=False)
        .reset_index(drop=True)
    )

    total = agg[col_val].sum()
    agg["PCT"] = (agg[col_val] / total * 100).round(2) if total > 0 else 0.0
    agg["PCT_ACUM"] = agg["PCT"].cumsum().round(2)

    def _clase(pct_acum: float) -> str:
        if pct_acum <= PARETO_THRESHOLD_A * 100:
            return "A"
        elif pct_acum <= PARETO_THRESHOLD_B * 100:
            return "B"
        return "C"

    agg["CLASE"] = agg["PCT_ACUM"].apply(_clase)
    agg["RANK"] = range(1, len(agg) + 1)
    return agg


def resumen_abc(df_abc: pd.DataFrame) -> pd.DataFrame:
    if df_abc.empty:
        return pd.DataFrame()

    total_ton = df_abc["PESO_TON"].sum()
    return (
        df_abc.groupby("CLASE", as_index=False)
        .agg(N_CLIENTES=("CLIENTE", "count"), PESO_TON=("PESO_TON", "sum"))
        .assign(PCT_VOLUMEN=lambda x: (x["PESO_TON"] / total_ton * 100).round(1))
        .sort_values("CLASE")
    )


def calcular_diversificacion(df_cliente_producto: pd.DataFrame) -> pd.DataFrame:
    if df_cliente_producto.empty:
        return pd.DataFrame()

    div = (
        df_cliente_producto.groupby("CLIENTE", as_index=False)
        .agg(N_PRODUCTOS=("PRODUCTO_LIMPIO", "nunique"), PESO_TON=("PESO_TON", "sum"))
        .sort_values("N_PRODUCTOS", ascending=False)
        .reset_index(drop=True)
    )

    max_prod = div["N_PRODUCTOS"].max()
    div["INDICE_DIVERSIFICACION"] = (
        (div["N_PRODUCTOS"] / max_prod * 100).round(1) if max_prod > 0 else 0.0
    )
    return div


def clientes_monoproducto(df_cliente_producto: pd.DataFrame) -> pd.DataFrame:
    if df_cliente_producto.empty:
        return pd.DataFrame()

    div = calcular_diversificacion(df_cliente_producto)
    mono = div[div["N_PRODUCTOS"] == 1].copy()
    prod_unico = df_cliente_producto.groupby("CLIENTE")["PRODUCTO_LIMPIO"].first().reset_index()
    return mono.merge(prod_unico, on="CLIENTE", how="left").reset_index(drop=True)


def matriz_cliente_familia(df_cliente_producto: pd.DataFrame) -> pd.DataFrame:
    if df_cliente_producto.empty:
        return pd.DataFrame()

    return df_cliente_producto.pivot_table(
        index="CLIENTE", columns="PRODUCTO_LIMPIO",
        values="PESO_TON", aggfunc="sum", fill_value=0,
    )


def calcular_concentracion_hhi(df_abc: pd.DataFrame) -> float:
    if df_abc.empty or "PCT" not in df_abc.columns:
        return 0.0
    return round(float((df_abc["PCT"] ** 2).sum()), 1)
