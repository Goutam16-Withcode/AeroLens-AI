'use client';

import React from 'react';

export interface PresetChip {
  id: string;
  label: string;
  prompt: string;
  badge: string;
  modalityA?: string;
  modalityB?: string;
  reqSecondImage?: boolean;
  icon: React.ReactNode;
}

interface TacticalUplinkBarProps {
  query: string;
  setQuery: (q: string) => void;
  onTransmit: () => void;
  isLoading: boolean;
  onSelectPreset?: (presetId: string, prompt: string) => void;
}

export const TacticalUplinkBar: React.FC<TacticalUplinkBarProps> = ({
  query,
  setQuery,
  onTransmit,
  isLoading,
  onSelectPreset,
}) => {
  const chips: PresetChip[] = [
    {
      id: 'vqa',
      label: 'VQA Scene Inquiry',
      badge: '1x OPTICAL',
      prompt: 'Is a residential building present in this scene?',
      modalityA: 'Optical',
      reqSecondImage: false,
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
      badge: '1x SCENE',
      prompt: 'Describe the land cover, major objects, and overall scene composition in this remote sensing image.',
      modalityA: 'Optical',
      reqSecondImage: false,
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
      badge: 'RETICLE',
      prompt: 'Locate and highlight all parked airplanes with a bounding box.',
      modalityA: 'Optical',
      reqSecondImage: false,
      icon: (
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M4 8V4m0 0h4M4 4l5 5m11-5h-4m4 0v4m0-4l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
        </svg>
      ),
    },
    {
      id: 'multi_detect',
      label: 'Multi-Object Detection',
      badge: 'MULTI-OBJ',
      prompt: 'Detect and identify all different objects in this image with high-accuracy bounding boxes and labels.',
      modalityA: 'Optical',
      reqSecondImage: false,
      icon: (
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <rect x="3" y="3" width="7" height="7" rx="1" />
          <rect x="14" y="3" width="7" height="7" rx="1" />
          <rect x="14" y="14" width="7" height="7" rx="1" />
          <rect x="3" y="14" width="7" height="7" rx="1" />
        </svg>
      ),
    },
    {
      id: 'bitemporal',
      label: 'Bi-Temporal Delta',
      badge: '2x TEMPORAL',
      prompt: 'What structural and land-cover changes occurred between these two observation dates?',
      modalityA: 'Optical',
      modalityB: 'Optical',
      reqSecondImage: true,
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
      badge: 'S2+S1 DUAL',
      prompt: 'Use both the optical and SAR images together to identify water boundaries beneath cloud cover.',
      modalityA: 'Optical',
      modalityB: 'SAR',
      reqSecondImage: true,
      icon: (
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
        </svg>
      ),
    },
    {
      id: 'wildfire',
      label: 'Wildfire Burn Scar',
      badge: 'DISASTER',
      prompt: 'Identify and evaluate burned vegetation, fire perimeters, and active burn scars in this remote sensing swath.',
      modalityA: 'Optical',
      reqSecondImage: false,
      icon: (
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z" />
        </svg>
      ),
    },
    {
      id: 'maritime',
      label: 'Maritime Harbor Fleet',
      badge: 'MARITIME',
      prompt: 'Detect and count all naval vessels, cargo ships, docks, and piers in this coastal maritime corridor.',
      modalityA: 'Optical',
      reqSecondImage: false,
      icon: (
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M2 20a2.4 2.4 0 0 0 2 1 2.4 2.4 0 0 0 2-1 2.4 2.4 0 0 1 2-1 2.4 2.4 0 0 1 2 1 2.4 2.4 0 0 0 2 1 2.4 2.4 0 0 0 2-1 2.4 2.4 0 0 1 2-1 2.4 2.4 0 0 1 2 1 2.4 2.4 0 0 0 2 1 2.4 2.4 0 0 0 2-1" />
          <path d="M4 18L3 12h18l-1 6" />
          <path d="M12 4v8" />
          <path d="M8 8l4-4 4 4" />
        </svg>
      ),
    },
  ];

  const [isListening, setIsListening] = React.useState<boolean>(false);

  const toggleVoiceInput = () => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert('Speech Recognition API is not supported in this browser. Please use Chrome, Edge, or Safari.');
      return;
    }

    if (isListening) {
      setIsListening(false);
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = 'en-US';

      recognition.onstart = () => {
        setIsListening(true);
      };

      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        if (transcript) {
          setQuery(transcript);
        }
      };

      recognition.onerror = () => {
        setIsListening(false);
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognition.start();
    } catch {
      setIsListening(false);
    }
  };

  const handleChipClick = (chip: PresetChip) => {
    setQuery(chip.prompt);
    if (onSelectPreset) {
      onSelectPreset(chip.id, chip.prompt);
    }
  };

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
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            onClick={toggleVoiceInput}
            title={isListening ? 'Stop listening' : 'Speak query hands-free via microphone'}
            style={{
              padding: '3px 8px',
              background: isListening ? '#fef2f2' : '#ffffff',
              border: `1px solid ${isListening ? '#ef4444' : 'var(--border-subtle)'}`,
              color: isListening ? '#ef4444' : 'var(--text-secondary)',
              borderRadius: '4px',
              fontFamily: 'var(--font-mono)',
              fontSize: '10px',
              fontWeight: 700,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              transition: 'all 0.15s ease',
            }}
          >
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
              <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
              <line x1="12" y1="19" x2="12" y2="23" />
              <line x1="8" y1="23" x2="16" y2="23" />
            </svg>
            <span>{isListening ? '● LISTENING...' : 'VOICE MIC'}</span>
          </button>
          <span className="panel-title-tag">INTELLIGENT TOOL PRESETS</span>
        </div>
      </div>

      <div className="preset-chips-container">
        {chips.map((chip) => {
          const isActive = query === chip.prompt;
          return (
            <button
              key={chip.id}
              className={`preset-chip ${isActive ? 'active-chip' : ''}`}
              onClick={() => handleChipClick(chip)}
              title={chip.prompt}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                padding: '6px 10px',
              }}
            >
              {chip.icon}
              <span>{chip.label}</span>
              <span
                style={{
                  fontSize: '8.5px',
                  fontWeight: 800,
                  padding: '1px 4px',
                  borderRadius: '3px',
                  background: isActive ? 'var(--accent-amber)' : 'rgba(0,0,0,0.06)',
                  color: isActive ? '#ffffff' : 'var(--text-muted)',
                  letterSpacing: '0.5px',
                }}
              >
                {chip.badge}
              </span>
            </button>
          );
        })}
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
            <div className="pulse-dot" style={{ background: '#ffffff' }} />
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
