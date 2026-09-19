# 🛰️ AeroLens AI — Production Deployment Guide
### Autonomous Orbital Earth Observation Cockpit (Next.js 15 + FastAPI)

This guide provides end-to-end, production-grade instructions for deploying both the **AeroLens AI Ground Station Frontend** (Next.js 15 Turbopack Cockpit) and the **AeroLens AI API Backend** (FastAPI Multimodal Vision-Language Core).

---

## 1. 🏗️ System Architecture Overview

AeroLens AI operates as a decoupled, dual-tier high-performance architecture:

```
                                  [ INTERNET / CLIENTS ]
                                            │
                                            ▼ HTTPS (443)
                             ┌─────────────────────────────┐
                             │     NGINX REVERSE PROXY     │
                             │  (SSL, Gzip, Rate Limiting) │
                             └──────────────┬──────────────┘
                                            │
                    ┌───────────────────────┴───────────────────────┐
                    ▼ Proxy Pass (3000)                             ▼ Proxy Pass (8000)
    ┌───────────────────────────────┐               ┌───────────────────────────────┐
    │     AEROLENS AI FRONTEND      │               │      AEROLENS AI BACKEND      │
    │   Next.js 15 + React 19 UI    │  HTTP / REST  │   FastAPI (Python 3.10+)      │
    │   Tactical Orbital Cockpit    │──────────────>│   Uvicorn ASGI Engine         │
    │   • 4-Slot Evidence Matrix    │  Swath Uplink │   • 5-Tool VLM Agent Core     │
    │   • Band Math & Caliper HUD   │               │   • Cloud VLM / Qwen3-VL      │
    │   • WGS-84 Orbit Tracker      │               │   • Spectral Math Engine      │
    └───────────────────────────────┘               └───────────────┬───────────────┘
                                                                    │
                                                    ┌───────────────┴───────────────┐
                                                    ▼ External API                  ▼ Local Weights
                                         ┌────────────────────┐          ┌────────────────────┐
                                         │ OpenRouter VLM API │          │ PyTorch / CUDA Core│
                                         │ (High Throughput)  │          │ (LoRA BigEarthNet) │
                                         └────────────────────┘          └────────────────────┘
```

---

## 2. 📋 Minimum & Recommended Specifications

| Component | Minimum Specification | Recommended Production Spec |
| :--- | :--- | :--- |
| **Operating System** | Ubuntu 22.04 LTS / Debian 12 / Windows Server 2022 | Ubuntu 24.04 LTS Linux |
| **CPU Architecture** | 2 vCPUs (x86_64) | 4–8 vCPUs |
| **System Memory (RAM)** | 4 GB RAM (with Cloud VLM) | 16 GB+ RAM (64 GB if hosting local Qwen3-VL) |
| **GPU Acceleration** | Not required (Cloud VLM mode enabled) | NVIDIA RTX 4090 / A10G / T4 (if local inference) |
| **Disk Storage** | 10 GB SSD | 50 GB NVMe SSD |
| **Network** | 100 Mbps egress/ingress | 1 Gbps egress (for high-res GeoTIFF downlinks) |

---

## 3. 🔐 Environment Configuration Matrix

### Backend Environment Variables (`.env` in repository root)
Create a `.env` file in the project root:

```ini
# ============================================================
# AEROLENS AI BACKEND CONFIGURATION
# ============================================================

# OpenRouter API Key for Cloud VLM reasoning & bounding box reticles
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Primary Vision-Language Model
OPENROUTER_MODEL=inclusionai/ling-3.0-flash-vl:free

# Force CPU mode (set to 1 to bypass CUDA if running on non-GPU server)
SATQUERY_FORCE_CPU=0

# Server Binding
HOST=0.0.0.0
PORT=8000

# CORS Whitelist (comma-separated allowed origins)
CORS_ORIGINS=http://localhost:3000,https://aerolens.yourdomain.com
```

### Frontend Environment Variables (`frontend/.env.production`)
Create a `.env.production` file in the `frontend/` directory:

```ini
# ============================================================
# AEROLENS AI FRONTEND CONFIGURATION
# ============================================================

# Public FastAPI Endpoint accessible by client browsers
NEXT_PUBLIC_API_URL=https://api.aerolens.yourdomain.com

# Production Environment
NODE_ENV=production
NEXT_TELEMETRY_DISABLED=1
```

---

## 4. 🐳 Deployment Method 1: Docker Compose (Recommended)

Docker Compose provides a single-command deployment with automated networking, volume mounting, and health check monitoring.

