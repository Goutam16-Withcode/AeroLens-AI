'use client';

import React, { useState, useEffect, useRef } from 'react';

interface ImageLightboxModalProps {
  isOpen: boolean;
  onClose: () => void;
  imageSrc: string | null;
  title?: string;
  subtitle?: string;
}

export const ImageLightboxModal: React.FC<ImageLightboxModalProps> = ({
  isOpen,
  onClose,
  imageSrc,
  title = 'ORBITAL HIGH-RESOLUTION FRAME',
  subtitle,
}) => {
  const [scale, setScale] = useState<number>(1);
  const [pos, setPos] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [dragStart, setDragStart] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [downloaded, setDownloaded] = useState<boolean>(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Reset transform whenever modal opens or image changes
  useEffect(() => {
    if (isOpen) {
      setScale(1);
      setPos({ x: 0, y: 0 });
      setDownloaded(false);
    }
  }, [isOpen, imageSrc]);

  // Keyboard shortcut handler
  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
      if (e.key === '+' || e.key === '=') zoomIn();
      if (e.key === '-' || e.key === '_') zoomOut();
      if (e.key === '0') resetZoom();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen || !imageSrc) return null;

  const zoomIn = () => setScale((s) => Math.min(4, Math.round((s + 0.25) * 100) / 100));
  const zoomOut = () => setScale((s) => Math.max(0.5, Math.round((s - 0.25) * 100) / 100));
  const resetZoom = () => {
    setScale(1);
    setPos({ x: 0, y: 0 });
  };

  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    if (e.deltaY < 0) {
      zoomIn();
    } else {
      zoomOut();
    }
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    if (scale <= 1) return;
    setIsDragging(true);
    setDragStart({ x: e.clientX - pos.x, y: e.clientY - pos.y });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return;
    setPos({
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y,
    });
  };

  const handleMouseUp = () => setIsDragging(false);

  const handleDownload = () => {
    try {
      const link = document.createElement('a');
      link.href = imageSrc;
      const cleanTitle = (title || 'aerolens_frame').toLowerCase().replace(/[^a-z0-9]/g, '_');
      const ts = new Date().toISOString().replace(/[:.]/g, '-');
      link.download = `${cleanTitle}_${ts}.png`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      setDownloaded(true);
      setTimeout(() => setDownloaded(false), 2500);
    } catch (err) {
      console.error('Download failed:', err);
    }
  };

  return (
    <div
      className="image-modal-backdrop"
      style={{
        zIndex: 9999,
        background: 'rgba(15, 23, 42, 0.88)',
        backdropFilter: 'blur(16px)',
        padding: '16px',
      }}
      onClick={onClose}
    >
      <div
        className="image-modal-content"
        style={{
          maxWidth: 'min(92vw, 960px)',
          maxHeight: '90vh',
          width: 'auto',
          margin: '0 auto',
          display: 'flex',
          flexDirection: 'column',
          background: '#1c1917',
          border: '1.5px solid rgba(255, 255, 255, 0.18)',
          borderRadius: '12px',
          boxShadow: '0 25px 70px rgba(0, 0, 0, 0.75)',
          padding: '0',
          overflow: 'hidden',
          color: '#ffffff',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Top Command Header */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '12px 18px',
            background: 'rgba(28, 25, 23, 0.96)',
            borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
            flexWrap: 'wrap',
            gap: '10px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div
              style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background: 'var(--accent-amber)',
                boxShadow: '0 0 8px var(--accent-amber)',
              }}
            />
            <div>
              <div
                style={{
                  fontFamily: 'var(--font-hud)',
                  fontSize: '13px',
                  fontWeight: 700,
                  letterSpacing: '0.08em',
                  color: '#fbf9f5',
                }}
              >
                {title.toUpperCase()}
              </div>
              {subtitle && (
                <div style={{ fontSize: '10.5px', color: 'rgba(255, 255, 255, 0.6)', fontFamily: 'var(--font-mono)' }}>
                  {subtitle}
                </div>
              )}
            </div>
          </div>

          {/* Action Tools */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {/* Zoom Controls */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                background: 'rgba(255, 255, 255, 0.08)',
                borderRadius: '6px',
                border: '1px solid rgba(255, 255, 255, 0.12)',
                padding: '2px',
              }}
            >
              <button
                onClick={zoomOut}
                title="Zoom Out (-)"
                style={{
                  padding: '4px 8px',
                  background: 'transparent',
                  border: 'none',
                  color: '#ffffff',
                  cursor: 'pointer',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '13px',
                  borderRadius: '4px',
                }}
              >
                −
              </button>
              <span
                style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: '11px',
                  color: 'var(--accent-amber)',
                  fontWeight: 700,
                  minWidth: '45px',
                  textAlign: 'center',
                }}
              >
                {Math.round(scale * 100)}%
              </span>
              <button
                onClick={zoomIn}
                title="Zoom In (+)"
                style={{
                  padding: '4px 8px',
                  background: 'transparent',
                  border: 'none',
                  color: '#ffffff',
                  cursor: 'pointer',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '13px',
                  borderRadius: '4px',
                }}
              >
                +
              </button>
              <button
                onClick={resetZoom}
                title="Reset Zoom (1:1)"
                style={{
                  padding: '4px 8px',
                  background: 'transparent',
                  border: 'none',
                  borderLeft: '1px solid rgba(255, 255, 255, 0.12)',
                  color: 'rgba(255, 255, 255, 0.7)',
                  cursor: 'pointer',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '10px',
                }}
              >
                FIT
              </button>
            </div>

            {/* DOWNLOAD BUTTON */}
            <button
              onClick={handleDownload}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '6px 14px',
                background: downloaded ? '#10b981' : 'var(--accent-amber)',
                color: '#ffffff',
                border: 'none',
                borderRadius: '6px',
                fontFamily: 'var(--font-mono)',
                fontSize: '11px',
                fontWeight: 700,
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                boxShadow: '0 2px 8px rgba(0, 0, 0, 0.3)',
              }}
              title="Download image frame directly to your local computer"
            >
              {downloaded ? (
                <>
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                  <span>SAVED!</span>
                </>
              ) : (
                <>
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                    <polyline points="7 10 12 15 17 10" />
                    <line x1="12" y1="15" x2="12" y2="3" />
                  </svg>
                  <span>DOWNLOAD FRAME</span>
                </>
              )}
            </button>

            {/* Close Button */}
            <button
              onClick={onClose}
              style={{
                width: '30px',
                height: '30px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                background: 'rgba(255, 255, 255, 0.1)',
                border: '1px solid rgba(255, 255, 255, 0.15)',
                borderRadius: '6px',
                color: '#ffffff',
                cursor: 'pointer',
                fontSize: '14px',
              }}
              title="Close viewer (ESC)"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Viewport Canvas */}
        <div
          ref={containerRef}
          style={{
            minHeight: '400px',
            maxHeight: '72vh',
            minWidth: 'min(90vw, 480px)',
            overflow: 'hidden',
            position: 'relative',
            background: '#0c0a09',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: scale > 1 ? (isDragging ? 'grabbing' : 'grab') : 'default',
            userSelect: 'none',
            padding: '18px',
          }}
          onWheel={handleWheel}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
        >
          {/* Scientific Reticle Gridlines Background */}
          <div
            style={{
              position: 'absolute',
              inset: 0,
              backgroundImage:
                'linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px)',
              backgroundSize: '24px 24px',
              pointerEvents: 'none',
            }}
          />

          <img
            src={imageSrc}
            alt={title}
            draggable={false}
            style={{
              maxWidth: '85vw',
              maxHeight: '66vh',
              width: 'auto',
              height: 'auto',
              objectFit: 'contain',
              transform: `translate(${pos.x}px, ${pos.y}px) scale(${scale})`,
              transition: isDragging ? 'none' : 'transform 0.12s ease-out',
              transformOrigin: 'center center',
              boxShadow: '0 10px 40px rgba(0,0,0,0.6)',
              borderRadius: '4px',
            }}
          />
        </div>

        {/* Modal Bottom Status Bar */}
        <div
          style={{
            padding: '8px 18px',
            background: 'rgba(28, 25, 23, 0.96)',
            borderTop: '1px solid rgba(255, 255, 255, 0.1)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            fontFamily: 'var(--font-mono)',
            fontSize: '11px',
            color: 'rgba(255, 255, 255, 0.65)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            <span>SCROLL: ZOOM IN/OUT</span>
            <span>·</span>
            <span>DRAG: PAN VIEWPORT</span>
            <span>·</span>
            <span>ESC: CLOSE</span>
          </div>

          <div style={{ color: 'var(--accent-amber)', fontWeight: 600 }}>
            AEROLENS RESOLUTION DECODER // LOSSLESS RENDER
          </div>
        </div>
      </div>
    </div>
  );
};
