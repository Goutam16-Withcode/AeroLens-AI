'use client';

import React, { useState, useRef } from 'react';

interface BitemporalSwipeSliderProps {
  imageBefore: string | null;
  imageAfter: string | null;
  titleBefore?: string;
  titleAfter?: string;
}

export const BitemporalSwipeSlider: React.FC<BitemporalSwipeSliderProps> = ({
  imageBefore,
  imageAfter,
  titleBefore = 'T1: BEFORE OBSERVATION',
  titleAfter = 'T2: AFTER OBSERVATION',
}) => {
  const [sliderPos, setSliderPos] = useState<number>(50);
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const handleMove = (clientX: number) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = clientX - rect.left;
    const pos = Math.max(0, min(100, (x / rect.width) * 100));
    setSliderPos(pos);
  };

  const min = (a: number, b: number) => (a < b ? a : b);

  return (
    <div className="panel-card" style={{ marginBottom: '18px' }}>
      <div className="panel-header">
        <div className="panel-title">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="16 3 21 3 21 8" />
            <line x1="4" y1="20" x2="21" y2="3" />
            <polyline points="21 16 21 21 16 21" />
            <line x1="15" y1="15" x2="21" y2="21" />
            <line x1="4" y1="4" x2="9" y2="9" />
          </svg>
          <span>INTERACTIVE BI-TEMPORAL COMPARISON SLIDER</span>
        </div>
        <span className="panel-title-tag">DRAG TO REVEAL</span>
      </div>

      {imageBefore && imageAfter ? (
        <div
          ref={containerRef}
          style={{
            position: 'relative',
            width: '100%',
            height: '280px',
            borderRadius: '8px',
            overflow: 'hidden',
            cursor: 'ew-resize',
            userSelect: 'none',
            background: '#f0eae0',
            border: '1px solid var(--border-subtle)',
          }}
          onMouseDown={() => setIsDragging(true)}
          onMouseUp={() => setIsDragging(false)}
          onMouseLeave={() => setIsDragging(false)}
          onMouseMove={(e) => isDragging && handleMove(e.clientX)}
          onTouchMove={(e) => handleMove(e.touches[0].clientX)}
        >
          {/* Bottom Image (After T2) */}
          <img
            src={imageAfter}
            alt={titleAfter}
            style={{
              position: 'absolute',
              inset: 0,
              width: '100%',
              height: '100%',
              objectFit: 'contain',
            }}
          />
          <div
            style={{
              position: 'absolute',
              bottom: '10px',
              right: '12px',
              fontFamily: 'var(--font-mono)',
              fontSize: '10px',
              padding: '3px 8px',
              background: 'rgba(190, 18, 60, 0.9)',
              color: '#ffffff',
              borderRadius: '4px',
              fontWeight: 700,
              boxShadow: '0 2px 6px rgba(0,0,0,0.15)',
            }}
          >
            {titleAfter}
          </div>

          {/* Top Image (Before T1) with Clip Path */}
          <div
            style={{
              position: 'absolute',
              inset: 0,
              width: `${sliderPos}%`,
              overflow: 'hidden',
              borderRight: '2.5px solid var(--accent-amber)',
              boxShadow: '2px 0 12px rgba(194, 109, 46, 0.4)',
            }}
          >
            <img
              src={imageBefore}
              alt={titleBefore}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: containerRef.current ? `${containerRef.current.clientWidth}px` : '100%',
                height: '100%',
                objectFit: 'contain',
                maxWidth: 'none',
              }}
            />
            <div
              style={{
                position: 'absolute',
                bottom: '10px',
                left: '12px',
                fontFamily: 'var(--font-mono)',
                fontSize: '10px',
                padding: '3px 8px',
                background: 'rgba(194, 109, 46, 0.95)',
                color: '#ffffff',
                borderRadius: '4px',
                fontWeight: 700,
                boxShadow: '0 2px 6px rgba(0,0,0,0.15)',
              }}
            >
              {titleBefore}
            </div>
          </div>

          {/* Divider Handle */}
          <div
            style={{
              position: 'absolute',
              top: '50%',
              left: `${sliderPos}%`,
              transform: 'translate(-50%, -50%)',
              width: '32px',
              height: '32px',
              background: 'var(--accent-amber)',
              color: '#ffffff',
              borderRadius: '50%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 800,
              boxShadow: '0 2px 10px rgba(194, 109, 46, 0.6)',
              pointerEvents: 'none',
              zIndex: 10,
            }}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <polyline points="7 16 3 12 7 8" />
              <polyline points="17 8 21 12 17 16" />
              <line x1="3" y1="12" x2="21" y2="12" />
            </svg>
          </div>
        </div>
      ) : (
        <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '12px', fontStyle: 'italic' }}>
          Ingest both Sensor A (Before) and Sensor B (After) to activate the real-time split-screen comparison slider.
        </div>
      )}
    </div>
  );
};
