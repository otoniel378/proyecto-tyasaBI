from pathlib import Path

import pandas as pd

from aceros_largos.loaders import _build_market_data_from_steel
from aceros_largos.loaders_new_data import (
    _annual_pct_change_from_index,
    _calculate_delta,
    _choose_preferred_series,
)


def test_market_data_accepts_balanza_ton_contract():
    data = _build_market_data_from_steel(
        {
            "comercio_exterior": {
                "balanza_comercial_ton": -6_000_000,
            }
        }
    )

    assert "trade_balance" in data
    assert data["trade_balance"]["label"] == "Balanza Comercial Acero Largos"
    assert data["trade_balance"]["trend_type"] == "down"
    assert "K ton" in data["trade_balance"]["value"]


def test_market_data_accepts_legacy_balanza_contract():
    data = _build_market_data_from_steel(
        {
            "comercio_exterior": {
                "balanza_comercial": 125_000,
            }
        }
    )

    assert data["trade_balance"]["trend_type"] == "up"


def test_calculate_delta_uses_diff_for_index_or_rate_series():
    df = pd.DataFrame(
        {
            "fecha": pd.to_datetime(["2026-02-01", "2026-01-01"]),
            "valor": [3.93, 4.12],
        }
    )

    assert round(_calculate_delta(df, mode="diff"), 2) == -0.19


def test_annual_pct_change_converts_index_to_inflation_rate():
    fechas = pd.date_range("2025-03-01", periods=13, freq="MS")[::-1]
    valores = [104.0] + [100.0] * 12
    df = pd.DataFrame({"fecha": fechas, "valor": valores})

    assert round(_annual_pct_change_from_index(df), 2) == 4.0


def test_choose_preferred_series_avoids_mixing_descriptions():
    df = pd.DataFrame(
        {
            "fecha": pd.to_datetime(["2026-02-01", "2026-01-01", "2026-02-01"]),
            "valor": [10.0, 9.0, 200.0],
            "descripcion": [
                "Variación porcentual anual|23---Construcción",
                "Variación porcentual anual|23---Construcción",
                "Índice de volumen físico base 2018=100|31-33---Industrias manufactureras",
            ],
        }
    )

    chosen = _choose_preferred_series(df, preferred_patterns=[r"23---Construcción"])

    assert len(chosen) == 2
    assert chosen["descripcion"].str.contains("23---Construcción", regex=False).all()


def test_bigquery_loaders_do_not_use_invalid_qualify_alias_filter():
    source = Path("aceros_largos/loaders_new_data.py").read_text(encoding="utf-8")

    assert "QUALIFY segmento IS NOT NULL" not in source
    assert "QUALIFY serie IS NOT NULL" not in source


def test_market_costs_page_is_not_registered_until_real_sources_exist():
    source = Path("app.py").read_text(encoding="utf-8")

    assert "pages/aceros_largos/03_mercado.py" not in source
    assert "al_mercado" not in source


def test_resumen_does_not_simulate_internal_demand_series():
    source = Path("pages/aceros_largos/01_resumen.py").read_text(encoding="utf-8")

    # No mock demand series
    assert "demanda_ton': [94" not in source
    # No simulated internal demand
    assert "demanda_ton': [" not in source


def test_macro_alerts_skip_non_dict_indicator_payloads():
    source = Path("pages/aceros_largos/02_macroeconomia.py").read_text(encoding="utf-8")

    # Accept either variable name: 'data' (old) or 'info' (new rewrite)
    assert ("if not isinstance(data, dict):" in source or
            "if not isinstance(info, dict):" in source)


def test_comercio_exterior_does_not_invent_usd_from_tons():
    source = Path("pages/aceros_largos/05_comercio_exterior.py").read_text(encoding="utf-8")

    assert "volumen_mensual_ton'] * 800" not in source
    assert "load_comercio_mock_data" not in source
    assert "K ton" in source


def test_macroeconomia_does_not_render_tiie_without_reliable_source():
    source = Path("pages/aceros_largos/02_macroeconomia.py").read_text(encoding="utf-8")

    assert "TIIE" not in source
    assert "tiie" not in source.lower()


def test_usd_mxn_loader_filters_to_real_exchange_rate_range():
    source = Path("aceros_largos/loaders_new_data.py").read_text(encoding="utf-8")

    assert "SAFE_CAST(valor AS FLOAT64) BETWEEN 10 AND 30" in source
    assert "4613" not in source
