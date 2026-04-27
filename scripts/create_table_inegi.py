"""
create_table_inegi.py — Crea tabla gold_indicadores_inegi en BigQuery.
"""

import os
import sys

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

from core.db_connector import get_bq_client

def crear_tabla():
    client = get_bq_client()
    dataset_id = "tyasa_bi"
    tabla_id = "gold_indicadores_inegi"
    
    try:
        sql = f"""
        CREATE TABLE IF NOT EXISTS `{client.project}.{dataset_id}.{tabla_id}` (
            Fecha STRING NOT NULL,
            Clave STRING NOT NULL,
            Nombre STRING NOT NULL,
            Valor FLOAT64,
            Actualizado TIMESTAMP
        )
        """
        client.query(sql).result()
        print("OK: Tabla creada/verificada")
    except Exception as e:
        print("Error: " + str(e))

if __name__ == "__main__":
    crear_tabla()