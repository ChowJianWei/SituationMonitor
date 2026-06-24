# Production image for the Actuarial Quant Engine (FastAPI).
# Build context = this directory (actuarial_quant_system/).
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install deps first for layer caching. numpy/scipy ship manylinux wheels,
# so no system build toolchain is required on slim.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code + SQL schema (frontend/, tests/, .venv are excluded via .dockerignore).
COPY src ./src
COPY db ./db

# Railway / Render / Fly inject $PORT; default to 8200 for local `docker run`.
ENV PORT=8200
EXPOSE 8200

# Bind to 0.0.0.0 and the platform-provided port. The 24/7 underwriting loop
# starts inside the app's lifespan, so this single process is the whole engine.
CMD ["sh", "-c", "uvicorn src.api_dashboard.main:app --host 0.0.0.0 --port ${PORT:-8200} --workers 1 --no-access-log"]
