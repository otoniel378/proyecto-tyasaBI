#!/bin/bash
# deploy.sh — Despliega la Cloud Function de INEGI y crea el Cloud Scheduler.
# Ejecutar UNA SOLA VEZ desde la raíz del proyecto:
#   bash cloud_functions/update_inegi/deploy.sh

set -e

PROJECT_ID="project-d0cf2519-d089-47d3-930"
REGION="us-central1"
FUNCTION_NAME="update-inegi-monthly"
INEGI_TOKEN="2840789b-d1ee-af89-6433-8d1f8a509bf9"

echo "=== 1. Desplegando Cloud Function ==="
gcloud functions deploy "$FUNCTION_NAME" \
    --gen2 \
    --runtime python311 \
    --region "$REGION" \
    --source cloud_functions/update_inegi \
    --entry-point update_inegi \
    --trigger-http \
    --no-allow-unauthenticated \
    --memory 512MB \
    --timeout 300s \
    --set-env-vars "PROJECT_ID=${PROJECT_ID},DATASET=tyasa_bi,INEGI_TOKEN=${INEGI_TOKEN}" \
    --project "$PROJECT_ID"

echo ""
echo "=== 2. Obteniendo URL de la función ==="
FUNCTION_URL=$(gcloud functions describe "$FUNCTION_NAME" \
    --gen2 --region "$REGION" \
    --format "value(serviceConfig.uri)" \
    --project "$PROJECT_ID")
echo "URL: $FUNCTION_URL"

echo ""
echo "=== 3. Obteniendo Service Account ==="
SA=$(gcloud iam service-accounts list \
    --project "$PROJECT_ID" \
    --format "value(email)" \
    --filter "displayName:Default compute service account OR email~compute@developer" \
    | head -1)
echo "Service Account: $SA"

echo ""
echo "=== 4. Creando Cloud Scheduler (día 1 de cada mes, 8:00 AM Ciudad de México = 14:00 UTC) ==="
gcloud scheduler jobs create http inegi-monthly-update \
    --location "$REGION" \
    --schedule "0 14 1 * *" \
    --time-zone "UTC" \
    --uri "$FUNCTION_URL" \
    --http-method POST \
    --oidc-service-account-email "$SA" \
    --project "$PROJECT_ID" \
    --description "Descarga mensual de 37 indicadores INEGI a gold_indicadores_inegi" \
    || echo "(Si el job ya existe, actualiza con: gcloud scheduler jobs update http inegi-monthly-update ...)"

echo ""
echo "=== LISTO ==="
echo "La función correrá automaticamente el dia 1 de cada mes a las 8:00 AM CDMX."
echo "Para probarla manualmente ahora:"
echo "  gcloud scheduler jobs run inegi-monthly-update --location $REGION"
