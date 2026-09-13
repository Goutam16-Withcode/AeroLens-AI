'use client';

import React, { useState } from 'react';
import { DetectedObject } from '../types/satquery';
import { ImageLightboxModal } from './ImageLightboxModal';

interface DetectedObjectsDeckProps {
  objects: DetectedObject[];
  annotatedImage: string | null;
  isLoading?: boolean;
}

export const DetectedObjectsDeck: React.FC<DetectedObjectsDeckProps> = ({
  objects,
  annotatedImage,
  isLoading,
}) => {
  const [isLightboxOpen, setIsLightboxOpen] = useState(false);
  const [filterCategory, setFilterCategory] = useState<string>('all');

  // Compute category counts
  const categoryCounts: Record<string, number> = {};
  objects.forEach((obj) => {
    const cat = obj.category || obj.label || 'Target';
    categoryCounts[cat] = (categoryCounts[cat] || 0) + 1;
  });

  const categories = Object.keys(categoryCounts);

  const filteredObjects =
    filterCategory === 'all'
      ? objects
      : objects.filter((o) => (o.category || o.label || '').toLowerCase() === filterCategory.toLowerCase());

  const getQuadrant = (xmin: number, ymin: number, xmax: number, ymax: number): string => {
    const cx = (xmin + xmax) / 2;
    const cy = (ymin + ymax) / 2;
    if (cx >= 0.4 && cx <= 0.6 && cy >= 0.4 && cy <= 0.6) return 'CENTER';
    const ns = cy < 0.5 ? 'NORTH' : 'SOUTH';
    const ew = cx < 0.5 ? 'WEST' : 'EAST';
    return `${ns}-${ew}`;
  };

  return (
    <>
      <div className="panel-card" style={{ marginBottom: '18px' }}>
        {/* Panel Header */}
        <div className="panel-header">
          <div className="panel-title">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M4 8V4m0 0h4M4 4l5 5m11-5h-4m4 0v4m0-4l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
            </svg>
            <span>MULTI-CLASS OBJECT GROUNDING & DETECTION TELEMETRY</span>
          </div>
          <span className="panel-title-tag">
            {objects.length > 0 ? `${objects.length} TARGETS IDENTIFIED` : 'SUB-METRIC BBOX'}
          </span>
        </div>

        {/* Content Body */}
        {isLoading ? (
          <div
            style={{
              padding: '36px',
              textAlign: 'center',
              fontFamily: 'var(--font-mono)',
              fontSize: '11.5px',
              color: 'var(--accent-amber)',
            }}
          >
            <div className="pulse-dot" style={{ margin: '0 auto 12px auto' }} />
            <span>LOCALIZING AIRBORNE, MARITIME & INFRASTRUCTURE TARGETS...</span>
          </div>
        ) : objects.length === 0 ? (
          <div
            style={{
              padding: '32px 20px',
              textAlign: 'center',
              background: '#faf6f0',
              borderRadius: '8px',
              border: '1px dashed var(--border-subtle)',
              fontFamily: 'var(--font-mono)',
              color: 'var(--text-muted)',
              fontSize: '11.5px',
            }}
          >
            <div style={{ marginBottom: '8px', color: 'var(--accent-amber)' }}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75">
                <circle cx="12" cy="12" r="10" />
                <line x1="22" y1="12" x2="18" y2="12" />
                <line x1="6" y1="12" x2="2" y2="12" />
                <line x1="12" y1="6" x2="12" y2="2" />
                <line x1="12" y1="22" x2="12" y2="18" />
              </svg>
            </div>
            <div>NO TARGET OBJECTS CURRENTLY LOCALIZED</div>
            <div style={{ fontSize: '10.5px', marginTop: '4px' }}>
              Submit an image with a query like <em>"Detect all airplanes, storage tanks, and buildings with bounding boxes"</em>
            </div>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {/* Top Stat Summary & Quick Actions */}
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                flexWrap: 'wrap',
                gap: '12px',
                padding: '12px 14px',
                background: '#f8f4ec',
                borderRadius: '8px',
                border: '1px solid var(--border-subtle)',
              }}
            >
              {/* Category Filter Pills */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', fontWeight: 700, color: 'var(--text-secondary)' }}>
                  FILTER:
                </span>
                <button
                  onClick={() => setFilterCategory('all')}
                  style={{
                    padding: '3px 10px',
                    borderRadius: '4px',
                    border: `1px solid ${filterCategory === 'all' ? 'var(--accent-amber)' : 'var(--border-subtle)'}`,
                    background: filterCategory === 'all' ? 'var(--accent-amber)' : '#ffffff',
                    color: filterCategory === 'all' ? '#ffffff' : 'var(--text-secondary)',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '10.5px',
                    fontWeight: 700,
                    cursor: 'pointer',
                  }}
                >
                  ALL ({objects.length})
                </button>
                {categories.map((cat) => (
                  <button
                    key={cat}
                    onClick={() => setFilterCategory(cat)}
                    style={{
                      padding: '3px 10px',
                      borderRadius: '4px',
                      border: `1px solid ${filterCategory === cat ? 'var(--accent-amber)' : 'var(--border-subtle)'}`,
                      background: filterCategory === cat ? 'var(--accent-amber)' : '#ffffff',
                      color: filterCategory === cat ? '#ffffff' : 'var(--text-secondary)',
                      fontFamily: 'var(--font-mono)',
                      fontSize: '10.5px',
                      fontWeight: 700,
                      cursor: 'pointer',
                    }}
                  >
                    {cat.toUpperCase()} ({categoryCounts[cat]})
                  </button>
                ))}
              </div>

              {/* Expand & Download Button */}
              {annotatedImage && (
                <button
                  onClick={() => setIsLightboxOpen(true)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    padding: '6px 14px',
                    background: 'var(--accent-amber)',
                    color: '#ffffff',
                    border: 'none',
                    borderRadius: '6px',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '11px',
                    fontWeight: 700,
                    cursor: 'pointer',
                    boxShadow: '0 2px 6px rgba(194, 109, 46, 0.25)',
                  }}
                >
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7" />
                  </svg>
                  <span>EXPAND & DOWNLOAD TARGET RETICLE</span>
                </button>
              )}
            </div>

            {/* Grid Layout: Visual Reticle Preview (Left) + Detailed Coordinate Cards (Right) */}
            <div style={{ display: 'grid', gridTemplateColumns: 'minmax(280px, 340px) 1fr', gap: '16px', alignItems: 'start' }}>
              {/* Target Reticle Thumbnail Preview */}
              {annotatedImage && (
                <div
                  style={{
                    background: '#1c1917',
                    borderRadius: '8px',
                    border: '1px solid var(--border-light)',
                    overflow: 'hidden',
                    position: 'relative',
                    boxShadow: '0 4px 14px rgba(0,0,0,0.1)',
                  }}
                >
                  <div
                    style={{
                      padding: '8px 12px',
                      background: 'rgba(28, 25, 23, 0.95)',
                      borderBottom: '1px solid rgba(255,255,255,0.1)',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      fontFamily: 'var(--font-hud)',
                      fontSize: '10.5px',
                      color: 'var(--accent-amber)',
                    }}
                  >
                    <span>ANNOTATED RETICLE OVERLAY</span>
                    <span style={{ color: '#ffffff', opacity: 0.7, fontSize: '9.5px' }}>CLICK TO ZOOM</span>
                  </div>

                  <div
                    style={{
                      cursor: 'zoom-in',
                      position: 'relative',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      background: '#0a0a0a',
                      minHeight: '220px',
                    }}
                    onClick={() => setIsLightboxOpen(true)}
                    title="Click to view full-resolution frame with zoom and download"
                  >
                    <img
                      src={annotatedImage}
                      alt="Detected Objects Reticle"
                      style={{ width: '100%', height: 'auto', maxHeight: '280px', objectFit: 'contain' }}
                    />
                  </div>

                  <div
                    style={{
                      padding: '6px 12px',
                      background: 'rgba(28, 25, 23, 0.95)',
                      borderTop: '1px solid rgba(255,255,255,0.08)',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      fontSize: '10px',
                      fontFamily: 'var(--font-mono)',
                      color: 'rgba(255,255,255,0.6)',
                    }}
                  >
                    <span>{objects.length} OBJECTS MARKED</span>
                    <span
                      onClick={() => setIsLightboxOpen(true)}
                      style={{ color: 'var(--accent-amber)', cursor: 'pointer', fontWeight: 600 }}
                    >
                      DOWNLOAD .PNG ⤓
                    </span>
                  </div>
                </div>
              )}

              {/* Localized Objects Table & Coordinates */}
              <div
                style={{
                  background: '#ffffff',
                  borderRadius: '8px',
                  border: '1px solid var(--border-subtle)',
                  overflowX: 'auto',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.03)',
                }}
              >
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '11px', fontFamily: 'var(--font-mono)' }}>
                  <thead>
                    <tr style={{ background: '#f5f0e8', borderBottom: '1px solid var(--border-subtle)', textAlign: 'left' }}>
                      <th style={{ padding: '8px 12px', fontWeight: 700, color: 'var(--text-secondary)' }}>ID</th>
                      <th style={{ padding: '8px 12px', fontWeight: 700, color: 'var(--text-secondary)' }}>CLASS</th>
                      <th style={{ padding: '8px 12px', fontWeight: 700, color: 'var(--text-secondary)' }}>CONFIDENCE</th>
                      <th style={{ padding: '8px 12px', fontWeight: 700, color: 'var(--text-secondary)' }}>QUADRANT</th>
                      <th style={{ padding: '8px 12px', fontWeight: 700, color: 'var(--text-secondary)' }}>BOUNDING BOX [YMIN, XMIN, YMAX, XMAX]</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredObjects.map((obj, idx) => {
                      const color = obj.color || '#c26d2e';
                      const quad = getQuadrant(obj.xmin, obj.ymin, obj.xmax, obj.ymax);
                      const pct = Math.round((obj.confidence || 0.9) * 100);

                      return (
                        <tr
                          key={obj.id || idx}
                          style={{
                            borderBottom: '1px solid var(--border-subtle)',
                            transition: 'background 0.15s ease',
                          }}
                        >
                          <td style={{ padding: '8px 12px', fontWeight: 700, color: 'var(--text-muted)' }}>
                            #{idx + 1}
                          </td>
                          <td style={{ padding: '8px 12px' }}>
                            <span
                              style={{
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: '5px',
                                padding: '2px 8px',
                                borderRadius: '4px',
                                background: `${color}18`,
                                color: color,
                                border: `1px solid ${color}44`,
                                fontWeight: 700,
                              }}
                            >
                              <span
                                style={{
                                  width: '6px',
                                  height: '6px',
                                  borderRadius: '50%',
                                  background: color,
                                }}
                              />
                              {(obj.category || obj.label).toUpperCase()}
                            </span>
                          </td>
                          <td style={{ padding: '8px 12px' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                              <div
                                style={{
                                  width: '50px',
                                  height: '5px',
                                  background: 'rgba(0,0,0,0.08)',
                                  borderRadius: '3px',
                                  overflow: 'hidden',
                                }}
                              >
                                <div
                                  style={{
                                    width: `${pct}%`,
                                    height: '100%',
                                    background: pct >= 85 ? '#10b981' : pct >= 70 ? '#f59e0b' : '#f43f5e',
                                  }}
                                />
                              </div>
                              <span style={{ fontWeight: 600 }}>{pct}%</span>
                            </div>
                          </td>
                          <td style={{ padding: '8px 12px', color: 'var(--text-secondary)' }}>
                            {quad}
                          </td>
                          <td style={{ padding: '8px 12px', color: 'var(--accent-amber)', fontWeight: 600 }}>
                            [{obj.ymin.toFixed(4)}, {obj.xmin.toFixed(4)}, {obj.ymax.toFixed(4)}, {obj.xmax.toFixed(4)}]
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Lightbox Modal with Zoom & Download */}
      {annotatedImage && (
        <ImageLightboxModal
          isOpen={isLightboxOpen}
          onClose={() => setIsLightboxOpen(false)}
          imageSrc={annotatedImage}
          title="MULTI-CLASS OBJECT GROUNDING & TARGET RETICLES"
          subtitle={`${objects.length} verified bounding boxes localized across spectral channels`}
        />
      )}
    </>
  );
};
