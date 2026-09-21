'use client';

import React, { useState } from 'react';
import { ImageLightboxModal } from '../ImageLightboxModal';
import { AnalysisResultPanel } from './AnalysisResultPanel';
import type { ChatMessage } from '@/types/chat';
import type { AnalysisResponse, EvidencePayload } from '@/types/satquery';

interface Props {
  message: ChatMessage;
  previewA: string | null;
  previewB: string | null;
  isExpanded: boolean;
  onToggleExpand: () => void;
  onRetry: () => void;
  onGenerateBriefing: (response: AnalysisResponse, query: string) => void;
  precedingUserQuery: string;
}

function toAnalysisResponse(message: ChatMessage): AnalysisResponse {
  const find = (role: string) => message.images.find((img) => img.role === role)?.imageUrl || null;
  const evidence: EvidencePayload = {
    slot1_original: find('evidence_original'),
    slot2_attention_or_diff: find('evidence_attention'),
    slot3_reticle_or_sar: find('evidence_reticle'),
    slot4_after: find('evidence_after'),
    is_single_image: !find('evidence_after'),
  };
  return {
    answer: message.content,
    evidence,
    detected_objects: message.metadata?.detected_objects || [],
    trace: message.metadata?.trace || null,
    trace_markdown: message.metadata?.trace_markdown || '',
  };
}

export const MessageBubble: React.FC<Props> = ({
  message,
  previewA,
  previewB,
  isExpanded,
  onToggleExpand,
  onRetry,
  onGenerateBriefing,
  precedingUserQuery,
}) => {
  const [lightbox, setLightbox] = useState<{ src: string; title: string } | null>(null);

  if (message.role === 'user') {
    return (
      <div style={{ marginBottom: '18px' }}>
        <div
          style={{
            display: 'inline-block',
            maxWidth: '85%',
            marginLeft: 'auto',
            background: 'var(--accent-amber-subtle)',
            border: '1px solid var(--accent-amber-border)',
            borderRadius: 'var(--radius-md)',
            padding: '10px 14px',
            float: 'right',
            clear: 'both',
          }}
        >
          <div style={{ fontSize: '13px', color: 'var(--text-main)', whiteSpace: 'pre-wrap' }}>{message.content}</div>
          {message.images.length > 0 && (
            <div style={{ display: 'flex', gap: '6px', marginTop: '8px', flexWrap: 'wrap' }}>
              {message.images.map((img) => (
                <img
                  key={img.publicId}
                  src={img.imageUrl}
                  alt={img.fileName}
                  onClick={() => setLightbox({ src: img.imageUrl, title: img.fileName })}
                  style={{ width: '56px', height: '56px', objectFit: 'cover', borderRadius: '6px', cursor: 'zoom-in', border: '1px solid var(--border-light)' }}
                />
              ))}
            </div>
          )}
        </div>
        <div style={{ clear: 'both' }} />
        <ImageLightboxModal isOpen={!!lightbox} onClose={() => setLightbox(null)} imageSrc={lightbox?.src || null} title={lightbox?.title} />
      </div>
    );
  }

  // Assistant message
  if (message.status === 'pending') {
    return (
      <div style={{ marginBottom: '18px', clear: 'both' }}>
        <div className="panel-card" style={{ padding: '14px', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span className="spinner" style={{ width: '14px', height: '14px', border: '2px solid var(--accent-amber-border)', borderTopColor: 'var(--accent-amber)', borderRadius: '50%', display: 'inline-block', animation: 'spin 0.8s linear infinite' }} />
          <span style={{ fontSize: '12.5px', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>Analyzing imagery…</span>
          <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
        </div>
      </div>
    );
  }

  if (message.status === 'failed') {
    return (
      <div style={{ marginBottom: '18px', clear: 'both' }}>
        <div
          style={{
            background: '#fef2f2',
            border: '1px solid #fecaca',
            color: '#991b1b',
            borderRadius: '8px',
            padding: '12px 14px',
            fontFamily: 'var(--font-mono)',
            fontSize: '12px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            gap: '10px',
          }}
        >
          <span>{message.metadata?.errorMessage || 'AI processing failed.'}</span>
          <button
            onClick={onRetry}
            style={{ padding: '5px 12px', borderRadius: '6px', border: '1px solid #dc2626', background: '#fff', color: '#dc2626', fontWeight: 700, cursor: 'pointer', flexShrink: 0 }}
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const response = toAnalysisResponse(message);

  if (!isExpanded) {
    return (
      <div style={{ marginBottom: '18px', clear: 'both' }}>
        <div
          className="panel-card"
          onClick={onToggleExpand}
          style={{ padding: '12px 14px', cursor: 'pointer' }}
        >
          <div style={{ fontSize: '10px', fontWeight: 700, color: 'var(--accent-amber)', letterSpacing: '0.05em', marginBottom: '4px' }}>
            ANALYSIS RESULT — click to expand
          </div>
          <div style={{ fontSize: '12.5px', color: 'var(--text-secondary)', overflow: 'hidden', textOverflow: 'ellipsis', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' }}>
            {message.content}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ marginBottom: '18px', clear: 'both' }}>
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '6px' }}>
        <button onClick={onToggleExpand} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', fontSize: '11px', cursor: 'pointer' }}>
          Collapse ▲
        </button>
      </div>
      <AnalysisResultPanel
        response={response}
        previewA={previewA}
        previewB={previewB}
        isLoading={false}
        onGenerateBriefing={() => onGenerateBriefing(response, precedingUserQuery)}
      />
    </div>
  );
};
