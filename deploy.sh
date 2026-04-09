#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# NEXUS — Google Cloud Run Deployment Script
# Usage: bash deploy.sh
# ═══════════════════════════════════════════════════════════════════════════════

set -e  # Exit on any error

# ── Configuration ─────────────────────────────────────────────────────────────
PROJECT_ID="logistics-491913"
REGION="us-central1"
SERVICE_NAME="logistics-agent"           # Same service name = same URL
APP_NAME="nexus-agent"
REPO="logistics-repo"

IMAGE="us-central1-docker.pkg.dev/$PROJECT_ID/$REPO/$APP_NAME:latest"

# ── Colors ─────────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

echo -e "${CYAN}"
echo "  ███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗"
echo "  ████╗  ██║██╔════╝╚██╗██╔╝██║   ██║██╔════╝"
echo "  ██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████╗"
echo "  ██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║╚════██║"
echo "  ██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝███████║"
echo "  ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝"
echo -e "${NC}"
echo -e "${GREEN}🚀 NEXUS Multi-Agent Deployment → Cloud Run${NC}"
echo -e "   Project: ${YELLOW}$PROJECT_ID${NC}"
echo -e "   Image:   ${YELLOW}$IMAGE${NC}"
echo -e "   Service: ${YELLOW}$SERVICE_NAME${NC}"
echo ""

# ── Step 1: Build Docker image ─────────────────────────────────────────────────
echo -e "${CYAN}[1/5] Building Docker image...${NC}"
docker build --no-cache -t "$IMAGE" .
echo -e "${GREEN}✅ Build complete${NC}"

# ── Step 2: Authenticate Docker ────────────────────────────────────────────────
echo -e "${CYAN}[2/5] Authenticating with Artifact Registry...${NC}"
gcloud auth print-access-token | docker login -u oauth2accesstoken \
  --password-stdin https://us-central1-docker.pkg.dev
echo -e "${GREEN}✅ Authenticated${NC}"

# ── Step 3: Push image ─────────────────────────────────────────────────────────
echo -e "${CYAN}[3/5] Pushing image to Artifact Registry...${NC}"
docker push "$IMAGE"
docker builder prune -f 2>/dev/null || true
echo -e "${GREEN}✅ Image pushed${NC}"

# ── Step 4: Get image digest ────────────────────────────────────────────────────
echo -e "${CYAN}[4/5] Getting image digest...${NC}"
DIGEST=$(docker inspect "$IMAGE" --format='{{index .RepoDigests 0}}' 2>/dev/null || echo "$IMAGE")
echo -e "   Digest: ${YELLOW}$DIGEST${NC}"

# ── Step 5: Deploy to Cloud Run ────────────────────────────────────────────────
echo -e "${CYAN}[5/5] Deploying to Cloud Run...${NC}"

gcloud run deploy "$SERVICE_NAME" \
  --image="$DIGEST" \
  --platform=managed \
  --region="$REGION" \
  --allow-unauthenticated \
  --set-env-vars="\
APP_MODE=demo,\
APP_ENV=production,\
GEMINI_MODEL=gemini-2.0-flash,\
GOOGLE_API_KEY=${GOOGLE_API_KEY:-demo},\
COMPOSIO_API_KEY=${COMPOSIO_API_KEY:-demo},\
MAILGUN_API_KEY=${MAILGUN_API_KEY:-demo},\
MAILGUN_DOMAIN=${MAILGUN_DOMAIN:-sandbox.mailgun.org},\
MAILGUN_TEST_MODE=true,\
LINEAR_API_KEY=${LINEAR_API_KEY:-demo},\
DATABASE_URL=sqlite:///./nexus.db" \
  --memory=1Gi \
  --cpu=1 \
  --timeout=300 \
  --port=8080 \
  --min-instances=0 \
  --max-instances=3 \
  --concurrency=80

echo ""
echo -e "${GREEN}════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ NEXUS deployed successfully!${NC}"
echo ""

# Get the URL
URL=$(gcloud run services describe "$SERVICE_NAME" --platform=managed --region="$REGION" --format="value(status.url)" 2>/dev/null)
if [ -n "$URL" ]; then
  echo -e "   🌐 Live URL: ${CYAN}$URL${NC}"
  echo -e "   📖 API Docs: ${CYAN}$URL/api/docs${NC}"
  echo -e "   ❤️  Health:   ${CYAN}$URL/health${NC}"
fi
echo -e "${GREEN}════════════════════════════════════════════════${NC}"
