#!/bin/bash
set -euo pipefail

# ╔══════════════════════════════════════════════════════════════════╗
# ║  GIGATON ENGINE — Push to GitHub + Deploy to GCP Cloud Run      ║
# ║  Run from: ~/Desktop/gigaton_engine                             ║
# ╚══════════════════════════════════════════════════════════════════╝

PROJECT_ID="${GCP_PROJECT_ID:-carmen-beach-properties}"
REGION="${GCP_REGION:-us-central1}"
REPO_NAME="gigaton-engine"
IMAGE_TAG="${IMAGE_TAG:-latest}"
GITHUB_REPO="${GITHUB_REPO:-todd-gig/gigaton-engine}"

echo ""
echo "════════════════════════════════════════════════════"
echo "  GIGATON ENGINE DEPLOYMENT"
echo "  Project: $PROJECT_ID | Region: $REGION"
echo "════════════════════════════════════════════════════"
echo ""

# ── Step 1: Run tests ────────────────────────────────────────────
echo "▸ Step 1: Running test suite..."
python3 -m pytest -p no:cacheprovider --tb=short -q
echo "  ✓ All tests passed"
echo ""

# ── Step 2: Git init + push ──────────────────────────────────────
echo "▸ Step 2: Git push to GitHub..."
if [ ! -d .git ]; then
    git init
    git remote add origin "git@github-todd:${GITHUB_REPO}.git" 2>/dev/null || \
    git remote set-url origin "git@github-todd:${GITHUB_REPO}.git"
fi
git add -A
git commit -m "Gigaton Engine v1.0.0 — unified sovereign intelligence

50 modules, 758 tests, L1→L4 pipeline + causal mapping + learning loop +
gap analysis + ROI engine + governance gates + silence recovery + segmentation
+ Apollo enrichment + NIX engine + 8-panel dashboard + FastAPI service.

Convergence of Gigaton Engine + Standalone Decision Engine + SIE." || echo "  (no new changes to commit)"
git branch -M master
git push -u origin master
echo "  ✓ Pushed to GitHub"
echo ""

# ── Step 3: Build container image ────────────────────────────────
echo "▸ Step 3: Building container image..."

# Configure docker for Artifact Registry
gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet

# Create Artifact Registry repo if it doesn't exist
gcloud artifacts repositories create "$REPO_NAME" \
    --repository-format=docker \
    --location="$REGION" \
    --project="$PROJECT_ID" \
    --description="Gigaton Engine container images" 2>/dev/null || true

IMAGE_URL="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/api:${IMAGE_TAG}"

# Build and push using Cloud Build (no local Docker needed)
gcloud builds submit \
    --tag "$IMAGE_URL" \
    --project "$PROJECT_ID" \
    --quiet
echo "  ✓ Image built: $IMAGE_URL"
echo ""

# ── Step 4: Deploy to Cloud Run ──────────────────────────────────
echo "▸ Step 4: Deploying to Cloud Run..."
gcloud run deploy gigaton-engine \
    --image "$IMAGE_URL" \
    --platform managed \
    --region "$REGION" \
    --project "$PROJECT_ID" \
    --allow-unauthenticated \
    --port 8080 \
    --cpu 1 \
    --memory 512Mi \
    --min-instances 0 \
    --max-instances 5 \
    --set-env-vars "ENVIRONMENT=production,APOLLO_MOCK_MODE=true,SIE_SILENCE_RECOVERY_ENABLED=true,SIE_SILENCE_RECOVERY_DRY_RUN=true,SIE_MAX_DAILY_ACTIONS=50" \
    --quiet
echo "  ✓ Deployed to Cloud Run"
echo ""

# ── Step 5: Get URL and verify ───────────────────────────────────
echo "▸ Step 5: Verifying deployment..."
SERVICE_URL=$(gcloud run services describe gigaton-engine \
    --platform managed \
    --region "$REGION" \
    --project "$PROJECT_ID" \
    --format "value(status.url)")

echo ""
echo "════════════════════════════════════════════════════"
echo "  DEPLOYMENT COMPLETE"
echo "════════════════════════════════════════════════════"
echo ""
echo "  API URL:     $SERVICE_URL"
echo "  Health:      $SERVICE_URL/api/v1/health"
echo "  Docs:        $SERVICE_URL/docs"
echo "  Status:      $SERVICE_URL/api/v1/status"
echo ""
echo "  Quick test:"
echo "    curl $SERVICE_URL/api/v1/health"
echo ""

# Health check
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$SERVICE_URL/api/v1/health" 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    echo "  ✓ Health check PASSED (HTTP 200)"
else
    echo "  ⚠ Health check returned HTTP $HTTP_CODE — service may still be starting"
fi
echo ""
