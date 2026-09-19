'use client';

import React, { useState } from 'react';
import { EvidencePayload } from '../types/satquery';
import { ImageLightboxModal } from './ImageLightboxModal';

interface EvidenceVisualizerProps {
  evidence: EvidencePayload | null;
  isLoading?: boolean;
}

export const EvidenceVisualizer: React.FC<EvidenceVisualizerProps> = ({ evidence, isLoading }) => {
  const [modalImage, setModalImage] = useState<{ src: string; title: string } | null>(null);

  const isSingle = evidence?.is_single_image !== false;

  const slots = [
    {
      id: 'slot1',
      title: 'SLOT 01: SENSOR STREAM',
      badge: 'OPTICAL T1',
      badgeBg: 'rgba(194, 109, 46, 0.1)',
      badgeColor: '#c26d2e',
      data: evidence?.slot1_original,
      desc: 'Base spectral ingestion channel',
    },
    {
      id: 'slot2',
      title: isSingle ? 'SLOT 02: ATTENTION SALIENCY' : 'SLOT 02: ATTENTION / SENSORY DIFF',
      badge: isSingle ? 'NEURAL SALIENCY' : 'HEATMAP DELTA',
      badgeBg: 'rgba(217, 119, 6, 0.1)',
      badgeColor: '#d97706',
      data: evidence?.slot2_attention_or_diff,
      desc: isSingle ? 'Multi-scale spatial attention gradient' : 'Attention saliency & pixel difference',
    },
    {
      id: 'slot3',
      title: isSingle ? 'SLOT 03: TARGET RETICLES' : 'SLOT 03: TARGET RETICLE / SAR',
      badge: isSingle ? 'TARGET RETICLES' : 'BBOX / SAR',
      badgeBg: 'rgba(27, 106, 72, 0.1)',
      badgeColor: '#1b6a48',
      data: evidence?.slot3_reticle_or_sar,
      desc: isSingle ? 'Precision tactical corner reticles' : 'Grounding coordinates & backscatter',
    },
    {
      id: 'slot4',
      title: isSingle ? 'SLOT 04: CIR SPECTRAL SYNTHESIS' : 'SLOT 04: TEMPORAL T2 / FUSION',
      badge: isSingle ? 'CIR FALSE-COLOR' : 'AFTER PASS',
      badgeBg: isSingle ? 'rgba(16, 185, 129, 0.1)' : 'rgba(190, 18, 60, 0.1)',
      badgeColor: isSingle ? '#059669' : '#be123c',
      data: evidence?.slot4_after,
      desc: isSingle ? 'NASA / USGS Infrared False-Color Composite' : 'Post-event secondary sensory frame',
    },
  ];

  return (
    <>
      <div className="panel-card" style={{ marginBottom: '18px' }}>
        <div className="panel-header">
          <div className="panel-title">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="3" width="7" height="7" />
              <rect x="14" y="3" width="7" height="7" />
              <rect x="14" y="14" width="7" height="7" />
              <rect x="3" y="14" width="7" height="7" />
            </svg>
            <span>MULTI-SPECTRAL EVIDENCE MATRIX</span>
          </div>
          <span className="panel-title-tag">4-SLOT DECODER</span>
        </div>

        <div className="evidence-matrix-grid">
          {slots.map((slot) => (
            <div key={slot.id} className="evidence-cell">
              <div className="cell-header">
                <span className="cell-title">{slot.title}</span>
                <span
                  className="cell-badge"
                  style={{
                    background: slot.badgeBg,
                    color: slot.badgeColor,
                    border: `1px solid ${slot.badgeColor}44`,
                  }}
                >
                  {slot.badge}
                </span>
              </div>

              <div className="cell-canvas">
                {isLoading ? (
                  <div className="cell-empty-state">
                    <div className="pulse-dot" style={{ background: slot.badgeColor }} />
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '10.5px', color: slot.badgeColor }}>
                      DECODING STREAM...
                    </span>
                  </div>
                ) : slot.data ? (
                  <img
                    src={slot.data}
                    alt={slot.title}
                    className="cell-img"
                    onClick={() => setModalImage({ src: slot.data!, title: slot.title })}
                    title="Click to view full-resolution frame"
                  />
                ) : (
                  <div className="cell-empty-state">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" style={{ opacity: 0.35 }}>
                      <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
                      <circle cx="8.5" cy="8.5" r="1.5" />
                      <polyline points="21 15 16 10 5 21" />
                    </svg>
                    <span style={{ fontSize: '10.5px', opacity: 0.5 }}>No Stream Decoded</span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Lightbox / Zoom Modal with Download */}
      {modalImage && (
        <ImageLightboxModal
          isOpen={Boolean(modalImage)}
          onClose={() => setModalImage(null)}
          imageSrc={modalImage.src}
          title={modalImage.title}
        />
      )}
    </>
  );
};
