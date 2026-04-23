"""
pages/aceros_largos/04_operaciones.py — Operaciones e Inventario
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from aceros_largos.loaders import load_operations_data, get_last_update, get_data_sources

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
st.title("⚙️ Aceros Largos — Operaciones e Inventario")
st.markdown("Monitoreo de producción, equipos y gestión de inventarios en tiempo real")

# ---------------------------------------------------------------------------
# DATOS
# ---------------------------------------------------------------------------
with st.spinner("Cargando datos operativos..."):
    data = load_operations_data()

# ---------------------------------------------------------------------------
# INDICADORES PRINCIPALES
# ---------------------------------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    # PRODUCCIÓN
    production = data["production"]
    trend_color = "#C62828" if production["trend_type"] == "down" else "#2E7D32"
    trend_icon = "📉" if production["trend_type"] == "down" else "📈"
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, rgba(27, 58, 92, 0.1) 0%, rgba(75, 123, 167, 0.05) 100%); 
                border: 1px solid rgba(75, 123, 167, 0.2); border-radius: 12px; padding: 20px; margin-bottom: 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <div style="font-size: 12px; color: #666; margin-bottom: 5px;">{production["label"]}</div>
                <div style="font-size: 32px; font-weight: bold; color: #1B3A5C; margin-bottom: 5px;">{production["value"]}</div>
                <div style="font-size: 11px; color: {trend_color};">{trend_icon} {production["trend"]}</div>
                <div style="font-size: 10px; color: #999; margin-top: 3px;">{production["unit"]}</div>
            </div>
            <div style="font-size: 32px; opacity: 0.3;">🏭</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    # STOCK CHATARRA
    stock = data["scrap_stock"]
    trend_color = "#C62828" if stock["trend_type"] == "up" else "#2E7D32"  # Up = malo (acumulación)
    trend_icon = "📈" if stock["trend_type"] == "up" else "📉"
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, rgba(27, 58, 92, 0.1) 0%, rgba(75, 123, 167, 0.05) 100%); 
                border: 1px solid rgba(75, 123, 167, 0.2); border-radius: 12px; padding: 20px; margin-bottom: 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <div style="font-size: 12px; color: #666; margin-bottom: 5px;">{stock["label"]}</div>
                <div style="font-size: 32px; font-weight: bold; color: #1B3A5C; margin-bottom: 5px;">{stock["value"]}</div>
                <div style="font-size: 11px; color: {trend_color};">{trend_icon} {stock["trend"]}</div>
                <div style="font-size: 10px; color: #999; margin-top: 3px;">{stock["unit"]}</div>
            </div>
            <div style="font-size: 32px; opacity: 0.3;">📦</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# ESTADO DE EQUIPOS
# ---------------------------------------------------------------------------
st.subheader("🔧 Estado de Equipos Principales")

equipment = data["equipment_status"]
cols = st.columns(2)

for i, eq in enumerate(equipment):
    with cols[i % 2]:
        # Mapeo de colores
        color_map = {
            "secondary": "#4A7BA7",
            "primary": "#1B3A5C", 
            "tertiary": "#C62828"
        }
        status_color = color_map.get(eq["color"], "#4A7BA7")
        
        # Iconos por estado
        icon_map = {
            "Operativo": "✅",
            "En instalación": "🔧",
            "Mantenimiento": "⚠️"
        }
        status_icon = icon_map.get(eq["status"], "ℹ️")
        
        st.markdown(f"""
        <div style="background-color: rgba(75, 123, 167, 0.05); border: 1px solid rgba(75, 123, 167, 0.2); 
                    border-radius: 10px; padding: 15px; margin-bottom: 10px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <div style="font-size: 14px; font-weight: bold; color: #1B3A5C; margin-bottom: 5px;">
                        {eq["name"]}
                    </div>
                    <div style="font-size: 12px; color: {status_color}; font-weight: bold;">
                        {status_icon} {eq["status"]}
                    </div>
                </div>
                <div style="font-size: 24px; opacity: 0.3;">⚙️</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# INVENTARIOS
# ---------------------------------------------------------------------------
st.subheader("📊 Niveles de Inventario por Producto")

inventory = data["inventory"]

# Gráfico de barras horizontal
fig = go.Figure()

