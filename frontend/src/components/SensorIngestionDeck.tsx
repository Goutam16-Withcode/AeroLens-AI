'use client';

import React, { useRef, useState } from 'react';

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

  const [isDraggingA, setIsDraggingA] = useState(false);
  const [isDraggingB, setIsDraggingB] = useState(false);

  const handleFileA = (file?: File) => {
    if (file) {
      setFileA(file);
      setPreviewA(URL.createObjectURL(file));
    }
  };

  const handleFileB = (file?: File) => {
    if (file) {
      setFileB(file);
      setPreviewB(URL.createObjectURL(file));
    }
  };

  return (
    <div className="panel-card" style={{ marginBottom: '18px' }}>
      <div className="panel-header">
        <div className="panel-title">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <rect x="2" y="2" width="20" height="8" rx="2" />
            <rect x="2" y="14" width="20" height="8" rx="2" />
            <line x1="6" y1="6" x2="6.01" y2="6" />
            <line x1="6" y1="18" x2="6.01" y2="18" />
          </svg>
          <span>SENSOR INGESTION</span>
        </div>
        <span className="panel-title-tag">DUAL CHANNEL // FULL VISIBILITY</span>
      </div>

      <div className="sensor-ports-grid">
        {/* Sensor A Port (Primary Swath) */}
        <div>
          <div
            className={`sensor-dropzone ${previewA ? 'has-file' : ''}`}
            style={{
              borderColor: isDraggingA ? 'var(--accent-amber)' : undefined,
            }}
            onClick={() => !previewA && inputARef.current?.click()}
            onDragOver={(e) => {
              e.preventDefault();
              setIsDraggingA(true);
            }}
            onDragLeave={() => setIsDraggingA(false)}
            onDrop={(e) => {
              e.preventDefault();
              setIsDraggingA(false);
              const f = e.dataTransfer.files?.[0];
              if (f) handleFileA(f);
            }}
          >
            <input
              type="file"
              ref={inputARef}
              style={{ display: 'none' }}
              accept="image/*,.tif,.tiff"
              onChange={(e) => handleFileA(e.target.files?.[0])}
            />

            {previewA ? (
              <>
                <img src={previewA} alt="Sensor A Swath" className="sensor-preview-image" />
                <div
                  style={{
                    position: 'absolute',
                    bottom: '6px',
                    left: '6px',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '9.5px',
                    fontWeight: 700,
                    padding: '3px 8px',
                    borderRadius: '4px',
                    background: 'rgba(255, 255, 255, 0.94)',
                    color: 'var(--accent-amber)',
                    border: '1px solid var(--accent-amber-border)',
                    boxShadow: '0 2px 6px rgba(0, 0, 0, 0.08)',
                  }}
                >
                  SENSOR A: INGESTED
                </div>
                <button
                  className="sensor-remove-btn"
                  title="Remove image"
                  onClick={(e) => {
                    e.stopPropagation();
                    setFileA(null);
                    setPreviewA(null);
                  }}
                >
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <line x1="18" y1="6" x2="6" y2="18" />
                    <line x1="6" y1="6" x2="18" y2="18" />
                  </svg>
                </button>
              </>
            ) : (
              <div className="cell-empty-state">
                <div style={{ color: 'var(--accent-amber)', marginBottom: '2px' }}>
                  {/* Optical Lens Aperture Vector */}
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75">
                    <circle cx="12" cy="12" r="10" />
                    <line x1="14.31" y1="8" x2="20.05" y2="17.94" />
                    <line x1="9.69" y1="8" x2="21.17" y2="8" />
                    <line x1="7.38" y1="12" x2="13.12" y2="2.06" />
                    <line x1="9.69" y1="16" x2="3.95" y2="6.06" />
                    <line x1="14.31" y1="16" x2="2.83" y2="16" />
                    <line x1="16.62" y1="12" x2="10.88" y2="21.94" />
                  </svg>
                </div>
                <div style={{ fontFamily: 'var(--font-hud)', fontSize: '12px', fontWeight: 600, color: 'var(--text-main)' }}>
                  SENSOR A (PRIMARY)
                </div>
                <div style={{ fontSize: '10.5px', color: 'var(--text-muted)' }}>
                  Optical RGB / GeoTIFF (Uncropped)
                </div>
              </div>
            )}
          </div>

          <select
            className="sensor-select"
            value={modalityA}
            onChange={(e) => setModalityA(e.target.value)}
          >
            <option value="Auto">Spectral Band: Auto-Detect</option>
            <option value="Optical">Optical (RGB / VNIR / Sentinel-2)</option>
            <option value="SAR">SAR (C-Band Radar Backscatter)</option>
          </select>
        </div>

        {/* Sensor B Port (SAR / Temporal T2) */}
        <div>
          <div
            className={`sensor-dropzone ${previewB ? 'has-file' : ''}`}
            style={{
              borderColor: isDraggingB ? 'var(--accent-emerald)' : undefined,
            }}
            onClick={() => !previewB && inputBRef.current?.click()}
            onDragOver={(e) => {
              e.preventDefault();
              setIsDraggingB(true);
            }}
            onDragLeave={() => setIsDraggingB(false)}
            onDrop={(e) => {
              e.preventDefault();
              setIsDraggingB(false);
              const f = e.dataTransfer.files?.[0];
              if (f) handleFileB(f);
            }}
          >
            <input
              type="file"
              ref={inputBRef}
              style={{ display: 'none' }}
              accept="image/*,.tif,.tiff"
              onChange={(e) => handleFileB(e.target.files?.[0])}
            />

            {previewB ? (
              <>
                <img src={previewB} alt="Sensor B Swath" className="sensor-preview-image" />
                <div
                  style={{
                    position: 'absolute',
                    bottom: '6px',
                    left: '6px',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '9.5px',
                    fontWeight: 700,
                    padding: '3px 8px',
                    borderRadius: '4px',
                    background: 'rgba(255, 255, 255, 0.94)',
                    color: 'var(--accent-emerald)',
                    border: '1px solid var(--accent-emerald-border)',
                    boxShadow: '0 2px 6px rgba(0, 0, 0, 0.08)',
                  }}
                >
                  SENSOR B: INGESTED
                </div>
                <button
                  className="sensor-remove-btn"
                  title="Remove secondary image"
                  onClick={(e) => {
                    e.stopPropagation();
                    setFileB(null);
                    setPreviewB(null);
                  }}
                >
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <line x1="18" y1="6" x2="6" y2="18" />
                    <line x1="6" y1="6" x2="18" y2="18" />
                  </svg>
                </button>
              </>
            ) : (
              <div className="cell-empty-state">
                <div style={{ color: 'var(--accent-emerald)', marginBottom: '2px' }}>
                  {/* Radar Waveform Vector */}
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75">
                    <path d="M2 12h3l3-8 4 16 3-8h7" />
                  </svg>
                </div>
                <div style={{ fontFamily: 'var(--font-hud)', fontSize: '12px', fontWeight: 600, color: 'var(--text-main)' }}>
                  SENSOR B (OPTIONAL)
                </div>
                <div style={{ fontSize: '10.5px', color: 'var(--text-muted)' }}>
                  SAR Radar / Temporal T2
                </div>
              </div>
            )}
          </div>

          <select
            className="sensor-select"
            value={modalityB}
            onChange={(e) => setModalityB(e.target.value)}
          >
            <option value="Auto">Spectral Band: Auto-Detect</option>
            <option value="Optical">Optical (T2 / Post-Disaster)</option>
            <option value="SAR">SAR (Sentinel-1 VV/VH Radar)</option>
          </select>
        </div>
      </div>
    </div>
  );
};
