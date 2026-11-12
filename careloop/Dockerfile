# -----------------------------------------------------------
# CareLoop — Multi-stage Dockerfile
# -----------------------------------------------------------

# Stage 1: Build frontend
FROM node:20-slim AS frontend-build
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ ./
RUN npx vite build

# Stage 2: Python backend + built frontend
FROM python:3.11-slim AS runtime
WORKDIR /app

# Copy backend and config
COPY backend/pyproject.toml ./
COPY backend/ ./
COPY config/ /config/
COPY config/ ./config/
RUN pip install --no-cache-dir .

# Copy built frontend into static/
COPY --from=frontend-build /build/dist ./static/

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
