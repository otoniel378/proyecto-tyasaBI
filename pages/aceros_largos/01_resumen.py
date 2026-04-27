"""
pages/aceros_largos/01_resumen.py — Resumen Ejecutivo Aceros Largos
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from aceros_largos.loaders import load_executive_summary, load_ticker_data, get_last_update, get_data_sources

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
st.title("📏 Aceros Largos — Resumen Ejecutivo")

# ---------------------------------------------------------------------------
# TICKER SUPERIOR
# ---------------------------------------------------------------------------
ticker_data = load_ticker_data()

# Crear columns dinámicamente para el ticker
cols = st.columns(len(ticker_data))
for i, item in enumerate(ticker_data):
    with cols[i]:
        color_class = {
            "tertiary": "#C62828",
            "white": "#FFFFFF", 
            "secondary": "#4A7BA7"
        }.get(item["color"], "#FFFFFF")
        
        st.markdown(f"""
        <div style="text-align: center; padding: 8px; background-color: rgba(75, 123, 167, 0.1); border-radius: 8px;">
            <div style="font-size: 11px; color: #666; margin-bottom: 2px;">{item["label"]}</div>
            <div style="font-size: 13px; font-weight: bold; color: {color_class};">{item["value"]}</div>
        </div>
        """, unsafe_allow_html=True)

st.divider()

# ---------------------------------------------------------------------------
# DATOS PRINCIPALES
# ---------------------------------------------------------------------------
with st.spinner("Cargando datos del resumen ejecutivo..."):
    data = load_executive_summary()

# ---------------------------------------------------------------------------
# KPIs PRINCIPALES
# ---------------------------------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    # EBITDA
    ebitda = data["ebitda"]
    trend_color = "#C62828" if ebitda["trend_type"] == "down" else "#2E7D32"
    trend_icon = "📉" if ebitda["trend_type"] == "down" else "📈"
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, rgba(27, 58, 92, 0.1) 0%, rgba(75, 123, 167, 0.05) 100%); 
                border: 1px solid rgba(75, 123, 167, 0.2); border-radius: 12px; padding: 20px; margin-bottom: 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <div style="font-size: 12px; color: #666; margin-bottom: 5px;">{ebitda["label"]}</div>
                <div style="font-size: 32px; font-weight: bold; color: #1B3A5C; margin-bottom: 5px;">{ebitda["value"]}</div>
                <div style="font-size: 11px; color: {trend_color};">{trend_icon} {ebitda["trend"]}</div>
            </div>
            <div style="font-size: 32px; opacity: 0.3;">💰</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    # MARGEN OPERATIVO
    margin = data["margin"]
    trend_color = "#C62828" if margin["trend_type"] == "down" else "#2E7D32"
    trend_icon = "📉" if margin["trend_type"] == "down" else "📈"
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, rgba(27, 58, 92, 0.1) 0%, rgba(75, 123, 167, 0.05) 100%); 
                border: 1px solid rgba(75, 123, 167, 0.2); border-radius: 12px; padding: 20px; margin-bottom: 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <div style="font-size: 12px; color: #666; margin-bottom: 5px;">{margin["label"]}</div>
                <div style="font-size: 32px; font-weight: bold; color: #1B3A5C; margin-bottom: 5px;">{margin["value"]}</div>
                <div style="font-size: 11px; color: {trend_color};">{trend_icon} {margin["trend"]}</div>
                <div style="font-size: 10px; color: #999; margin-top: 3px;">{margin["unit"]}</div>
            </div>
            <div style="font-size: 32px; opacity: 0.3;">📊</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# GRÁFICOS PRINCIPALES
# ---------------------------------------------------------------------------
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📈 Tendencia de Ventas")
    sales_trend = data["sales_trend"]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[item["mes"] for item in sales_trend],
        y=[item["ventas"] for item in sales_trend],
        mode='lines+markers',
        line=dict(color='#4A7BA7', width=3),
        marker=dict(size=8, color='#4A7BA7'),
        name='Ventas (Índice)',
        hovertemplate='<b>%{x}</b><br>Ventas: %{y}<extra></extra>'
    ))
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Arial", size=12),
        xaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.1)'),
        yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.1)', title="Índice de Ventas"),
        height=300,
        margin=dict(l=20, r=20, t=20, b=20)
    )
    
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("🎯 Metas de Producción")
    goals = data["production_goals"]
    
    fig = go.Figure()
    for i, goal in enumerate(goals):
        fig.add_trace(go.Bar(
            x=[goal["pct"]],
            y=[goal["label"]],
            orientation='h',
            marker_color=goal["color"],
            text=[f"{goal['pct']}%"],
            textposition='inside',
            textfont=dict(color='white', size=12, family='Arial Black'),
            name=goal["label"],
            hovertemplate=f'<b>{goal["label"]}</b><br>Progreso: {goal["pct"]}%<extra></extra>'
        ))
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Arial", size=12),
        xaxis=dict(range=[0, 100], title="% Completado", showgrid=True, gridcolor='rgba(0,0,0,0.1)'),
        yaxis=dict(showgrid=False),
        height=300,
        margin=dict(l=20, r=20, t=20, b=20),
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# VENTAS REGIONALES
# ---------------------------------------------------------------------------
st.subheader("🌎 Distribución de Ventas Regionales")

regional_data = data["regional_sales"]
col1, col2, col3 = st.columns(3)

for i, region in enumerate(regional_data):
    with [col1, col2, col3][i]:
        color_map = {
            "green": "#2E7D32",
            "red": "#C62828", 
            "blue": "#1976D2"
        }
        color = color_map.get(region["color"], "#4A7BA7")
        
        st.markdown(f"""
        <div style="text-align: center; padding: 15px; background-color: rgba(75, 123, 167, 0.05); 
                    border: 1px solid rgba(75, 123, 167, 0.2); border-radius: 10px;">
            <div style="font-size: 14px; color: #666; margin-bottom: 8px;">{region["label"]}</div>
            <div style="font-size: 28px; font-weight: bold; color: {color};">{region["pct"]}%</div>
        </div>
        """, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# FOOTER
# ---------------------------------------------------------------------------
st.divider()

col1, col2 = st.columns([1, 1])
with col1:
    st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 8px;">
        <span style="display: inline-flex; width: 8px; height: 8px; background-color: #4A7BA7; 
                     border-radius: 50%; animation: pulse 2s infinite;"></span>
        <span style="font-size: 10px; color: #666; font-weight: bold; text-transform: uppercase; 
                     letter-spacing: 1px;">Sistemas Operativos · Live Feed Activo</span>
    </div>
    """, unsafe_allow_html=True)

with col2:
    sources = " · ".join(get_data_sources())
    st.markdown(f"""
    <div style="text-align: right; font-size: 10px; color: #999;">
        Última actualización: {get_last_update()}<br>
        {sources}
    </div>
    """, unsafe_allow_html=True)