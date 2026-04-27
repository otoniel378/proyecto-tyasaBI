"""
filters.py — Filtros globales reutilizables para el sidebar.
Cada funcion renderiza un control en el sidebar y devuelve el valor seleccionado.
Los filtros que dependen de catalogos importan del area activa (Aceros Planos Negros).
Cuando otras areas se integren, podran sobreescribir estos filtros con sus propios loaders.
"""

import streamlit as st
import pandas as pd
from datetime import date
from config import COLORS
from aceros_planos.negros.loaders import (
    get_catalogo_clientes,
    get_catalogo_productos,
    get_catalogo_procesos,
    get_rango_fechas,
)


def filtro_rango_fechas(key_prefix: str = "") -> tuple[date, date]:
    fecha_min, fecha_max = get_rango_fechas()

    if fecha_min is None or fecha_max is None:
        st.sidebar.warning("No se pudo determinar el rango de fechas.")
        today = date.today()
        return today.replace(year=today.year - 2), today

    fecha_inicio = st.sidebar.date_input(
        "Fecha inicio",
        value=fecha_min.date() if hasattr(fecha_min, "date") else fecha_min,
        min_value=fecha_min.date() if hasattr(fecha_min, "date") else fecha_min,
        max_value=fecha_max.date() if hasattr(fecha_max, "date") else fecha_max,
        key=f"{key_prefix}_fecha_inicio",
    )
    fecha_fin = st.sidebar.date_input(
        "Fecha fin",
        value=fecha_max.date() if hasattr(fecha_max, "date") else fecha_max,
        min_value=fecha_min.date() if hasattr(fecha_min, "date") else fecha_min,
        max_value=fecha_max.date() if hasattr(fecha_max, "date") else fecha_max,
        key=f"{key_prefix}_fecha_fin",
    )

    if fecha_inicio > fecha_fin:
        st.sidebar.error("La fecha inicio no puede ser posterior a la fecha fin.")

    return fecha_inicio, fecha_fin


def filtro_clientes(key_prefix: str = "", multiselect: bool = True) -> list[str] | str:
    opciones = get_catalogo_clientes()

    if not opciones:
        st.sidebar.info("Sin clientes disponibles.")
        return [] if multiselect else ""

    if multiselect:
        return st.sidebar.multiselect(
            "Clientes", options=opciones, default=[],
            placeholder="Todos los clientes", key=f"{key_prefix}_clientes",
        )
    else:
        return st.sidebar.selectbox("Cliente", options=opciones, key=f"{key_prefix}_cliente")


def filtro_productos(key_prefix: str = "", multiselect: bool = True) -> list[str] | str:
    opciones = get_catalogo_productos()

    if not opciones:
        st.sidebar.info("Sin productos disponibles.")
        return [] if multiselect else ""

    if multiselect:
        return st.sidebar.multiselect(
            "Productos", options=opciones, default=[],
            placeholder="Todos los productos", key=f"{key_prefix}_productos",
        )
    else:
        return st.sidebar.selectbox("Producto", options=opciones, key=f"{key_prefix}_producto")


def filtro_procesos(key_prefix: str = "") -> list[str]:
    opciones = get_catalogo_procesos()

    if not opciones:
        st.sidebar.info("Sin procesos disponibles.")
        return []

    return st.sidebar.multiselect(
        "Procesos", options=opciones, default=[],
        placeholder="Todos los procesos", key=f"{key_prefix}_procesos",
    )


def aplicar_filtro_fechas(
    df: pd.DataFrame,
    fecha_inicio: date,
    fecha_fin: date,
    col: str = "PERIODO",
) -> pd.DataFrame:
    if df.empty or col not in df.columns:
        return df

    df = df.copy()
    df[col] = pd.to_datetime(df[col], errors="coerce")
    mask = (df[col].dt.date >= fecha_inicio) & (df[col].dt.date <= fecha_fin)
    return df[mask].reset_index(drop=True)


def aplicar_filtro_lista(
    df: pd.DataFrame,
    seleccion: list[str],
    col: str,
) -> pd.DataFrame:
    if df.empty or col not in df.columns or not seleccion:
        return df
    return df[df[col].isin(seleccion)].reset_index(drop=True)


def sidebar_header(titulo: str, icono: str = "🔩") -> None:
    st.sidebar.markdown(
        f"""
        <div style='
            text-align:center;
            padding:8px 0 16px 0;
            border-bottom:2px solid {COLORS["primary"]};
            margin-bottom:12px;
        '>
            <div style='font-size:1.8rem;'>{icono}</div>
            <div style='
                color:{COLORS["primary"]};
                font-weight:700;
                font-size:0.9rem;
                text-transform:uppercase;
                letter-spacing:0.05em;
            '>{titulo}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
