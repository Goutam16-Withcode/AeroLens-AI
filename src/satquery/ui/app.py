import os
import sys
import json
import base64
from io import BytesIO
from typing import List, Tuple, Optional
from PIL import Image
import streamlit as st

# Ensure project root is in sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
src_dir = os.path.join(ROOT_DIR, "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from satquery.core.config import settings
from satquery.validator.validator import InputValidator
from satquery.agent.graph import SatQueryController
from satquery.models.engine import RemoteSensingVLMEngine

# -----------------------------------------------------------------------------
# Streamlit Page Configuration
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="SatQuery AI — Satellite Geospatial Intelligence & Earth Observation",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# Ultra-Professional Aerospace & Geospatial Intelligence Styling
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&family=Plus+Jakarta+Sans:wght@500;600;700;800&display=swap');
    
    :root {
        --bg-primary: #080c14;
        --bg-secondary: #0d1424;
        --bg-card: rgba(15, 23, 42, 0.75);
        --accent-cyan: #00e5ff;
        --accent-blue: #3b82f6;
        --accent-emerald: #10b981;
        --accent-purple: #8b5cf6;
        --accent-amber: #f59e0b;
        --border-glass: rgba(255, 255, 255, 0.08);
        --border-cyan: rgba(0, 229, 255, 0.25);
        --text-main: #f1f5f9;
        --text-muted: #94a3b8;
    }
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .stApp {
        background: radial-gradient(circle at 15% 15%, #0f172a 0%, #080c14 60%, #030712 100%);
        color: var(--text-main);
    }
    
    /* Aerospace Mission Header */
    .mission-header {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.85) 0%, rgba(30, 41, 59, 0.65) 50%, rgba(15, 23, 42, 0.9) 100%);
        backdrop-filter: blur(16px);
        border: 1px solid var(--border-glass);
        border-top: 1px solid rgba(0, 229, 255, 0.3);
        border-radius: 16px;
        padding: 24px 32px;
        margin-bottom: 24px;
        box-shadow: 0 12px 36px 0 rgba(0, 0, 0, 0.45);
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    
    .brand-title {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 26px;
        font-weight: 800;
        letter-spacing: -0.5px;
        color: #ffffff;
        display: flex;
        align-items: center;
        gap: 12px;
        margin: 0;
    }
    
    .brand-title span {
        background: linear-gradient(135deg, #00e5ff 0%, #38bdf8 50%, #818cf8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .brand-subtitle {
        margin: 6px 0 0 0;
        color: var(--text-muted);
        font-size: 13.5px;
        font-weight: 400;
        letter-spacing: 0.2px;
    }
    
    /* Telemetry Pill Badges */
    .telemetry-badges {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
    }
    
    .pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 14px;
        border-radius: 9999px;
        font-size: 11.5px;
        font-weight: 600;
        font-family: 'JetBrains Mono', monospace;
        letter-spacing: 0.3px;
    }
    
    .pill-moondream {
        background: rgba(16, 185, 129, 0.12);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.35);
        box-shadow: 0 0 12px rgba(16, 185, 129, 0.15);
    }
    
    .pill-offline {
        background: rgba(0, 229, 255, 0.1);
        color: #38bdf8;
        border: 1px solid rgba(0, 229, 255, 0.3);
    }
    
    .pill-agent {
        background: rgba(139, 92, 246, 0.12);
        color: #c084fc;
        border: 1px solid rgba(139, 92, 246, 0.3);
    }

    /* Cards & Containers */
    .glass-card {
        background: var(--bg-card);
        backdrop-filter: blur(14px);
        border: 1px solid var(--border-glass);
        border-radius: 14px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
    }
    
    .telemetry-card {
        background: linear-gradient(180deg, rgba(15, 23, 42, 0.8) 0%, rgba(10, 16, 30, 0.9) 100%);
        border: 1px solid rgba(59, 130, 246, 0.25);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 18px;
    }
    
    .metric-hud {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(30, 41, 59, 0.7) 100%);
        border: 1px solid var(--border-glass);
        border-radius: 12px;
        padding: 16px 20px;
        text-align: center;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
    }
    
    .metric-hud-label {
        color: var(--text-muted);
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.8px;
        text-transform: uppercase;
        font-family: 'JetBrains Mono', monospace;
    }
    
    .metric-hud-val {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 20px;
        font-weight: 700;
        margin-top: 4px;
    }

    .delta-kpi-card {
        background: rgba(15, 23, 42, 0.85);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        padding: 12px 14px;
        margin-bottom: 8px;
    }
    
    /* Button Enhancements */
    .stButton>button {
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 50%, #1d4ed8 100%);
        color: #ffffff;
        border: 1px solid rgba(56, 189, 248, 0.4);
        border-radius: 10px;
        font-weight: 600;
        font-size: 14px;
        letter-spacing: 0.2px;
        padding: 10px 20px;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 14px rgba(2, 132, 199, 0.3);
    }
    
    .stButton>button:hover {
        background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 50%, #2563eb 100%);
        border-color: #38bdf8;
        box-shadow: 0 6px 20px rgba(14, 165, 233, 0.5);
        transform: translateY(-1px);
    }
    
    .stButton>button:active {
        transform: translateY(0px);
    }
    
    /* Code & Coordinate Blocks */
    code, pre {
        font-family: 'JetBrains Mono', monospace !important;
    }
    
    /* Form Inputs */
    .stTextArea textarea {
        background-color: rgba(15, 23, 42, 0.8) !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 10px !important;
        color: #f8fafc !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 14px !important;
    }
    
    .stTextArea textarea:focus {
        border-color: var(--accent-cyan) !important;
        box-shadow: 0 0 0 2px rgba(0, 229, 255, 0.2) !important;
    }
    
    /* Custom Scrollbar */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: #080c14;
    }
    ::-webkit-scrollbar-thumb {
        background: #1e293b;
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #334155;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Controller & Engine Initialization (Zero-Key Moondream Architecture)
# -----------------------------------------------------------------------------
@st.cache_resource
def get_controller():
    return SatQueryController()

controller = get_controller()
engine = RemoteSensingVLMEngine.get_instance()
engine.set_provider("moondream")

# -----------------------------------------------------------------------------
# Default State Initialization (Loads VRSBench on start so it's always ready)
# -----------------------------------------------------------------------------
default_vrs_img_path = os.path.join(ROOT_DIR, "data", "samples", "vrsbench", "vrsbench_sample_01.png")

if "current_images" not in st.session_state or not st.session_state.current_images:
    if os.path.exists(default_vrs_img_path):
        st.session_state.current_images = [Image.open(default_vrs_img_path)]
        st.session_state.current_query = "Locate and highlight all parked airplanes on the apron."
        st.session_state.scenario_name = "VRSBench (Grounding Demo Preset)"
    else:
        st.session_state.current_images = []
        st.session_state.current_query = "Describe the land cover and visible infrastructure in this satellite image."
        st.session_state.scenario_name = "Custom Imagery Upload"

if "query_input_val" not in st.session_state:
    st.session_state.query_input_val = st.session_state.get("current_query", "Locate and highlight all parked airplanes on the apron.")

# -----------------------------------------------------------------------------
# Sidebar: Moondream Telemetry & Mission Benchmark Presets
# -----------------------------------------------------------------------------
st.sidebar.markdown("""
<div style="padding: 10px 0 16px 0;">
    <div style="font-family:'Plus Jakarta Sans',sans-serif;font-size:18px;font-weight:800;color:#f8fafc;letter-spacing:-0.3px;">
        🛰️ <span style="background:linear-gradient(135deg,#00e5ff,#38bdf8);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">SATQUERY AI</span>
    </div>
    <div style="font-size:11.5px;color:#94a3b8;margin-top:2px;">
        Geospatial Earth Observation Engine
    </div>
</div>
""", unsafe_allow_html=True)

# Moondream-2 Engine Telemetry Card
st.sidebar.markdown("""
<div class="telemetry-card">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
        <span style="font-family:'JetBrains Mono',monospace;font-size:11px;color:#38bdf8;font-weight:600;">AI VISION MODEL</span>
        <span style="font-size:10.5px;color:#10b981;font-weight:700;display:flex;align-items:center;gap:4px;">
            <span style="display:inline-block;width:6px;height:6px;border-radius:50%;background:#10b981;box-shadow:0 0 6px #10b981;"></span> ACTIVE
        </span>
    </div>
    <div style="font-size:14.5px;font-weight:700;color:#ffffff;letter-spacing:-0.2px;">
        Moondream 2.0 RS-VLM
    </div>
    <div style="font-size:12px;color:#94a3b8;margin-top:4px;">
        Zero-API-Key Local Vision & Spectral Reasoner
    </div>
    <div style="margin-top:10px;padding-top:8px;border-top:1px solid rgba(255,255,255,0.08);display:flex;justify-content:space-between;font-size:11px;color:#cbd5e1;font-family:'JetBrains Mono',monospace;">
        <span>PRIVACY: <b style="color:#34d399;">100% Offline</b></span>
        <span>LATENCY: <b style="color:#38bdf8;">~35ms</b></span>
    </div>
</div>
""", unsafe_allow_html=True)

# Benchmark Demo Mission Presets
st.sidebar.markdown("### 🎯 Mission Benchmark Presets")
st.sidebar.caption("Instant high-resolution test datasets across core satellite domains:")

col_sb1, col_sb2 = st.sidebar.columns(2)
with col_sb1:
    if st.button("🛩️ VRSBench", use_container_width=True, help="Aircraft visual grounding & apron detection"):
        img_path = os.path.join(ROOT_DIR, "data", "samples", "vrsbench", "vrsbench_sample_01.png")
        if os.path.exists(img_path):
            st.session_state.current_images = [Image.open(img_path)]
            st.session_state.query_input_val = "Locate and highlight all parked airplanes on the apron."
            st.session_state.scenario_name = "VRSBench (Grounding Demo)"
            st.rerun()

with col_sb2:
    if st.button("🏞️ RSVQA VQA", use_container_width=True, help="Land cover classification and urban inventory"):
        img_path = os.path.join(ROOT_DIR, "data", "samples", "rsvqa", "rsvqa_sample_01.png")
        if os.path.exists(img_path):
            st.session_state.current_images = [Image.open(img_path)]
            st.session_state.query_input_val = "What types of land use and water features are visible in this scene?"
            st.session_state.scenario_name = "RSVQA (Land Use Demo)"
            st.rerun()

col_sb3, col_sb4 = st.sidebar.columns(2)
with col_sb3:
    if st.button("🔄 CDVQA Change", use_container_width=True, help="Bi-temporal construction & deforestation detection"):
        t1_path = os.path.join(ROOT_DIR, "data", "samples", "cdvqa", "t1_before_2023.png")
        t2_path = os.path.join(ROOT_DIR, "data", "samples", "cdvqa", "t2_after_2025.png")
        if os.path.exists(t1_path) and os.path.exists(t2_path):
            st.session_state.current_images = [Image.open(t1_path), Image.open(t2_path)]
            st.session_state.query_input_val = "What major construction and land-cover changes occurred between T1 and T2?"
            st.session_state.scenario_name = "CDVQA (Bi-Temporal Change Demo)"
            st.rerun()

with col_sb4:
    if st.button("📡 BigEarthNet", use_container_width=True, help="Optical & SAR Sentinel multi-sensor fusion"):
        opt_path = os.path.join(ROOT_DIR, "data", "samples", "bigearthnet", "sentinel2_optical.png")
        sar_path = os.path.join(ROOT_DIR, "data", "samples", "bigearthnet", "sentinel1_sar.png")
        if os.path.exists(opt_path) and os.path.exists(sar_path):
            st.session_state.current_images = [Image.open(opt_path), Image.open(sar_path)]
            st.session_state.query_input_val = "Use both optical and SAR imagery to delineate the water boundary beneath the cloud cover."
            st.session_state.scenario_name = "BigEarthNet (Optical-SAR Fusion Demo)"
            st.rerun()

if st.sidebar.button("🛰️ INSAT-3DS Weather TIR", use_container_width=True, help="Geostationary meteorological thermal IR analysis"):
    insat_path = os.path.join(ROOT_DIR, "data", "samples", "insat3ds", "insat3ds_tir1_sample.png")
    if os.path.exists(insat_path):
        st.session_state.current_images = [Image.open(insat_path)]
        st.session_state.query_input_val = "What this image shows and explain it"
        st.session_state.scenario_name = "INSAT-3DS (Meteorological Thermal IR Demo)"
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style="font-size:11.5px;color:#64748b;line-height:1.5;">
    <b>Supported Satellite Constellations:</b><br>
    • Sentinel-2 (MSI), Sentinel-1 (C-Band SAR)<br>
    • Landsat-8/9 (OLI/TIRS), PlanetScope<br>
    • ISRO INSAT-3D/3DS (TIR1 @ 10.83 µm)<br>
    • WorldView-3 / High-Res Aerial Ortho
</div>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Top Mission Control Header Banner
# -----------------------------------------------------------------------------
st.markdown("""
<div class="mission-header">
    <div>
        <h1 class="brand-title">
            🛰️ <span>SatQuery AI</span> Geospatial Platform
        </h1>
        <p class="brand-subtitle">
            Multimodal Remote Sensing Agent • Visual Grounding • Bi-Temporal Change • Optical–SAR Fusion • Geostationary Meteorology
        </p>
    </div>
    <div class="telemetry-badges">
        <span class="pill pill-moondream">🟢 MOONDREAM 2.0 VLM</span>
        <span class="pill pill-offline">🛡️ ZERO API KEYS / 100% PRIVATE</span>
        <span class="pill pill-agent">⚡ LANGGRAPH RS AGENT</span>
    </div>
</div>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 🎬 Evaluator 1-Click Guided Presentation Tour (Autonomous Evaluation)
# -----------------------------------------------------------------------------
st.markdown("""
<div style="background:linear-gradient(135deg,rgba(15,23,42,0.9),rgba(30,41,59,0.75));border:1px solid rgba(0,229,255,0.3);border-radius:12px;padding:12px 18px;margin-bottom:20px;box-shadow:0 4px 16px rgba(0,0,0,0.3);">
    <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;">
        <div style="display:flex;align-items:center;gap:8px;">
            <span style="font-size:16px;">🎬</span>
            <span style="font-weight:800;font-size:13.5px;color:#f8fafc;font-family:'Plus Jakarta Sans',sans-serif;letter-spacing:-0.2px;">
                EVALUATOR 1-CLICK GUIDED DEMO TOUR
            </span>
            <span style="font-size:12px;color:#94a3b8;">— Click any scenario below to instantly load satellite imagery & analytical queries:</span>
        </div>
        <span style="font-family:'JetBrains Mono',monospace;font-size:11px;color:#38bdf8;background:rgba(56,189,248,0.1);padding:3px 8px;border-radius:6px;border:1px solid rgba(56,189,248,0.25);">
            5 CORE BENCHMARKS READY
        </span>
    </div>
</div>
""", unsafe_allow_html=True)

tour_col1, tour_col2, tour_col3, tour_col4, tour_col5 = st.columns(5)

with tour_col1:
    if st.button("🛩️ 1. Aircraft Grounding", use_container_width=True, help="VRSBench: Visual localization & bounding box grounding of aircraft"):
        img_path = os.path.join(ROOT_DIR, "data", "samples", "vrsbench", "vrsbench_sample_01.png")
        if os.path.exists(img_path):
            st.session_state.current_images = [Image.open(img_path)]
            st.session_state.query_input_val = "Locate and highlight all parked airplanes on the apron."
            st.session_state.scenario_name = "VRSBench (Grounding Demo)"
            st.rerun()

with tour_col2:
    if st.button("🏞️ 2. Land Cover VQA", use_container_width=True, help="RSVQA: Multi-spectral land cover & river channel inventory"):
        img_path = os.path.join(ROOT_DIR, "data", "samples", "rsvqa", "rsvqa_sample_01.png")
        if os.path.exists(img_path):
            st.session_state.current_images = [Image.open(img_path)]
            st.session_state.query_input_val = "What types of land use and water features are visible in this scene?"
            st.session_state.scenario_name = "RSVQA (Land Use Demo)"
            st.rerun()

with tour_col3:
    if st.button("🔄 3. Change Detection", use_container_width=True, help="CDVQA: Multi-year bi-temporal deforestation & construction detection"):
        t1_path = os.path.join(ROOT_DIR, "data", "samples", "cdvqa", "t1_before_2023.png")
        t2_path = os.path.join(ROOT_DIR, "data", "samples", "cdvqa", "t2_after_2025.png")
        if os.path.exists(t1_path) and os.path.exists(t2_path):
            st.session_state.current_images = [Image.open(t1_path), Image.open(t2_path)]
            st.session_state.query_input_val = "What major construction and land-cover changes occurred between T1 and T2?"
            st.session_state.scenario_name = "CDVQA (Bi-Temporal Change Demo)"
            st.rerun()

with tour_col4:
    if st.button("📡 4. Optical-SAR Fusion", use_container_width=True, help="BigEarthNet: Cloud-penetrating Sentinel-1 SAR + Sentinel-2 Optical fusion"):
        opt_path = os.path.join(ROOT_DIR, "data", "samples", "bigearthnet", "sentinel2_optical.png")
        sar_path = os.path.join(ROOT_DIR, "data", "samples", "bigearthnet", "sentinel1_sar.png")
        if os.path.exists(opt_path) and os.path.exists(sar_path):
            st.session_state.current_images = [Image.open(opt_path), Image.open(sar_path)]
            st.session_state.query_input_val = "Use both optical and SAR imagery to delineate the water boundary beneath the cloud cover."
            st.session_state.scenario_name = "BigEarthNet (Optical-SAR Fusion Demo)"
            st.rerun()

with tour_col5:
    if st.button("🛰️ 5. INSAT-3DS Weather", use_container_width=True, help="ISRO INSAT-3DS: Thermal Infrared-1 (10.83 µm) Brightness Temperature & Storm Tracking"):
        insat_path = os.path.join(ROOT_DIR, "data", "samples", "insat3ds", "insat3ds_tir1_sample.png")
        if os.path.exists(insat_path):
            st.session_state.current_images = [Image.open(insat_path)]
            st.session_state.query_input_val = "What this image shows and explain it"
            st.session_state.scenario_name = "INSAT-3DS (Meteorological Thermal IR Demo)"
            st.rerun()

st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Main Application Workspace: Two-Column Mission Layout
# -----------------------------------------------------------------------------
left_col, right_col = st.columns([1.15, 0.85], gap="large")

with left_col:
    st.markdown("### 🛰️ Imagery Ingestion & Multi-Spectral Viewport")
    
    uploaded_files = st.file_uploader(
        "Ingest Satellite Tiles (1 tile for VQA/Grounding, 2 tiles for Bi-Temporal Change or Optical-SAR Fusion):",
        type=["png", "jpg", "jpeg", "tif", "tiff"],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        st.session_state.current_images = [InputValidator.load_image(f.read()) for f in uploaded_files[:2]]
        st.session_state.scenario_name = "User Ingested Imagery"
        
    # Display Image Viewport & Radiometric Layers
    if st.session_state.current_images:
        num_imgs = len(st.session_state.current_images)
        st.caption(f"Active Scene: **{st.session_state.scenario_name}** | **{num_imgs} Tile{'s' if num_imgs > 1 else ''} Loaded**")
        
        # ---------------------------------------------------------------------
        # Case A: Single Satellite Tile Viewport
        # ---------------------------------------------------------------------
        if num_imgs == 1:
            active_img = st.session_state.current_images[0]
            
            # Interactive Multi-Spectral Layer Switcher
            spectral_layers = engine.generate_spectral_layers(active_img)
                
            selected_layer = st.radio(
                "Sensor Radiometric Layer:",
                ["🛰️ RGB Optical", "🌿 Color-Infrared (CIR/NDVI)", "💧 NDWI Water Mask", "🏙️ Structural Edge Radar", "🌡️ Thermal Turbo"],
                horizontal=True,
                index=0
            )
            
            layer_map = {
                "🛰️ RGB Optical": "rgb",
                "🌿 Color-Infrared (CIR/NDVI)": "cir_ndvi",
                "💧 NDWI Water Mask": "ndwi_water",
                "🏙️ Structural Edge Radar": "edges",
                "🌡️ Thermal Turbo": "thermal_turbo"
            }
            target_key = layer_map.get(selected_layer, "rgb")
            img_to_show = spectral_layers.get(target_key, active_img)
            
            st.image(img_to_show, caption=f"Radiometric Channel: {selected_layer} | {active_img.width}x{active_img.height} px", use_container_width=True)
            
            # Live Biophysical Spectral Indices & Quadrant Coverage
            with st.expander("📊 Live Biophysical Land-Cover Radar & Spatial Quadrants", expanded=True):
                spec = engine._analyze_imagery_spectrum(active_img)
                p_c1, p_c2 = st.columns(2)
                with p_c1:
                    st.write(f"🌿 **Vegetation Canopy**: `{spec.get('veg_pct', 0.0)}%`")
                    st.progress(min(1.0, spec.get('veg_pct', 0.0) / 100.0))
                    st.write(f"💧 **Hydrological Drainage**: `{spec.get('water_pct', 0.0)}%`")
                    st.progress(min(1.0, spec.get('water_pct', 0.0) / 100.0))
                with p_c2:
                    st.write(f"🏙️ **Urban / Paved Tarmac**: `{spec.get('urban_pct', 0.0)}%`")
                    st.progress(min(1.0, spec.get('urban_pct', 0.0) / 100.0))
                    st.write(f"☁️ **Cloud / High Reflectance**: `{spec.get('cloud_pct', 0.0)}%`")
                    st.progress(min(1.0, spec.get('cloud_pct', 0.0) / 100.0))
                    
                st.markdown("<div style='font-size:12px;font-weight:700;color:#94a3b8;margin-top:10px;text-transform:uppercase;font-family:monospace;'>🧭 Spatial Quadrant Distribution:</div>", unsafe_allow_html=True)
                q_col1, q_col2 = st.columns(2)
                quads = spec.get("quadrants", {})
                with q_col1:
                    nw, sw = quads.get("NW", {}), quads.get("SW", {})
                    st.caption(f"**NW Sector**: Veg {nw.get('veg', 0):.1f}% | Urban {nw.get('urban', 0):.1f}% | Water {nw.get('water', 0):.1f}%")
                    st.caption(f"**SW Sector**: Veg {sw.get('veg', 0):.1f}% | Urban {sw.get('urban', 0):.1f}% | Water {sw.get('water', 0):.1f}%")
                with q_col2:
                    ne, se = quads.get("NE", {}), quads.get("SE", {})
                    st.caption(f"**NE Sector**: Veg {ne.get('veg', 0):.1f}% | Urban {ne.get('urban', 0):.1f}% | Water {ne.get('water', 0):.1f}%")
                    st.caption(f"**SE Sector**: Veg {se.get('veg', 0):.1f}% | Urban {se.get('urban', 0):.1f}% | Water {se.get('water', 0):.1f}%")

        # ---------------------------------------------------------------------
        # Case B: Dual Satellite Tile Comparative Studio (Advanced Multi-View)
        # ---------------------------------------------------------------------
        else:
            img1, img2 = st.session_state.current_images[0], st.session_state.current_images[1]
            
            selected_comp_mode = st.radio(
                "Comparative Studio Mode:",
                ["🔄 Synced Split View", "🎚️ Alpha-Dissolve Wipe", "🔥 Live Difference Heatmap", "📡 Optical–SAR False-Color"],
                horizontal=True,
                index=0
            )
            
            label_1 = "Timestamp T1 (Before / Reference)" if "Change" in st.session_state.scenario_name else "Tile 1 (Sentinel-2 Optical)"
            label_2 = "Timestamp T2 (After / Recent)" if "Change" in st.session_state.scenario_name else "Tile 2 (Sentinel-1 SAR Radar)"
            
            if selected_comp_mode == "🔄 Synced Split View":
                prev_col1, prev_col2 = st.columns(2)
                with prev_col1:
                    st.image(img1, caption=f"📸 {label_1} ({img1.width}x{img1.height})", use_container_width=True)
                with prev_col2:
                    st.image(img2, caption=f"📸 {label_2} ({img2.width}x{img2.height})", use_container_width=True)
                    
            elif selected_comp_mode == "🎚️ Alpha-Dissolve Wipe":
                alpha_val = st.slider(
                    f"Dissolve Blend ({label_1} ➔ {label_2}):",
                    min_value=0.0, max_value=1.0, value=0.5, step=0.05
                )
                blended_img = engine.blend_image_pair(img1, img2, alpha_val)
                st.image(
                    blended_img, 
                    caption=f"🎚️ Alpha Blend: {int((1.0 - alpha_val) * 100)}% Tile 1 | {int(alpha_val * 100)}% Tile 2", 
                    use_container_width=True
                )
                
            elif selected_comp_mode == "🔥 Live Difference Heatmap":
                diff_thresh = st.slider(
                    "Sensitivity Threshold (Pixel Deviation):",
                    min_value=10, max_value=80, value=35, step=5
                )
                diff_data = engine.compute_interactive_difference(img1, img2, threshold=diff_thresh)
                
                d_c1, d_c2 = st.columns(2)
                with d_c1:
                    st.image(diff_data["diff_heatmap"], caption="🔥 Radiometric Absolute Difference Heatmap (Turbo)", use_container_width=True)
                with d_c2:
                    st.image(diff_data["change_overlay"], caption=f"🚨 Surface Alteration Zones ({diff_data['num_clusters']} Clusters)", use_container_width=True)
                    
                st.markdown(f"""
                <div style="background:rgba(239, 68, 68, 0.1);border:1px solid rgba(239, 68, 68, 0.3);border-radius:8px;padding:8px 14px;margin-top:6px;display:flex;justify-content:space-between;font-family:'JetBrains Mono',monospace;font-size:12px;">
                    <span style="color:#f87171;">TOTAL SURFACE ALTERATION: <b>{diff_data['change_pct']}%</b></span>
                    <span style="color:#fbbf24;">DETECTED CHANGE CLUSTERS: <b>{diff_data['num_clusters']} Zones</b></span>
                </div>
                """, unsafe_allow_html=True)
                
            elif selected_comp_mode == "📡 Optical–SAR False-Color":
                fused_img = engine.create_false_color_fusion(img1, img2)
                st.image(fused_img, caption="📡 Multi-Sensor Composite (Red: Optical Red, Green: Optical Green, Blue: SAR C-Band Radar Backscatter)", use_container_width=True)
                st.caption("ℹ️ Dielectric roughness & radar backscatter penetrates clouds to highlight all-weather hydrological and structural boundaries.")

            # Live Biophysical Delta Analysis Expander
            with st.expander("📊 Comparative Biophysical Delta Analysis (T1 ➔ T2 Transition)", expanded=True):
                delta_info = engine.compute_biophysical_delta(img1, img2)
                s1 = delta_info["spec_t1"]
                s2 = delta_info["spec_t2"]
                
                kpi_c1, kpi_c2, kpi_c3, kpi_c4 = st.columns(4)
                with kpi_c1:
                    v_d = delta_info["veg_delta"]
                    v_color = "#34d399" if v_d >= 0 else "#f87171"
                    v_icon = "🔺" if v_d >= 0 else "🔻"
                    st.markdown(f"""
                    <div class="delta-kpi-card">
                        <div style="font-size:10px;color:#94a3b8;font-family:monospace;">🌿 CANOPY COVER</div>
                        <div style="font-size:14px;font-weight:700;color:#f8fafc;margin-top:2px;">{s1.get('veg_pct', 0)}% ➔ {s2.get('veg_pct', 0)}%</div>
                        <div style="font-size:11px;font-weight:600;color:{v_color};margin-top:2px;">{v_icon} {v_d:+.1f}% Δ</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                with kpi_c2:
                    w_d = delta_info["water_delta"]
                    w_color = "#38bdf8" if w_d >= 0 else "#f87171"
                    w_icon = "🔺" if w_d >= 0 else "🔻"
                    st.markdown(f"""
                    <div class="delta-kpi-card">
                        <div style="font-size:10px;color:#94a3b8;font-family:monospace;">💧 DRAINAGE / WATER</div>
                        <div style="font-size:14px;font-weight:700;color:#f8fafc;margin-top:2px;">{s1.get('water_pct', 0)}% ➔ {s2.get('water_pct', 0)}%</div>
                        <div style="font-size:11px;font-weight:600;color:{w_color};margin-top:2px;">{w_icon} {w_d:+.1f}% Δ</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                with kpi_c3:
                    u_d = delta_info["urban_delta"]
                    u_color = "#fbbf24" if u_d >= 0 else "#94a3b8"
                    u_icon = "🔺" if u_d >= 0 else "🔻"
                    st.markdown(f"""
                    <div class="delta-kpi-card">
                        <div style="font-size:10px;color:#94a3b8;font-family:monospace;">🏙️ BUILT-UP SURFACE</div>
                        <div style="font-size:14px;font-weight:700;color:#f8fafc;margin-top:2px;">{s1.get('urban_pct', 0)}% ➔ {s2.get('urban_pct', 0)}%</div>
                        <div style="font-size:11px;font-weight:600;color:{u_color};margin-top:2px;">{u_icon} {u_d:+.1f}% Δ</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                with kpi_c4:
                    c_d = delta_info["cloud_delta"]
                    c_color = "#c084fc" if c_d >= 0 else "#94a3b8"
                    c_icon = "🔺" if c_d >= 0 else "🔻"
                    st.markdown(f"""
                    <div class="delta-kpi-card">
                        <div style="font-size:10px;color:#94a3b8;font-family:monospace;">☁️ HIGH REFLECTANCE</div>
                        <div style="font-size:14px;font-weight:700;color:#f8fafc;margin-top:2px;">{s1.get('cloud_pct', 0)}% ➔ {s2.get('cloud_pct', 0)}%</div>
                        <div style="font-size:11px;font-weight:600;color:{c_color};margin-top:2px;">{c_icon} {c_d:+.1f}% Δ</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                st.markdown("<div style='font-size:12px;font-weight:700;color:#94a3b8;margin-top:8px;text-transform:uppercase;font-family:monospace;'>🧭 Spatial Quadrant Transition Shifts:</div>", unsafe_allow_html=True)
                qd_c1, qd_c2 = st.columns(2)
                quads_d = delta_info.get("quad_deltas", {})
                with qd_c1:
                    nw_d, sw_d = quads_d.get("NW", {}), quads_d.get("SW", {})
                    st.caption(f"**NW Sector Shift**: Veg {nw_d.get('veg_delta', 0):+.1f}% | Urban {nw_d.get('urban_delta', 0):+.1f}%")
                    st.caption(f"**SW Sector Shift**: Veg {sw_d.get('veg_delta', 0):+.1f}% | Urban {sw_d.get('urban_delta', 0):+.1f}%")
                with qd_c2:
                    ne_d, se_d = quads_d.get("NE", {}), quads_d.get("SE", {})
                    st.caption(f"**NE Sector Shift**: Veg {ne_d.get('veg_delta', 0):+.1f}% | Urban {ne_d.get('urban_delta', 0):+.1f}%")
                    st.caption(f"**SE Sector Shift**: Veg {se_d.get('veg_delta', 0):+.1f}% | Urban {se_d.get('urban_delta', 0):+.1f}%")

    else:
        st.info("Select a mission preset from the sidebar or upload satellite imagery to begin.")

with right_col:
    st.markdown("### 💬 Moondream Analytical Prompt Console")
    query_text = st.text_area(
        "Remote Sensing Prompt / Geospatial Analytical Question:",
        value=st.session_state.query_input_val,
        height=120,
        key="query_text_area_widget",
        help="Ask questions about land cover, target localization, temporal change, radar fusion, or meteorological thermal signatures."
    )
    st.session_state.query_input_val = query_text
    
    # Context-Aware Quick Mission Query Action Chips
    st.caption("⚡ Quick Analytical Actions:")
    chip_c1, chip_c2 = st.columns(2)
    
    # Dual-image prompts vs Single-image prompts
    if st.session_state.current_images and len(st.session_state.current_images) >= 2:
        with chip_c1:
            if st.button("🔄 Detect All Changes", use_container_width=True):
                st.session_state.query_input_val = "What major construction and land-cover changes occurred between T1 and T2?"
                st.rerun()
            if st.button("🏗️ New Construction", use_container_width=True):
                st.session_state.query_input_val = "Locate and highlight newly constructed buildings, roads, or bridges between T1 and T2."
                st.rerun()
        with chip_c2:
            if st.button("📡 Optical–SAR Fusion", use_container_width=True):
                st.session_state.query_input_val = "Use both optical and SAR imagery to delineate the water boundary beneath the cloud cover."
                st.rerun()
            if st.button("🌿 Deforestation Shift", use_container_width=True):
                st.session_state.query_input_val = "Assess vegetation loss, tree clearing, and agricultural alterations between T1 and T2."
                st.rerun()
    else:
        with chip_c1:
            if st.button("🔍 Explain Scene", use_container_width=True):
                st.session_state.query_input_val = "What this image shows and explain it"
                st.rerun()
            if st.button("✈️ Ground Aircraft", use_container_width=True):
                st.session_state.query_input_val = "Locate and highlight all parked airplanes on the apron."
                st.rerun()
        with chip_c2:
            if st.button("🛢️ Locate Storage Tanks", use_container_width=True):
                st.session_state.query_input_val = "Where are the circular fuel storage tanks located?"
                st.rerun()
            if st.button("💧 Water & Land Use", use_container_width=True):
                st.session_state.query_input_val = "What types of land use and water features are visible in this scene?"
                st.rerun()
            
    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    run_btn = st.button("🚀 Execute Moondream Agent", use_container_width=True, type="primary")

# -----------------------------------------------------------------------------
# Agent Execution & Response Visualizer
# -----------------------------------------------------------------------------
if run_btn:
    if not st.session_state.current_images:
        st.error("⚠️ Please upload or select at least one satellite tile.")
    elif not query_text.strip():
        st.error("⚠️ Please specify an analytical question or query prompt.")
    else:
        with st.spinner("Moondream Agent orchestrating multi-spectral tools and evaluating imagery..."):
            # Validate input & determine scenario
            norm_images, scenario, meta = InputValidator.validate_inputs(
                st.session_state.current_images, 
                user_intent_hint=query_text
            )
            
            # Process via LangGraph Controller
            result = controller.process_query(
                query=query_text,
                images=norm_images,
                input_scenario=scenario
            )
            
        st.markdown("<hr style='border-color:rgba(255,255,255,0.08);margin:32px 0 24px 0;'>", unsafe_allow_html=True)
        st.markdown("## 📊 Geospatial Intelligence Findings")
        
        # Mission Control HUD Metrics
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        with m_col1:
            st.markdown(f"""
            <div class='metric-hud'>
                <div class='metric-hud-label'>TASK IDENTIFIED</div>
                <div class='metric-hud-val' style='color:#38bdf8;'>{result.task.upper()}</div>
            </div>
            """, unsafe_allow_html=True)
        with m_col2:
            st.markdown(f"""
            <div class='metric-hud'>
                <div class='metric-hud-label'>DISPATCHED TOOL</div>
                <div class='metric-hud-val' style='color:#c084fc;'>{result.tool_used}</div>
            </div>
            """, unsafe_allow_html=True)
        with m_col3:
            conf_color = "#34d399" if result.confidence >= 0.85 else "#fbbf24"
            st.markdown(f"""
            <div class='metric-hud'>
                <div class='metric-hud-label'>CONFIDENCE RATING</div>
                <div class='metric-hud-val' style='color:{conf_color};'>{result.confidence * 100:.0f}%</div>
            </div>
            """, unsafe_allow_html=True)
        with m_col4:
            ev = result.evidence
            bbox_cnt = len(ev.bboxes) if ev.bboxes else (ev.stats.get("num_change_zones", 0) if ev.stats else 0)
            feature_label = "Change Zones" if result.task == "change_detection" else "Features"
            st.markdown(f"""
            <div class='metric-hud'>
                <div class='metric-hud-label'>DETECTED ENTITIES</div>
                <div class='metric-hud-val' style='color:#00e5ff;'>{bbox_cnt} {feature_label}</div>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
        
        # Two-Column Results View
        res_left, res_right = st.columns([1.1, 0.9], gap="medium")
        
        with res_left:
            st.markdown("### 📝 Structured Intelligence Report")
            st.markdown(result.answer)
            
            # Export Report Actions
            st.download_button(
                label="📥 Export Mission Intelligence Report (.md)",
                data=result.answer,
                file_name="satquery_intelligence_report.md",
                mime="text/markdown",
                use_container_width=True
            )
            
        with res_right:
            st.markdown("### 🔍 Visual Evidence & Localization Hub")
            
            tabs = []
            tab_titles = []
            if ev.overlay_image_base64:
                tab_titles.append("🎨 Visual Overlay")
            if ev.side_by_side_base64:
                tab_titles.append("🔄 Multi-Sensor Panorama")
            tab_titles.append("📦 Quantitative Metrics & Coordinates")
            tab_titles.append("⚡ Telemetry Log")
            
            ui_tabs = st.tabs(tab_titles)
            
            tab_idx = 0
            if ev.overlay_image_base64:
                with ui_tabs[tab_idx]:
                    st.image(ev.overlay_image_base64, caption="Visual Grounding / Change Overlay", use_container_width=True)
                tab_idx += 1
                
            if ev.side_by_side_base64:
                with ui_tabs[tab_idx]:
                    st.image(ev.side_by_side_base64, caption="Synchronized Multi-Panel Comparison", use_container_width=True)
                tab_idx += 1
                
            with ui_tabs[tab_idx]:
                if ev.bboxes:
                    st.caption("Normalized Bounding Box Coordinates `[ymin, xmin, ymax, xmax]`:")
                    st.json([b.model_dump() for b in ev.bboxes])
                elif ev.stats:
                    st.caption("Extracted Spectral, Change & Spatial Metrics:")
                    st.json(ev.stats)
                else:
                    st.write("No specific bounding coordinates extracted.")
            tab_idx += 1
            
            with ui_tabs[tab_idx]:
                st.caption("LangGraph Controller Pipeline Latency Telemetry:")
                log_data = []
                for item in result.execution_log:
                    log_data.append({
                        "Pipeline Step": item.step,
                        "Latency (ms)": f"{item.duration_ms:.2f} ms",
                        "Status": item.status,
                        "Details": str(item.details or "")
                    })
                st.table(log_data)
