import React, { useState } from 'react';
import type { Conversation } from '@/types/chat';

interface Props {
  conversation: Conversation;
  isActive: boolean;
  onSelect: () => void;
  onRename: (newTitle: string) => void;
  onDelete: () => void;
}

function relativeTime(millis: number): string {
  const diff = Date.now() - millis;
  const min = Math.floor(diff / 60000);
  if (min < 1) return 'just now';
  if (min < 60) return `${min}m ago`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr}h ago`;
  const days = Math.floor(hr / 24);
  return `${days}d ago`;
}

export const ConversationListItem: React.FC<Props> = ({ conversation, isActive, onSelect, onRename, onDelete }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [draftTitle, setDraftTitle] = useState(conversation.title);
  const [menuOpen, setMenuOpen] = useState(false);

  const commitRename = () => {
    setIsEditing(false);
    if (draftTitle.trim() && draftTitle.trim() !== conversation.title) {
      onRename(draftTitle.trim());
    } else {
      setDraftTitle(conversation.title);
    }
  };

  const ts = conversation.updatedAt?.toMillis?.() ?? null;

  return (
    <div
      onClick={() => !isEditing && onSelect()}
      style={{
        position: 'relative',
        padding: '9px 10px',
        borderRadius: 'var(--radius-sm)',
        background: isActive ? 'var(--accent-amber-subtle)' : 'transparent',
        border: `1px solid ${isActive ? 'var(--accent-amber-border)' : 'transparent'}`,
        cursor: 'pointer',
        marginBottom: '3px',
        transition: 'background 0.15s ease',
      }}
      onMouseEnter={(e) => {
        if (!isActive) e.currentTarget.style.background = 'var(--bg-secondary)';
      }}
      onMouseLeave={(e) => {
        if (!isActive) e.currentTarget.style.background = 'transparent';
      }}
    >
      {isEditing ? (
        <input
          autoFocus
          value={draftTitle}
          onChange={(e) => setDraftTitle(e.target.value)}
          onBlur={commitRename}
          onKeyDown={(e) => {
            if (e.key === 'Enter') commitRename();
            if (e.key === 'Escape') {
              setDraftTitle(conversation.title);
              setIsEditing(false);
            }
          }}
          onClick={(e) => e.stopPropagation()}
          style={{
            width: '100%',
            fontSize: '12.5px',
            padding: '2px 4px',
            border: '1px solid var(--accent-amber)',
            borderRadius: '4px',
            background: 'var(--bg-input)',
            color: 'var(--text-main)',
          }}
        />
      ) : (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '6px' }}>
          <div style={{ minWidth: 0, flex: 1 }}>
            <div
              style={{
                fontSize: '12.5px',
                fontWeight: isActive ? 700 : 600,
                color: isActive ? 'var(--accent-amber)' : 'var(--text-main)',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
              }}
            >
              {conversation.title}
            </div>
            <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '2px', fontFamily: 'var(--font-mono)' }}>
              {ts ? relativeTime(ts) : '—'}
            </div>
          </div>

          <div style={{ position: 'relative' }}>
            <button
              onClick={(e) => {
                e.stopPropagation();
                setMenuOpen((v) => !v);
              }}
              style={{
                background: 'none',
                border: 'none',
                color: 'var(--text-muted)',
                cursor: 'pointer',
                fontSize: '14px',
                padding: '2px 4px',
                lineHeight: 1,
              }}
              aria-label="Conversation options"
            >
              ⋯
            </button>
            {menuOpen && (
              <div
                onClick={(e) => e.stopPropagation()}
                style={{
                  position: 'absolute',
                  right: 0,
                  top: '22px',
                  background: 'var(--bg-surface)',
                  border: '1px solid var(--border-light)',
                  borderRadius: 'var(--radius-sm)',
                  boxShadow: '0 6px 18px rgba(28,25,23,0.14)',
                  zIndex: 20,
                  minWidth: '110px',
                  overflow: 'hidden',
                }}
              >
                <button
                  onClick={() => {
                    setMenuOpen(false);
                    setIsEditing(true);
                  }}
                  style={menuBtnStyle}
                >
                  Rename
                </button>
                <button
                  onClick={() => {
                    setMenuOpen(false);
                    onDelete();
                  }}
                  style={{ ...menuBtnStyle, color: 'var(--accent-coral)' }}
                >
                  Delete
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

const menuBtnStyle: React.CSSProperties = {
  display: 'block',
  width: '100%',
  textAlign: 'left',
  padding: '8px 12px',
  fontSize: '12px',
  background: 'none',
  border: 'none',
  cursor: 'pointer',
  color: 'var(--text-main)',
};
