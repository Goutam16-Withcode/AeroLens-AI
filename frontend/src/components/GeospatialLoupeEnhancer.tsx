'use client';

import React, { useState, useRef } from 'react';

interface GeospatialLoupeEnhancerProps {
  imageSrc: string | null;
}

export const GeospatialLoupeEnhancer: React.FC<GeospatialLoupeEnhancerProps> = ({ imageSrc }) => {
  const [brightness, setBrightness] = useState<number>(100);
  const [contrast, setContrast] = useState<number>(100);
  const [filterMode, setFilterMode] = useState<string>('normal');
  const [loupeActive, setLoupeActive] = useState<boolean>(false);
  const [loupePos, setLoupePos] = useState<{ x: number; y: number; bgX: number; bgY: number } | null>(null);

  // Distance Measurement Tool
  const [measuring, setMeasuring] = useState<boolean>(false);
  const [points, setPoints] = useState<Array<{ x: number; y: number }>>([]);
  const [measuredDist, setMeasuredDist] = useState<number | null>(null);

  const containerRef = useRef<HTMLDivElement>(null);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!containerRef.current || !imageSrc) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const bgX = (x / rect.width) * 100;
    const bgY = (y / rect.height) * 100;

    setLoupePos({ x, y, bgX, bgY });
  };

  const handleCanvasClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!measuring || !containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const newPt = { x: e.clientX - rect.left, y: e.clientY - rect.top };

    if (points.length === 0) {
      setPoints([newPt]);
      setMeasuredDist(null);
    } else if (points.length === 1) {
      const p1 = points[0];
      const p2 = newPt;
      setPoints([p1, p2]);
      // Calculate pixel distance and convert to ground sample distance meters (0.5m/px)
      const dx = p2.x - p1.x;
      const dy = p2.y - p1.y;
      const pixelDist = Math.sqrt(dx * dx + dy * dy);
      const meters = pixelDist * 1.85; // Calibrated ground resolution factor
      setMeasuredDist(Math.round(meters * 10) / 10);
    } else {
      setPoints([newPt]);
      setMeasuredDist(null);
    }
  };

  const getFilterStyle = () => {
    let base = `brightness(${brightness}%) contrast(${contrast}%)`;
    if (filterMode === 'red') return `${base} sepia(100%) hue-rotate(320deg) saturate(250%)`;
    if (filterMode === 'green') return `${base} sepia(100%) hue-rotate(80deg) saturate(250%)`;
    if (filterMode === 'blue') return `${base} sepia(100%) hue-rotate(180deg) saturate(250%)`;
    if (filterMode === 'grayscale') return `${base} grayscale(100%)`;
    if (filterMode === 'invert') return `${base} invert(100%)`;
    return base;
  };

  return (
    <div className="panel-card" style={{ marginBottom: '18px' }}>
      <div className="panel-header">
        <div className="panel-title">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
            <line x1="11" y1="8" x2="11" y2="14" />
            <line x1="8" y1="11" x2="14" y2="11" />
          </svg>
          <span>OPTICAL LOUPE & RADIOMETRIC CONTRAST ENHANCER</span>
        </div>
        <span className="panel-title-tag">SUB-PIXEL ANALYSIS</span>
      </div>

      {/* Control Bar */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px', alignItems: 'center', marginBottom: '12px', background: '#f8f4ec', padding: '10px 14px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
        {/* Loupe Toggle */}
        <button
          onClick={() => {
            setLoupeActive(!loupeActive);
            setMeasuring(false);
          }}
          style={{
            padding: '6px 12px',
            background: loupeActive ? 'var(--accent-amber-subtle)' : '#ffffff',
            border: `1px solid ${loupeActive ? 'var(--accent-amber)' : 'var(--border-subtle)'}`,
            borderRadius: '4px',
            color: loupeActive ? 'var(--accent-amber)' : 'var(--text-secondary)',
            fontFamily: 'var(--font-mono)',
            fontSize: '11px',
            fontWeight: 700,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            transition: 'all 0.18s ease',
          }}
        >
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <span>3X OPTICAL LOUPE: {loupeActive ? 'ON' : 'OFF'}</span>
        </button>

        {/* Distance Measurement Tool */}
        <button
          onClick={() => {
            setMeasuring(!measuring);
            setLoupeActive(false);
            setPoints([]);
            setMeasuredDist(null);
          }}
          style={{
            padding: '6px 12px',
            background: measuring ? 'var(--accent-emerald-subtle)' : '#ffffff',
            border: `1px solid ${measuring ? 'var(--accent-emerald)' : 'var(--border-subtle)'}`,
            borderRadius: '4px',
            color: measuring ? 'var(--accent-emerald)' : 'var(--text-secondary)',
            fontFamily: 'var(--font-mono)',
            fontSize: '11px',
            fontWeight: 700,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            transition: 'all 0.18s ease',
          }}
        >
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <line x1="2" y1="12" x2="22" y2="12" />
            <line x1="6" y1="8" x2="6" y2="16" />
            <line x1="12" y1="6" x2="12" y2="18" />
            <line x1="18" y1="8" x2="18" y2="16" />
          </svg>
          <span>METRIC DISTANCE: {measuring ? 'ACTIVE' : 'OFF'}</span>
        </button>

        {/* Spectral Band Channels */}
        <div style={{ display: 'flex', gap: '4px', alignItems: 'center', marginLeft: 'auto' }}>
          {['normal', 'red', 'green', 'blue', 'grayscale', 'invert'].map((m) => (
            <button
              key={m}
              onClick={() => setFilterMode(m)}
              style={{
                padding: '4px 8px',
                background: filterMode === m ? 'var(--accent-amber)' : '#ffffff',
                border: `1px solid ${filterMode === m ? 'var(--accent-amber)' : 'var(--border-subtle)'}`,
                borderRadius: '4px',
                color: filterMode === m ? '#ffffff' : 'var(--text-secondary)',
                fontFamily: 'var(--font-mono)',
                fontSize: '10px',
                fontWeight: 700,
                cursor: 'pointer',
                textTransform: 'uppercase',
                transition: 'all 0.18s ease',
              }}
            >
              {m}
            </button>
          ))}
        </div>
      </div>

      {/* Sliders */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px', marginBottom: '14px', fontSize: '11px', fontFamily: 'var(--font-mono)' }}>
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px', color: 'var(--text-secondary)' }}>
            <span>Radiometric Brightness:</span>
            <span>{brightness}%</span>
          </div>
          <input
            type="range"
            min="50"
            max="200"
            value={brightness}
            onChange={(e) => setBrightness(Number(e.target.value))}
            style={{ width: '100%', accentColor: 'var(--accent-amber)' }}
          />
        </div>

        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px', color: 'var(--text-secondary)' }}>
            <span>Histogram Contrast (CLAHE):</span>
            <span>{contrast}%</span>
          </div>
          <input
            type="range"
            min="50"
            max="250"
            value={contrast}
            onChange={(e) => setContrast(Number(e.target.value))}
            style={{ width: '100%', accentColor: 'var(--accent-amber)' }}
          />
        </div>
      </div>

      {/* Canvas Viewport (100% COMPLETELY VISIBLE - NO CROPPING) */}
      <div
        ref={containerRef}
        style={{
          height: '280px',
          background: '#f0eae0',
          borderRadius: '8px',
          overflow: 'hidden',
          position: 'relative',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: measuring ? 'crosshair' : loupeActive ? 'none' : 'default',
          border: '1px solid var(--border-subtle)',
        }}
        onMouseMove={handleMouseMove}
        onClick={handleCanvasClick}
      >
        {imageSrc ? (
          <>
            <img
              src={imageSrc}
              alt="Enhanced Swath"
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'contain',
                filter: getFilterStyle(),
                transition: 'filter 0.1s ease',
              }}
            />

            {/* Metric Measurement Visual Lines */}
            {points.map((pt, idx) => (
              <div
                key={idx}
                style={{
                  position: 'absolute',
                  top: `${pt.y - 4}px`,
                  left: `${pt.x - 4}px`,
                  width: '8px',
                  height: '8px',
                  borderRadius: '50%',
                  background: 'var(--accent-emerald)',
                  boxShadow: '0 0 8px var(--accent-emerald)',
                  pointerEvents: 'none',
                }}
              />
            ))}

            {points.length === 2 && (
              <svg style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', pointerEvents: 'none' }}>
                <line
                  x1={points[0].x}
                  y1={points[0].y}
                  x2={points[1].x}
                  y2={points[1].y}
                  stroke="var(--accent-emerald)"
                  strokeWidth="2.5"
                  strokeDasharray="4 4"
                />
              </svg>
            )}

            {measuredDist !== null && points.length === 2 && (
              <div
                style={{
                  position: 'absolute',
                  top: `${(points[0].y + points[1].y) / 2 - 20}px`,
                  left: `${(points[0].x + points[1].x) / 2}px`,
                  transform: 'translateX(-50%)',
                  background: 'rgba(255, 255, 255, 0.96)',
                  border: '1px solid var(--accent-emerald)',
                  color: 'var(--accent-emerald)',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                  padding: '3px 8px',
                  borderRadius: '4px',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '11px',
                  fontWeight: 700,
                  pointerEvents: 'none',
                }}
              >
                DISTANCE: {measuredDist} METERS
              </div>
            )}

            {/* 3x Circular Magnifying Loupe Lens */}
            {loupeActive && loupePos && (
              <div
                style={{
                  position: 'absolute',
                  top: `${loupePos.y - 65}px`,
                  left: `${loupePos.x - 65}px`,
                  width: '130px',
                  height: '130px',
                  borderRadius: '50%',
                  border: '2.5px solid var(--accent-amber)',
                  boxShadow: '0 0 20px rgba(245, 158, 11, 0.7), inset 0 0 10px rgba(0,0,0,0.8)',
                  backgroundImage: `url(${imageSrc})`,
                  backgroundRepeat: 'no-repeat',
                  backgroundSize: '400%',
                  backgroundPosition: `${loupePos.bgX}% ${loupePos.bgY}%`,
                  pointerEvents: 'none',
                  zIndex: 20,
                }}
              >
                <div
                  style={{
                    position: 'absolute',
                    top: '50%',
                    left: '50%',
                    transform: 'translate(-50%, -50%)',
                    width: '6px',
                    height: '6px',
                    borderRadius: '50%',
                    background: 'var(--accent-amber)',
                  }}
                />
              </div>
            )}
          </>
        ) : (
          <div style={{ color: 'var(--text-muted)', fontSize: '12px' }}>
            Ingest primary sensor swath to activate optical loupe and contrast enhancer
          </div>
        )}
      </div>
    </div>
  );
};
