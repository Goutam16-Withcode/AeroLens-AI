'use client';

import React from 'react';
import { AnalysisResponse } from '../types/satquery';

interface MissionBriefingModalProps {
  isOpen: boolean;
  onClose: () => void;
  query: string;
  response: AnalysisResponse | null;
}

export const MissionBriefingModal: React.FC<MissionBriefingModalProps> = ({
  isOpen,
  onClose,
  query,
  response,
}) => {
  if (!isOpen || !response) return null;

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="image-modal-backdrop" onClick={onClose}>
      <div
        className="image-modal-content"
        style={{
          maxWidth: '800px',
          width: '90vw',
          maxHeight: '88vh',
          overflowY: 'auto',
          background: '#fdfcf9',
          border: '1.5px solid var(--accent-amber)',
          borderRadius: '12px',
          padding: '28px 32px',
          boxShadow: '0 20px 60px rgba(41, 37, 36, 0.25)',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <button className="modal-close-btn" onClick={onClose}>
          ✕
        </button>

        {/* Report Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', borderBottom: '2px solid var(--border-subtle)', paddingBottom: '16px', marginBottom: '20px' }}>
          <div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--accent-amber)', letterSpacing: '0.12em', fontWeight: 700 }}>
              NATIONAL REMOTE SENSING & GEOSPATIAL INTELLIGENCE // AEROLENS AI
            </div>
            <h2 style={{ fontFamily: 'var(--font-hud)', fontSize: '22px', fontWeight: 800, color: 'var(--text-pure)', margin: '4px 0' }}>
              ORBITAL MISSION INTELLIGENCE BRIEFING
            </h2>
            <div style={{ fontSize: '11.5px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
              PASS REF: SQ-EO-2026-X9 · TIMESTAMP: {new Date().toUTCString()}
            </div>
          </div>

          <div style={{ textAlign: 'right' }}>
            <span style={{ background: 'var(--accent-amber-subtle)', border: '1px solid var(--accent-amber)', color: 'var(--accent-amber)', padding: '4px 10px', borderRadius: '4px', fontFamily: 'var(--font-mono)', fontSize: '10.5px', fontWeight: 700 }}>
              UNCLASSIFIED // SCIENTIFIC
            </span>
          </div>
        </div>

        {/* Tactical Query */}
        <div style={{ background: '#f5f0e8', border: '1px solid var(--border-subtle)', borderRadius: '6px', padding: '12px 16px', marginBottom: '18px' }}>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>
            MISSION INQUIRY & TARGET OBJECTIVE
          </div>
          <div style={{ fontSize: '14px', color: 'var(--text-pure)', fontWeight: 600, marginTop: '2px' }}>
            &ldquo;{query}&rdquo;
          </div>
        </div>

        {/* VLM Assessment */}
        <div style={{ marginBottom: '20px' }}>
          <div style={{ fontFamily: 'var(--font-hud)', fontSize: '13px', fontWeight: 700, color: 'var(--accent-amber)', marginBottom: '8px', textTransform: 'uppercase' }}>
            1.0 AUTONOMOUS VLM INTELLIGENCE SYNTHESIS
          </div>
          <div style={{ background: '#f8f4ec', borderLeft: '3.5px solid var(--accent-amber)', padding: '14px 18px', borderRadius: '4px', fontSize: '13.5px', lineHeight: '1.7', color: 'var(--text-main)', whiteSpace: 'pre-wrap' }}>
            {response.answer}
          </div>
        </div>

        {/* Evidence Frame Snapshot Grid */}
        <div style={{ marginBottom: '20px' }}>
          <div style={{ fontFamily: 'var(--font-hud)', fontSize: '13px', fontWeight: 700, color: 'var(--accent-amber)', marginBottom: '10px', textTransform: 'uppercase' }}>
            2.0 MULTI-SPECTRAL DECODED EVIDENCE MATRIX
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px' }}>
            {response.evidence.slot1_original && (
              <div style={{ background: '#f0eae0', borderRadius: '6px', overflow: 'hidden', border: '1px solid var(--border-subtle)' }}>
                <img src={response.evidence.slot1_original} alt="Slot 1" style={{ width: '100%', height: '90px', objectFit: 'contain' }} />
                <div style={{ padding: '4px 6px', fontSize: '9px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', fontWeight: 600 }}>SLOT 01: OPTICAL</div>
              </div>
            )}
            {response.evidence.slot2_attention_or_diff && (
              <div style={{ background: '#f0eae0', borderRadius: '6px', overflow: 'hidden', border: '1px solid var(--border-subtle)' }}>
                <img src={response.evidence.slot2_attention_or_diff} alt="Slot 2" style={{ width: '100%', height: '90px', objectFit: 'contain' }} />
                <div style={{ padding: '4px 6px', fontSize: '9px', fontFamily: 'var(--font-mono)', color: 'var(--accent-amber)', fontWeight: 600 }}>SLOT 02: ATTN/DIFF</div>
              </div>
            )}
            {response.evidence.slot3_reticle_or_sar && (
              <div style={{ background: '#f0eae0', borderRadius: '6px', overflow: 'hidden', border: '1px solid var(--border-subtle)' }}>
                <img src={response.evidence.slot3_reticle_or_sar} alt="Slot 3" style={{ width: '100%', height: '90px', objectFit: 'contain' }} />
                <div style={{ padding: '4px 6px', fontSize: '9px', fontFamily: 'var(--font-mono)', color: 'var(--accent-emerald)', fontWeight: 600 }}>SLOT 03: RETICLE/SAR</div>
              </div>
            )}
            {response.evidence.slot4_after && (
              <div style={{ background: '#f0eae0', borderRadius: '6px', overflow: 'hidden', border: '1px solid var(--border-subtle)' }}>
                <img src={response.evidence.slot4_after} alt="Slot 4" style={{ width: '100%', height: '90px', objectFit: 'contain' }} />
                <div style={{ padding: '4px 6px', fontSize: '9px', fontFamily: 'var(--font-mono)', color: 'var(--accent-coral)', fontWeight: 600 }}>SLOT 04: T2 AFTER</div>
              </div>
            )}
          </div>
        </div>

        {/* Telemetry Footer */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid var(--border-subtle)', paddingTop: '16px', marginTop: '24px' }}>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-muted)' }}>
            CONFIDENCE: {Math.round((response.trace?.confidence || 0.9) * 100)}% · LATENCY: {response.trace?.elapsed_seconds.toFixed(2)}s
          </div>

          <button
            onClick={handlePrint}
            style={{
              padding: '9px 18px',
              background: 'var(--accent-amber)',
              border: 'none',
              borderRadius: '6px',
              color: '#ffffff',
              fontFamily: 'var(--font-hud)',
              fontSize: '12px',
              fontWeight: 700,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              boxShadow: '0 2px 8px rgba(194, 109, 46, 0.3)',
            }}
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="6 9 6 2 18 2 18 9" />
              <path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2" />
              <rect x="6" y="14" width="12" height="8" />
            </svg>
            <span>PRINT / EXPORT PDF BRIEFING</span>
          </button>
        </div>
      </div>
    </div>
  );
};
