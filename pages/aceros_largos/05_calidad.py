"""
pages/aceros_largos/05_calidad.py — Calidad y Certificaciones
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from aceros_largos.loaders import load_quality_data, get_last_update, get_data_sources

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
st.title("✅ Aceros Largos — Calidad y Certificaciones")
st.markdown("Monitoreo de estándares de calidad, pruebas de laboratorio y certificaciones vigentes")

# ---------------------------------------------------------------------------
# DATOS
# ---------------------------------------------------------------------------
with st.spinner("Cargando datos de calidad..."):
    data = load_quality_data()

# ---------------------------------------------------------------------------
# INDICADORES PRINCIPALES
# ---------------------------------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    # ÍNDICE DE CALIDAD
    quality = data["quality_index"]
    trend_color = "#2E7D32" if quality["trend_type"] == "up" else "#C62828"
    trend_icon = "📈" if quality["trend_type"] == "up" else "📉"
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, rgba(27, 58, 92, 0.1) 0%, rgba(75, 123, 167, 0.05) 100%); 
                border: 1px solid rgba(75, 123, 167, 0.2); border-radius: 12px; padding: 20px; margin-bottom: 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <div style="font-size: 12px; color: #666; margin-bottom: 5px;">{quality["label"]}</div>
                <div style="font-size: 32px; font-weight: bold; color: #1B3A5C; margin-bottom: 5px;">{quality["value"]}</div>
                <div style="font-size: 11px; color: {trend_color};">{trend_icon} {quality["trend"]}</div>
                <div style="font-size: 10px; color: #999; margin-top: 3px;">{quality["unit"]}</div>
            </div>
            <div style="font-size: 32px; opacity: 0.3;">🏆</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    # CERTIFICACIONES ACTIVAS
    certs = data["certs_count"]
    trend_color = "#2E7D32" if certs["trend_type"] == "up" else "#C62828"
    trend_icon = "📈" if certs["trend_type"] == "up" else "📉"
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, rgba(27, 58, 92, 0.1) 0%, rgba(75, 123, 167, 0.05) 100%); 
                border: 1px solid rgba(75, 123, 167, 0.2); border-radius: 12px; padding: 20px; margin-bottom: 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <div style="font-size: 12px; color: #666; margin-bottom: 5px;">{certs["label"]}</div>
                <div style="font-size: 32px; font-weight: bold; color: #1B3A5C; margin-bottom: 5px;">{certs["value"]}</div>
                <div style="font-size: 11px; color: {trend_color};">{trend_icon} {certs["trend"]}</div>
                <div style="font-size: 10px; color: #999; margin-top: 3px;">{certs["unit"]}</div>
            </div>
            <div style="font-size: 32px; opacity: 0.3;">📜</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# PRUEBAS DE LABORATORIO
# ---------------------------------------------------------------------------
st.subheader("🧪 Resultados de Pruebas de Laboratorio")

tests = data["tests"]

# Crear gráfico de barras para las pruebas
test_names = [test["test"] for test in tests]
test_results = [100 if test["ok"] else 0 for test in tests]
test_colors = ["#2E7D32" if test["ok"] else "#C62828" for test in tests]

fig = go.Figure()

for i, test in enumerate(tests):
    # Determinar el porcentaje basado en el resultado
    if "100%" in test["result"]:
        percentage = 100
    elif "99.7%" in test["result"]:
        percentage = 99.7
    else:
        percentage = 95  # Por defecto
    
    fig.add_trace(go.Bar(
        y=[test["test"]],
        x=[percentage],
        orientation='h',
        marker_color="#2E7D32" if test["ok"] else "#C62828",
        text=[test["result"]],
        textposition='inside',
        textfont=dict(color='white', size=11, family='Arial Black'),
        name=test["test"],
        hovertemplate=f'<b>{test["test"]}</b><br>Resultado: {test["result"]}<extra></extra>'
    ))

fig.update_layout(
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    font=dict(family="Arial", size=12),
    xaxis=dict(range=[0, 100], title="% Aprobación", showgrid=True, gridcolor='rgba(0,0,0,0.1)'),
    yaxis=dict(showgrid=False),
    height=300,
    margin=dict(l=20, r=20, t=20, b=40),
    showlegend=False
)

st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# CERTIFICACIONES VIGENTES
# ---------------------------------------------------------------------------
st.subheader("📋 Certificaciones y Normativas Vigentes")

certifications = data["certifications"]

# Dividir certificaciones en columnas
cols = st.columns(2)

for i, cert in enumerate(certifications):
    with cols[i % 2]:
        status_icon = "✅" if cert["active"] else "❌"
        status_color = "#2E7D32" if cert["active"] else "#C62828"
        bg_color = "rgba(46, 125, 50, 0.1)" if cert["active"] else "rgba(198, 40, 40, 0.1)"
        border_color = "#2E7D32" if cert["active"] else "#C62828"
        
        st.markdown(f"""
        <div style="background-color: {bg_color}; border-left: 4px solid {border_color}; 
                    padding: 12px; margin-bottom: 10px; border-radius: 0 8px 8px 0;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <div style="font-size: 14px; font-weight: bold; color: #1B3A5C; margin-bottom: 3px;">
                        {cert["name"]}
                    </div>
                    <div style="font-size: 11px; color: #666;">{cert["desc"]}</div>
                </div>
                <div style="font-size: 20px;">{status_icon}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# INDICADORES ADICIONALES DE CALIDAD
