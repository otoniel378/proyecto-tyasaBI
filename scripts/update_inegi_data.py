"""
update_inegi_data.py — Descarga indicadores INEGI vía BIE API y hace upsert en gold_indicadores_inegi.

Requiere token gratuito: https://www.inegi.org.mx/app/desarrolladores/generaToken/Inicio

Ejecutar mensualmente (los datos INEGI son mensuales/trimestrales):
    python scripts/update_inegi_data.py

O configurar token en .streamlit/secrets.toml:
    [inegi]
    token = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
"""

import os
import sys
import time
import warnings
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests
from google.cloud import bigquery

warnings.filterwarnings("ignore")

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, _ROOT)

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
PROJECT_ID = "project-d0cf2519-d089-47d3-930"
DATASET    = "tyasa_bi"
TABLE      = "gold_indicadores_inegi"
TABLE_FULL = f"{PROJECT_ID}.{DATASET}.{TABLE}"


def _load_token_from_secrets() -> str:
    """Lee el token INEGI de .streamlit/secrets.toml si existe."""
    secrets_path = Path(_ROOT) / ".streamlit" / "secrets.toml"
    if not secrets_path.exists():
        return ""
    try:
        import tomllib  # Python 3.11+
    except ImportError:
        try:
            import tomli as tomllib  # pip install tomli
        except ImportError:
            return ""
    try:
        with open(secrets_path, "rb") as f:
            secrets = tomllib.load(f)
        return secrets.get("inegi", {}).get("token", "")
    except Exception:
        return ""


INEGI_TOKEN = os.environ.get("INEGI_TOKEN", "") or _load_token_from_secrets()

# Catálogo completo de indicadores (IDs INEGI BIE → nombre técnico)
INDICADORES = {
    # ── ACTIVIDAD INDUSTRIAL (IMAI) ───────────────────────────────────────────
    "736407": "IMAI_ActividadIndustrial_Indice",
    "736418": "IMAI_Manufactureras_Indice",
    "736414": "IMAI_Construccion_Indice",
    "736475": "IMAI_MetalicasBasicas_331_Indice",
    "736476": "IMAI_HierroAcero_3311_Indice",
    "736481": "IMAI_ProductosMetalicos_332_Indice",
    "736491": "IMAI_MaquinariaEquipo_333_Indice",
    "736526": "IMAI_ActividadIndustrial_VarAnual",
    "736533": "IMAI_Construccion_VarAnual",
    "736594": "IMAI_MetalicasBasicas_331_VarAnual",
    # ── EMIM ─────────────────────────────────────────────────────────────────
    "910468": "EMIM_VolFisico_Desest_Indice",
    "910470": "EMIM_VolFisico_Desest_VarAnual",
    # ── ENEC ─────────────────────────────────────────────────────────────────
    "720332": "ENEC_ValorProd_ObraTotal",
    "720334": "ENEC_ValorProd_Edificacion",
    "720340": "ENEC_ValorProd_Transporte_Urb",
    # ── EMEC ─────────────────────────────────────────────────────────────────
    "718504": "EMEC_Ingresos_ComercioMayor_43",
    "718506": "EMEC_Ingresos_ComercioMenor_46",
    # ── IGAE ─────────────────────────────────────────────────────────────────
    "737173": "IGAE_Secundario_Indice",
    "737149": "IGAE_Secundario_VarAnual",
    # ── BALANZA COMERCIAL SIDERURGIA ──────────────────────────────────────────
    "133094": "BC_Siderurgia_Importaciones",
    "133031": "BC_Siderurgia_Exportaciones",
    # ── INPP ─────────────────────────────────────────────────────────────────
    "910503": "INPP_Manufactura_3133",
    "910502": "INPP_Construccion_23",
    "910501": "INPP_Energia_22",
    "910500": "INPP_Mineria_SinPetroleo",
    "910499": "INPP_Mineria_ConPetroleo",
    "910491": "INPP_SinPetroleo_ConServicios",
    # ── INPC ─────────────────────────────────────────────────────────────────
    "910396": "INPC_Total_Mensual",
    "909294": "INPC_Energeticos_NoSubyacente",
    "910398": "INPC_Energeticos_Gobierno",
    "910393": "INPC_Subyacente_Total",
    # ── IFB ──────────────────────────────────────────────────────────────────
    "741034": "IFB_Construccion",
    "741030": "IFB_Maquinaria_Importada",
    "741025": "IFB_Maquinaria_Nacional",
    # ── CONFIANZA ─────────────────────────────────────────────────────────────
    "701407": "ICE_Construccion",
    "701401": "ICE_Global",
    "334497": "ICC_Confianza_Consumidor",
}

BATCH_SIZE = 20   # INEGI BIE soporta múltiples IDs por request
BIE_BASE   = "https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml"


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------
def _bie_url(ids: list[str], token: str) -> str:
    ids_str = ",".join(ids)
    return f"{BIE_BASE}/INDICATOR/{ids_str}/es/0700/false/BIE/2.0/{token}.json"


