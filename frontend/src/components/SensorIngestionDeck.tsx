"use client";

import React, { useRef } from "react";

interface SensorIngestionDeckProps {
  fileA: File | null;
  setFileA: (file: File | null) => void;
  previewA: string | null;
  setPreviewA: (url: string | null) => void;
  modalityA: string;
  setModalityA: (mod: string) => void;

  fileB: File | null;
  setFileB: (file: File | null) => void;
  previewB: string | null;
  setPreviewB: (url: string | null) => void;
  modalityB: string;
  setModalityB: (mod: string) => void;
}

export const SensorIngestionDeck: React.FC<SensorIngestionDeckProps> = ({
  fileA,
  setFileA,
  previewA,
  setPreviewA,
  modalityA,
  setModalityA,
  fileB,
  setFileB,
  previewB,
  setPreviewB,
  modalityB,
  setModalityB,
}) => {
  const inputARef = useRef<HTMLInputElement>(null);
  const inputBRef = useRef<HTMLInputElement>(null);

  const handleFileAChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setFileA(file);
      setPreviewA(URL.createObjectURL(file));
    }
  };

  const handleFileBChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setFileB(file);
      setPreviewB(URL.createObjectURL(file));
    }
  };

  return (
    <div className="hud-deck-card">
      <div className="hud-panel-title">
        <span>[01]</span> SENSOR INGESTION PORTS (PRIMARY OPTICAL & SECONDARY SAR / TEMPORAL)
      </div>

      <div className="ingestion-grid">
        {/* Port A */}
        <div>
          <div
            className={`upload-port ${previewA ? "active-port" : ""}`}
            onClick={() => inputARef.current?.click()}
          >
            <input
              type="file"
              ref={inputARef}
              style={{ display: "none" }}
              accept="image/*,.tif,.tiff"
              onChange={handleFileAChange}
            />
            {previewA ? (
              <img src={previewA} alt="Sensor A Swath" className="upload-preview-img" />
            ) : (
              <div style={{ textAlign: "center", padding: "20px" }}>
                <div style={{ fontSize: "36px", marginBottom: "10px" }}>🛰️</div>
                <div style={{ fontFamily: "var(--font-hud)", fontSize: "14px", fontWeight: 700, color: "var(--optical-cyan)" }}>
                  INGEST SENSOR A (PRIMARY SWATH)
                </div>
                <div style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "6px" }}>
                  Click to browse GeoTIFF, TIFF, PNG, or JPEG
                </div>
              </div>
            )}
          </div>

          <select
            className="modality-selector"
            value={modalityA}
            onChange={(e) => setModalityA(e.target.value)}
          >
            <option value="Auto">Spectral Channel: Auto-Detect</option>
            <option value="Optical">Spectral Channel: Optical (RGB / VIS-NIR)</option>
            <option value="SAR">Spectral Channel: SAR (C-Band Radar Backscatter)</option>
          </select>
        </div>

        {/* Port B */}
        <div>
          <div
            className={`upload-port ${previewB ? "active-port" : ""}`}
            onClick={() => inputBRef.current?.click()}
          >
            <input
              type="file"
              ref={inputBRef}
              style={{ display: "none" }}
              accept="image/*,.tif,.tiff"
              onChange={handleFileBChange}
            />
            {previewB ? (
              <img src={previewB} alt="Sensor B Swath" className="upload-preview-img" />
            ) : (
              <div style={{ textAlign: "center", padding: "20px" }}>
                <div style={{ fontSize: "36px", marginBottom: "10px" }}>📡</div>
                <div style={{ fontFamily: "var(--font-hud)", fontSize: "14px", fontWeight: 700, color: "var(--sat-gold-bright)" }}>
                  INGEST SENSOR B (OPTIONAL: SAR / TEMPORAL T2)
                </div>
                <div style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "6px" }}>
                  For Optical-SAR Fusion or Change-VQA Delta
                </div>
              </div>
            )}
          </div>

          <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
            <select
              className="modality-selector"
              style={{ flex: 1 }}
              value={modalityB}
              onChange={(e) => setModalityB(e.target.value)}
            >
              <option value="Auto">Spectral Channel: Auto-Detect</option>
              <option value="Optical">Spectral Channel: Optical (T2 / After)</option>
              <option value="SAR">Spectral Channel: SAR (C-Band Radar)</option>
            </select>
            {previewB && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setFileB(null);
                  setPreviewB(null);
                }}
                style={{
                  background: "rgba(255, 42, 109, 0.2)",
                  border: "1px solid var(--thermal-ruby)",
                  color: "var(--thermal-ruby)",
                  borderRadius: "6px",
                  padding: "8px 12px",
                  fontSize: "12px",
                  fontFamily: "var(--font-mono)",
                  cursor: "pointer",
                  marginTop: "10px",
                }}
              >
                Clear
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
