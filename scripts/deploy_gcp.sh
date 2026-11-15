#!/bin/bash
# ==============================================================================
# Stubble2Power - Google Cloud Production Deployment Script
# Deploys FastAPI Backend & Streamlit Frontend to Google Cloud Run in asia-south1
# ==============================================================================

set -euo pipefail

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-brandpr-512618}"
REGION="${GCP_REGION:-asia-south1}"
REPO_NAME="stubble2power-repo"
BACKEND_SERVICE="stubble2power-backend"
FRONTEND_SERVICE="stubble2power-frontend"

echo "=================================================================="
echo " Starting Stubble2Power Deployment to Google Cloud Run"
echo " Project ID : ${PROJECT_ID}"
echo " Region     : ${REGION}"
echo "=================================================================="

# 1. Verify gcloud authentication
echo "[1/6] Verifying Google Cloud CLI authentication..."
ACTIVE_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" || true)
if [ -z "${ACTIVE_ACCOUNT}" ]; then
    echo "ERROR: No active gcloud account found. Please run 'gcloud auth login'."
    exit 1
fi
echo "Authenticated as: ${ACTIVE_ACCOUNT}"

# 2. Configure active project
echo "[2/6] Configuring active project to ${PROJECT_ID}..."
gcloud config set project "${PROJECT_ID}"
gcloud config set run/region "${REGION}"

# 3. Enable required Google Cloud APIs
echo "[3/6] Ensuring required Google Cloud APIs are enabled..."
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com \
    secretmanager.googleapis.com \
    --project="${PROJECT_ID}"

# 4. Ensure Artifact Registry repository exists
echo "[4/6] Checking Artifact Registry repository..."
if ! gcloud artifacts repositories describe "${REPO_NAME}" --location="${REGION}" --project="${PROJECT_ID}" >/dev/null 2>&1; then
    echo "Creating Artifact Registry repository '${REPO_NAME}' in ${REGION}..."
    gcloud artifacts repositories create "${REPO_NAME}" \
        --repository-format=docker \
        --location="${REGION}" \
        --description="Stubble2Power Container Repository" \
        --project="${PROJECT_ID}"
fi

IMAGE_TAG="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/app:latest"

# 5. Build and submit multi-stage container image
echo "[5/6] Building production container image via Cloud Build..."
gcloud builds submit --tag "${IMAGE_TAG}" --project="${PROJECT_ID}" .

# 6. Deploy Microservices to Cloud Run
echo "[6/6] Deploying Stubble2Power services to Cloud Run..."

# Generate high-entropy JWT secret if not provided
JWT_SECRET="${JWT_SECRET_KEY:-$(python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || openssl rand -hex 32)}"
NASA_KEY="${NASA_FIRMS_MAP_KEY:-}"

# Deploy FastAPI Backend
echo "Deploying ${BACKEND_SERVICE}..."
gcloud run deploy "${BACKEND_SERVICE}" \
    --image="${IMAGE_TAG}" \
    --region="${REGION}" \
    --project="${PROJECT_ID}" \
    --platform=managed \
    --allow-unauthenticated \
    --port=8000 \
    --command="uvicorn" \
    --args="backend.main:app,--host,0.0.0.0,--port,8000" \
    --set-env-vars="APP_ENV=production,API_HOST=0.0.0.0,API_PORT=8000,JWT_SECRET_KEY=${JWT_SECRET},NASA_FIRMS_MAP_KEY=${NASA_KEY}" \
    --cpu=1 \
    --memory=1Gi \
    --min-instances=0 \
    --max-instances=5

BACKEND_URL=$(gcloud run services describe "${BACKEND_SERVICE}" --region="${REGION}" --project="${PROJECT_ID}" --format="value(status.url)")
echo "FastAPI Backend deployed successfully at: ${BACKEND_URL}"

# Deploy Streamlit Frontend
echo "Deploying ${FRONTEND_SERVICE}..."
gcloud run deploy "${FRONTEND_SERVICE}" \
    --image="${IMAGE_TAG}" \
    --region="${REGION}" \
    --project="${PROJECT_ID}" \
    --platform=managed \
    --allow-unauthenticated \
    --port=8501 \
    --command="streamlit" \
    --args="run,app.py,--server.port,8501,--server.address,0.0.0.0,--server.enableCORS,false,--server.enableXsrfProtection,false" \
    --set-env-vars="APP_ENV=production,API_BASE_URL=${BACKEND_URL},JWT_SECRET_KEY=${JWT_SECRET},NASA_FIRMS_MAP_KEY=${NASA_KEY}" \
    --cpu=1 \
    --memory=1Gi \
    --min-instances=0 \
    --max-instances=5

FRONTEND_URL=$(gcloud run services describe "${FRONTEND_SERVICE}" --region="${REGION}" --project="${PROJECT_ID}" --format="value(status.url)")

echo "=================================================================="
echo " Deployment Complete!"
echo " Frontend Web Dashboard : ${FRONTEND_URL}"
echo " Backend API Endpoint   : ${BACKEND_URL}"
echo " API Documentation      : ${BACKEND_URL}/docs"
echo "=================================================================="
