@echo off
REM ─────────────────────────────────────────────────────────────
REM TYASA BI — Actualización diaria de variables de mercado
REM Configura en Windows Task Scheduler para correr cada día
REM a las 7:00 AM (después de que abran los mercados asiáticos)
REM ─────────────────────────────────────────────────────────────

cd /d C:\Users\OTONIEL\Desktop\TYASA-BI\proyecto-tyasaBI

REM Crear carpeta de logs si no existe
if not exist logs mkdir logs

REM Ejecutar actualización con log
echo [%date% %time%] Iniciando actualizacion... >> logs\update_market.log
python -X utf8 scripts\update_market_data.py >> logs\update_market.log 2>&1
echo [%date% %time%] Actualizacion completada. >> logs\update_market.log
echo. >> logs\update_market.log