for inv in inventory:
    fig.add_trace(go.Bar(
        y=[inv["name"]],
        x=[inv["pct"]],
        orientation='h',
        marker_color=inv["color"],
        text=[f"{inv['pct']}% ({inv['mt']:,} MT)"],
        textposition='inside',
        textfont=dict(color='white', size=12, family='Arial Black'),
        name=inv["name"],
        hovertemplate=f'<b>{inv["name"]}</b><br>Stock: {inv["mt"]:,} MT<br>Máximo: {inv["max"]:,} MT<br>Ocupación: {inv["pct"]}%<extra></extra>'
    ))

fig.update_layout(
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    font=dict(family="Arial", size=12),
    xaxis=dict(range=[0, 100], title="% Ocupación de Capacidad", showgrid=True, gridcolor='rgba(0,0,0,0.1)'),
    yaxis=dict(showgrid=False),
    height=250,
    margin=dict(l=20, r=20, t=20, b=40),
    showlegend=False
)

st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# TABLA DETALLADA DE INVENTARIOS
# ---------------------------------------------------------------------------
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📋 Detalle de Inventarios")
    
    # Crear tabla personalizada
    for inv in inventory:
        # Determinar estado según porcentaje
        if inv["pct"] >= 80:
            status_color = "#C62828"
            status_text = "Crítico"
            status_icon = "🔴"
        elif inv["pct"] >= 60:
            status_color = "#F57C00" 
            status_text = "Alto"
            status_icon = "🟡"
        else:
            status_color = "#2E7D32"
            status_text = "Normal"
            status_icon = "🟢"
        
        st.markdown(f"""
        <div style="display: flex; justify-content: space-between; align-items: center; 
                    padding: 12px; margin-bottom: 8px; background-color: rgba(75, 123, 167, 0.05); 
                    border-radius: 8px; border-left: 4px solid {status_color};">
            <div>
                <div style="font-size: 14px; font-weight: bold; color: #1B3A5C;">{inv["name"]}</div>
                <div style="font-size: 11px; color: #666;">Stock: {inv["mt"]:,} MT · Max: {inv["max"]:,} MT</div>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 16px; font-weight: bold; color: {status_color};">{inv["pct"]}%</div>
                <div style="font-size: 10px; color: {status_color};">{status_icon} {status_text}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

with col2:
    st.subheader("⚡ Alertas Operativas")
    
    # Generar alertas dinámicas
    alerts = []
    
    # Verificar inventarios críticos
    for inv in inventory:
        if inv["pct"] >= 80:
            alerts.append({
                "type": "crítica",
                "message": f"Inventario {inv['name']} en nivel crítico ({inv['pct']}%)",
                "color": "#C62828",
                "icon": "🚨"
            })
        elif inv["pct"] >= 70:
            alerts.append({
                "type": "advertencia",
                "message": f"Inventario {inv['name']} elevado ({inv['pct']}%)",
                "color": "#F57C00", 
                "icon": "⚠️"
            })
    
    # Alertas de equipos
    for eq in equipment:
        if eq["status"] == "Mantenimiento":
            alerts.append({
                "type": "info",
                "message": f"{eq['name']} en mantenimiento",
                "color": "#1976D2",
                "icon": "🔧"
            })
    
    # Mostrar alertas
    if alerts:
        for alert in alerts:
            st.markdown(f"""
            <div style="padding: 10px; margin-bottom: 8px; background-color: rgba(255, 255, 255, 0.8); 
                        border-left: 4px solid {alert["color"]}; border-radius: 0 8px 8px 0;">
                <div style="font-size: 11px; color: {alert["color"]}; font-weight: bold;">
                    {alert["icon"]} {alert["message"]}
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.success("✅ Sin alertas críticas")

# ---------------------------------------------------------------------------
# EFICIENCIA OPERATIVA
# ---------------------------------------------------------------------------
st.subheader("📈 Indicadores de Eficiencia")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("OEE (Overall Equipment Effectiveness)", "87.2%", "+2.3%")

with col2:
    st.metric("Tiempo de Ciclo Promedio", "12.4 min", "-0.8 min")

with col3:
    st.metric("Utilización de Capacidad", "78.5%", "-3.1%")

with col4:
    st.metric("Índice de Calidad", "99.85%", "+0.05%")

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
                     letter-spacing: 1px;">Sistemas SCADA · Datos en Tiempo Real</span>
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