### Step 1: Clone Repository
```bash
git clone https://github.com/Goutam16-Withcode/SatQuery-AI.git aerolens-ai
cd aerolens-ai
```

### Step 2: Configure Environment
```bash
cp .env.example .env
nano .env
# Enter your OPENROUTER_API_KEY
```

### Step 3: Launch Containers
```bash
docker compose up -d --build
```

### Step 4: Verify Service Health
```bash
# Check running containers
docker compose ps

# View live aggregate logs
docker compose logs -f

# Verify backend health endpoint
curl -f http://localhost:8000/api/status
```

Access the application:
- **Cockpit Frontend**: `http://localhost:3000`
- **FastAPI Core**: `http://localhost:8000`
- **Interactive Swagger Docs**: `http://localhost:8000/docs`

---

## 5. 🐧 Deployment Method 2: Bare-Metal / Linux VM (Systemd + PM2)

For deployment on Amazon EC2, Google Compute Engine, DigitalOcean Droplet, or on-premises servers.

### 5.1 System Prerequisites
```bash
# Update package repositories
sudo apt-get update && sudo apt-get upgrade -y

# Install Python 3.10+, pip, venv, and imaging libraries
sudo apt-get install -y python3 python3-pip python3-venv \
    build-essential curl git libgl1 libglib2.0-0 libgomp1

# Install Node.js 20 LTS
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install PM2 Process Manager globally
sudo npm install -g pm2
```

---

### 5.2 Deploy the FastAPI Backend
```bash
# Navigate to project directory
cd /opt/aerolens-ai

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

#### Configure Backend Systemd Service
Create `/etc/systemd/system/aerolens-backend.service`:
```ini
[Unit]
Description=AeroLens AI FastAPI Backend Service
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/aerolens-ai
EnvironmentFile=/opt/aerolens-ai/.env
ExecStart=/opt/aerolens-ai/venv/bin/python -m uvicorn src.satquery.api.server:app --host 127.0.0.1 --port 8000 --workers 4
Restart=always
RestartSec=5
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
```

Enable and start the backend service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable aerolens-backend
sudo systemctl start aerolens-backend
sudo systemctl status aerolens-backend
```

---

### 5.3 Deploy the Next.js Frontend
```bash
cd /opt/aerolens-ai/frontend

# Install dependencies
npm ci

# Configure production environment
cat <<EOF > .env.production
NEXT_PUBLIC_API_URL=https://api.aerolens.yourdomain.com
NODE_ENV=production
NEXT_TELEMETRY_DISABLED=1
EOF

# Build Next.js production bundle
npm run build

# Start frontend via PM2
pm2 start npm --name "aerolens-frontend" -- start -- -p 3000

# Save PM2 state to resurrect on system reboot
pm2 save
pm2 startup
```

---

## 6. 🌐 Deployment Method 3: Cloud PaaS (Vercel + Render / Fly.io)

For teams seeking serverless frontend hosting with managed backend containers.

