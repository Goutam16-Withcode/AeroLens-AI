---
title: SatQuery AI — Multimodal Remote Sensing Agent
emoji: 🛰️
colorFrom: blue
colorTo: indigo
sdk: streamlit
app_file: src/satquery/ui/app.py
pinned: false
---

# 🛰️ SatQuery AI — Multimodal Remote Sensing Agent

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Docker Ready](https://img.shields.io/badge/Docker-Containerized-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agentic%20Flow-1C3C3C?logo=langchain&logoColor=white)](https://github.com/langchain-ai/langgraph)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**SatQuery AI** is an advanced multimodal remote-sensing intelligence agent designed for satellite imagery reasoning, earth observation analysis, and meteorological inspection. It integrates **Moondream2 / Vision-LLMs**, **OpenCV**, **LangGraph dynamic routing**, and a dark aerospace-grade **Streamlit** dashboard.

---

## 🚀 Key Capabilities

1. **Visual Question Answering (VQA) & Scene Captioning**: Natural language querying for high-resolution optical and multispectral satellite scenes.
2. **Visual Grounding & Localization**: Identifies target features (aircraft, oil tanks, vessels, runways, water bodies) with pixel-exact bounding boxes and spatial quadrant mapping (NW, NE, SW, SE, Center).
3. **Bi-Temporal Change Detection**: Automated pixel difference computation (`cv2.absdiff`) combined with semantic VLM reasoning to detect and narrate surface alterations between $T_1$ (before) and $T_2$ (after).
4. **Optical–SAR Multi-Sensor Fusion**: Dual-pass synthesis uniting Sentinel-2 (optical color/texture) and Sentinel-1 (C-band radar backscatter for cloud penetration and roughness).
5. **Meteorological Thermal IR Analysis**: Calibration of INSAT-3D/3DS and GOES thermal infrared channels (TIR1 @ 10.83 µm, WV @ 6.9 µm) for cloud-top brightness temperature ($T_B$) profiling and cyclone tracking.
6. **Zero-API-Key Offline Engine**: Built-in standalone computer vision and spectral analysis with optional plug-and-play fallbacks for **Ollama**, **Groq**, **Gemini**, and **OpenAI**.

---

## 🦙 Ollama Setup & Local Model Guide

SatQuery AI can run 100% locally on your machine with zero cloud dependencies using **Ollama** and **Moondream2** (or Llama 3.2-Vision).

### 1. Install Ollama

- **Windows**: Download and run the installer from [ollama.com/download/windows](https://ollama.com/download/windows).
- **macOS**: Download from [ollama.com/download/mac](https://ollama.com/download/mac) or run `brew install ollama`.
- **Linux**: Run the official installation script:
  ```bash
  curl -fsSL https://ollama.com/install.sh | sh
  ```

### 2. Pull the Vision Model

Open your terminal or PowerShell and pull the lightweight, ultra-fast **Moondream2** vision model (~1.7 GB):

```bash
ollama run moondream
```

*(Optional)* For higher-parameter vision models (requires ~8GB+ VRAM):
```bash
ollama run llama3.2-vision
```

### 3. Verify Ollama is Active

Check that the Ollama server is responding at its default local port (`11434`):
```bash
curl http://localhost:11434/api/tags
```

### 4. Configure SatQuery AI for Ollama

In your project root, copy `.env.example` to `.env` (or update `.env`):
```ini
# Set provider to ollama
SATQUERY_PROVIDER=ollama

# Ollama Endpoint Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=moondream
```

---

## 💻 Local Quick Start (Python)

### 1. Clone the Repository

```bash
git clone https://github.com/Goutam16-Withcode/SatQuery-AI.git
cd SatQuery-AI
```

### 2. Create and Activate a Virtual Environment

**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**On Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Prepare Benchmark Samples (1-Click)

Download and generate the benchmark demo presets (VRSBench, RSVQA, CDVQA, BigEarthNet, INSAT-3DS):
```bash
python scripts/download_samples.py
```

### 5. Launch the Dashboard

```bash
streamlit run src/satquery/ui/app.py
```

Open your browser and navigate to **`http://localhost:8501`**.

---

## 🐳 Docker & Docker Compose Setup

SatQuery AI includes production-ready containerization for zero-dependency execution on any OS.

### 1. Run with Docker Compose (Recommended)

```bash
docker compose up -d
```

Access the UI at **`http://localhost:8501`**.

To stop the container:
```bash
docker compose down
```

### 2. Build & Run Manually with Docker CLI

```bash
# Build the Docker image
docker build -t satquery-ai:latest .

# Run the container
docker run -d -p 8501:8501 --name satquery-ai satquery-ai:latest
```

---

## ☁️ Cloud Deployment

### Option A: Streamlit Community Cloud (Free 1-Click)

1. Fork or push this repository to GitHub.
2. Go to **[share.streamlit.io](https://share.streamlit.io/)** and click **New App**.
3. Configure the deployment:
   - **Repository:** `your-username/SatQuery-AI`
   - **Branch:** `main`
   - **Main file path:** `src/satquery/ui/app.py`
4. Click **Deploy!**

### Option B: Hugging Face Spaces

1. Create a new Space at [huggingface.co/new-space](https://huggingface.co/new-space).
2. Choose **Streamlit** SDK.
3. Link your GitHub repository or push directly to the Hugging Face Space Git remote.

### Option C: Render / Railway / PaaS

The repository includes `render.yaml` and `Procfile` for instant container and web service deployment on Render or Railway.

---

## ⚙️ Environment Variables Reference

Create a `.env` file in the project root to customize engine behavior:

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `SATQUERY_PROVIDER` | `moondream` | Active AI vision engine (`moondream`, `ollama`, `gemini`, `openai`, `groq`) |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Local Ollama server endpoint |
| `OLLAMA_MODEL` | `moondream` | Ollama model identifier (`moondream`, `llama3.2-vision`) |
| `GROQ_API_KEY` | *(Optional)* | Groq Cloud API Key for Llama-3.2-Vision acceleration |
| `GEMINI_API_KEY` | *(Optional)* | Google Gemini API Key for Gemini Flash multimodal reasoning |
| `OPENAI_API_KEY` | *(Optional)* | OpenAI API Key for GPT-4o vision fallback |

---

## 🎯 Benchmark Demo Presets

The SatQuery AI UI includes 5 ready-to-test benchmark scenarios:

| Preset Scenario | Sensor / Domain | Sample Query |
| :--- | :--- | :--- |
| **🛩️ VRSBench Grounding** | Optical High-Res | *"Locate and highlight all parked airplanes on the apron."* |
| **🏞️ RSVQA Land Cover** | Sentinel-2 Optical | *"What types of land use and water features are visible in this scene?"* |
| **🔄 CDVQA Change Detection** | Bi-Temporal ($T_1 \rightarrow T_2$) | *"What major construction and land-cover changes occurred between T1 and T2?"* |
| **📡 BigEarthNet SAR Fusion** | Sentinel-1 SAR + Sentinel-2 | *"Use both optical and SAR imagery to delineate the water boundary beneath cloud cover."* |
| **🌀 INSAT-3DS Meteorology** | Geostationary TIR & WV | *"Analyze brightness temperature and detect deep convective clouds over the cyclone."* |

---

## 🧪 Running Tests

SatQuery AI includes a test suite covering agent graphs, computer vision tools, input validation, and edge cases:

```bash
pytest
```

---

## 📁 Project Structure

```
SatQuery-AI/
├── .streamlit/
│   └── config.toml             # Dark aerospace theme & server configs
├── data/
│   └── samples/                # Demo satellite presets (VRSBench, RSVQA, CDVQA, etc.)
├── scripts/
│   ├── download_samples.py     # Automated sample dataset downloader
│   └── test_engine_format.py   # VLM format validator
├── src/
│   └── satquery/
│       ├── agent/              # LangGraph state machine & router controller
│       ├── core/               # Configuration settings & environment loader
│       ├── models/             # Multimodal VLM engine & spectral analyzer
│       ├── tools/              # Visual grounding, change detection & SAR fusion
│       ├── ui/
│       │   └── app.py          # Main Streamlit web application
│       └── validator/          # Input schema & coordinate bounds validation
├── tests/                      # Pytest unit & integration test suite
├── Dockerfile                  # Production container definition
├── docker-compose.yml          # Container orchestration configuration
├── packages.txt                # Linux OS dependencies (libgl1, libglib2.0)
├── requirements.txt            # Python dependencies
└── render.yaml                 # PaaS blueprint configuration
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
