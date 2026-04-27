"""
alertas.py — Detección de anomalías y alertas comerciales para TYASA.

Funciones principales:
  detectar_clientes_en_fuga      — Clientes con caída sostenida de volumen
  detectar_enfriamiento          — Clientes con compra menor al promedio reciente
  detectar_cambio_mix            — Cambio significativo en mezcla de productos
  calcular_proyeccion_cierre_mes — Proyección de cierre mensual vs objetivo
  detectar_anomalias_volumen     — Detección estadística de outliers en serie mensual
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from datetime import date


# ── Clientes en fuga ──────────────────────────────────────────────────────────

def detectar_clientes_en_fuga(
    df_mensual: pd.DataFrame,
    n_meses_ventana: int = 3,
    umbral_caida_pct: float = 30.0,
    min_historico_meses: int = 6,
) -> pd.DataFrame:
    """
    Detecta clientes cuyo volumen promedio en los últimos n_meses_ventana
    cayó más de umbral_caida_pct% respecto al periodo anterior equivalente.

    df_mensual: columnas CLIENTE, PERIODO, PESO_TON
    Retorna DataFrame con: CLIENTE, PROMEDIO_RECIENTE, PROMEDIO_ANTERIOR,
                           CAIDA_PCT, SEVERIDAD
    """
    required = {"CLIENTE", "PERIODO", "PESO_TON"}
    if not required.issubset(df_mensual.columns):
        return pd.DataFrame()

    df = df_mensual.copy()
    df["PERIODO"] = pd.to_datetime(df["PERIODO"], errors="coerce")
    df = df.dropna(subset=["PERIODO"])

    max_fecha = df["PERIODO"].max()
    corte_reciente = max_fecha - pd.DateOffset(months=n_meses_ventana)
    corte_anterior = corte_reciente - pd.DateOffset(months=n_meses_ventana)

    results = []
    for cliente, grp in df.groupby("CLIENTE"):
        hist = grp.set_index("PERIODO")["PESO_TON"].resample("MS").sum()
        if len(hist) < min_historico_meses:
            continue
        reciente = hist[hist.index > corte_reciente].mean()
        anterior = hist[(hist.index > corte_anterior) & (hist.index <= corte_reciente)].mean()
        if anterior == 0:
            continue
        caida = (reciente - anterior) / anterior * 100
        if caida <= -umbral_caida_pct:
            sev = "alta" if caida <= -60 else "media" if caida <= -40 else "baja"
            results.append({
                "CLIENTE": cliente,
                "PROMEDIO_RECIENTE": round(reciente, 2),
                "PROMEDIO_ANTERIOR": round(anterior, 2),
                "CAIDA_PCT": round(caida, 1),
                "SEVERIDAD": sev,
            })

    if not results:
        return pd.DataFrame(columns=["CLIENTE", "PROMEDIO_RECIENTE", "PROMEDIO_ANTERIOR",
                                     "CAIDA_PCT", "SEVERIDAD"])
    return pd.DataFrame(results).sort_values("CAIDA_PCT")


# ── Enfriamiento ──────────────────────────────────────────────────────────────

def detectar_enfriamiento(
    df_mensual: pd.DataFrame,
    meses_referencia: int = 6,
    umbral_pct: float = 25.0,
) -> pd.DataFrame:
    """
    Clientes cuyo último mes registrado está por debajo de umbral_pct%
    respecto a su promedio de los últimos meses_referencia meses.

    Retorna DataFrame con: CLIENTE, ULTIMO_MES, PROMEDIO_REF, DIFF_PCT, SEVERIDAD
    """
    required = {"CLIENTE", "PERIODO", "PESO_TON"}
    if not required.issubset(df_mensual.columns):
        return pd.DataFrame()

    df = df_mensual.copy()
    df["PERIODO"] = pd.to_datetime(df["PERIODO"], errors="coerce")
    df = df.dropna(subset=["PERIODO"])
    max_fecha = df["PERIODO"].max()
    corte = max_fecha - pd.DateOffset(months=meses_referencia)

    results = []
    for cliente, grp in df.groupby("CLIENTE"):
        hist = grp.set_index("PERIODO")["PESO_TON"].resample("MS").sum()
        ultimo = hist.iloc[-1] if len(hist) >= 1 else 0
        ref = hist[(hist.index > corte) & (hist.index < hist.index[-1])]
        promedio = ref.mean() if len(ref) >= 2 else 0
        if promedio == 0:
            continue
        diff = (ultimo - promedio) / promedio * 100
        if diff <= -umbral_pct:
            sev = "alta" if diff <= -50 else "media" if diff <= -30 else "baja"
            results.append({
                "CLIENTE": cliente,
                "ULTIMO_MES": round(ultimo, 2),
                "PROMEDIO_REF": round(promedio, 2),
                "DIFF_PCT": round(diff, 1),
                "SEVERIDAD": sev,
            })

    if not results:
        return pd.DataFrame(columns=["CLIENTE", "ULTIMO_MES", "PROMEDIO_REF",
                                     "DIFF_PCT", "SEVERIDAD"])
    return pd.DataFrame(results).sort_values("DIFF_PCT")


# ── Cambio de mix ─────────────────────────────────────────────────────────────

def detectar_cambio_mix(
    df_cli_prod: pd.DataFrame,
    df_cli_prod_hist: pd.DataFrame | None = None,
    umbral_cambio_pct: float = 15.0,
) -> pd.DataFrame:
    """
    Detecta clientes cuya participación de algún producto cambió más de
    umbral_cambio_pct puntos porcentuales vs el mix histórico.

    df_cli_prod: columnas CLIENTE, PRODUCTO_LIMPIO, PESO_TON (periodo actual)
    df_cli_prod_hist: mismo esquema (periodo histórico de referencia)
    Retorna DataFrame con: CLIENTE, PRODUCTO, SHARE_ACTUAL, SHARE_HIST, DELTA_PP
    """
    required = {"CLIENTE", "PRODUCTO_LIMPIO", "PESO_TON"}
    if not required.issubset(df_cli_prod.columns):
        return pd.DataFrame()
    if df_cli_prod_hist is None or df_cli_prod_hist.empty:
        return pd.DataFrame()

    def _shares(df: pd.DataFrame) -> pd.DataFrame:
        tot = df.groupby("CLIENTE")["PESO_TON"].transform("sum")
        d = df.copy()
        d["SHARE"] = d["PESO_TON"] / tot.replace(0, np.nan) * 100
        return d[["CLIENTE", "PRODUCTO_LIMPIO", "SHARE"]]

    actual = _shares(df_cli_prod)
    hist = _shares(df_cli_prod_hist)

    merged = actual.merge(hist, on=["CLIENTE", "PRODUCTO_LIMPIO"],
                          suffixes=("_ACT", "_HIST"), how="outer").fillna(0)
    merged["DELTA_PP"] = merged["SHARE_ACT"] - merged["SHARE_HIST"]
    result = merged[merged["DELTA_PP"].abs() >= umbral_cambio_pct].copy()
    result = result.rename(columns={
        "PRODUCTO_LIMPIO": "PRODUCTO",
        "SHARE_ACT": "SHARE_ACTUAL",
        "SHARE_HIST": "SHARE_HIST",
    })
    return result.sort_values("DELTA_PP", ascending=False).reset_index(drop=True)


# ── Proyección cierre mes ─────────────────────────────────────────────────────

def calcular_proyeccion_cierre_mes(
    df_mensual_total: pd.DataFrame,
    objetivo_mensual: float | None = None,
) -> dict:
    """
    Proyecta el cierre del mes en curso basado en el volumen acumulado
    y la proporción de días transcurridos.

    df_mensual_total: columnas PERIODO, PESO_TON (serie mensual total)
    objetivo_mensual: objetivo de toneladas del mes (opcional)

    Retorna dict con:
      mes_actual, acumulado_real, promedio_12m, proyeccion_fin_mes,
      objetivo, pct_objetivo, dias_restantes, avance_pct_mes
    """
    if df_mensual_total.empty:
        return {}

    df = df_mensual_total.copy()
    df["PERIODO"] = pd.to_datetime(df["PERIODO"], errors="coerce")
    df = df.dropna(subset=["PERIODO"]).sort_values("PERIODO")

    hoy = date.today()
    mes_actual = pd.Period(hoy, "M")
    total_dias_mes = (pd.Period(hoy, "M") + 1).start_time.date() - pd.Period(hoy, "M").start_time.date()
    dias_transcurridos = hoy.day
    avance_pct = dias_transcurridos / total_dias_mes.days

    # Volumen del mes actual en BQ (puede ser parcial o del último cierre)
    df_actual = df[df["PERIODO"].dt.to_period("M") == mes_actual]
    acumulado = float(df_actual["PESO_TON"].sum()) if not df_actual.empty else 0.0

    # Promedio de los últimos 12 meses cerrados
    meses_cerrados = df[df["PERIODO"].dt.to_period("M") < mes_actual].tail(12)
    promedio_12m = float(meses_cerrados["PESO_TON"].mean()) if not meses_cerrados.empty else 0.0

    # Proyección: si tenemos datos del mes actual, extrapolar; si no, usar promedio
    if acumulado > 0 and avance_pct > 0:
        proyeccion = acumulado / avance_pct
    else:
        proyeccion = promedio_12m

    dias_restantes = total_dias_mes.days - dias_transcurridos
    objetivo = objetivo_mensual or promedio_12m
    pct_objetivo = (proyeccion / objetivo * 100) if objetivo > 0 else 0.0

    return {
        "mes_actual": hoy.strftime("%B %Y"),
        "acumulado_real": round(acumulado, 1),
        "promedio_12m": round(promedio_12m, 1),
        "proyeccion_fin_mes": round(proyeccion, 1),
        "objetivo": round(objetivo, 1),
        "pct_objetivo": round(pct_objetivo, 1),
        "dias_restantes": dias_restantes,
        "avance_pct_mes": round(avance_pct * 100, 1),
    }


# ── Anomalías estadísticas en volumen ────────────────────────────────────────

def detectar_anomalias_volumen(
    df_mensual: pd.DataFrame,
    n_sigma: float = 2.0,
    ventana: int = 12,
) -> pd.DataFrame:
    """
    Detecta meses con volumen anómalo (> n_sigma desviaciones estándar
    sobre media móvil de ventana meses).

    df_mensual: columnas PERIODO, PESO_TON (serie mensual total o por cliente)
    Retorna DataFrame con: PERIODO, PESO_TON, MEDIA_MOV, STD_MOV, Z_SCORE, TIPO
    """
    required = {"PERIODO", "PESO_TON"}
    if not required.issubset(df_mensual.columns):
        return pd.DataFrame()

    df = df_mensual.copy()
    df["PERIODO"] = pd.to_datetime(df["PERIODO"], errors="coerce")
    df = df.dropna(subset=["PERIODO"]).sort_values("PERIODO").reset_index(drop=True)

    df["MEDIA_MOV"] = df["PESO_TON"].rolling(ventana, min_periods=3).mean()
    df["STD_MOV"] = df["PESO_TON"].rolling(ventana, min_periods=3).std()
    df["Z_SCORE"] = (df["PESO_TON"] - df["MEDIA_MOV"]) / df["STD_MOV"].replace(0, np.nan)

    anomalas = df[df["Z_SCORE"].abs() >= n_sigma].copy()
    anomalas["TIPO"] = anomalas["Z_SCORE"].apply(
        lambda z: "pico" if z > 0 else "caída"
    )
    return anomalas[["PERIODO", "PESO_TON", "MEDIA_MOV", "STD_MOV", "Z_SCORE", "TIPO"]].reset_index(drop=True)
