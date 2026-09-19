# AeroLens AI — Production FastAPI Backend Dockerfile
FROM python:3.10-slim

# Prevent Python from writing .pyc files & enable unbuffered stdout
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PORT=8000 \
    PYTHONPATH=/app:/app/src

WORKDIR /app

# Install system dependencies for OpenCV, PIL, RasterIO, and geospatial processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy dependencies first for Docker caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code and benchmark samples
COPY . .

# Expose FastAPI backend port
EXPOSE 8000

# Healthcheck to verify FastAPI backend is responsive
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl --fail http://localhost:8000/api/status || exit 1

# Launch AeroLens AI FastAPI server
CMD ["python", "-m", "uvicorn", "src.satquery.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
