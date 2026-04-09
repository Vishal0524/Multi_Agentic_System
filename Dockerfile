# ─────────────────────────────────────────────────────────────────────────────
# NEXUS Multi-Agent — Cloud Run Dockerfile
# Single container: Vite builds static assets → FastAPI serves everything
# Port: 8080 (Cloud Run default)
# ─────────────────────────────────────────────────────────────────────────────

# Stage 1: Build React frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package.json ./
RUN npm install
COPY frontend/ ./
# Set production API URL (FastAPI serves from same origin)
ENV VITE_API_BASE_URL=""
RUN npm run build

# Stage 2: Python backend + serve static
FROM python:3.11-slim AS final

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libffi-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ ./

# Copy built frontend into static/ folder (FastAPI will serve it)
COPY --from=frontend-builder /app/frontend/dist ./static/

# Create non-root user
RUN useradd -m -u 1000 nexus && chown -R nexus:nexus /app
USER nexus

# Cloud Run uses PORT env var — default 8080
ENV PORT=8080
ENV APP_MODE=demo

EXPOSE 8080

# Start FastAPI serving both API and static frontend
CMD uvicorn api.main:app \
    --host 0.0.0.0 \
    --port ${PORT} \
    --workers 1 \
    --timeout-keep-alive 300