def _fetch_batch(ids: list[str], token: str) -> list[dict]:
    """Descarga un batch de indicadores desde INEGI BIE API. Retorna filas listas para BQ."""
    url = _bie_url(ids, token)
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        print(f"  ✗ Error HTTP: {e}")
        return []
    except ValueError:
        print("  ✗ Respuesta no es JSON válido")
        return []

    series = data.get("Series", [])
    rows = []
    ts = datetime.utcnow().isoformat()

    for serie in series:
        clave   = str(serie.get("INDICADOR", ""))
        nombre  = INDICADORES.get(clave, serie.get("NOMBRE_IND", clave))
        obs_list = serie.get("OBS", [])
        for obs in obs_list:
            periodo = obs.get("PERIODO", "")
            val_str = obs.get("OBS_VALUE", "N/E")
            # Normalizar periodo YYYY/MM → YYYY-MM  |  trimestral YYYY/T1 → ignorar (solo mensuales)
            if "/" not in periodo:
                continue
            parts = periodo.split("/")
            if len(parts) != 2:
                continue
            year, subperiod = parts
            if subperiod.startswith("T"):
                fecha = f"{year}-{(int(subperiod[1]) - 1) * 3 + 1:02d}"
            else:
                try:
                    fecha = f"{year}-{int(subperiod):02d}"
                except ValueError:
                    continue
            try:
                valor = float(val_str) if val_str not in ("N/E", "", "N/A", "null") else None
            except ValueError:
                valor = None
            if valor is None:
                continue
            rows.append({
                "Fecha":       fecha,
                "Clave":       clave,
                "Nombre":      nombre,
                "Valor":       valor,
                "Actualizado": ts,
            })
    return rows


def upsert_bq(client: bigquery.Client, rows: list[dict]) -> int:
    """MERGE temporal: carga a staging y luego MERGE en tabla final."""
    if not rows:
        return 0

    df = pd.DataFrame(rows)

    staging = f"{PROJECT_ID}.{DATASET}._staging_inegi"
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        schema=[
            bigquery.SchemaField("Fecha",       "STRING"),
            bigquery.SchemaField("Clave",        "STRING"),
            bigquery.SchemaField("Nombre",       "STRING"),
            bigquery.SchemaField("Valor",        "FLOAT64"),
            bigquery.SchemaField("Actualizado",  "STRING"),
        ],
    )
    client.load_table_from_dataframe(df, staging, job_config=job_config).result()

    merge_sql = f"""
    MERGE `{TABLE_FULL}` AS T
    USING `{staging}`   AS S
    ON  T.Clave = S.Clave AND T.Fecha = S.Fecha
    WHEN MATCHED THEN
        UPDATE SET Nombre = S.Nombre, Valor = S.Valor, Actualizado = CURRENT_TIMESTAMP()
    WHEN NOT MATCHED THEN
        INSERT (Fecha, Clave, Nombre, Valor, Actualizado)
        VALUES (S.Fecha, S.Clave, S.Nombre, S.Valor, CURRENT_TIMESTAMP())
    """
    client.query(merge_sql).result()
    client.delete_table(staging, not_found_ok=True)
    return len(rows)


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def run(token: str | None = None):
    token = token or INEGI_TOKEN
    if not token:
        print("ERROR: Falta INEGI_TOKEN.")
        print("  1. Registra un token gratis en https://www.inegi.org.mx/app/desarrolladores/generaToken/Inicio")
        print("  2. Agrégalo en .streamlit/secrets.toml:  [inegi]  token = \"xxxx\"")
        print("  3. O exporta la variable de entorno: set INEGI_TOKEN=xxxx  (Windows)")
        sys.exit(1)

    client = bigquery.Client(project=PROJECT_ID)
    ids    = list(INDICADORES.keys())
    batches = [ids[i:i + BATCH_SIZE] for i in range(0, len(ids), BATCH_SIZE)]

    all_rows = []
    print(f"Descargando {len(ids)} indicadores en {len(batches)} batches...")
    for i, batch in enumerate(batches, 1):
        print(f"  Batch {i}/{len(batches)}: {batch[:3]}...")
        rows = _fetch_batch(batch, token)
        all_rows.extend(rows)
        if i < len(batches):
            time.sleep(1)   # respetar rate-limit INEGI

    print(f"  Registros descargados: {len(all_rows)}")

    if all_rows:
        inserted = upsert_bq(client, all_rows)
        print(f"✓ Upsert en {TABLE_FULL}: {inserted} filas procesadas")
    else:
        print("✗ No se obtuvieron datos — verifica el token o los IDs")

    return len(all_rows)


if __name__ == "__main__":
    # Permite pasar el token como argumento: python update_inegi_data.py <token>
    token_arg = sys.argv[1] if len(sys.argv) > 1 else None
    run(token_arg)
