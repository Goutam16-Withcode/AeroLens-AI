'use client';

import React from 'react';

interface TacticalUplinkBarProps {
  query: string;
  setQuery: (q: string) => void;
  onTransmit: () => void;
  isLoading: boolean;
}

export const TacticalUplinkBar: React.FC<TacticalUplinkBarProps> = ({
  query,
  setQuery,
  onTransmit,
  isLoading,
}) => {
  const chips = [
    {
      id: 'vqa',
      label: 'VQA Scene Inquiry',
      prompt: 'Is a residential building present in this scene?',
      icon: (
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="11" cy="11" r="8" />
          <line x1="21" y1="21" x2="16.65" y2="16.65" />
        </svg>
      ),
    },
    {
      id: 'caption',
      label: 'Land-Cover Caption',
      prompt: 'Describe the land cover, major objects, and overall scene composition in this remote sensing image.',
      icon: (
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <polygon points="12 2 2 7 12 12 22 7 12 2" />
          <polyline points="2 17 12 22 22 17" />
          <polyline points="2 12 12 17 22 12" />
        </svg>
      ),
    },
    {
      id: 'grounding',
      label: 'Target Grounding',
      prompt: 'Locate and highlight all parked airplanes with a bounding box.',
      icon: (
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M4 8V4m0 0h4M4 4l5 5m11-5h-4m4 0v4m0-4l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
        </svg>
      ),
    },
    {
      id: 'bitemporal',
      label: 'Bi-Temporal Delta',
      prompt: 'What structural and land-cover changes occurred between these two observation dates?',
      icon: (
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="10" />
          <polyline points="12 6 12 12 14 14" />
        </svg>
      ),
    },
    {
      id: 'sar_fusion',
      label: 'Optical-SAR Fusion',
      prompt: 'Use both the optical and SAR images together to identify water boundaries and built-up areas beneath clouds.',
      icon: (
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
        </svg>
      ),
    },
  ];

  return (
    <div className="panel-card">
      <div className="panel-header">
        <div className="panel-title">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="4 17 10 11 4 5" />
            <line x1="12" y1="19" x2="20" y2="19" />
          </svg>
          <span>MISSION OBJECTIVE UPLINK</span>
        </div>
        <span className="panel-title-tag">TOOL PRESETS</span>
      </div>

      <div className="preset-chips-container">
        {chips.map((chip) => (
          <button
            key={chip.id}
            className={`preset-chip ${query === chip.prompt ? 'active-chip' : ''}`}
            onClick={() => setQuery(chip.prompt)}
          >
            {chip.icon}
            <span>{chip.label}</span>
          </button>
        ))}
      </div>

      <div className="query-box-wrap">
        <textarea
          className="query-input"
          placeholder="Enter geospatial mission inquiry, prompt, or target coordinates..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => {
            if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
              onTransmit();
            }
          }}
          rows={3}
        />
        <div
          style={{
            position: 'absolute',
            bottom: '8px',
            right: '12px',
            fontSize: '10px',
            fontFamily: 'var(--font-mono)',
            color: 'var(--text-muted)',
            pointerEvents: 'none',
          }}
        >
          Ctrl + Enter to Transmit
        </div>
      </div>

      <button
        className="btn-transmit"
        onClick={onTransmit}
        disabled={isLoading || !query.trim()}
      >
        {isLoading ? (
          <>
            <div className="pulse-dot" style={{ background: '#080c14' }} />
            <span>ORBITAL REASONING IN PROGRESS...</span>
          </>
        ) : (
          <>
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
            <span>TRANSMIT MISSION UPLINK</span>
          </>
        )}
      </button>
    </div>
  );
};
