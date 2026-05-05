"""
contexto_mercado.py — Analytics de contexto externo para Aceros Planos Negros.
Conecta datos INEGI y variables de mercado global con la demanda interna.
Sin imports de Streamlit — solo pandas/numpy puro.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# ── Claves INEGI relevantes para Aceros Planos ───────────────────────────────
CLAVES_INEGI_PLANOS = [
    "736418",  # IMAI Manufactureras
    "736476",  # IMAI Hierro y Acero 3311
    "736481",  # IMAI Productos Metálicos 332
    "736491",  # IMAI Maquinaria 333
    "737173",  # IGAE Secundario Índice
    "737149",  # IGAE Secundario Var Anual
    "718504",  # EMEC Comercio Mayor
    "910503",  # INPP Manufactura
    "910396",  # INPC Total
    "741034",  # IFB Construcción
    "741030",  # IFB Maquinaria Importada
]

LABELS_INEGI_PLANOS = {
    "736418": "IMAI Manufactura",
    "736476": "IMAI Hierro y Acero",
    "736481": "IMAI Prod. Metálicos",
    "736491": "IMAI Maquinaria",
    "737173": "IGAE Secundario (idx)",
    "737149": "IGAE Sec. Var. Anual",
    "718504": "EMEC Com. Mayoreo",
    "910503": "INPP Manufactura",
    "910396": "INPC Total",
    "741034": "IFB Construcción",
    "741030": "IFB Maq. Importada",
}

# Variables de mercado y su efecto en demanda de aceros planos
_VARS_CONFIG = {
    "ETF_Acero_Global":   {"signo": +1, "label": "ETF Acero Global",   "umbral_alza": 0.03},
    "USD_MXN":            {"signo": +1, "label": "USD/MXN",            "umbral_alza": 0.0},   # alto = importaciones caras = favorable
    "ArcelorMittal":      {"signo": +1, "label": "ArcelorMittal",      "umbral_alza": 0.02},
    "Ternium_MX":         {"signo": +1, "label": "Ternium MX",         "umbral_alza": 0.02},
    "VIX":                {"signo": -1, "label": "VIX",                "umbral_alza": 0.0},   # alto = incertidumbre = desfavorable
    "SP500":              {"signo": +1, "label": "SP500",              "umbral_alza": 0.02},
}

_INEGI_CONFIG = {
    "736418": {"signo": +1, "label": "IMAI Manufactureras"},
    "737149": {"signo": +1, "label": "IGAE Sec. Var. Anual"},
    "910503": {"signo": +1, "label": "INPP Manufactura"},
    "741030": {"signo": +1, "label": "IFB Maq. Importada"},
    "718504": {"signo": +1, "label": "EMEC Com. Mayoreo"},
}


# ─────────────────────────────────────────────────────────────────────────────
def _latest_values(df_vars: pd.DataFrame) -> dict[str, dict]:
    """Extrae el valor más reciente y la variación 30d de cada variable."""
    if df_vars.empty or "nombre" not in df_vars.columns:
        return {}
    out = {}
    for nombre, grp in df_vars.groupby("nombre"):
        grp = grp.sort_values("fecha")
        if grp.empty:
            continue
        vals = pd.to_numeric(grp["valor"], errors="coerce").dropna()
        if vals.empty:
            continue
        ultimo = float(vals.iloc[-1])
        delta_30 = (
            (ultimo - float(vals.iloc[-31])) / abs(float(vals.iloc[-31])) * 100
            if len(vals) >= 31 and float(vals.iloc[-31]) != 0
            else 0.0
        )
        delta_7 = (
            (ultimo - float(vals.iloc[-8])) / abs(float(vals.iloc[-8])) * 100
            if len(vals) >= 8 and float(vals.iloc[-8]) != 0
            else 0.0
        )
        out[nombre] = {"ultimo": ultimo, "delta_30": delta_30, "delta_7": delta_7, "serie": vals.tolist()}
    return out


def _score_variable(nombre: str, info: dict, latest: dict) -> tuple[float, str | None, str | None]:
    """
    Calcula puntaje 0-2 para una variable de mercado.
    Retorna (score, factor_positivo, factor_negativo).
    """
    if nombre not in latest:
        return 1.0, None, None   # neutral si no hay datos

    cfg  = _VARS_CONFIG.get(nombre, {"signo": +1, "label": nombre, "umbral_alza": 0.02})
    d30  = latest[nombre]["delta_30"]
    val  = latest[nombre]["ultimo"]
    lbl  = cfg["label"]
    sig  = cfg["signo"]

    # Caso especial USD/MXN: favorable si > 19
    if nombre == "USD_MXN":
        if val > 19.5:
            return 2.0, f"{lbl} {val:.2f} — importaciones costosas, precio local favorecido", None
        elif val > 18.5:
            return 1.0, None, None
        else:
            return 0.0, None, f"{lbl} {val:.2f} — peso fuerte facilita importaciones competidoras"

    # Caso especial VIX: desfavorable si > 25
    if nombre == "VIX":
        if val > 30:
            return 0.0, None, f"VIX {val:.0f} — alta incertidumbre frena inversión industrial"
        elif val > 20:
            return 0.5, None, f"VIX {val:.0f} — incertidumbre moderada"
        else:
            return 2.0, f"VIX {val:.0f} — ambiente de baja volatilidad, favorable para capex", None

    # Caso general: movimiento en la dirección correcta
    impacto = d30 * sig
    if impacto > 4:
        return 2.0, f"{lbl} +{d30:.1f}% (30d) — señal positiva para demanda acero", None
    elif impacto > 1:
        return 1.5, f"{lbl} +{d30:.1f}% (30d) — tendencia favorable", None
    elif impacto > -1:
        return 1.0, None, None
    elif impacto > -4:
        return 0.5, None, f"{lbl} {d30:.1f}% (30d) — tendencia desfavorable"
    else:
        return 0.0, None, f"{lbl} {d30:.1f}% (30d) — presión negativa sobre demanda"


def calcular_indice_condicion_comercial(
    df_vars: pd.DataFrame,
    df_inegi_alertas: pd.DataFrame,
) -> dict:
    """
    Retorna un índice 0-10 de qué tan favorable está el entorno para vender
    acero plano en México. Combina variables de mercado (60%) e INEGI (40%).
    """
    factores_pos: list[str] = []
    factores_neg: list[str] = []

    # ── Variables de mercado (60%) ────────────────────────────────────────────
    latest = _latest_values(df_vars)
    vars_score = 0.0
    vars_max   = 0.0
    for nombre, cfg in _VARS_CONFIG.items():
        score, pos, neg = _score_variable(nombre, cfg, latest)
        vars_score += score
        vars_max   += 2.0
        if pos:
            factores_pos.append(pos)
        if neg:
            factores_neg.append(neg)

    score_mercado = (vars_score / vars_max * 10) if vars_max > 0 else 5.0

    # ── INEGI (40%) ───────────────────────────────────────────────────────────
    score_inegi = 5.0   # neutral por defecto si no hay datos
    if not df_inegi_alertas.empty and "Clave" in df_inegi_alertas.columns:
        inegi_scores = []
        for clave, cfg in _INEGI_CONFIG.items():
            row = df_inegi_alertas[df_inegi_alertas["Clave"] == clave]
            if row.empty:
                inegi_scores.append(1.0)
                continue
            z    = float(row.iloc[0].get("z_score", 0.0) or 0.0)
            varm = float(row.iloc[0].get("var_mom", 0.0) or 0.0)
            lbl  = cfg["label"]
            sig  = cfg["signo"]

            impacto = z * sig
            mom_ok  = varm * sig > 0

            if impacto > 1.5:
                inegi_scores.append(2.0)
                factores_pos.append(f"{lbl} z={z:+.1f}σ — por encima de su histórico")
            elif impacto > 0.5:
                inegi_scores.append(1.5)
                if mom_ok:
                    factores_pos.append(f"{lbl} MoM {varm:+.1f}% — mejorando")
            elif impacto < -1.5:
                inegi_scores.append(0.0)
                factores_neg.append(f"{lbl} z={z:+.1f}σ — por debajo de su histórico")
            elif impacto < -0.5:
                inegi_scores.append(0.5)
            else:
                inegi_scores.append(1.0)

        if inegi_scores:
            score_inegi = (sum(inegi_scores) / (len(inegi_scores) * 2)) * 10

    # ── Índice combinado ──────────────────────────────────────────────────────
    indice = round(score_mercado * 0.6 + score_inegi * 0.4, 1)
    indice = max(0.0, min(10.0, indice))

    if indice >= 6.5:
        nivel, color = "Favorable", "#2E7D32"
    elif indice >= 4.0:
        nivel, color = "Moderado", "#E65100"
    else:
        nivel, color = "Adverso", "#C62828"

    ultima = "N/D"
    if not df_vars.empty and "fecha" in df_vars.columns:
        try:
            ultima = str(pd.to_datetime(df_vars["fecha"]).max().strftime("%d %b %Y"))
        except Exception:
            pass

    return {
        "indice": indice,
        "nivel": nivel,
        "color": color,
        "factores_positivos": factores_pos[:5],
        "factores_negativos": factores_neg[:5],
        "score_mercado": round(score_mercado, 1),
        "score_inegi": round(score_inegi, 1),
        "ultima_actualizacion": ultima,
    }


# ─────────────────────────────────────────────────────────────────────────────
def calcular_correlaciones_lag(
    df_demanda_mensual: pd.DataFrame,
    df_vars_mercado: pd.DataFrame,
    variables: list[str],
    max_lag_dias: int = 90,
) -> list[dict]:
    """
    Pearson entre cada variable de mercado y la demanda mensual con lags 0/30/60/90 días.
    """
    if df_demanda_mensual.empty or df_vars_mercado.empty:
        return []

    demand = df_demanda_mensual.copy()
    if "PERIODO" not in demand.columns or "PESO_TON" not in demand.columns:
        return []

    demand["PERIODO"] = pd.to_datetime(demand["PERIODO"], errors="coerce")
    demand = demand.dropna(subset=["PERIODO"]).sort_values("PERIODO")
    demand["ym"] = demand["PERIODO"].dt.to_period("M")
    demand_m = demand.groupby("ym")["PESO_TON"].sum().reset_index()

    lags = [0, 30, 60, 90]
    lags = [l for l in lags if l <= max_lag_dias]
    resultados = []

    for var in variables:
        df_v = df_vars_mercado[df_vars_mercado["nombre"] == var].copy()
        if df_v.empty:
            continue
        df_v["fecha"] = pd.to_datetime(df_v["fecha"], errors="coerce")
        df_v = df_v.dropna(subset=["fecha"]).sort_values("fecha")
        df_v["valor"] = pd.to_numeric(df_v["valor"], errors="coerce")

        mejor_r, mejor_lag, mejor_interp = 0.0, 0, ""
        for lag in lags:
            df_v_lag = df_v.copy()
            df_v_lag["fecha_adj"] = df_v_lag["fecha"] - pd.Timedelta(days=lag)
            df_v_lag["ym"] = df_v_lag["fecha_adj"].dt.to_period("M")
            v_m = df_v_lag.groupby("ym")["valor"].mean().reset_index()
            merged = demand_m.merge(v_m, on="ym", how="inner")
            if len(merged) < 6:
                continue
            try:
                r = float(merged["PESO_TON"].corr(merged["valor"]))
                if not np.isnan(r) and abs(r) > abs(mejor_r):
                    mejor_r   = r
                    mejor_lag = lag
            except Exception:
                continue

        if abs(mejor_r) < 0.15:
            continue

        dir_var = "sube" if mejor_r > 0 else "baja"
        dir_dem = "aumenta" if mejor_r > 0 else "disminuye"
        plazo   = f"en {mejor_lag} días" if mejor_lag > 0 else "simultáneamente"
        interp  = (
            f"Cuando {var.replace('_',' ')} {dir_var}, "
            f"la demanda de Aceros Planos {dir_dem} {plazo} "
            f"(r={mejor_r:+.2f})"
        )

        resultados.append({
            "variable":       var,
            "mejor_lag_dias": mejor_lag,
            "correlacion":    round(mejor_r, 3),
            "interpretacion": interp,
            "significativa":  abs(mejor_r) >= 0.4,
        })

    return sorted(resultados, key=lambda x: abs(x["correlacion"]), reverse=True)


# ─────────────────────────────────────────────────────────────────────────────
def detectar_ventanas_oportunidad(
    df_vars: pd.DataFrame,
    df_inegi: pd.DataFrame,
) -> list[dict]:
    """
    Detecta ventanas de oportunidad activas combinando variables de mercado e INEGI.
    """
    ventanas: list[dict] = []
    latest = _latest_values(df_vars)

    def _add(tipo, desc, nivel, accion, vars_inv):
        ventanas.append({
            "tipo": tipo,
            "descripcion": desc,
            "nivel": nivel,
            "accion_sugerida": accion,
            "variables_involucradas": vars_inv,
        })

    # ── Ventana 1: USD/MXN alto (importaciones caras) ────────────────────────
    if "USD_MXN" in latest:
        val = latest["USD_MXN"]["ultimo"]
        d30 = latest["USD_MXN"]["delta_30"]
        if val > 19.5:
            _add(
                "Ventaja Cambiaria",
                f"USD/MXN en {val:.2f} — acero importado más caro que producción local.",
                "Alta",
                "Ofrecer precio firme a clientes que compran acero importado; comunicar ventaja de costo.",
                ["USD_MXN"],
            )
        elif val > 18.5 and d30 > 2:
            _add(
                "Tipo de Cambio en Alza",
                f"USD/MXN subiendo ({d30:+.1f}% en 30d) — presión creciente sobre importaciones.",
                "Media",
                "Anticipar ajuste de precios; advertir a clientes sobre riesgo de alza.",
                ["USD_MXN"],
            )

    # ── Ventana 2: VIX bajo + Manufactureras activas ─────────────────────────
    vix_ok  = "VIX" in latest and latest["VIX"]["ultimo"] < 18
    mfr_ok  = False
    if not df_inegi.empty and "Clave" in df_inegi.columns:
        row_mfr = df_inegi[df_inegi["Clave"] == "736418"]
        if not row_mfr.empty:
            z_mfr  = float(row_mfr.iloc[0].get("z_score", 0) or 0)
            mfr_ok = z_mfr > 0.2

    if vix_ok and mfr_ok:
        _add(
            "Ambiente Expansivo",
            "Volatilidad baja + manufactura activa — condición óptima para capex industrial.",
            "Alta",
            "Activar clientes dormidos; proponer pedidos de largo plazo con precio fijo.",
            ["VIX", "736418"],
        )
    elif vix_ok:
        _add(
            "Baja Volatilidad",
            f"VIX {latest.get('VIX', {}).get('ultimo', 0):.0f} — entorno estable para inversión.",
            "Media",
            "Momento favorable para propuestas de contratos anuales.",
            ["VIX"],
        )

    # ── Ventana 3: ETF Acero Global subiendo ──────────────────────────────────
    if "ETF_Acero_Global" in latest:
        d30 = latest["ETF_Acero_Global"]["delta_30"]
        if d30 > 8:
            _add(
                "Precios Globales Acero en Alza",
                f"ETF Acero Global +{d30:.1f}% en 30d — precios HRC globales subiendo.",
                "Alta",
                "Ajustar precios locales antes del próximo ciclo; comunicar tendencia global a clientes.",
                ["ETF_Acero_Global"],
            )
        elif d30 > 4:
            _add(
                "Señal Alcista en Acero Global",
                f"ETF Acero Global +{d30:.1f}% en 30d — presión alcista moderada.",
                "Media",
                "Revisar lista de precios; considerar ajuste preventivo.",
                ["ETF_Acero_Global"],
            )

    # ── Ventana 4: Ternium subiendo (competidor activo) ───────────────────────
    if "Ternium_MX" in latest:
        d30_tx = latest["Ternium_MX"]["delta_30"]
        if d30_tx > 8:
            _add(
                "Competidor Ajustando Precios",
                f"Ternium MX +{d30_tx:.1f}% en 30d — posible alza de precios del competidor.",
                "Alta",
                "Monitorear comunicados de Ternium; si sube precios, capturar clientes con oferta competitiva.",
                ["Ternium_MX"],
            )

    # ── Ventana 5: Manufactura en expansión (INEGI) ───────────────────────────
    if not df_inegi.empty and "Clave" in df_inegi.columns:
        for clave, label in [("736491", "IMAI Maquinaria"), ("736481", "IMAI Prod. Metálicos")]:
            row = df_inegi[df_inegi["Clave"] == clave]
            if row.empty:
                continue
            z   = float(row.iloc[0].get("z_score", 0) or 0)
            mom = float(row.iloc[0].get("var_mom", 0) or 0)
            if z > 1.5 and mom > 0:
                _add(
                    f"Sector Industrial Expandiéndose",
                    f"{label} z={z:+.1f}σ — sector consume más lámina y productos metálicos.",
                    "Alta",
                    f"Activar prospección en sector {label.replace('IMAI ','')}; priorizar clientes industriales.",
                    [clave],
                )
                break

    # ── Señales adversas ──────────────────────────────────────────────────────
    if "ETF_Acero_Global" in latest and latest["ETF_Acero_Global"]["delta_30"] < -8:
        d = latest["ETF_Acero_Global"]["delta_30"]
        _add(
            "Precios Globales Acero a la Baja",
            f"ETF Acero Global {d:.1f}% en 30d — presión bajista en precios.",
            "Baja",
            "Posición defensiva en precios; evitar comprometer inventario a precios fijos altos.",
            ["ETF_Acero_Global"],
        )

    return ventanas


# ─────────────────────────────────────────────────────────────────────────────
def obtener_indicadores_inegi_relevantes(df_alertas: pd.DataFrame) -> dict:
    """
    Filtra df_alertas a indicadores relevantes para Aceros Planos.
    """
    if df_alertas.empty:
        return {"claves_relevantes": CLAVES_INEGI_PLANOS, "alertas_activas": pd.DataFrame(), "kpis_clave": {}}

    alertas = df_alertas[df_alertas["Clave"].isin(CLAVES_INEGI_PLANOS)].copy() if "Clave" in df_alertas.columns else pd.DataFrame()

    kpis: dict = {}
    if not alertas.empty:
        for _, row in alertas.iterrows():
            clave = str(row.get("Clave", ""))
            if clave in LABELS_INEGI_PLANOS:
                kpis[LABELS_INEGI_PLANOS[clave]] = {
                    "valor":  row.get("ult_valor"),
                    "alerta": row.get("alerta", "Normal"),
                    "var_mom": row.get("var_mom"),
                    "z_score": row.get("z_score"),
                }

    return {
        "claves_relevantes": CLAVES_INEGI_PLANOS,
        "alertas_activas":   alertas,
        "kpis_clave":        kpis,
    }
