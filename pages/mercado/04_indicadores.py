"""
04_indicadores.py - Dashboard Indicadores INEGI.
"""

import os, sys
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)

import streamlit as st
import pandas as pd
from datetime import datetime
from config import COLORS

from mercado.inegi.loaders import (
    load_todos_indicadores,
    load_indicador,
    INDICADORES_CONFIG
)
from core.components.charts import linea_temporal, barras_horizontales
from core.components.kpi_cards import render_kpi_row, seccion_titulo

def main():
    render()

def render():
    st.markdown(
        "<h2 style='color:#1B3A5C;margin-bottom:4px;'>Indicadores INEGI</h2>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='color:#6B7280;'>Indicadores economicos y de actividad industrial</p>",
        unsafe_allow_html=True,
    )
    st.divider()

    try:
        df = load_todos_indicadores()
    except Exception as e:
        df = pd.DataFrame()

    if df.empty:
        st.info("No hay datos de indicadores INEGI disponibles.")
        st.markdown("""
        Para cargar los datos:
        1. python scripts/create_table_inegi.py
        2. python scripts/script_inegi.py
        """)
        st.stop()

    # Selector de indicador
    claves_disponibles = list(INDICADORES_CONFIG.items())
    opciones = ["[{}] {}".format(c, n) for c, n in claves_disponibles]
    opciones.insert(0, "Vista General")

    seleccion = st.selectbox("Seleccionar indicador", opciones, label_visibility="collapsed")

    # ---------------------------------------------------------------------------
    # Vista General - resumen con graficos
    # ---------------------------------------------------------------------------
    if seleccion == "Vista General":
        df = load_todos_indicadores()
        
        # KPIs generales
        ult_fecha = df["Fecha"].max() if not df.empty else None
        num_indicadores = df["Nombre"].nunique()
        
        render_kpi_row([
            {"label": "Indicadores", "value": num_indicadores, "icon": "📊"},
            {"label": "Periodos", "value": len(df), "icon": "📅"},
            {"label": "Ultima fecha", "value": ult_fecha[:7] if ult_fecha else "—", "icon": "🗓️"},
        ])
        
        seccion_titulo("Resumen de Indicadores", "Variacion vs primer periodo")
        
        # Calcular variacion
        resumen = df.groupby("Nombre").agg({
            "Valor": ["last", "first"],
            "Fecha": "max"
        }).reset_index()
        resumen.columns = ["Indicador", "Ultimo valor", "Primer valor", "Ultima fecha"]
        
        try:
            resumen["Var_Pct"] = ((resumen["Ultimo valor"] - resumen["Primer valor"]) / resumen["Primer valor"] * 100).round(1)
        except:
            resumen["Var_Pct"] = 0
        
        # Top 10 grafico de barras
        top_var = resumen.nlargest(10, "Var_Pct")
        
        if not top_var.empty:
            fig = barras_horizontales(
                top_var,
                y="Indicador",
                x="Var_Pct",
                titulo="Top 10 - Crecimiento (%)"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Peores 10
        bottom_var = resumen.nsmallest(10, "Var_Pct")
        
        if not bottom_var.empty:
            fig2 = barras_horizontales(
                bottom_var,
                y="Indicador",
                x="Var_Pct",
                titulo="Top 10 - Declive (%)"
            )
            st.plotly_chart(fig2, use_container_width=True)

    # ---------------------------------------------------------------------------
    # Vista individual de indicador
    # ---------------------------------------------------------------------------
    else:
        clave = seleccion.split("]")[0].replace("[", "")
        df = load_indicador(clave)
        
        if df.empty:
            st.warning("Sin datos para este indicador")
        else:
            ultimo = df.iloc[-1]
            anterior = df.iloc[-2] if len(df) > 1 else None
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Valor actual", "{:,.1f}".format(ultimo["Valor"]))
            with col2:
                if anterior is not None and anterior["Valor"] != 0:
                    var = ((ultimo["Valor"] - anterior["Valor"]) / anterior["Valor"] * 100)
                    st.metric("Vs mes anterior", "{:+.1f}%".format(var))
            with col3:
                st.metric("Periodos", "{}".format(len(df)))
            
            # Serie historica en grafico
            df_plot = df.sort_values("Fecha")
            
            seccion_titulo("Serie Historica", "Evolucion temporal")
            
            fig_linea = linea_temporal(
                df_plot,
                x="Fecha",
                y="Valor",
                titulo=INDICADORES_CONFIG.get(clave, clave),
                show_area=True
            )
            st.plotly_chart(fig_linea, use_container_width=True)

    st.divider()
    st.caption("Fuente: INEGI BIE | Actualizado: {}".format(datetime.now().strftime("%Y-%m-%d")))

if __name__ == "__main__":
    main()