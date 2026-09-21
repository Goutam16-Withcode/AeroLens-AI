'use client';

import React, { useMemo, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useConversations } from '@/hooks/useConversations';
import { groupConversationsByRecency } from '@/services/conversationService';
import { ConversationListItem } from './ConversationListItem';
import { SidebarSkeleton } from './SidebarSkeleton';
import { DeleteConfirmModal } from './DeleteConfirmModal';
import type { Conversation } from '@/types/chat';

interface Props {
  activeConversationId: string | null;
  onSelectConversation: (id: string | null) => void;
  /** Mobile drawer open/close. */
  isOpen: boolean;
  onClose: () => void;
  /** Desktop collapse (sidebar fully hidden, toggled from the header). */
  collapsed: boolean;
}

export const Sidebar: React.FC<Props> = ({ activeConversationId, onSelectConversation, isOpen, onClose, collapsed }) => {
  const { user, signOut } = useAuth();
  const { conversations, loading, error, rename, remove } = useConversations();
  const [search, setSearch] = useState('');
  const [pendingDelete, setPendingDelete] = useState<Conversation | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [cleanupWarning, setCleanupWarning] = useState<string | null>(null);

  const filtered = useMemo(() => {
    if (!search.trim()) return conversations;
    const q = search.trim().toLowerCase();
    return conversations.filter((c) => c.title.toLowerCase().includes(q) || c.lastMessage.toLowerCase().includes(q));
  }, [conversations, search]);

  const grouped = useMemo(() => groupConversationsByRecency(filtered), [filtered]);

  const handleConfirmDelete = async () => {
    if (!pendingDelete) return;
    setIsDeleting(true);
    try {
      const { storageCleanupFailed } = await remove(pendingDelete.conversationId);
      if (storageCleanupFailed) {
        setCleanupWarning('Conversation deleted, but some uploaded images may not have been fully removed from storage.');
      }
      if (activeConversationId === pendingDelete.conversationId) {
        onSelectConversation(null);
      }
    } finally {
      setIsDeleting(false);
      setPendingDelete(null);
    }
  };

  return (
    <>
      {/* Mobile scrim */}
      {isOpen && (
        <div
          onClick={onClose}
          style={{ position: 'fixed', inset: 0, background: 'var(--bg-overlay)', zIndex: 90, display: 'none' }}
          className="sidebar-scrim"
        />
      )}

      <aside
        className={`chat-sidebar ${isOpen ? 'chat-sidebar-open' : ''} ${collapsed ? 'chat-sidebar-collapsed' : ''}`}
        style={{
          width: '272px',
          minWidth: '272px',
          borderRight: '1px solid var(--border-subtle)',
          background: 'var(--bg-secondary)',
          display: 'flex',
          flexDirection: 'column',
          height: '100vh',
          position: 'fixed',
          top: 0,
          left: 0,
          zIndex: 50,
          transition: 'width 0.18s ease, min-width 0.18s ease, left 0.22s ease',
        }}
      >
        <div style={{ padding: '14px 12px 8px' }}>
          <button
            onClick={() => {
              onSelectConversation(null);
              onClose();
            }}
            style={{
              width: '100%',
              padding: '10px 12px',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-light)',
              background: 'var(--bg-surface)',
              color: 'var(--text-main)',
              fontWeight: 700,
              fontSize: '12.5px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}
          >
            <span style={{ fontSize: '14px' }}>+</span> New Chat
          </button>

          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search conversations…"
            style={{
              width: '100%',
              marginTop: '10px',
              padding: '8px 10px',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--border-light)',
              background: 'var(--bg-input)',
              color: 'var(--text-main)',
              fontSize: '12px',
              outline: 'none',
            }}
          />
        </div>

        <div style={{ flex: 1, overflowY: 'auto', padding: '4px 10px' }}>
          {loading && <SidebarSkeleton />}

          {!loading && error && (
            <div style={{ fontSize: '11.5px', color: 'var(--accent-coral)', padding: '10px 4px' }}>{error}</div>
          )}

          {!loading && !error && filtered.length === 0 && (
            <div style={{ textAlign: 'center', padding: '32px 10px', color: 'var(--text-muted)' }}>
              <div style={{ fontSize: '26px', marginBottom: '8px' }}>🛰️</div>
              <div style={{ fontSize: '12.5px', fontWeight: 600, marginBottom: '4px', color: 'var(--text-secondary)' }}>
                {search ? 'No matching missions' : 'No missions yet'}
              </div>
              <div style={{ fontSize: '11px' }}>
                {search ? 'Try a different search term.' : 'Start a new chat to begin your first analysis.'}
              </div>
            </div>
          )}

          {!loading &&
            grouped.map((group) => (
              <div key={group.label} style={{ marginBottom: '14px' }}>
                <div
                  style={{
                    fontSize: '10px',
                    fontWeight: 700,
                    letterSpacing: '0.06em',
                    textTransform: 'uppercase',
                    color: 'var(--text-muted)',
                    padding: '6px 6px 4px',
                  }}
                >
                  {group.label}
                </div>
                {group.items.map((c) => (
                  <ConversationListItem
                    key={c.conversationId}
                    conversation={c}
                    isActive={c.conversationId === activeConversationId}
                    onSelect={() => {
                      onSelectConversation(c.conversationId);
                      onClose();
                    }}
                    onRename={(title) => rename(c.conversationId, title)}
                    onDelete={() => setPendingDelete(c)}
                  />
                ))}
              </div>
            ))}
        </div>

        {user && (
          <div
            style={{
              padding: '12px',
              borderTop: '1px solid var(--border-subtle)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: '8px',
            }}
          >
            <div style={{ minWidth: 0 }}>
              <div style={{ fontSize: '11.5px', fontWeight: 600, color: 'var(--text-main)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {user.displayName || user.email}
              </div>
            </div>
            <button
              onClick={() => signOut()}
              style={{ background: 'none', border: 'none', color: 'var(--text-muted)', fontSize: '11px', cursor: 'pointer', fontWeight: 600 }}
            >
              Sign out
            </button>
          </div>
        )}
      </aside>

      {pendingDelete && (
        <DeleteConfirmModal
          title={pendingDelete.title}
          isDeleting={isDeleting}
          onCancel={() => setPendingDelete(null)}
          onConfirm={handleConfirmDelete}
        />
      )}

      {cleanupWarning && (
        <div
          style={{
            position: 'fixed',
            bottom: '16px',
            left: '50%',
            transform: 'translateX(-50%)',
            background: 'var(--bg-surface)',
            border: '1px solid var(--accent-amber-border)',
            color: 'var(--accent-amber)',
            borderRadius: 'var(--radius-sm)',
            padding: '10px 16px',
            fontSize: '12px',
            zIndex: 300,
            boxShadow: '0 8px 20px rgba(28,25,23,0.15)',
          }}
        >
          {cleanupWarning}{' '}
          <button onClick={() => setCleanupWarning(null)} style={{ marginLeft: '8px', border: 'none', background: 'none', cursor: 'pointer', fontWeight: 700 }}>
            Dismiss
          </button>
        </div>
      )}

      <style>{`
        .chat-sidebar-collapsed {
          left: -272px !important;
        }
        @media (max-width: 860px) {
          .chat-sidebar {
            left: -272px;
            box-shadow: 0 0 0 rgba(0,0,0,0);
          }
          .chat-sidebar-collapsed {
            left: -272px !important;
          }
          .chat-sidebar-open {
            left: 0 !important;
            box-shadow: 8px 0 24px rgba(28,25,23,0.18);
          }
          .sidebar-scrim { display: block !important; }
        }
      `}</style>
    </>
  );
};