# ---------------------------------------------------------------------------
st.subheader("📊 Indicadores Adicionales de Calidad")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Tasa de Rechazo", "0.15%", "-0.05%", delta_color="inverse")

with col2:
    st.metric("Reclamos de Cliente", "2", "-3", delta_color="inverse")

with col3:
    st.metric("Tiempo de Respuesta Lab", "4.2 hrs", "-0.8 hrs", delta_color="inverse")

with col4:
    st.metric("Auditorías Aprobadas", "100%", "0%")

# ---------------------------------------------------------------------------
# GRÁFICO DE TENDENCIA DE CALIDAD
# ---------------------------------------------------------------------------
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📈 Tendencia Histórica de Calidad")
    
    # Datos simulados de tendencia
    months = ["Oct", "Nov", "Dic", "Ene", "Feb", "Mar"]
    quality_trend = [99.78, 99.82, 99.80, 99.83, 99.81, 99.85]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=months,
        y=quality_trend,
        mode='lines+markers',
        line=dict(color='#2E7D32', width=3),
        marker=dict(size=8, color='#2E7D32'),
        fill='tonexty',
        fillcolor='rgba(46, 125, 50, 0.1)',
        name='Índice de Calidad',
        hovertemplate='<b>%{x}</b><br>Calidad: %{y}%<extra></extra>'
    ))
    
    # Línea objetivo
    fig.add_hline(y=99.5, line_dash="dash", line_color="#4A7BA7", 
                  annotation_text="Objetivo: 99.5%")
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Arial", size=12),
        xaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.1)'),
        yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.1)', 
                  title="% Índice de Calidad", range=[99.5, 100]),
        height=300,
        margin=dict(l=20, r=20, t=20, b=20),
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("🎯 Objetivos de Calidad")
    
    objectives = [
        {"metric": "Índice de Calidad", "target": "≥99.5%", "current": "99.85%", "status": "✅"},
        {"metric": "Tasa de Rechazo", "target": "≤0.2%", "current": "0.15%", "status": "✅"},
        {"metric": "Reclamos", "target": "≤5/mes", "current": "2/mes", "status": "✅"},
        {"metric": "Certificaciones", "target": "100%", "current": "100%", "status": "✅"}
    ]
    
    for obj in objectives:
        st.markdown(f"""
        <div style="background-color: rgba(75, 123, 167, 0.05); border-radius: 8px; 
                    padding: 10px; margin-bottom: 8px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <div style="font-size: 12px; font-weight: bold; color: #1B3A5C;">{obj["metric"]}</div>
                    <div style="font-size: 10px; color: #666;">Meta: {obj["target"]} | Actual: {obj["current"]}</div>
                </div>
                <div style="font-size: 16px;">{obj["status"]}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# ANÁLISIS DE CUMPLIMIENTO NORMATIVO
# ---------------------------------------------------------------------------
st.subheader("⚖️ Cumplimiento Normativo")

st.markdown("""
### 🎯 **Estado de Certificaciones**

**🟢 Certificaciones Nacionales:**
- **ISO 9001:2015** - Gestión de Calidad (Vigente hasta 2027)
- **NMX-B-457-CANACERO** - Varilla Corrugada Nacional (Renovada 2024)
- **NTC-2017 Sísmica (CDMX)** - Resistencia Antisísmica (Cumplimiento total)

**🟢 Certificaciones Internacionales:**
- **ISO 14001:2015** - Gestión Ambiental (Auditoría anual exitosa)
- **ISO 45001:2018** - Seguridad Ocupacional (Sin no conformidades)
- **ASTM A615 Gr.60** - Exportación USA (Calificación permanente)

**📊 Resultados de Auditorías 2025:**
- Auditorías internas: **12/12 exitosas**
- Auditorías externas: **6/6 aprobadas sin observaciones**
- Tiempo promedio de respuesta a hallazgos: **3.2 días**
""")

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
                     letter-spacing: 1px;">Laboratorio Certificado · Ensayos en Tiempo Real</span>
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