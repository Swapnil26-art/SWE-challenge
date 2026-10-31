# ── Stage 1: Build React frontend ─────────────────────────────────────────────
FROM node:18-alpine AS frontend-build

WORKDIR /build/frontend

COPY frontend/react-app/package.json frontend/react-app/package-lock.json ./
RUN npm ci

COPY frontend/react-app/ ./
RUN npm run build

# ── Stage 2: Python backend (serves React + API) ───────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy Flask app
COPY backend/app.py ./app.py

# Copy built React dist
COPY --from=frontend-build /build/frontend/dist ./frontend/dist

# Tell Flask where the static files are (absolute path inside container)
ENV STATIC_FOLDER=/app/frontend/dist
ENV PORT=5000

EXPOSE 5000

CMD ["python", "app.py"]
