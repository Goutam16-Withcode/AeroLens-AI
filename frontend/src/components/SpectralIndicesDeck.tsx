'use client';

import React, { useState } from 'react';

interface SpectralIndicesDeckProps {
  fileA: File | null;
  previewA: string | null;
}

export const SpectralIndicesDeck: React.FC<SpectralIndicesDeckProps> = ({ fileA, previewA }) => {
  const [activeTab, setActiveTab] = useState<string>('ndvi');
  const [processedImg, setProcessedImg] = useState<string | null>(null);
  const [stats, setStats] = useState<any | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

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
    { id: 'ndvi', label: 'NDVI (Vegetation Index)', desc: 'Normalized Difference Vegetation Index' },
    { id: 'ndwi', label: 'NDWI (Water / Inundation)', desc: 'Normalized Difference Water Index' },
    { id: 'ndbi', label: 'NDBI (Urban / Impervious)', desc: 'Built-Up Surface Density Index' },
    { id: 'cir', label: 'CIR (Color Infrared Composite)', desc: 'Near-Infrared Composite Synthesis' },
  ];

  return (
    <div className="panel-card" style={{ marginBottom: '18px' }}>
      <div className="panel-header">
        <div className="panel-title">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
          </svg>
          <span>SCIENTIFIC SPECTRAL INDICES // BAND MATH DECK</span>
        </div>
        <span className="panel-title-tag">LIVE RADIOMETRIC PROCESSING</span>
      </div>

      {/* Index Selector Buttons */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '8px', marginBottom: '14px' }}>
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => calculateIndex(tab.id)}
            disabled={!previewA || loading}
            style={{
              padding: '8px 10px',
              background: activeTab === tab.id && processedImg ? 'var(--accent-amber-subtle)' : '#f5f0e8',
              border: `1px solid ${activeTab === tab.id && processedImg ? 'var(--accent-amber)' : 'var(--border-subtle)'}`,
              borderRadius: '6px',
              color: activeTab === tab.id && processedImg ? 'var(--accent-amber)' : 'var(--text-secondary)',
              fontFamily: 'var(--font-mono)',
              fontSize: '11px',
              fontWeight: 600,
              cursor: previewA ? 'pointer' : 'not-allowed',
              opacity: previewA ? 1 : 0.45,
              transition: 'all 0.2s ease',
              textAlign: 'center',
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Processed View & Statistics */}
      {processedImg ? (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px', alignItems: 'center' }}>
          <div style={{ height: '210px', background: '#f0eae0', borderRadius: '8px', overflow: 'hidden', position: 'relative', border: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '4px' }}>
            <img src={processedImg} alt="Processed Index" style={{ width: '100%', height: '100%', objectFit: 'contain' }} />
            <div style={{ position: 'absolute', bottom: '8px', left: '8px', fontFamily: 'var(--font-mono)', fontSize: '10px', fontWeight: 700, background: 'rgba(255, 255, 255, 0.94)', padding: '2px 7px', borderRadius: '4px', color: 'var(--accent-amber)', border: '1px solid var(--accent-amber-border)', boxShadow: '0 2px 4px rgba(0,0,0,0.06)' }}>
              {stats?.index_name}
            </div>
          </div>

          <div style={{ background: '#f8f4ec', border: '1px solid var(--border-subtle)', borderRadius: '8px', padding: '14px', fontSize: '12px' }}>
            <div style={{ fontFamily: 'var(--font-hud)', fontSize: '13px', color: 'var(--text-pure)', fontWeight: 700, marginBottom: '8px' }}>
              RADIOMETRIC QUANTITATIVE ANALYSIS
            </div>

            {stats?.vegetation_coverage_pct !== undefined && (
              <div style={{ marginBottom: '6px', display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Canopy Biomass Coverage:</span>
                <strong style={{ color: 'var(--accent-emerald)', fontFamily: 'var(--font-mono)' }}>{stats.vegetation_coverage_pct}%</strong>
              </div>
            )}

            {stats?.water_coverage_pct !== undefined && (
              <div style={{ marginBottom: '6px', display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Inundation / Water Surface:</span>
                <strong style={{ color: '#0284c7', fontFamily: 'var(--font-mono)' }}>{stats.water_coverage_pct}%</strong>
              </div>
            )}

            {stats?.urban_coverage_pct !== undefined && (
              <div style={{ marginBottom: '6px', display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Impervious Built-up Area:</span>
                <strong style={{ color: 'var(--accent-amber)', fontFamily: 'var(--font-mono)' }}>{stats.urban_coverage_pct}%</strong>
              </div>
            )}

            {stats?.mean_index !== undefined && (
              <div style={{ marginBottom: '6px', display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Mean Index Ratio:</span>
                <strong style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-pure)' }}>{stats.mean_index}</strong>
              </div>
            )}

            <div style={{ marginTop: '10px', paddingTop: '8px', borderTop: '1px solid var(--border-subtle)', fontSize: '10.5px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
              Palette: {stats?.colormap || stats?.description}
            </div>
          </div>
        </div>
      ) : (
        <div style={{ padding: '18px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '12px', fontStyle: 'italic' }}>
          {loading ? 'Executing radiometric band math calculations...' : 'Click an index above (NDVI / NDWI / NDBI / CIR) to run live multi-spectral radiometric analysis.'}
        </div>
      )}
    </div>
  );
};
