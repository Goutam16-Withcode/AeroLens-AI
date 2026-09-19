'use client';

import React, { useState } from 'react';
import { ImageLightboxModal } from './ImageLightboxModal';

interface SpectralIndicesDeckProps {
  fileA: File | null;
  previewA: string | null;
}

export const SpectralIndicesDeck: React.FC<SpectralIndicesDeckProps> = ({ fileA, previewA }) => {
  const [activeTab, setActiveTab] = useState<string>('ndvi');
  const [processedImg, setProcessedImg] = useState<string | null>(null);
  const [stats, setStats] = useState<any | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [blendOpacity, setBlendOpacity] = useState<number>(100);
  const [lightboxOpen, setLightboxOpen] = useState<boolean>(false);

  const calculateIndex = async (indexType: string) => {
    if (!fileA && !previewA) return;
    setActiveTab(indexType);
    setLoading(true);

    try {
      let fileToSend: File;
      if (fileA) {
        fileToSend = fileA;
      } else {
        // Convert preview data URL to blob
        const res = await fetch(previewA!);
        const blob = await res.blob();
        fileToSend = new File([blob], 'sensor_a.png', { type: 'image/png' });
      }

      const formData = new FormData();
      formData.append('index_type', indexType);
      formData.append('image', fileToSend);

      const r = await fetch('http://localhost:8000/api/spectral-indices', {
        method: 'POST',
        body: formData,
      });

      if (r.ok) {
        const data = await r.json();
        setProcessedImg(data.processed_image);
        setStats(data.statistics);
      }
    } catch (err) {
      console.error('Spectral index calculation error:', err);
    } finally {
      setLoading(false);
    }
  };

  const tabs = [
    {
      id: 'ndvi',
      label: 'NDVI (Vegetation Index)',
      sub: 'USGS Canopy Biomass',
      legend: [
        { label: 'Bare Soil (<0.1)', color: '#d97706' },
        { label: 'Sparse (0.2)', color: '#a3e635' },
        { label: 'Moderate (0.4)', color: '#22c55e' },
        { label: 'Dense Canopy (0.6+)', color: '#059669' },
      ],
      gradient: 'linear-gradient(90deg, #d97706 0%, #fef08a 25%, #a3e635 50%, #22c55e 75%, #059669 100%)',
    },
    {
      id: 'ndwi',
      label: 'NDWI (Water / Inundation)',
      sub: 'Hydrological Shoreline',
      legend: [
        { label: 'Dry Ground', color: '#64748b' },
        { label: 'Wetland / Shore', color: '#06b6d4' },
        { label: 'Open Deep Water', color: '#0e7490' },
      ],
      gradient: 'linear-gradient(90deg, #475569 0%, #0891b2 50%, #0e7490 80%, #1e3a8a 100%)',
    },
    {
      id: 'ndbi',
      label: 'NDBI (Urban / Impervious)',
      sub: 'Built-up Infrastructure',
      legend: [
        { label: 'Natural / Green', color: '#64748b' },
        { label: 'Suburban / Roads', color: '#f59e0b' },
        { label: 'Dense Urban Core', color: '#e11d48' },
      ],
      gradient: 'linear-gradient(90deg, #475569 0%, #f59e0b 55%, #e11d48 100%)',
    },
    {
      id: 'cir',
      label: 'CIR (Color Infrared Composite)',
      sub: 'NASA False-Color Standard',
      legend: [
        { label: 'Velvet Crimson (Vegetation)', color: '#dc2626' },
        { label: 'Silver-Cyan (Urban / Soil)', color: '#94a3b8' },
        { label: 'Deep Navy (Water Bodies)', color: '#0f172a' },
      ],
      gradient: 'linear-gradient(90deg, #0f172a 0%, #0e7490 25%, #94a3b8 50%, #f87171 75%, #dc2626 100%)',
    },
    {
      id: 'nbr',
      label: 'NBR (Burn / Wildfire Severity)',
      sub: 'USGS Fire Perimeter',
      legend: [
        { label: 'High Severity Burn', color: '#e11d48' },
        { label: 'Moderate Scorch', color: '#d97706' },
        { label: 'Unburned Canopy', color: '#10b981' },
      ],
      gradient: 'linear-gradient(90deg, #e11d48 0%, #f59e0b 45%, #10b981 100%)',
    },
    {
      id: 'savi',
      label: 'SAVI (Soil-Adjusted Vegetation)',
      sub: 'Arid Canopy (L=0.5)',
      legend: [
        { label: 'Bare Arid Soil', color: '#78716c' },
        { label: 'Sparse Vegetation', color: '#a3e635' },
        { label: 'Dense Canopy', color: '#059669' },
      ],
      gradient: 'linear-gradient(90deg, #78716c 0%, #a3e635 50%, #059669 100%)',
    },
  ];

  const currentTab = tabs.find((t) => t.id === activeTab) || tabs[0];

  const handleDownload = () => {
    if (!processedImg) return;
    const a = document.createElement('a');
    a.href = processedImg;
    a.download = `satquery-${activeTab}-spectral-map.png`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  return (
    <div className="panel-card" style={{ marginBottom: '18px' }}>
      {/* Lightbox Modal for Processed Image Zoom & Download */}
      <ImageLightboxModal
        isOpen={lightboxOpen}
        onClose={() => setLightboxOpen(false)}
        imageSrc={processedImg}
        title={stats?.index_name || `SPECTRAL INDEX // ${activeTab.toUpperCase()}`}
        subtitle="100% UNCOMPRESSED RADIOMETRIC PIXEL MATRIX — CLICK DOWNLOAD TO EXPORT PNG"
      />

      <div className="panel-header">
        <div className="panel-title">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
          </svg>
          <span>SCIENTIFIC SPECTRAL INDICES // BAND MATH DECK</span>
        </div>
        <span className="panel-title-tag">PEER-REVIEWED RADIOMETRIC ENGINES</span>
      </div>

      {/* Index Selector Buttons */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
          gap: '8px',
          marginBottom: '14px',
        }}
      >
        {tabs.map((tab) => {
          const isSelected = activeTab === tab.id && processedImg;
          return (
            <button
              key={tab.id}
              onClick={() => calculateIndex(tab.id)}
              disabled={!previewA || loading}
              style={{
                padding: '8px 10px',
                background: isSelected ? 'var(--accent-amber-subtle)' : '#f5f0e8',
                border: `1.5px solid ${isSelected ? 'var(--accent-amber)' : 'var(--border-subtle)'}`,
                borderRadius: '6px',
                color: isSelected ? 'var(--accent-amber)' : 'var(--text-secondary)',
                fontFamily: 'var(--font-mono)',
                fontSize: '11px',
                fontWeight: 700,
                cursor: previewA ? 'pointer' : 'not-allowed',
                opacity: previewA ? 1 : 0.45,
                transition: 'all 0.2s ease',
                textAlign: 'center',
                boxShadow: isSelected ? '0 2px 6px rgba(217, 119, 6, 0.15)' : 'none',
              }}
            >
              <div>{tab.label}</div>
              <div style={{ fontSize: '9px', fontWeight: 500, color: 'var(--text-muted)', marginTop: '2px' }}>
                {tab.sub}
              </div>
            </button>
          );
        })}
      </div>

      {/* Processed View & Statistics */}
      {processedImg ? (
        <div>
          <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '14px', alignItems: 'start' }}>
            {/* Interactive Image Display with Blend Slider and Enlarge */}
            <div>
              <div
                onClick={() => setLightboxOpen(true)}
                title="Click to expand high-resolution frame & download"
                style={{
                  height: '240px',
                  background: '#0b111e',
                  borderRadius: '8px',
                  overflow: 'hidden',
                  position: 'relative',
                  border: '1.5px solid var(--accent-amber-border)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  cursor: 'zoom-in',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.12)',
                }}
              >
                {/* Base Raw Image */}
                {previewA && (
                  <img
                    src={previewA}
                    alt="Raw Satellite Swath"
                    style={{
                      position: 'absolute',
                      width: '100%',
                      height: '100%',
                      objectFit: 'contain',
                    }}
                  />
                )}

                {/* Overlaid Spectral Index Image with Dynamic Blend Opacity */}
                <img
                  src={processedImg}
                  alt="Processed Spectral Index"
                  style={{
                    position: 'absolute',
                    width: '100%',
                    height: '100%',
                    objectFit: 'contain',
                    opacity: blendOpacity / 100,
                    transition: 'opacity 0.1s ease-out',
                  }}
                />

                {/* Tactical Corner Reticles */}
                <div style={{ position: 'absolute', top: 6, left: 6, width: 10, height: 10, borderTop: '2px solid var(--accent-amber)', borderLeft: '2px solid var(--accent-amber)', pointerEvents: 'none' }} />
                <div style={{ position: 'absolute', top: 6, right: 6, width: 10, height: 10, borderTop: '2px solid var(--accent-amber)', borderRight: '2px solid var(--accent-amber)', pointerEvents: 'none' }} />
                <div style={{ position: 'absolute', bottom: 6, left: 6, width: 10, height: 10, borderBottom: '2px solid var(--accent-amber)', borderLeft: '2px solid var(--accent-amber)', pointerEvents: 'none' }} />
                <div style={{ position: 'absolute', bottom: 6, right: 6, width: 10, height: 10, borderBottom: '2px solid var(--accent-amber)', borderRight: '2px solid var(--accent-amber)', pointerEvents: 'none' }} />

                {/* Badge Indicator */}
                <div
                  style={{
                    position: 'absolute',
                    top: '8px',
                    left: '8px',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '9.5px',
                    fontWeight: 700,
                    background: 'rgba(15, 23, 42, 0.88)',
                    padding: '3px 8px',
                    borderRadius: '4px',
                    color: '#f8fafc',
                    border: '1px solid rgba(255,255,255,0.15)',
                    backdropFilter: 'blur(4px)',
                  }}
                >
                  {stats?.index_name}
                </div>

                {/* Click to Enlarge Hover Prompt */}
                <div
                  style={{
                    position: 'absolute',
                    bottom: '8px',
                    right: '8px',
                    background: 'rgba(217, 119, 6, 0.92)',
                    color: '#ffffff',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '10px',
                    fontWeight: 700,
                    padding: '3px 8px',
                    borderRadius: '4px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    boxShadow: '0 2px 6px rgba(0,0,0,0.2)',
                  }}
                >
                  <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <circle cx="11" cy="11" r="8" />
                    <line x1="21" y1="21" x2="16.65" y2="16.65" />
                    <line x1="11" y1="8" x2="11" y2="14" />
                    <line x1="8" y1="11" x2="14" y2="11" />
                  </svg>
                  <span>CLICK TO EXPAND / DOWNLOAD</span>
                </div>
              </div>

              {/* Opacity Blend Slider */}
              <div
                style={{
                  marginTop: '10px',
                  background: '#f8f4ec',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: '6px',
                  padding: '8px 12px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                }}
              >
                <span
                  style={{
                    fontSize: '10.5px',
                    fontFamily: 'var(--font-mono)',
                    color: 'var(--text-secondary)',
                    fontWeight: 600,
                    whiteSpace: 'nowrap',
                  }}
                >
                  SWATH BLEND:
                </span>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={blendOpacity}
                  onChange={(e) => setBlendOpacity(Number(e.target.value))}
                  style={{
                    flex: 1,
                    accentColor: 'var(--accent-amber)',
                    cursor: 'pointer',
                  }}
                />
                <span
                  style={{
                    fontSize: '11px',
                    fontFamily: 'var(--font-mono)',
                    fontWeight: 700,
                    color: 'var(--accent-amber)',
                    minWidth: '40px',
                    textAlign: 'right',
                  }}
                >
                  {blendOpacity}%
                </span>
              </div>

              {/* Tactical Quick Actions */}
              <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
                <button
                  onClick={() => setLightboxOpen(true)}
                  style={{
                    flex: 1,
                    padding: '7px 10px',
                    background: '#ffffff',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: '6px',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '10.5px',
                    fontWeight: 700,
                    color: 'var(--text-primary)',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '6px',
                    boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
                  }}
                >
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <circle cx="11" cy="11" r="8" />
                    <line x1="21" y1="21" x2="16.65" y2="16.65" />
                  </svg>
                  <span>EXPAND LIGHTBOX</span>
                </button>

                <button
                  onClick={handleDownload}
                  style={{
                    flex: 1,
                    padding: '7px 10px',
                    background: 'var(--accent-amber-subtle)',
                    border: '1px solid var(--accent-amber-border)',
                    borderRadius: '6px',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '10.5px',
                    fontWeight: 700,
                    color: 'var(--accent-amber)',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '6px',
                    boxShadow: '0 1px 3px rgba(217, 119, 6, 0.1)',
                  }}
                >
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                    <polyline points="7 10 12 15 17 10" />
                    <line x1="12" y1="15" x2="12" y2="3" />
                  </svg>
                  <span>EXPORT PNG MAP</span>
                </button>
              </div>
            </div>

            {/* Scientific Quantitative Analysis Panel */}
            <div
              style={{
                background: '#f8f4ec',
                border: '1px solid var(--border-subtle)',
                borderRadius: '8px',
                padding: '14px',
                fontSize: '12px',
              }}
            >
              <div
                style={{
                  fontFamily: 'var(--font-hud)',
                  fontSize: '12px',
                  color: 'var(--text-pure)',
                  fontWeight: 700,
                  marginBottom: '10px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  borderBottom: '1px solid var(--border-subtle)',
                  paddingBottom: '6px',
                }}
              >
                <span>QUANTITATIVE RS ANALYTICS</span>
                <span style={{ fontSize: '10px', color: 'var(--accent-amber)', fontFamily: 'var(--font-mono)' }}>
                  {stats?.algorithm ? 'ACTIVE' : 'READY'}
                </span>
              </div>

              {stats?.health_classification && (
                <div style={{ marginBottom: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ color: 'var(--text-secondary)', fontSize: '11px' }}>Canopy Classification:</span>
                  <strong style={{ color: 'var(--accent-emerald)', fontFamily: 'var(--font-mono)', fontSize: '11.5px' }}>
                    {stats.health_classification}
                  </strong>
                </div>
              )}

              {stats?.vegetation_coverage_pct !== undefined && (
                <div style={{ marginBottom: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ color: 'var(--text-secondary)', fontSize: '11px' }}>Vegetation Biomass:</span>
                  <strong style={{ color: 'var(--accent-emerald)', fontFamily: 'var(--font-mono)', fontSize: '12px' }}>
                    {stats.vegetation_coverage_pct}%
                  </strong>
                </div>
              )}

              {stats?.burn_classification && (
                <div style={{ marginBottom: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ color: 'var(--text-secondary)', fontSize: '11px' }}>Fire Severity Regime:</span>
                  <strong style={{ color: '#e11d48', fontFamily: 'var(--font-mono)', fontSize: '11.5px' }}>
                    {stats.burn_classification}
                  </strong>
                </div>
              )}

              {stats?.burned_area_pct !== undefined && (
                <div style={{ marginBottom: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ color: 'var(--text-secondary)', fontSize: '11px' }}>Burn Scar Footprint:</span>
                  <strong style={{ color: '#e11d48', fontFamily: 'var(--font-mono)', fontSize: '12px' }}>
                    {stats.burned_area_pct}%
                  </strong>
                </div>
              )}

              {stats?.classification && (
                <div style={{ marginBottom: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ color: 'var(--text-secondary)', fontSize: '11px' }}>Soil-Adjusted Regime:</span>
                  <strong style={{ color: '#10b981', fontFamily: 'var(--font-mono)', fontSize: '11.5px' }}>
                    {stats.classification}
                  </strong>
                </div>
              )}

              {stats?.soil_adjusted_canopy_pct !== undefined && (
                <div style={{ marginBottom: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ color: 'var(--text-secondary)', fontSize: '11px' }}>Adjusted Canopy Footprint:</span>
                  <strong style={{ color: '#10b981', fontFamily: 'var(--font-mono)', fontSize: '12px' }}>
                    {stats.soil_adjusted_canopy_pct}%
                  </strong>
                </div>
              )}

              {stats?.water_classification && (
                <div style={{ marginBottom: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ color: 'var(--text-secondary)', fontSize: '11px' }}>Water Hydro Regime:</span>
                  <strong style={{ color: '#0284c7', fontFamily: 'var(--font-mono)', fontSize: '11.5px' }}>
                    {stats.water_classification}
                  </strong>
                </div>
              )}

              {stats?.water_coverage_pct !== undefined && (
                <div style={{ marginBottom: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ color: 'var(--text-secondary)', fontSize: '11px' }}>Surface Water / Inundation:</span>
                  <strong style={{ color: '#0284c7', fontFamily: 'var(--font-mono)', fontSize: '12px' }}>
                    {stats.water_coverage_pct}%
                  </strong>
                </div>
              )}

              {stats?.urban_classification && (
                <div style={{ marginBottom: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ color: 'var(--text-secondary)', fontSize: '11px' }}>Built-Up Impervious:</span>
                  <strong style={{ color: 'var(--accent-amber)', fontFamily: 'var(--font-mono)', fontSize: '11.5px' }}>
                    {stats.urban_classification}
                  </strong>
                </div>
              )}

              {stats?.urban_coverage_pct !== undefined && (
                <div style={{ marginBottom: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ color: 'var(--text-secondary)', fontSize: '11px' }}>Infrastructure Footprint:</span>
                  <strong style={{ color: 'var(--accent-amber)', fontFamily: 'var(--font-mono)', fontSize: '12px' }}>
                    {stats.urban_coverage_pct}%
                  </strong>
                </div>
              )}

              {stats?.mean_index !== undefined && (
                <div style={{ marginBottom: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ color: 'var(--text-secondary)', fontSize: '11px' }}>Mean Radiometric Ratio:</span>
                  <strong style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-pure)', fontSize: '12px' }}>
                    {stats.mean_index}
                  </strong>
                </div>
              )}

              {stats?.description && (
                <div style={{ margin: '8px 0', fontSize: '10.5px', lineHeight: '1.4', color: 'var(--text-secondary)', fontStyle: 'italic', background: '#f0eae0', padding: '6px 8px', borderRadius: '4px' }}>
                  {stats.description}
                </div>
              )}

              {/* Radiometric Legend Bar */}
              <div style={{ marginTop: '12px', paddingTop: '8px', borderTop: '1px solid var(--border-subtle)' }}>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', color: 'var(--text-secondary)', marginBottom: '4px', fontWeight: 600 }}>
                  CALIBRATED RADIOMETRIC PALETTE:
                </div>
                <div
                  style={{
                    height: '8px',
                    borderRadius: '4px',
                    background: currentTab.gradient,
                    marginBottom: '6px',
                    border: '1px solid var(--border-subtle)',
                  }}
                />
                <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
                  {currentTab.legend.map((item, idx) => (
                    <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '10px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                      <span style={{ width: '8px', height: '8px', borderRadius: '2px', background: item.color, display: 'inline-block' }} />
                      <span>{item.label}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '12px' }}>
          {loading ? (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
              <div className="pulse-dot" />
              <span>Synthesizing radiometric spectral band math matrix...</span>
            </div>
          ) : (
            <span>Click any spectral index above (NDVI / NDWI / NDBI / CIR) to compute live multi-spectral radiometric analysis on Sensor A.</span>
          )}
        </div>
      )}
    </div>
  );
};
