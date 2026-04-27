"""
clientes.py — Análisis de comportamiento y perfil de clientes para TYASA.

Funciones:
  calcular_frecuencia_compra     — Días promedio entre pedidos
  predecir_proximo_pedido        — Fecha estimada del próximo pedido (naive)
  calcular_estacionalidad_cliente — Índices de estacionalidad por mes
  generar_briefing_visita        — Resumen ejecutivo para visita comercial
  detectar_cambio_mix_cliente    — Variación de mezcla de productos por cliente
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from datetime import date, timedelta


# ── Frecuencia de compra ──────────────────────────────────────────────────────

def calcular_frecuencia_compra(
    df_ventas: pd.DataFrame,
    cliente: str,
) -> dict:
    """
    Calcula la frecuencia media de compra (días entre pedidos) para un cliente.

    df_ventas: columnas CLIENTE, PERIODO, PESO_TON (puede tener N_EMBARQUES)
    Retorna dict: freq_dias, cv, ultima_compra, dias_sin_comprar
    """
    required = {"CLIENTE", "PERIODO", "PESO_TON"}
    if not required.issubset(df_ventas.columns):
        return {}

    df = df_ventas[df_ventas["CLIENTE"] == cliente].copy()
    if df.empty:
        return {}

    df["PERIODO"] = pd.to_datetime(df["PERIODO"], errors="coerce")
    df = df.dropna(subset=["PERIODO"]).sort_values("PERIODO")

    fechas = df["PERIODO"].drop_duplicates().sort_values()
    if len(fechas) < 2:
        return {"freq_dias": None, "cv": None,
                "ultima_compra": str(fechas.iloc[-1].date()) if len(fechas) >= 1 else None,
                "dias_sin_comprar": None}

    diffs = fechas.diff().dropna().dt.days.values
    freq_dias = float(np.mean(diffs))
    cv = float(np.std(diffs) / freq_dias) if freq_dias > 0 else 0.0
    ultima = fechas.iloc[-1].date()
    dias_sin_comprar = (date.today() - ultima).days

    return {
        "freq_dias": round(freq_dias, 1),
        "cv": round(cv, 3),
        "ultima_compra": str(ultima),
        "dias_sin_comprar": dias_sin_comprar,
    }


# ── Predicción próximo pedido ─────────────────────────────────────────────────

def predecir_proximo_pedido(
    df_ventas: pd.DataFrame,
    cliente: str,
) -> dict:
    """
    Estima la fecha del próximo pedido sumando la frecuencia media a la última compra.
    Retorna dict: fecha_estimada, dias_para_pedido, alerta (True si ya pasó)
    """
    freq = calcular_frecuencia_compra(df_ventas, cliente)
    if not freq or freq.get("freq_dias") is None:
        return {}

    ultima = pd.to_datetime(freq["ultima_compra"]).date()
    freq_d = int(round(freq["freq_dias"]))
    fecha_est = ultima + timedelta(days=freq_d)
    dias_para = (fecha_est - date.today()).days

    return {
        "fecha_estimada": str(fecha_est),
        "dias_para_pedido": dias_para,
        "alerta": dias_para < 0,
    }


# ── Estacionalidad del cliente ────────────────────────────────────────────────

def calcular_estacionalidad_cliente(
    df_mensual: pd.DataFrame,
    cliente: str,
    n_anios: int = 3,
) -> pd.Series:
    """
    Calcula índice de estacionalidad mensual (ratio mes / promedio anual).
    Retorna Series indexada en 1..12 con los índices, o vacía si no hay datos.
    """
    required = {"CLIENTE", "PERIODO", "PESO_TON"}
    if not required.issubset(df_mensual.columns):
        return pd.Series(dtype=float)

    df = df_mensual[df_mensual["CLIENTE"] == cliente].copy()
    if df.empty:
        return pd.Series(dtype=float)

    df["PERIODO"] = pd.to_datetime(df["PERIODO"], errors="coerce")
    df = df.dropna(subset=["PERIODO"])
    df["ANIO"] = df["PERIODO"].dt.year
    df["MES"] = df["PERIODO"].dt.month

    anios_max = df["ANIO"].max()
    df = df[df["ANIO"] >= anios_max - n_anios + 1]
    if df.empty:
        return pd.Series(dtype=float)

    pivot = df.pivot_table(index="MES", columns="ANIO", values="PESO_TON",
                           aggfunc="sum", fill_value=0)
    media_mes = pivot.mean(axis=1)
    media_global = media_mes.mean()
    if media_global == 0:
        return pd.Series(dtype=float)
    return (media_mes / media_global).round(3)


# ── Briefing de visita ────────────────────────────────────────────────────────

def generar_briefing_visita(
    df_mensual: pd.DataFrame,
    df_cli_prod: pd.DataFrame,
    cliente: str,
    n_meses: int = 6,
) -> dict:
    """
    Genera un resumen ejecutivo para preparar una visita comercial.
    Retorna dict con: compra_total_6m, compra_promedio_mes, top_productos,
                      tendencia, frecuencia, ultimo_pedido, dias_sin_comprar
    """
    result: dict = {"cliente": cliente}

    # Volumen reciente
    if not df_mensual.empty and {"CLIENTE", "PERIODO", "PESO_TON"}.issubset(df_mensual.columns):
        dfm = df_mensual[df_mensual["CLIENTE"] == cliente].copy()
        dfm["PERIODO"] = pd.to_datetime(dfm["PERIODO"], errors="coerce")
        dfm = dfm.dropna(subset=["PERIODO"]).sort_values("PERIODO")
        reciente = dfm.tail(n_meses)
        result["compra_total_6m"] = round(float(reciente["PESO_TON"].sum()), 1)
        result["compra_promedio_mes"] = round(float(reciente["PESO_TON"].mean()), 1)

        if len(dfm) >= 2:
            mitad = len(dfm) // 2
            primera = dfm.iloc[:mitad]["PESO_TON"].mean()
            segunda = dfm.iloc[mitad:]["PESO_TON"].mean()
            if primera > 0:
                var = (segunda - primera) / primera * 100
                result["tendencia"] = "creciente" if var > 10 else "decreciente" if var < -10 else "estable"
                result["tendencia_pct"] = round(var, 1)

    # Top productos
    if not df_cli_prod.empty and {"CLIENTE", "PRODUCTO_LIMPIO", "PESO_TON"}.issubset(df_cli_prod.columns):
        dfp = df_cli_prod[df_cli_prod["CLIENTE"] == cliente]
        top = dfp.nlargest(3, "PESO_TON")[["PRODUCTO_LIMPIO", "PESO_TON"]]
        result["top_productos"] = top.to_dict("records")

    # Frecuencia
    freq = calcular_frecuencia_compra(df_mensual.rename(columns={"PERIODO": "PERIODO"}), cliente)
    result.update({k: freq.get(k) for k in ["freq_dias", "ultima_compra", "dias_sin_comprar"]})

    return result


# ── Cambio de mix por cliente ─────────────────────────────────────────────────

def detectar_cambio_mix_cliente(
    df_mensual_prod: pd.DataFrame,
    cliente: str,
    n_meses_actual: int = 3,
    n_meses_hist: int = 6,
) -> pd.DataFrame:
    """
    Compara la participación de cada producto en los últimos n_meses_actual
    vs los n_meses_hist anteriores para un cliente específico.

    df_mensual_prod: columnas CLIENTE, PERIODO, PRODUCTO_LIMPIO, PESO_TON
    Retorna DataFrame: PRODUCTO, SHARE_ACTUAL, SHARE_HIST, DELTA_PP
    """
    required = {"CLIENTE", "PERIODO", "PRODUCTO_LIMPIO", "PESO_TON"}
    if not required.issubset(df_mensual_prod.columns):
        return pd.DataFrame()

    df = df_mensual_prod[df_mensual_prod["CLIENTE"] == cliente].copy()
    if df.empty:
        return pd.DataFrame()

    df["PERIODO"] = pd.to_datetime(df["PERIODO"], errors="coerce")
    df = df.dropna(subset=["PERIODO"]).sort_values("PERIODO")
    max_fecha = df["PERIODO"].max()
    corte_act = max_fecha - pd.DateOffset(months=n_meses_actual)
    corte_hist = corte_act - pd.DateOffset(months=n_meses_hist)

    actual = df[df["PERIODO"] > corte_act].groupby("PRODUCTO_LIMPIO")["PESO_TON"].sum()
    hist = df[(df["PERIODO"] > corte_hist) & (df["PERIODO"] <= corte_act)].groupby("PRODUCTO_LIMPIO")["PESO_TON"].sum()

    def _to_share(s: pd.Series) -> pd.Series:
        tot = s.sum()
        return (s / tot * 100) if tot > 0 else s * 0

    share_act = _to_share(actual)
    share_hist = _to_share(hist)

    combined = pd.concat({"SHARE_ACTUAL": share_act, "SHARE_HIST": share_hist}, axis=1).fillna(0)
    combined["DELTA_PP"] = combined["SHARE_ACTUAL"] - combined["SHARE_HIST"]
    combined = combined.reset_index().rename(columns={"PRODUCTO_LIMPIO": "PRODUCTO"})
    return combined.sort_values("DELTA_PP", ascending=False).reset_index(drop=True)
