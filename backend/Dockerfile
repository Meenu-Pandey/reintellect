# ReIntellect Backend — Production Dockerfile
# python:3.11-slim keeps image lean while matching the required Python version

FROM python:3.11-slim

# Install system dependencies needed by OpenCV and curl (for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd --gid 1001 appgroup && \
    useradd --uid 1001 --gid appgroup --shell /bin/bash --create-home appuser

WORKDIR /app

# Install Python dependencies first (layer caching)
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e . 2>/dev/null || pip install --no-cache-dir \
    fastapi==0.111.* \
    "uvicorn[standard]==0.29.*" \
    "ultralytics==8.2.*" \
    aiosqlite==0.20.* \
    hypothesis==6.100.* \
    pytest==8.2.* \
    pytest-asyncio==0.23.* \
    pytest-cov==5.* \
    httpx==0.27.* \
    opencv-python-headless==4.9.* \
    "torch>=2.2,<3" \
    shapely==2.0.*\
    "lapx>=0.5.2"

# Copy application source
COPY . .

# Ensure data directory exists and set permissions
RUN mkdir -p /data && chown -R appuser:appgroup /app /data

# Switch to non-root user
USER appuser

# Database lives in /data (mounted volume in compose)
ENV DB_PATH=/data/reintellect.db
ENV VIDEO_SOURCE=demo
ENV LOG_LEVEL=INFO
ENV PYTHONPATH=/app

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
