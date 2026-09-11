'use client';

import React, { useState } from 'react';

interface GeospatialTelemetryHUDProps {
  imageSrc: string | null;
}

export const GeospatialTelemetryHUD: React.FC<GeospatialTelemetryHUDProps> = ({ imageSrc }) => {
  const [coords, setCoords] = useState<{ x: number; y: number; lat: string; lon: string } | null>(null);

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
        <span className="panel-title-tag">WGS84 SUB-METRIC HUD</span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 240px', gap: '14px' }}>
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
                  <div style={{ position: 'absolute', top: `${coords.y}px`, left: 0, right: 0, height: '1.5px', background: 'rgba(194, 109, 46, 0.8)', pointerEvents: 'none' }} />
                  <div style={{ position: 'absolute', left: `${coords.x}px`, top: 0, bottom: 0, width: '1.5px', background: 'rgba(194, 109, 46, 0.8)', pointerEvents: 'none' }} />
                  {/* Floating tooltip badge */}
                  <div
                    style={{
                      position: 'absolute',
                      top: `${Math.min(180, coords.y + 10)}px`,
                      left: `${Math.min(260, coords.x + 10)}px`,
                      background: 'rgba(255, 255, 255, 0.96)',
                      border: '1px solid var(--accent-amber)',
                      boxShadow: '0 4px 12px rgba(41, 37, 36, 0.12)',
                      padding: '5px 9px',
                      borderRadius: '4px',
                      fontFamily: 'var(--font-mono)',
                      fontSize: '10.5px',
                      fontWeight: 700,
                      color: 'var(--accent-amber)',
                      pointerEvents: 'none',
                    }}
                  >
                    <div>{coords.lat}, {coords.lon}</div>
                    <div style={{ color: 'var(--text-muted)', fontSize: '9.5px', fontWeight: 500 }}>Pixel: [{coords.x}, {coords.y}]</div>
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

        {/* Telemetry Metrics Sidebar */}
        <div style={{ background: '#f8f4ec', border: '1px solid var(--border-subtle)', borderRadius: '8px', padding: '12px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', fontSize: '11px', fontFamily: 'var(--font-mono)' }}>
          <div>
            <div style={{ color: 'var(--text-muted)', fontSize: '9.5px', marginBottom: '2px' }}>GEODETIC DATUM</div>
            <div style={{ color: 'var(--accent-amber)', fontWeight: 700 }}>WGS-84 / EPSG:4326</div>
          </div>

          <div>
            <div style={{ color: 'var(--text-muted)', fontSize: '9.5px', marginBottom: '2px' }}>GROUND RESOLUTION (GSD)</div>
            <div style={{ color: 'var(--accent-emerald)', fontWeight: 700 }}>0.5m / pixel (High-Res)</div>
          </div>

          <div>
            <div style={{ color: 'var(--text-muted)', fontSize: '9.5px', marginBottom: '2px' }}>SOLAR ZENITH / AZIMUTH</div>
            <div style={{ color: 'var(--text-pure)', fontWeight: 600 }}>41.8° · Az 138.4°</div>
          </div>

          <div>
            <div style={{ color: 'var(--text-muted)', fontSize: '9.5px', marginBottom: '2px' }}>RADIOMETRIC DEPTH</div>
            <div style={{ color: 'var(--text-pure)', fontWeight: 600 }}>12-bit (4,096 DN levels)</div>
          </div>
        </div>
      </div>
    </div>
  );
};
