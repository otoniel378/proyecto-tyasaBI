"""
update_market_data.py — Actualización diaria de variables de mercado en BigQuery.
Descarga los últimos 10 días desde yfinance y hace upsert en gold_variables_mercado.

Ejecutar diariamente:
    python scripts/update_market_data.py
O configurar en Task Scheduler con:
    scripts/run_daily_update.bat
"""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
import numpy as np
from google.cloud import bigquery
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

PROJECT_ID = "project-d0cf2519-d089-47d3-930"
DATASET    = "tyasa_bi"
CLIENT     = bigquery.Client(project=PROJECT_ID)

TICKERS = {
    'BZ=F'    : ('Brent_USD',          'Energía'),
    'CL=F'    : ('WTI_USD',            'Energía'),
    'NG=F'    : ('Gas_HenryHub_USD',   'Energía'),
    'TTF=F'   : ('Gas_TTF_Europa',     'Energía'),
    'TIO=F'   : ('Mineral_Hierro',     'Insumos_Acero'),
    'HG=F'    : ('Cobre_USD',          'Insumos_Acero'),
    'ALI=F'   : ('Aluminio_USD',       'Insumos_Acero'),
    'SLX'     : ('ETF_Acero_Global',   'Sector_Acero'),
    'TX'      : ('Ternium_MX',         'Sector_Acero'),
    'MT'      : ('ArcelorMittal',      'Sector_Acero'),
    'NUE'     : ('Nucor_EAF',          'Sector_Acero'),
    'STLD'    : ('SteelDynamics_EAF',  'Sector_Acero'),
    'BDRY'    : ('ETF_Flete_Seco',     'Logistica'),
    'ZIM'     : ('ZIM_Contenedor',     'Logistica'),
    'MATX'    : ('Matson_Pacifico',    'Logistica'),
    'SBLK'    : ('StarBulk',           'Logistica'),
    '^VIX'    : ('VIX',               'Riesgo_Mercados'),
    '^GSPC'   : ('SP500',             'Riesgo_Mercados'),
    'GC=F'    : ('Oro_USD',           'Riesgo_Mercados'),
    'DX-Y.NYB': ('Dolar_Index',       'Riesgo_Mercados'),
    'TLT'     : ('Bonos_20y',         'Riesgo_Mercados'),
    '^N225'   : ('Nikkei_Japon',      'Asia'),
    '^KS11'   : ('KOSPI_Corea',       'Asia'),
    'FXI'     : ('ETF_China',         'Asia'),
    'EWJ'     : ('ETF_Japon',         'Asia'),
    'EWY'     : ('ETF_Corea',         'Asia'),
    'EWG'     : ('ETF_Alemania',      'Europa'),
    'EEM'     : ('ETF_Emergentes',    'Europa'),
    'EWW'     : ('ETF_Mexico',        'Mexico'),
    'MXN=X'   : ('USD_MXN',          'Mexico'),
}

SCHEMA_VARIABLES = [
    bigquery.SchemaField("fecha",      "DATE",      mode="REQUIRED"),
    bigquery.SchemaField("ticker",     "STRING",    mode="REQUIRED"),
    bigquery.SchemaField("nombre",     "STRING",    mode="REQUIRED"),
    bigquery.SchemaField("categoria",  "STRING",    mode="REQUIRED"),
    bigquery.SchemaField("valor",      "FLOAT64",   mode="NULLABLE"),
    bigquery.SchemaField("cargado_en", "TIMESTAMP", mode="REQUIRED"),
]


def actualizar_precios(dias_atras: int = 10) -> int:
    """
    Descarga los últimos `dias_atras` días de todos los tickers
    y hace upsert (delete + insert) en gold_variables_mercado.
    Retorna el número de filas insertadas.
    """
    import yfinance as yf

    inicio = (datetime.utcnow() - timedelta(days=dias_atras)).strftime("%Y-%m-%d")
    ahora  = datetime.utcnow()
    rows   = []

    print(f"Descargando {inicio} → hoy ({len(TICKERS)} tickers)...")
    for ticker, (nombre, categoria) in TICKERS.items():
        try:
            df_t = yf.download(ticker, start=inicio, progress=False, auto_adjust=True)
            if df_t.empty:
                print(f"  ✗ {nombre}: sin datos")
                continue
            s = df_t['Close'].squeeze()
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
            print(f"  ✓ {nombre}: {len(s)} obs")
        except Exception as e:
            print(f"  ✗ {nombre}: {e}")

    if not rows:
        print("Sin datos nuevos para insertar.")
        return 0

    df_new = pd.DataFrame(rows)

    # Upsert: borrar fechas descargadas y reinsertar
    fechas_unicas = sorted(df_new["fecha"].unique())
    fechas_str    = ", ".join(f"DATE '{f}'" for f in fechas_unicas)
    print(f"\nEliminando registros existentes para {len(fechas_unicas)} fechas...")
    CLIENT.query(f"""
        DELETE FROM `{PROJECT_ID}.{DATASET}.gold_variables_mercado`
        WHERE fecha IN ({fechas_str})
    """).result()

    # Insertar frescos
    table_id   = f"{PROJECT_ID}.{DATASET}.gold_variables_mercado"
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_APPEND",
        schema=SCHEMA_VARIABLES,
    )
    job = CLIENT.load_table_from_dataframe(df_new, table_id, job_config=job_config)
    job.result()

    n = len(df_new)
    print(f"✓ {n:,} filas actualizadas en gold_variables_mercado")
    return n


def verificar_ultima_fecha() -> str:
    """Retorna la fecha más reciente en BQ."""
    row = list(CLIENT.query(f"""
        SELECT MAX(fecha) AS ultima
        FROM `{PROJECT_ID}.{DATASET}.gold_variables_mercado`
    """).result())
    return str(row[0]["ultima"]) if row else "desconocida"


if __name__ == "__main__":
    print("=" * 55)
    print(f"TYASA BI — Actualización diaria de mercado")
    print(f"UTC: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 55)

    n = actualizar_precios(dias_atras=10)

    ultima = verificar_ultima_fecha()
    print(f"\n✓ Última fecha en BQ: {ultima}")
    print(f"✓ Total filas insertadas: {n:,}")
    print("=" * 55)
