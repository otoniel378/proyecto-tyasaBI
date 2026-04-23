"""
pages/aceros_largos/02_macroeconomia.py — Análisis Macroeconómico
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from aceros_largos.loaders import load_macro_data, get_last_update, get_data_sources

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
st.title("📊 Aceros Largos — Macroeconomía")
st.markdown("Indicadores macroeconómicos clave que impactan el sector siderúrgico")

# ---------------------------------------------------------------------------
# DATOS
# ---------------------------------------------------------------------------
with st.spinner("Cargando datos macroeconómicos..."):
    data = load_macro_data()

# ---------------------------------------------------------------------------
# INDICADORES PRINCIPALES
# ---------------------------------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    # TASA DE INTERÉS
    rate = data["interest_rate"]
    trend_color = "#C62828" if rate["trend_type"] == "down" else "#2E7D32"
    trend_icon = "📉" if rate["trend_type"] == "down" else "📈"
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, rgba(27, 58, 92, 0.1) 0%, rgba(75, 123, 167, 0.05) 100%); 
                border: 1px solid rgba(75, 123, 167, 0.2); border-radius: 12px; padding: 20px; margin-bottom: 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <div style="font-size: 12px; color: #666; margin-bottom: 5px;">{rate["label"]}</div>
                <div style="font-size: 32px; font-weight: bold; color: #1B3A5C; margin-bottom: 5px;">{rate["value"]}</div>
                <div style="font-size: 11px; color: {trend_color};">{trend_icon} {rate["trend"]}</div>
                <div style="font-size: 10px; color: #999; margin-top: 3px;">{rate["unit"]}</div>
            </div>
            <div style="font-size: 32px; opacity: 0.3;">🏦</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    # INFLACIÓN
    inflation = data["inflation"]
    trend_color = "#C62828" if inflation["trend_type"] == "up" else "#2E7D32"
    trend_icon = "📈" if inflation["trend_type"] == "up" else "📉"
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, rgba(27, 58, 92, 0.1) 0%, rgba(75, 123, 167, 0.05) 100%); 
                border: 1px solid rgba(75, 123, 167, 0.2); border-radius: 12px; padding: 20px; margin-bottom: 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <div style="font-size: 12px; color: #666; margin-bottom: 5px;">{inflation["label"]}</div>
                <div style="font-size: 32px; font-weight: bold; color: #1B3A5C; margin-bottom: 5px;">{inflation["value"]}</div>
                <div style="font-size: 11px; color: {trend_color};">{trend_icon} {inflation["trend"]}</div>
                <div style="font-size: 10px; color: #999; margin-top: 3px;">{inflation["unit"]}</div>
            </div>
            <div style="font-size: 32px; opacity: 0.3;">📈</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# TENDENCIA CONSTRUCCIÓN
# ---------------------------------------------------------------------------
st.subheader("🏗️ Tendencia del Sector Construcción")
st.markdown("Evolución de la actividad constructora (principal demandante de aceros largos)")

construction_data = data["construction_trend"]

fig = go.Figure()

# Separar datos históricos de proyección
historic_data = [item for item in construction_data if "Pron" not in item["mes"]]
forecast_data = [construction_data[-2], construction_data[-1]]  # Nov'25 + Pron'26

# Línea histórica
fig.add_trace(go.Scatter(
    x=[item["mes"] for item in historic_data],
    y=[item["val"] for item in historic_data],
    mode='lines+markers',
    line=dict(color='#C62828', width=3),
    marker=dict(size=8, color='#C62828'),
    name='Construcción Histórica',
    hovertemplate='<b>%{x}</b><br>Variación: %{y}%<extra></extra>'
))

# Línea proyección
fig.add_trace(go.Scatter(
    x=[item["mes"] for item in forecast_data],
    y=[item["val"] for item in forecast_data],
    mode='lines+markers',
    line=dict(color='#2E7D32', width=3, dash='dash'),
    marker=dict(size=8, color='#2E7D32'),
    name='Proyección 2026',
    hovertemplate='<b>%{x}</b><br>Proyección: %{y}%<extra></extra>'
))

# Línea cero
fig.add_hline(y=0, line_dash="dot", line_color="rgba(0,0,0,0.3)")

fig.update_layout(
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    font=dict(family="Arial", size=12),
    xaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.1)'),
    yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.1)', title="Variación % YoY"),
    height=400,
    margin=dict(l=20, r=20, t=20, b=20),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# SEÑALES DE MERCADO
# ---------------------------------------------------------------------------
st.subheader("🔍 Señales Clave del Mercado")
signals = data["market_signals"]

# Agrupar por impacto
alto_impacto = [s for s in signals if s["impacto"] == "Alto"]
medio_impacto = [s for s in signals if s["impacto"] == "Medio"]
oportunidades = [s for s in signals if s["impacto"] == "Oport."]

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("#### 🔴 Alto Impacto")
    for signal in alto_impacto:
        st.markdown(f"""
        <div style="background-color: rgba(198, 40, 40, 0.1); border-left: 4px solid #C62828; 
                    padding: 12px; margin-bottom: 8px; border-radius: 0 8px 8px 0;">
            <div style="font-size: 13px; font-weight: bold; color: #C62828; margin-bottom: 4px;">
                {signal["label"]}
            </div>
            <div style="font-size: 11px; color: #666;">{signal["val"]}</div>
        </div>
        """, unsafe_allow_html=True)

with col2:
    st.markdown("#### 🟡 Impacto Medio")
    for signal in medio_impacto:
        st.markdown(f"""
        <div style="background-color: rgba(255, 193, 7, 0.1); border-left: 4px solid #FFC107; 
                    padding: 12px; margin-bottom: 8px; border-radius: 0 8px 8px 0;">
            <div style="font-size: 13px; font-weight: bold; color: #F57C00; margin-bottom: 4px;">
                {signal["label"]}
            </div>
            <div style="font-size: 11px; color: #666;">{signal["val"]}</div>
        </div>
        """, unsafe_allow_html=True)

with col3:
    st.markdown("#### 🟢 Oportunidades")
    for signal in oportunidades:
        st.markdown(f"""
        <div style="background-color: rgba(46, 125, 50, 0.1); border-left: 4px solid #2E7D32; 
                    padding: 12px; margin-bottom: 8px; border-radius: 0 8px 8px 0;">
            <div style="font-size: 13px; font-weight: bold; color: #2E7D32; margin-bottom: 4px;">
                {signal["label"]}
            </div>
            <div style="font-size: 11px; color: #666;">{signal["val"]}</div>
        </div>
        """, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# ANÁLISIS CONTEXTUAL
# ---------------------------------------------------------------------------
st.subheader("📋 Análisis Contextual")

st.markdown("""
### 🎯 **Factores Clave 2026**

**🔴 Riesgos Principales:**
- **Crisis de construcción residencial** (-15.6% YoY) impacta directamente demanda de varilla y alambrón
- **Recorte inversión pública** (-9.7% interanual) reduce demanda de perfiles estructurales  
- **Aranceles anti-dumping** (25-50%) limitan exportaciones competitivas a mercados clave

**🟢 Factores Positivos:**
- **Nearshoring activo** genera oportunidades en infraestructura industrial
- **Inversión TYASA** ($450 MDD nuevo laminador) fortalece capacidad productiva
- **Tasa Banxico estable** (7.00%) puede estimular inversión privada gradualmente

**⚖️ Balances:**
- **Depreciación MXN** (+1.64% vs USD) mejora competitividad exportadora pero encarece importaciones
- **Estabilización inflacionaria** (-0.52pp) reduce presiones de costos de insumos
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
                     letter-spacing: 1px;">Datos Macroeconómicos · Banxico & INEGI</span>
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