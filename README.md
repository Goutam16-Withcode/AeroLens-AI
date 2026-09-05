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

SatQuery AI is a local agentic remote-sensing analysis system designed to run on local GPU hardware (NVIDIA RTX 5050, 8GB VRAM) powered by **Moondream2**, **OpenCV**, **LangGraph**, and **Streamlit**.

---

## 🚀 Key Capabilities

1. **Visual Question Answering (VQA) & Captioning**: Natural language queries and scene-level land-cover descriptions.
2. **Visual Grounding & Localization**: Identifying and delineating target features (runways, airplanes, fuel tanks, water bodies) with coordinates and visual bounding box overlays.
3. **Bi-Temporal Change Detection**: Automated pixel-difference computation via OpenCV (`cv2.absdiff`) paired with Moondream2 semantic interpretation to detect and narrate surface alterations between $T_1$ (before) and $T_2$ (after).
4. **Optical–SAR Multi-Sensor Fusion**: Complementary dual-pass feature extraction uniting Sentinel-2 (optical color/texture) and Sentinel-1 (radar backscatter, cloud penetration, dielectric roughness).
5. **Agentic Routing Controller**: LangGraph state machine dynamically classifying query intent and dispatching to specialized tools with full execution telemetry.

---

## 📦 Quick Start Guide

### 1. Start Ollama with Moondream2
Ensure Ollama is running locally with the `moondream` model:
```bash
ollama run moondream
```

### 2. Prepare Demo Samples (1-Click)
Run the automated sample preparation script (pulls slices or prepares benchmark presets for VRSBench, RSVQA, CDVQA, BigEarthNet):
```bash
python scripts/download_samples.py
```

### 3. Verify Moondream Output Format (Optional)
```bash
python scripts/test_engine_format.py
```

### 4. Launch SatQuery AI Dashboard
```bash
streamlit run src/satquery/ui/app.py
```

---

## 🎯 Benchmark Demo Presets

The UI comes equipped with 4 ready-to-test benchmark scenarios aligned with the internal round problem statement:
- **🛩️ VRSBench Grounding**: `"Locate and highlight all parked airplanes on the apron."`
- **🏞️ RSVQA Land Cover**: `"What types of land use and water features are visible in this scene?"`
- **🔄 CDVQA Change Detection**: `"What major construction and land-cover changes occurred between T1 and T2?"`
- **📡 BigEarthNet Optical–SAR Fusion**: `"Use both optical and SAR imagery to delineate the water boundary beneath the cloud cover."`

---

## ⚙️ Architecture & Deployment Configuration

SatQuery AI supports dual execution modes via the `SATQUERY_ENGINE_MODE` environment variable:

- **Local Dev Mode (`SATQUERY_ENGINE_MODE=ollama`)**: Default zero-overhead HTTP client calling local Ollama (`http://localhost:11434`).
- **Cloud / Hugging Face Spaces Mode (`SATQUERY_ENGINE_MODE=transformers`)**: Direct in-process Transformers model loader (`vikhyatk/moondream2`).