### Frontend Deployment on Vercel
1. Connect your GitHub repository to [Vercel](https://vercel.com/).
2. Set **Root Directory** to `frontend`.
3. Set **Framework Preset** to `Next.js`.
4. Configure **Environment Variables**:
   - `NEXT_PUBLIC_API_URL` = `https://your-backend-app.onrender.com`
5. Click **Deploy**. Vercel will automatically build and distribute the cockpit on their global Edge CDN.

### Backend Deployment on Render / Railway / Fly.io
1. Create a new **Web Service** pointing to the repository.
2. Select **Docker** environment (uses root `Dockerfile`).
3. Set **Environment Variables**:
   - `OPENROUTER_API_KEY` = your API key
   - `SATQUERY_FORCE_CPU` = `1` (if utilizing free/standard CPU instances)
   - `PORT` = `8000`
4. Set **Health Check Path** to `/api/status`.
5. Deploy and copy the public HTTPS URL into the frontend's `NEXT_PUBLIC_API_URL`.

---

## 7. 🛡️ Production Nginx Reverse Proxy with SSL

Install Nginx and configure HTTPS termination with Let's Encrypt Certbot:

```bash
sudo apt-get install -y nginx certbot python3-certbot-nginx
```

Create `/etc/nginx/sites-available/aerolens`:

```nginx
# Rate Limiting Zones
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=15r/s;

server {
    listen 80;
    server_name aerolens.yourdomain.com api.aerolens.yourdomain.com;
    return 301 https://$host$request_uri;
}

# 1. Frontend Cockpit
server {
    listen 443 ssl http2;
    server_name aerolens.yourdomain.com;

    # SSL Certificates (managed via Certbot)
    ssl_certificate /etc/letsencrypt/live/aerolens.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/aerolens.yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml image/svg+xml;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}

# 2. FastAPI Backend API
server {
    listen 443 ssl http2;
    server_name api.aerolens.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/aerolens.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/aerolens.yourdomain.com/privkey.pem;

    # Satellite Swath Upload Ceiling (permits up to 50MB GeoTIFF uploads)
    client_max_body_size 50M;

    location / {
        limit_req zone=api_limit burst=25 nodelay;

        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Extended timeouts for deep VLM reasoning on large swaths
        proxy_connect_timeout 90s;
        proxy_send_timeout 90s;
        proxy_read_timeout 90s;
    }
}
```

Enable the configuration and obtain SSL certificate:
```bash
sudo ln -s /etc/nginx/sites-available/aerolens /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Generate SSL certificates
sudo certbot --nginx -d aerolens.yourdomain.com -d api.aerolens.yourdomain.com
```

---

## 8. 🔄 CI/CD Automation (GitHub Actions)

Create `.github/workflows/deploy.yml` for automated testing, container builds, and deployment on every push to `main`:

```yaml
name: AeroLens AI CI/CD Pipeline

on:
  push:
    branches: [ "main" ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.10
        uses: actions/setup-python@v5
        with:
          python-version: "3.10"

      - name: Install Backend Dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest

      - name: Run Backend Pytest Suite
        run: |
          pytest tests/ -v

      - name: Set up Node.js 20
        uses: actions/setup-node@v4
        with:
          node-version: "20"

      - name: Verify Frontend Build
        working-directory: ./frontend
        run: |
          npm ci
          npx tsc --noEmit
          npm run build

  docker-build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: actions/setup-buildx-action@v3

      - name: Build Backend Docker Image
        uses: docker/build-push-action@v5
        with:
          context: .
          file: ./Dockerfile
          push: false
          tags: aerolens-backend:latest

      - name: Build Frontend Docker Image
        uses: docker/build-push-action@v5
        with:
          context: ./frontend
          file: ./frontend/Dockerfile
          push: false
          tags: aerolens-frontend:latest
```

---

## 9. 🩺 Health Monitoring & Telemetry Endpoints

Verify production system health with these telemetry endpoints:

```bash
# 1. System Status & Adaptation Lock
curl -s https://api.aerolens.yourdomain.com/api/status | jq .

# Expected Output:
# {
#   "status": "online",
#   "downlink_freq": "8.2 GHz (X-BAND)",
#   "orbit": "LEO 540KM · SSO (98.2°)",
#   "model_id": "Qwen/Qwen3-VL-4B-Instruct",
#   "model_ready": true,
#   "device": "CUDA GPU",
#   "adaptation": "Autonomous VLM Engine · Zero-Latency Neural Core",
#   "timestamp": "2026-09-19 17:30:00 UTC"
# }

# 2. Benchmark Missions Telemetry
curl -s https://api.aerolens.yourdomain.com/api/examples | jq .
```

---

## 10. 🔧 Operational Troubleshooting Runbook

### Issue: `net::ERR_CONNECTION_REFUSED` on `:8000`
- **Cause**: Backend service not running or bound strictly to `127.0.0.1` inside Docker.
- **Fix**: Verify backend is bound to `0.0.0.0:8000`. Check service status: `sudo systemctl status aerolens-backend` or `docker compose ps`.

### Issue: CORS error in browser console
- **Cause**: The browser domain is not listed in `CORS_ORIGINS`.
- **Fix**: Add your domain to `CORS_ORIGINS` in `.env` and reload the backend.

### Issue: Large Satellite Image Upload Fails (HTTP 413 Payload Too Large)
- **Cause**: Default Nginx or reverse proxy limit is 1MB–2MB.
- **Fix**: Set `client_max_body_size 50M;` inside your Nginx server block.

### Issue: Out-of-Memory (OOM) on local GPU
- **Cause**: PyTorch attempting to allocate full model weights on a GPU with < 8GB VRAM.
- **Fix**: Set `SATQUERY_FORCE_CPU=1` in `.env` to enable the zero-crash CPU mode, or configure `OPENROUTER_API_KEY` to utilize cloud VLM acceleration.

---

**AeroLens AI** is configured for mission-critical reliability, sub-second telemetry downlink, and publication-grade orbital intelligence.
