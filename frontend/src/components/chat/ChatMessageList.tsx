'use client';

import React, { useEffect, useMemo, useRef, useState } from 'react';
import { MessageBubble } from './MessageBubble';
import type { ChatMessage } from '@/types/chat';
import type { AnalysisResponse } from '@/types/satquery';

interface Props {
  messages: ChatMessage[];
  loading: boolean;
  hasMore: boolean;
  loadingMore: boolean;
  onLoadOlder: () => void;
  onRetry: (assistantMessageId: string) => void;
  onGenerateBriefing: (response: AnalysisResponse, query: string) => void;
}

export const ChatMessageList: React.FC<Props> = ({ messages, loading, hasMore, loadingMore, onLoadOlder, onRetry, onGenerateBriefing }) => {
  const bottomRef = useRef<HTMLDivElement>(null);
  const [manuallyExpanded, setManuallyExpanded] = useState<Record<string, boolean>>({});

  const lastAssistantId = useMemo(() => {
    for (let i = messages.length - 1; i >= 0; i--) {
      if (messages[i].role === 'assistant') return messages[i].messageId;
    }
    return null;
  }, [messages]);

  // Pair each assistant message with the query text/preview images of the
  // user message that triggered it. Computed once per messages change
  // (not mutated during the render map) to satisfy the rules-of-react
  // immutability check. Must stay above any early returns (rules-of-hooks).
  const turnContext = useMemo(() => {
    const contexts: { userQuery: string; previewA: string | null; previewB: string | null }[] = [];
    let lastUserQuery = '';
    let lastPreviewA: string | null = null;
    let lastPreviewB: string | null = null;
    for (const m of messages) {
      if (m.role === 'user') {
        lastUserQuery = m.content;
        lastPreviewA = m.images.find((i) => i.role === 'input_a')?.imageUrl || null;
        lastPreviewB = m.images.find((i) => i.role === 'input_b')?.imageUrl || null;
      }
      contexts.push({ userQuery: lastUserQuery, previewA: lastPreviewA, previewB: lastPreviewB });
    }
    return contexts;
  }, [messages]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [messages.length]);

  if (loading) {
    return (
      <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontSize: '12px' }}>
        Loading conversation…
      </div>
    );
  }

  if (messages.length === 0) {
    return (
      <div style={{ padding: '60px 20px', textAlign: 'center', color: 'var(--text-muted)' }}>
        <div style={{ fontSize: '34px', marginBottom: '10px' }}>🛰️</div>
        <div style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '6px' }}>
          Ready for mission uplink
        </div>
        <div style={{ fontSize: '12px' }}>Attach satellite imagery and send a query to begin this analysis.</div>
      </div>
    );
  }

  return (
    <div style={{ padding: '18px', minHeight: '100%' }}>
      {hasMore && (
        <div style={{ textAlign: 'center', marginBottom: '14px' }}>
          <button
            onClick={onLoadOlder}
            disabled={loadingMore}
            style={{
              padding: '6px 14px',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--border-light)',
              background: 'var(--bg-surface)',
              color: 'var(--text-secondary)',
              fontSize: '11.5px',
              cursor: loadingMore ? 'not-allowed' : 'pointer',
            }}
          >
            {loadingMore ? 'Loading…' : 'Load earlier messages'}
          </button>
        </div>
      )}

      {messages.map((m, idx) => {
        const ctx = turnContext[idx];
        const isExpanded = m.messageId === lastAssistantId ? manuallyExpanded[m.messageId] ?? true : manuallyExpanded[m.messageId] ?? false;
        return (
          <MessageBubble
            key={m.messageId}
            message={m}
            previewA={ctx.previewA}
            previewB={ctx.previewB}
            isExpanded={isExpanded}
            onToggleExpand={() => setManuallyExpanded((prev) => ({ ...prev, [m.messageId]: !isExpanded }))}
            onRetry={() => onRetry(m.messageId)}
            onGenerateBriefing={onGenerateBriefing}
            precedingUserQuery={ctx.userQuery}
          />
        );
      })}
      <div ref={bottomRef} />
    </div>
  );
};
