'use client';

import React, { useEffect, useState } from 'react';

export const SatelliteOrbitRadar: React.FC = () => {
  const [azimuth, setAzimuth] = useState(134.5);
  const [elevation, setElevation] = useState(48.2);
  const [doppler, setDoppler] = useState(+18.4);
  const [altitude, setAltitude] = useState(542.1);

  useEffect(() => {
    const timer = setInterval(() => {
      setAzimuth((prev) => (prev + 0.15) % 360);
      setDoppler((prev) => (prev > -20 ? prev - 0.05 : 20));
      setAltitude((prev) => 542.0 + Math.sin(Date.now() / 3000) * 1.5);
      setElevation((prev) => Math.max(10, Math.min(85, prev + Math.sin(Date.now() / 2000) * 0.2)));
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="panel-card" style={{ marginBottom: '18px' }}>
      <div className="panel-header">
        <div className="panel-title">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
          </svg>
          <span>SPACECRAFT ORBITAL RADAR & PASS TELEMETRY</span>
        </div>
        <span className="panel-title-tag">LEO PASS #881</span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px', fontSize: '11px', fontFamily: 'var(--font-mono)' }}>
        <div style={{ background: '#f8f4ec', border: '1px solid var(--border-subtle)', padding: '10px 12px', borderRadius: '6px' }}>
          <div style={{ color: 'var(--text-muted)', fontSize: '9.5px' }}>ORBIT ALTITUDE</div>
          <div style={{ color: 'var(--accent-amber)', fontSize: '13px', fontWeight: 700, marginTop: '2px' }}>
            {altitude.toFixed(1)} KM
          </div>
          <div style={{ color: 'var(--accent-emerald)', fontSize: '9.5px', marginTop: '2px', fontWeight: 600 }}>7.62 KM/S (LEO)</div>
        </div>

        <div style={{ background: '#f8f4ec', border: '1px solid var(--border-subtle)', padding: '10px 12px', borderRadius: '6px' }}>
          <div style={{ color: 'var(--text-muted)', fontSize: '9.5px' }}>AZIMUTH / ELEVATION</div>
          <div style={{ color: 'var(--accent-emerald)', fontSize: '13px', fontWeight: 700, marginTop: '2px' }}>
            {azimuth.toFixed(1)}° · {elevation.toFixed(1)}°
          </div>
          <div style={{ color: 'var(--text-muted)', fontSize: '9.5px', marginTop: '2px' }}>TRACKING ACQUIRED</div>
        </div>

        <div style={{ background: '#f8f4ec', border: '1px solid var(--border-subtle)', padding: '10px 12px', borderRadius: '6px' }}>
          <div style={{ color: 'var(--text-muted)', fontSize: '9.5px' }}>DOPPLER SHIFT</div>
          <div style={{ color: doppler > 0 ? '#0284c7' : '#be123c', fontSize: '13px', fontWeight: 700, marginTop: '2px' }}>
            {doppler > 0 ? `+${doppler.toFixed(2)}` : doppler.toFixed(2)} kHz
          </div>
          <div style={{ color: 'var(--text-muted)', fontSize: '9.5px', marginTop: '2px' }}>X-BAND (8.2 GHz)</div>
        </div>

        <div style={{ background: '#f8f4ec', border: '1px solid var(--border-subtle)', padding: '10px 12px', borderRadius: '6px' }}>
          <div style={{ color: 'var(--text-muted)', fontSize: '9.5px' }}>NEXT PASS (AOS)</div>
          <div style={{ color: 'var(--accent-amber)', fontSize: '13px', fontWeight: 700, marginTop: '2px' }}>
            14M 22S
          </div>
          <div style={{ color: 'var(--accent-emerald)', fontSize: '9.5px', marginTop: '2px', fontWeight: 600 }}>SUN-SYNCHRONOUS</div>
        </div>
      </div>
    </div>
  );
};
