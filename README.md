---
title: AeroLens AI — Autonomous Orbital Earth Observation Cockpit
emoji: 🛰️
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 3000
pinned: false
---

# 🛰️ AeroLens AI — Autonomous Orbital Earth Observation Cockpit

[![Next.js 15](https://img.shields.io/badge/Next.js-15%20Turbopack-black?logo=next.js&logoColor=white)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Docker Ready](https://img.shields.io/badge/Docker-Containerized-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**AeroLens AI** is an advanced aerospace ground station cockpit and autonomous multimodal remote sensing agentic platform. Built for mission-critical satellite earth observation, bi-temporal disaster monitoring, and multi-sensor intelligence, it unites state-of-the-art **Vision-Language Models (VLMs)**, **USGS & NASA scientific spectral band math**, and a high-performance **Next.js 15 + FastAPI** architecture.

---

## 🌟 Ground Station Cockpit Modules

```
 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │                                   AEROLENS AI COCKPIT                                  │
 ├───────────────────┬───────────────────┬────────────────────┬───────────────────────────┤
 │ [01] EVIDENCE     │ [02] BAND MATH    │ [03] COMPARISON    │ [04] 3X LOUPE & CLAHE     │
 │ 4-Slot Multi-     │ NDVI, NDWI, NDBI, │ Bi-temporal swipe, │ Multi-scale (2X/4X/8X),   │
 │ Spectral Decoder  │ CIR, NBR, SAVI    │ blink comparator,  │ high-pass edge filter &   │
 │ (Optical, Heatmap,│ with calibrated   │ & continuous cross-│ metric/imperial/nautical  │
 │ Reticle, CIR)     │ radiometric blend │ fade dissolve      │ distance measuring caliper│
 ├───────────────────┴───────────────────┴────────────────────┴───────────────────────────┤
 │ [05] HUD INSPECTOR                         │ [06] TARGET DETECTIONS                    │
 │ Live WGS-84 coordinates, SSO ground track  │ Precision multi-class object grounding    │
 │ orbit minimap & 12-bit RGB histogram       │ (airplanes, tanks, ships) with NMS reticle│
 └────────────────────────────────────────────┴───────────────────────────────────────────┘
```

### 1. `[01]` Multi-Spectral Evidence Matrix (4-Slot Decoder)
- **Slot 01 (Sensor Stream)**: Primary optical sensor swath (RGB / Panchromatic T1).
- **Slot 02 (Attention Saliency)**: Multi-scale spatial saliency & attention gradient heatmap generated via Sobel gradient magnitude and Turbo colormap fusion.
- **Slot 03 (Target Reticles)**: Precision tactical corner reticles with bounding boxes on detected objects or salient infrastructure.
- **Slot 04 (CIR Spectral Synthesis / After Pass)**: Peer-reviewed **NASA False-Color Infrared (CIR)** composite (velvety crimson vegetation canopy, deep navy water, and silver-cyan urban structures) or temporal $T_2$ frame.

### 2. `[02]` Scientific Spectral Indices // Band Math Deck
- **NDVI** (*Normalized Difference Vegetation Index*): USGS calibrated biomass index isolating live canopy chlorophyll.
- **NDWI** (*Normalized Difference Water Index*): Hydrological shoreline and flood inundation boundary delineation.
- **NDBI** (*Normalized Difference Built-Up Index*): High-density concrete, asphalt, and impervious infrastructure mapping.
- **CIR** (*Color Infrared Composite*): Authentic NASA false-color NIR-R-G standard.
- **NBR** (*Normalized Burn Ratio*): Wildfire perimeter, ash burn scar, and scorch severity assessment.
- **SAVI** (*Soil-Adjusted Vegetation Index*): Huete $L=0.5$ background decoupling for accurate arid land canopy quantification.
- **Dual-Engine Architecture**: Processes via FastAPI NumPy/SciPy matrix engine with zero-latency client-side HTML5 Canvas fallback.

### 3. `[03]` Bi-Temporal Comparison Slider & Blink Comparator
- **Interactive Split Slider**: Smooth drag comparison between baseline $T_1$ and post-event $T_2$.
- **Astronomical Blink Comparator**: Rapid toggling at 1 Hz, 2 Hz, or 4 Hz to detect subtle structural deviations.
- **Continuous Cross-Fade**: Variable alpha dissolution between observation passes.

### 4. `[04]` 3X Optical Loupe & Spatial Enhancer
- **Multi-Level Zoom**: 2X, 4X, and 8X optical magnification.
- **Contrast Limited Adaptive Histogram Equalization (CLAHE)**: Reveals shadow details and enhances dark terrain contrast.
- **High-Pass Edge Filter**: Isolates linear infrastructure (runways, roadways, canals, ship hulls).
- **Measurement Caliper**: Interactive pixel-to-ground distance calculator in Meters (**M**), Feet (**FT**), and Nautical Miles (**NM**).

### 5. `[05]` Geospatial Telemetry HUD & Orbit Radar
- **Live WGS-84 Coordinate Tracking**: Dynamically computes latitude/longitude and UTM grid coordinates as you inspect the swath.
- **Sun-Synchronous Orbit (SSO) Ground Track**: SVG orbital minimap displaying real-time ground station coverage and satellite track.
- **12-bit Radiometric RGB Histogram**: Live channel distribution and dynamic range readout.

### 6. `[06]` Multi-Class Target Detections & Reticles
- Identifies and grounds airplanes, bulk storage tanks, maritime vessels, and infrastructure.
- Non-Maximum Suppression (NMS) and geometric scoring to eliminate false positive clustering.
- Sub-metric bounding box coordinates with 1-click reticle export.

---

## 🎙️ Hands-Free Tactical Uplink Bar
- **Voice Uplink (Web Speech API)**: Click the microphone icon to query the cockpit hands-free.
- **Preset Mission Chips**: Quick-load scenarios including Wildfire Burn Assessment, Maritime Fleet Tracking, Dual-Sensor SAR Fusion, and Flooding Change Detection.

---

## 🚀 Quick Start Guide

### Prerequisites
- **Node.js**: v18.17+ or v20+
- **Python**: 3.10+
- **npm** or **pnpm**

---

### Step 1: Clone the Repository

```bash
git clone https://github.com/Goutam16-Withcode/SatQuery-AI.git
cd SatQuery-AI
```

---

### Step 2: Launch the Backend (FastAPI)

```powershell
# Windows PowerShell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Start the SatQuery AI API server
uvicorn src.satquery.api.server:app --host 0.0.0.0 --port 8000 --reload
```

```bash
# Linux / macOS
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start the SatQuery AI API server
uvicorn src.satquery.api.server:app --host 0.0.0.0 --port 8000 --reload
```

The FastAPI backend will be live at **`http://localhost:8000`** with interactive Swagger documentation at **`http://localhost:8000/docs`**.

---

### Step 3: Launch the Cockpit Frontend (Next.js)

In a new terminal window:

```bash
cd frontend
npm install
npm run dev
```

Open your browser and navigate to **`http://localhost:3000`**.

---

## 🐳 Docker & Container Orchestration

Run the complete SatQuery AI cockpit with a single command:

```bash
docker compose up -d --build
```

- **Next.js Cockpit**: `http://localhost:3000`
- **FastAPI Core**: `http://localhost:8000`

To shut down:
```bash
docker compose down
```

---

## 📡 API Reference

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/analyze` | `POST` | Primary VLM multimodal reasoning pipeline with 4-slot evidence output. |
| `/api/spectral-indices` | `POST` | Computes calibrated NDVI, NDWI, NDBI, CIR, NBR, or SAVI with statistics. |
| `/api/detect` | `POST` | Direct multi-class object grounding with NMS-suppressed target reticles. |
| `/api/examples` | `GET` | Returns pre-calibrated benchmark missions (Disaster, Fusion, Grounding). |
| `/api/status` | `GET` | Ground station telemetry, orbit pass status, and inference core state. |

---

## 📁 Repository Structure

```
SatQuery-AI/
├── app.py                      # Multi-tool Agent Controller & single-image evidence synthesizer
├── src/
│   └── satquery/
│       ├── api/
│       │   └── server.py       # FastAPI REST API & telemetry endpoints
│       ├── core/
│       │   ├── cloud_vlm.py    # Zero-latency VLM grounding parser & bounding box extractor
│       │   └── spectral_indices.py # Scientific NDVI/NDWI/NDBI/CIR/NBR/SAVI engine
│       ├── models/
│       │   └── engine.py       # Remote sensing computer vision & NMS target detector
│       └── training/
│           └── train.py        # Multimodal PEFT QLoRA fine-tuning pipeline
├── frontend/                   # Next.js 15 Aerospace Ground Station Cockpit
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx        # Main mission control cockpit layout
│   │   │   └── layout.tsx      # High-tech HUD typography & metadata
│   │   └── components/
│   │       ├── OrbitalHeader.tsx        # Real-time telemetry, dual Local/UTC clock
│   │       ├── EvidenceVisualizer.tsx   # 4-Slot Multi-Spectral Evidence Matrix
│   │       ├── SpectralIndicesDeck.tsx  # Interactive Band Math Deck with Canvas fallback
│   │       ├── BitemporalSwipeSlider.tsx# Dual-frame swipe & astronomical blink comparator
│   │       ├── GeospatialLoupeEnhancer.tsx # 8X optical loupe, CLAHE & distance caliper
│   │       ├── GeospatialTelemetryHUD.tsx  # WGS-84 tracker, SSO orbit radar & RGB histogram
│   │       ├── DetectedObjectsDeck.tsx  # Multi-class target reticle inventory
│   │       └── TacticalUplinkBar.tsx    # Speech voice recognition uplink & mission chips
├── data/                       # Benchmark missions (Sentinel-2, SAR, Disaster)
├── Dockerfile                  # Production container definition
├── docker-compose.yml          # Full-stack container orchestration
├── requirements.txt            # Python dependencies
└── README.md                   # Technical documentation
```

---

## 🧪 Testing Suite

Run the full test suite covering agent graph routing, spectral calculations, and coordinate bounding:

```bash
pytest tests/ -v
```

---

## 📄 License

SatQuery AI is open-source software licensed under the [MIT License](LICENSE).
