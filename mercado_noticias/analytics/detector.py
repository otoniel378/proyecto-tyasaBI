"""
detector.py — Detección automática de quiebres estructurales en variables de mercado.
Implementa Prueba de Chow + z-score para alertas en tiempo real.
"""
import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from scipy.stats import f as f_dist, ttest_ind


@dataclass
class QuiebreResult:
    variable:    str
    categoria:   str
    fecha_corte: pd.Timestamp
    F_stat:      float | None
    p_value:     float | None
    sigma:       float | None
    cambio_pct:  float | None
    media_pre:   float | None
    media_post:  float | None
    severidad:   str
    quiebre:     bool


def chow_test(serie: pd.Series, fecha_corte: pd.Timestamp) -> tuple[float | None, float | None]:
    y = serie.dropna().sort_index()
    n = len(y)
    if n < 20:
        return None, None
    X = np.column_stack([np.ones(n), np.arange(n)])
    idx = int((y.index >= fecha_corte).argmax())
    if idx < 10 or (n - idx) < 5:
        return None, None

    def rss(Xm, ym):
        b, _, _, _ = np.linalg.lstsq(Xm, ym, rcond=None)
        return float(np.sum((ym - Xm @ b) ** 2))

    rf = rss(X, y.values)
    r1 = rss(X[:idx], y.values[:idx])
    r2 = rss(X[idx:], y.values[idx:])
    k  = X.shape[1]
    d  = (r1 + r2) / (n - 2 * k)
    if d <= 0:
        return None, None
    F = ((rf - r1 - r2) / k) / d
    p = float(1 - f_dist.cdf(max(F, 0), k, n - 2 * k))
    return round(F, 3), round(p, 4)


def calcular_sigma(serie: pd.Series, fecha_corte: pd.Timestamp) -> float | None:
    pre  = serie[serie.index <  fecha_corte].dropna()
    post = serie[serie.index >= fecha_corte].dropna()
    if len(pre) < 10 or len(post) < 1:
        return None
    mu  = pre.mean()
    std = pre.std()
    if std == 0:
        return None
    return round(float((post.mean() - mu) / std), 2)


def calcular_cambio(serie: pd.Series, fecha_corte: pd.Timestamp) -> tuple[float | None, float | None, float | None]:
    pre  = serie[serie.index <  fecha_corte].dropna()
    post = serie[serie.index >= fecha_corte].dropna()
    if len(pre) < 5 or len(post) < 1:
        return None, None, None
    mp  = float(pre.mean())
    mpo = float(post.mean())
    pct = (mpo - mp) / abs(mp) * 100 if mp != 0 else None
    return round(mp, 2), round(mpo, 2), round(pct, 2) if pct is not None else None


def clasificar_severidad(sigma: float | None, p_value: float | None) -> str:
    if sigma is None:
        return "Sin datos"
    s = abs(sigma)
    if s >= 4.0 or (p_value is not None and p_value < 0.001 and s >= 3):
        return "Crítico"
    if s >= 2.5 or (p_value is not None and p_value < 0.01 and s >= 2):
        return "Alto"
    if s >= 1.5 or (p_value is not None and p_value < 0.05):
        return "Moderado"
    return "Normal"


