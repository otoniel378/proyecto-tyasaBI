"""
main.py — Cloud Function HTTP trigger para actualización diaria de variables de mercado.
Cloud Scheduler llama a esta función cada día a las 7:00 AM México (13:00 UTC).

Deploy:
    gcloud functions deploy update-market-daily \
        --gen2 --runtime python311 --region us-central1 \
        --source cloud_functions/update_market \
        --entry-point update_market \
        --trigger-http --no-allow-unauthenticated \
        --memory 512MB --timeout 300s \
        --set-env-vars PROJECT_ID=project-d0cf2519-d089-47d3-930,DATASET=tyasa_bi
"""

import os
import functions_framework
import pandas as pd
import numpy as np
from google.cloud import bigquery
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings("ignore")

PROJECT_ID = os.environ.get("PROJECT_ID", "project-d0cf2519-d089-47d3-930")
DATASET    = os.environ.get("DATASET",    "tyasa_bi")

TICKERS = {
    "BZ=F"    : ("Brent_USD",          "Energía"),
    "CL=F"    : ("WTI_USD",            "Energía"),
    "NG=F"    : ("Gas_HenryHub_USD",   "Energía"),
    "TTF=F"   : ("Gas_TTF_Europa",     "Energía"),
    "TIO=F"   : ("Mineral_Hierro",     "Insumos_Acero"),
    "HG=F"    : ("Cobre_USD",          "Insumos_Acero"),
    "ALI=F"   : ("Aluminio_USD",       "Insumos_Acero"),
    "SLX"     : ("ETF_Acero_Global",   "Sector_Acero"),
    "TX"      : ("Ternium_MX",         "Sector_Acero"),
    "MT"      : ("ArcelorMittal",      "Sector_Acero"),
    "NUE"     : ("Nucor_EAF",          "Sector_Acero"),
    "STLD"    : ("SteelDynamics_EAF",  "Sector_Acero"),
    "BDRY"    : ("ETF_Flete_Seco",     "Logistica"),
    "ZIM"     : ("ZIM_Contenedor",     "Logistica"),
    "MATX"    : ("Matson_Pacifico",    "Logistica"),
    "SBLK"    : ("StarBulk",           "Logistica"),
    "^VIX"    : ("VIX",               "Riesgo_Mercados"),
    "^GSPC"   : ("SP500",             "Riesgo_Mercados"),
    "GC=F"    : ("Oro_USD",           "Riesgo_Mercados"),
    "DX-Y.NYB": ("Dolar_Index",       "Riesgo_Mercados"),
    "TLT"     : ("Bonos_20y",         "Riesgo_Mercados"),
    "^N225"   : ("Nikkei_Japon",      "Asia"),
    "^KS11"   : ("KOSPI_Corea",       "Asia"),
    "FXI"     : ("ETF_China",         "Asia"),
    "EWJ"     : ("ETF_Japon",         "Asia"),
    "EWY"     : ("ETF_Corea",         "Asia"),
    "EWG"     : ("ETF_Alemania",      "Europa"),
    "EEM"     : ("ETF_Emergentes",    "Europa"),
    "EWW"     : ("ETF_Mexico",        "Mexico"),
    "MXN=X"   : ("USD_MXN",          "Mexico"),
}

SCHEMA = [
    bigquery.SchemaField("fecha",      "DATE",      mode="REQUIRED"),
    bigquery.SchemaField("ticker",     "STRING",    mode="REQUIRED"),
    bigquery.SchemaField("nombre",     "STRING",    mode="REQUIRED"),
    bigquery.SchemaField("categoria",  "STRING",    mode="REQUIRED"),
    bigquery.SchemaField("valor",      "FLOAT64",   mode="NULLABLE"),
    bigquery.SchemaField("cargado_en", "TIMESTAMP", mode="REQUIRED"),
]


def _actualizar_precios(dias_atras: int = 10) -> dict:
    import yfinance as yf

    client = bigquery.Client(project=PROJECT_ID)
    inicio = (datetime.utcnow() - timedelta(days=dias_atras)).strftime("%Y-%m-%d")
    ahora  = datetime.utcnow()
    rows   = []
    errores = []

    for ticker, (nombre, categoria) in TICKERS.items():
        try:
            df_t = yf.download(ticker, start=inicio, progress=False, auto_adjust=True)
            if df_t.empty:
                errores.append(nombre)
                continue
            s = df_t["Close"].squeeze()
            if isinstance(s, pd.DataFrame):
                s = s.iloc[:, 0]
            s = s.dropna()
            for fecha, valor in s.items():
                rows.append({
                    "fecha":      fecha.date(),
                    "ticker":     ticker,
                    "nombre":     nombre,
                    "categoria":  categoria,
                    "valor":      float(valor) if not np.isnan(valor) else None,
                    "cargado_en": ahora,
                })
        except Exception as e:
            errores.append(f"{nombre}: {e}")

    if not rows:
        return {"filas": 0, "errores": errores, "ultima_fecha": None}

    df_new     = pd.DataFrame(rows)
    fechas_str = ", ".join(f"DATE '{f}'" for f in sorted(df_new["fecha"].unique()))

    # Upsert: delete fechas y reinsertar
    client.query(f"""
        DELETE FROM `{PROJECT_ID}.{DATASET}.gold_variables_mercado`
        WHERE fecha IN ({fechas_str})
    """).result()

    table_id   = f"{PROJECT_ID}.{DATASET}.gold_variables_mercado"
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_APPEND",
        schema=SCHEMA,
    )
    job = client.load_table_from_dataframe(df_new, table_id, job_config=job_config)
    job.result()

    ultima = str(df_new["fecha"].max())
    return {"filas": len(rows), "errores": errores, "ultima_fecha": ultima}


@functions_framework.http
def update_market(request):
    """
    Entry point para Cloud Functions.
    Cloud Scheduler llama con POST vacío cada día.
    """
    try:
        resultado = _actualizar_precios(dias_atras=10)
        msg = (
            f"OK | filas={resultado['filas']} "
            f"| ultima={resultado['ultima_fecha']} "
            f"| errores={len(resultado['errores'])}"
        )
        print(msg)
        if resultado["errores"]:
            print("Errores:", resultado["errores"])
        return msg, 200
    except Exception as e:
        import traceback
        err = traceback.format_exc()
        print(f"ERROR: {err}")
        return f"ERROR: {e}", 500
