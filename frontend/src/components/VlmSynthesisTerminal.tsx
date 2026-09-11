'use client';

import React, { useState } from 'react';

interface VlmSynthesisTerminalProps {
  answer: string | null;
  confidence?: number | null;
  isLoading?: boolean;
}

export const VlmSynthesisTerminal: React.FC<VlmSynthesisTerminalProps> = ({
  answer,
  confidence,
  isLoading,
}) => {
  const [copied, setCopied] = useState(false);
  const [speaking, setSpeaking] = useState(false);

  const handleCopy = () => {
    if (!answer) return;
    navigator.clipboard.writeText(answer);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleSpeak = () => {
    if (!answer) return;
    if (speaking) {
      window.speechSynthesis?.cancel();
      setSpeaking(false);
      return;
    }
    const utterance = new SpeechSynthesisUtterance(answer);
    utterance.rate = 1.05;
    utterance.onend = () => setSpeaking(false);
    window.speechSynthesis?.speak(utterance);
    setSpeaking(true);
  };

  const getConfidenceDetails = (conf: number | null | undefined) => {
    if (conf === null || conf === undefined) return null;
    const pct = Math.round(conf * 100);
    let color = 'var(--accent-emerald)';
    let level = 'HIGH';
    if (pct < 70) {
      color = 'var(--accent-coral)';
      level = 'LOW';
    } else if (pct < 85) {
      color = 'var(--accent-amber)';
      level = 'MODERATE';
    }
    return { pct, color, level };
  };

  const conf = getConfidenceDetails(confidence);

  return (
    <div className="panel-card" style={{ marginBottom: '18px' }}>
      <div className="panel-header">
        <div className="panel-title">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <polyline points="14 2 14 8 20 8" />
            <line x1="16" y1="13" x2="8" y2="13" />
            <line x1="16" y1="17" x2="8" y2="17" />
          </svg>
          <span>SYNTHESIZED INTELLIGENCE REPORT</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {conf && (
            <div
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '11px',
                fontWeight: 700,
                padding: '3px 9px',
                borderRadius: '4px',
                border: `1px solid ${conf.color}55`,
                background: '#ffffff',
                color: conf.color,
                display: 'flex',
                alignItems: 'center',
                gap: '5px',
                boxShadow: '0 1px 4px rgba(0,0,0,0.04)',
              }}
            >
              <div
                style={{
                  width: '6px',
                  height: '6px',
                  borderRadius: '50%',
                  background: conf.color,
                }}
              />
              <span>CONFIDENCE: {conf.pct}% ({conf.level})</span>
            </div>
          )}

          {answer && (
            <>
              <button
                onClick={handleSpeak}
                style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: '10.5px',
                  fontWeight: 600,
                  padding: '4px 9px',
                  background: speaking ? 'var(--accent-amber-subtle)' : '#f5f0e8',
                  border: `1px solid ${speaking ? 'var(--accent-amber)' : 'var(--border-subtle)'}`,
                  borderRadius: '4px',
                  color: speaking ? 'var(--accent-amber)' : 'var(--text-secondary)',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  transition: 'all 0.18s ease',
                }}
                title="Read aloud"
              >
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
                  <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07" />
                </svg>
                <span>{speaking ? 'STOP' : 'VOICE'}</span>
              </button>

              <button
                onClick={handleCopy}
                style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: '10.5px',
                  fontWeight: 600,
                  padding: '4px 10px',
                  background: copied ? 'var(--accent-emerald-subtle)' : '#f5f0e8',
                  border: `1px solid ${copied ? 'var(--accent-emerald)' : 'var(--border-subtle)'}`,
                  borderRadius: '4px',
                  color: copied ? 'var(--accent-emerald)' : 'var(--text-secondary)',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  transition: 'all 0.18s ease',
                }}
              >
                {copied ? (
                  <>
                    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                      <polyline points="20 6 9 17 4 12" />
                    </svg>
                    <span>COPIED</span>
                  </>
                ) : (
                  <>
                    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                      <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
                    </svg>
                    <span>COPY</span>
                  </>
                )}
              </button>
            </>
          )}
        </div>
      </div>

      <div className="intel-report-box">
        {isLoading ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--accent-amber)', padding: '6px 0' }}>
            <div className="pulse-dot" style={{ background: 'var(--accent-amber)' }} />
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '12px' }}>
              Qwen3-VL neural reasoning in progress... Synthesizing multi-spectral downlink...
            </span>
          </div>
        ) : answer ? (
          <div className="intel-text">{answer}</div>
        ) : (
          <div style={{ color: 'var(--text-muted)', fontSize: '12.5px', fontStyle: 'italic' }}>
            Telemetry standby. Ingest sensor swath and uplink mission inquiry to generate orbital intelligence.
          </div>
        )}
      </div>
    </div>
  );
};
