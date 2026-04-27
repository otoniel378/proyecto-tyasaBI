# TYASA BI — Contexto para Claude Code

## Proyecto
Plataforma de Inteligencia Comercial multi-área para TYASA.
Stack: Python · Streamlit · BigQuery · Plotly · XGBoost · Statsmodels · Gemini API
GCP Project: project-d0cf2519-d089-47d3-930
Dataset BQ: tyasa_bi

## Estructura del repo
app.py                            ← Hub principal, navegación 4 áreas (Mercado Global · CASTRIP · Aceros Largos · SBQ)
config.py                         ← Colores dark theme, parámetros, rutas, áreas
assets/style.css                  ← CSS tema ejecutivo oscuro (bg #0F1923, surface #1A2535, accent #E05C2D)
core/
  db_connector.py                 ← Cliente BigQuery singleton
  validators.py                   ← Validaciones de DataFrames
  components/
    charts.py                     ← 12 tipos de gráficos Plotly (paleta dark TYASA)
    filters.py                    ← Filtros sidebar
    kpi_cards.py                  ← KPI: card / compact / sparkline / gauge / badge
    tables.py                     ← Tablas exportables a Excel
    alertas_panel.py              ← render_anomalia_card / render_termometro_mes / render_semaforo_area
aceros_planos/
  negros/                         ← COMPLETADO (5 módulos)
    loaders.py                    ← 12 funciones con @st.cache_data(ttl=600)
    analytics/
      kpis.py                     ← KPIResumen dataclass
      segmentacion.py             ← ABC, Pareto, HHI, Gini
      series_tiempo.py            ← Variación MoM, volatilidad, heatmap
      forecasting.py              ← ETS | SARIMA | XGBoost | Naive | Auto
      mix_productos.py            ← Co-ocurrencia, cross-sell
  castrip/                        ← COMPLETADO (9 módulos, loaders AREA_FILTER=CASTRIP)
    loaders.py                    ← Misma estructura que negros/, AREA_FILTER="CASTRIP"
  galvanizados/                   ← EN DESARROLLO
  formados/                       ← EN DESARROLLO
aceros_largos/                    ← COMPLETADO (5 páginas, contenido sin cambios)
aceros_sbq/                       ← PRÓXIMO
analytics/                        ← Módulos analíticos transversales
  alertas.py                      ← detectar_clientes_en_fuga / enfriamiento / anomalias / proyeccion_mes
  clientes.py                     ← frecuencia_compra / proximo_pedido / estacionalidad / briefing_visita
  condicion_mercado.py            ← indice_condicion / ventanas_oportunidad / correlaciones_lag
mercado_noticias/                 ← COMPLETADO
  loaders.py                      ← Variables, quiebres, noticias desde BQ
  inegi_loader.py                 ← 10 indicadores INEGI con @st.cache_data(ttl=3600)
  analytics/
    detector.py                   ← Detección quiebres estructurales (Chow test)
    noticias.py                   ← Google News RSS + NewsAPI + GRUPOS_NACIONAL/INTERNACIONAL
    ai_analysis.py                ← Análisis IA con Gemini 2.0-flash + caché JSON
    mananera.py                   ← Análisis mañanera presidencial (yt-dlp + transcripción + Gemini)
pages/
  hub.py                          ← Landing page dark theme (4 área cards + KPIs de estado)
  aceros_sbq/coming_soon.py
  mercado/
    00_mercado_global.py          ← Vista integrada: Quiebres · Variables · INEGI · Siderúrgico · Mañanera
    01_monitor.py                 ← Monitor de quiebres + alertas IA
    02_variables.py               ← 31 series siderúrgicas históricas
    03_industria.py               ← Monitor siderúrgico + noticias nacionales/internacionales
  castrip/
    00_alertas.py                 ← Panel alertas: proyección mes, fuga, anomalías
    01_resumen.py                 ← Resumen ejecutivo
    02_segmentacion.py            ← Segmentación ABC, Pareto, HHI
    03_series_tiempo.py           ← Series temporales + YoY + heatmap
    04_forecasting.py             ← ETS/SARIMA/XGBoost auto forecast
    05_mix_productos.py           ← Mix, treemap, co-ocurrencia
    06_clientes.py                ← Briefing visita, frecuencia, estacionalidad, mix cliente
    07_condicion_mercado.py       ← Índice condición, ventanas, correlaciones lag
    08_mercado_contexto.py        ← Noticias + Mañanera + INEGI
  aceros_largos/01-05_*.py       ← 5 páginas (contenido sin cambios)
scripts/
  create_market_tables.py         ← Inicialización tablas BQ (one-time)
  update_market_data.py           ← Update diario desde yfinance
cloud_functions/
  update_market/main.py           ← Cloud Function HTTP (trigger 7 AM MX = 13 UTC)

## Convenciones
- Naming tablas BQ: bronze_ | silver_ | gold_ + descripción
- Columnas clave: PESO_TON, CLIENTE, PRODUCTO_LIMPIO, PERIODO, AREA, DIVISION
- AREA_FILTER por loader: "NEGROS" | "GALVANIZADOS" | "FORMADOS" | "CASTRIP"
- Tema dark: background=#0F1923 | surface=#1A2535 | surface2=#243044 | accent=#E05C2D | primary=#4A9FD4
- Todos los loaders usan @st.cache_data(ttl=600)
- BQ client usa @st.cache_resource (una sola conexión por sesión)
- Nuevas páginas CASTRIP importan loaders de aceros_planos/castrip/loaders.py y analytics de aceros_planos/negros/analytics/
- Caché IA en cache/ai_summaries/<hash>.json | cache/mananera/<fecha>.json (no repetir llamadas a Gemini)
- Componentes DOM-estable: usar st.empty() + HTML strings, no componentes Streamlit condicionales
- NO poner textos instruccionales/descriptivos en subtítulos, captions ni headers de la UI
- INEGI loader con @st.cache_data(ttl=3600): máximo 10 indicadores por request

## Estado actual
- Mercado Global:              ✅ COMPLETADO (vista integrada 5 tabs + 3 páginas legacy)
- CASTRIP:                     ✅ COMPLETADO (9 módulos 00-08)
- Aceros Planos Negros:        ✅ COMPLETADO (5 módulos, ~62 KB)
- Aceros Largos:               ✅ COMPLETADO (5 páginas, solo contenido)
- Aceros Planos Galvanizados:  🚧 EN DESARROLLO
- Aceros Planos Formados:      🚧 EN DESARROLLO
- Aceros SBQ:                  🔜 PRÓXIMO

## Tablas BigQuery activas
- silver_ventas_limpias         ← Datos completos de ventas (fuente principal)
- gold_demanda_cliente          ← Agrupado por cliente
- gold_demanda_producto         ← Agrupado por producto
- gold_demanda_mensual          ← Serie temporal mensual
- gold_cliente_producto         ← Matriz cliente × producto
- gold_demanda_proceso          ← Agrupado por proceso productivo
- gold_variables_mercado        ← 31 series siderúrgicas diarias (yfinance)
- gold_quiebres_detectados      ← Quiebres estructurales (Chow test)
- gold_noticias_vinculadas      ← Noticias enlazadas a variables

## Reglas
1. Nunca hardcodear credenciales — usar get_bq_client() y secrets.toml
2. Siempre usar table_ref() para referenciar tablas BQ
3. Nuevas páginas importan desde core/ y siguen estructura existente
4. Al agregar área nueva: actualizar config.py → AREAS y app.py → st.navigation()
5. Nuevos loaders van en aceros_planos/<subseccion>/loaders.py con AREA_FILTER propio
6. Cada página nueva tiene sidebar_header() + st.spinner() en carga de datos
7. Caché de análisis IA en JSON — nunca llamar Gemini si ya existe la respuesta

## Notas de sesiones
Las notas de cada sesión se guardan en:
C:\Users\OTONIEL\Desktop\obsidian\sesiones\
Plantilla: templates/sesion-claude.md
Última sesión: 2026-04-23 — Rediseño completo dark theme + CASTRIP + analytics

## Regla de documentación en Obsidian
Cuando el usuario pida "anota esto en Obsidian" o "actualiza Obsidian" al final de una tarea:
1. Crear o actualizar C:\Users\OTONIEL\Desktop\obsidian\sesiones\YYYY-MM-DD-<tema>.md
2. Actualizar la sección correspondiente en C:\Users\OTONIEL\Desktop\obsidian\proyectos\bi-principal.md
   - Módulos completados / en desarrollo
   - Tablas BQ nuevas
   - Decisiones arquitectónicas nuevas
   - Log de sesiones
3. Si hay una nueva tabla BQ, decisión de arquitectura o módulo nuevo → reflejar en este CLAUDE.md también