def detectar_quiebres(
    df_variables: pd.DataFrame,
    fecha_corte: pd.Timestamp,
    umbral_sigma: float = 1.5,
) -> list[QuiebreResult]:
    """
    Recibe df en formato long (fecha, nombre, categoria, valor).
    Retorna lista de QuiebreResult para todas las variables con quiebre detectado.
    """
    resultados = []
    nombres = df_variables["nombre"].unique() if not df_variables.empty else []

    for nombre in nombres:
        sub = df_variables[df_variables["nombre"] == nombre].copy()
        sub = sub.set_index("fecha")["valor"].sort_index()
        cat = df_variables[df_variables["nombre"] == nombre]["categoria"].iloc[0]

        sigma  = calcular_sigma(sub, fecha_corte)
        if sigma is None or abs(sigma) < umbral_sigma:
            resultados.append(QuiebreResult(
                variable=nombre, categoria=cat,
                fecha_corte=fecha_corte,
                F_stat=None, p_value=None, sigma=sigma,
                cambio_pct=None, media_pre=None, media_post=None,
                severidad="Normal", quiebre=False,
            ))
            continue

        F, p = chow_test(sub, fecha_corte)
        mp, mpo, pct = calcular_cambio(sub, fecha_corte)
        sev = clasificar_severidad(sigma, p)

        resultados.append(QuiebreResult(
            variable=nombre, categoria=cat,
            fecha_corte=fecha_corte,
            F_stat=F, p_value=p, sigma=sigma,
            cambio_pct=pct, media_pre=mp, media_post=mpo,
            severidad=sev,
            quiebre=(p < 0.05 if p is not None else abs(sigma) >= umbral_sigma),
        ))

    return resultados


def detectar_quiebres_automatico(
    df_variables: pd.DataFrame,
    umbral_sigma: float = 2.0,
    ventana_base: int = 180,
    ventana_alerta: int = 5,
    dias_excluir_recientes: int = 45,
) -> list[dict]:
    """
    Detecta quiebres en tiempo real usando z-score con baseline limpio.

    Clave: excluye los últimos `dias_excluir_recientes` días del baseline
    para evitar que el evento actual contamine la media de referencia.
    Ejemplo con datos a 2026-04-09 y dias_excluir_recientes=45:
      - Baseline: hasta ~Feb 23 2026 (pre-Ormuz), últimos 180 días de ese período
      - Reciente: últimos 5 días hábiles
    """
    alertas = []
    if df_variables.empty:
        return alertas

    nombres = df_variables["nombre"].unique()

    for nombre in nombres:
        sub = (df_variables[df_variables["nombre"] == nombre]
               .set_index("fecha")["valor"]
               .sort_index()
               .dropna())

        if len(sub) < ventana_base + ventana_alerta + dias_excluir_recientes:
            continue

        cat = df_variables[df_variables["nombre"] == nombre]["categoria"].iloc[0]

        # Baseline limpio: excluir los últimos N días para no contaminar con el evento
        serie_pre = sub.iloc[:-dias_excluir_recientes]
        if len(serie_pre) < ventana_base:
            continue
        base    = serie_pre.iloc[-ventana_base:]   # últimos `ventana_base` días del período pre-evento
        reciente = sub.iloc[-ventana_alerta:]       # últimos 5 días hábiles reales

        mu  = float(base.mean())
        std = float(base.std())
        if std == 0:
            continue

        sigma_actual = float((reciente.mean() - mu) / std)
        cambio_7d    = (
            float((sub.iloc[-1] - sub.iloc[-8]) / abs(sub.iloc[-8]) * 100)
            if len(sub) >= 8 else 0.0
        )

        if abs(sigma_actual) >= umbral_sigma:
            tendencia = 'sube' if sigma_actual > 0 else 'baja'
            alertas.append({
                'variable':        nombre,
                'categoria':       cat,
                'fecha_deteccion': sub.index[-1],
                'sigma_actual':    round(sigma_actual, 2),
                'valor_actual':    round(float(sub.iloc[-1]), 2),
                'media_base':      round(mu, 2),
                'cambio_7d_pct':   round(cambio_7d, 1),
                'tendencia':       tendencia,
                'severidad':       clasificar_severidad(sigma_actual, None),
            })

    alertas.sort(key=lambda x: abs(x['sigma_actual']), reverse=True)
    return alertas


def resumen_quiebres(resultados: list[QuiebreResult]) -> pd.DataFrame:
    if not resultados:
        return pd.DataFrame()
    rows = [vars(r) for r in resultados]
    df = pd.DataFrame(rows)
    df["fecha_corte"] = pd.to_datetime(df["fecha_corte"])
    return df.sort_values("sigma", key=lambda x: x.abs(), ascending=False).reset_index(drop=True)
