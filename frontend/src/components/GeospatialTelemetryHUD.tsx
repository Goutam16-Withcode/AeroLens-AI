'use client';

import React, { useState } from 'react';

interface GeospatialTelemetryHUDProps {
  imageSrc: string | null;
}

export const GeospatialTelemetryHUD: React.FC<GeospatialTelemetryHUDProps> = ({ imageSrc }) => {
  const [coords, setCoords] = useState<{ x: number; y: number; lat: string; lon: string } | null>(null);

  const [copied, setCopied] = useState<boolean>(false);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = Math.round(e.clientX - rect.left);
    const y = Math.round(e.clientY - rect.top);
    
    // Simulate high-precision geospatial geodetic coordinates
    const latBase = 28.6139 + (y / rect.height) * 0.04;
    const lonBase = 77.2090 + (x / rect.width) * 0.04;

    setCoords({
      x,
      y,
      lat: `${latBase.toFixed(4)}° N`,
      lon: `${lonBase.toFixed(4)}° E`,
    });
  };

  const handleCopyCoords = () => {
    if (!coords) return;
    const text = `${coords.lat}, ${coords.lon} | Pixel [${coords.x}, ${coords.y}] | WGS-84`;
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <div className="panel-card" style={{ marginBottom: '18px' }}>
      <div className="panel-header">
        <div className="panel-title">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <line x1="22" y1="12" x2="18" y2="12" />
            <line x1="6" y1="12" x2="2" y2="12" />
            <line x1="12" y1="6" x2="12" y2="2" />
            <line x1="12" y1="22" x2="12" y2="18" />
          </svg>
          <span>ORBITAL GEOSPATIAL TELEMETRY & HUD INSPECTOR</span>
        </div>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          {coords && (
            <button
              onClick={handleCopyCoords}
              style={{
                padding: '3px 8px',
                background: copied ? 'var(--accent-emerald-subtle)' : '#ffffff',
                border: `1px solid ${copied ? 'var(--accent-emerald)' : 'var(--border-subtle)'}`,
                color: copied ? 'var(--accent-emerald)' : 'var(--text-secondary)',
                borderRadius: '4px',
                fontFamily: 'var(--font-mono)',
                fontSize: '10px',
                fontWeight: 700,
                cursor: 'pointer',
                transition: 'all 0.15s ease',
              }}
            >
              {copied ? '✓ COORDS COPIED' : 'COPY WGS-84 COORDS'}
            </button>
          )}
          <span className="panel-title-tag">WGS84 SUB-METRIC HUD</span>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '14px' }}>
        {/* Interactive Image Target Box */}
        <div
          style={{
            height: '240px',
            background: '#f0eae0',
            borderRadius: '8px',
            overflow: 'hidden',
            position: 'relative',
            cursor: 'crosshair',
            border: '1px solid var(--border-subtle)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
          onMouseMove={handleMouseMove}
          onMouseLeave={() => setCoords(null)}
        >
          {imageSrc ? (
            <>
              <img src={imageSrc} alt="Telemetry Swath" style={{ width: '100%', height: '100%', objectFit: 'contain' }} />
              {coords && (
                <>
                  {/* Crosshair horizontal & vertical lines */}
                  <div style={{ position: 'absolute', top: `${coords.y}px`, left: 0, right: 0, height: '1.5px', background: 'rgba(194, 109, 46, 0.85)', pointerEvents: 'none' }} />
                  <div style={{ position: 'absolute', left: `${coords.x}px`, top: 0, bottom: 0, width: '1.5px', background: 'rgba(194, 109, 46, 0.85)', pointerEvents: 'none' }} />
                  {/* Floating tooltip badge */}
                  <div
                    style={{
                      position: 'absolute',
                      top: `${Math.min(180, coords.y + 10)}px`,
                      left: `${Math.min(220, coords.x + 10)}px`,
                      background: 'rgba(255, 255, 255, 0.96)',
                      border: '1px solid var(--accent-amber)',
                      boxShadow: '0 4px 12px rgba(41, 37, 36, 0.15)',
                      padding: '5px 9px',
                      borderRadius: '4px',
                      fontFamily: 'var(--font-mono)',
                      fontSize: '10.5px',
                      fontWeight: 700,
                      color: 'var(--accent-amber)',
                      pointerEvents: 'none',
                      zIndex: 10,
                    }}
                  >
                    <div>{coords.lat}, {coords.lon}</div>
                    <div style={{ color: 'var(--text-muted)', fontSize: '9.5px', fontWeight: 500 }}>Pixel: [{coords.x}, {coords.y}] · MGRS: 43R BK</div>
                  </div>
                </>
              )}
            </>
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-muted)', fontSize: '11px' }}>
              Hover crosshair requires primary sensor swath
            </div>
          )}
        </div>

        {/* Telemetry Metrics Sidebar & Orbital Mini-Map */}
        <div style={{ background: '#f8f4ec', border: '1px solid var(--border-subtle)', borderRadius: '8px', padding: '12px', display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '11px', fontFamily: 'var(--font-mono)' }}>
          {/* Orbital Ground Track Mini-Map */}
          <div style={{ background: '#0b111e', borderRadius: '6px', padding: '8px', border: '1px solid rgba(255,255,255,0.08)', position: 'relative', overflow: 'hidden' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px', fontSize: '9.5px', color: '#94a3b8' }}>
              <span>ORBITAL GROUND TRACK (SSO 98.2°)</span>
              <span style={{ color: 'var(--accent-amber)', fontWeight: 700 }}>PASS #144</span>
            </div>

            {/* SVG Cylindrical Projection Map with Orbit Path */}
            <svg viewBox="0 0 200 65" style={{ width: '100%', height: '55px', display: 'block' }}>
              {/* World Graticule lines */}
              <line x1="0" y1="32.5" x2="200" y2="32.5" stroke="#1e293b" strokeWidth="1" strokeDasharray="3 3" />
              <line x1="100" y1="0" x2="100" y2="65" stroke="#1e293b" strokeWidth="1" strokeDasharray="3 3" />
              
              {/* Landmass Outlines (Stylized) */}
              <path d="M 20 18 Q 35 15 45 28 Q 35 45 25 35 Z" fill="#1e293b" opacity="0.6" />
              <path d="M 40 38 Q 50 40 45 55 Q 38 52 40 38 Z" fill="#1e293b" opacity="0.6" />
              <path d="M 85 15 Q 115 12 125 30 Q 100 35 90 25 Z" fill="#1e293b" opacity="0.6" />
              <path d="M 90 28 Q 110 32 105 50 Q 95 48 90 28 Z" fill="#1e293b" opacity="0.6" />
              <path d="M 125 18 Q 165 20 170 38 Q 145 40 130 25 Z" fill="#1e293b" opacity="0.6" />
              <path d="M 155 45 Q 175 48 170 58 Q 155 56 155 45 Z" fill="#1e293b" opacity="0.6" />

              {/* Orbit Sun-Synchronous Ground Track */}
              <path
                d="M 50 0 Q 75 32.5 100 65 M 110 0 Q 135 32.5 160 65"
                fill="none"
                stroke="var(--accent-amber)"
                strokeWidth="1.5"
                strokeDasharray="4 2"
                opacity="0.85"
              />

              {/* Sub-Satellite Point & Sensor Footprint */}
              <rect x="127" y="27" width="16" height="11" fill="rgba(16, 185, 129, 0.3)" stroke="var(--accent-emerald)" strokeWidth="1" />
              <circle cx="135" cy="32.5" r="3.5" fill="var(--accent-amber)" />
              <circle cx="135" cy="32.5" r="7" fill="none" stroke="var(--accent-amber)" strokeWidth="0.8" opacity="0.7" />
            </svg>
          </div>

          {/* Radiometric Histogram Bars */}
          <div style={{ background: '#ffffff', borderRadius: '6px', padding: '8px 10px', border: '1px solid var(--border-subtle)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px', fontSize: '9.5px', color: 'var(--text-muted)' }}>
              <span>RADIOMETRIC HISTOGRAM (12-BIT DN)</span>
              <span style={{ color: 'var(--text-pure)', fontWeight: 600 }}>RGB SWATH</span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ width: '12px', fontSize: '9px', color: '#e11d48', fontWeight: 700 }}>R</span>
                <div style={{ flex: 1, height: '4px', background: '#f1f5f9', borderRadius: '2px', overflow: 'hidden' }}>
                  <div style={{ width: coords ? `${Math.min(95, 30 + (coords.x % 60))}%` : '58%', height: '100%', background: '#e11d48' }} />
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ width: '12px', fontSize: '9px', color: '#16a34a', fontWeight: 700 }}>G</span>
                <div style={{ flex: 1, height: '4px', background: '#f1f5f9', borderRadius: '2px', overflow: 'hidden' }}>
                  <div style={{ width: coords ? `${Math.min(95, 25 + (coords.y % 65))}%` : '64%', height: '100%', background: '#16a34a' }} />
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ width: '12px', fontSize: '9px', color: '#2563eb', fontWeight: 700 }}>B</span>
                <div style={{ flex: 1, height: '4px', background: '#f1f5f9', borderRadius: '2px', overflow: 'hidden' }}>
                  <div style={{ width: coords ? `${Math.min(95, 35 + ((coords.x + coords.y) % 55))}%` : '42%', height: '100%', background: '#2563eb' }} />
                </div>
              </div>
            </div>
          </div>

          {/* Quick Metrics */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px', fontSize: '10px' }}>
            <div>
              <div style={{ color: 'var(--text-muted)', fontSize: '9px' }}>DATUM</div>
              <div style={{ color: 'var(--accent-amber)', fontWeight: 700 }}>WGS-84 / EPSG:4326</div>
            </div>

            <div>
              <div style={{ color: 'var(--text-muted)', fontSize: '9px' }}>GSD RESOLUTION</div>
              <div style={{ color: 'var(--accent-emerald)', fontWeight: 700 }}>0.5m / pixel</div>
            </div>

            <div>
              <div style={{ color: 'var(--text-muted)', fontSize: '9px' }}>SOLAR ZENITH</div>
              <div style={{ color: 'var(--text-pure)', fontWeight: 600 }}>41.8° · Az 138.4°</div>
            </div>

            <div>
              <div style={{ color: 'var(--text-muted)', fontSize: '9px' }}>RADIOMETRIC DEPTH</div>
              <div style={{ color: 'var(--text-pure)', fontWeight: 600 }}>12-bit (4,096 DN)</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
