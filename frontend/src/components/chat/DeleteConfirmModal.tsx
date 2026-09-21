import React from 'react';

interface Props {
  title: string;
  onCancel: () => void;
  onConfirm: () => void;
  isDeleting: boolean;
}

export const DeleteConfirmModal: React.FC<Props> = ({ title, onCancel, onConfirm, isDeleting }) => (
  <div
    style={{
      position: 'fixed',
      inset: 0,
      background: 'var(--bg-overlay)',
      zIndex: 200,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '16px',
    }}
    onClick={onCancel}
  >
    <div
      className="panel-card"
      style={{ maxWidth: '380px', width: '100%', padding: '20px' }}
      onClick={(e) => e.stopPropagation()}
    >
      <div style={{ fontWeight: 700, fontSize: '14px', color: 'var(--text-pure)', marginBottom: '8px' }}>
        Delete conversation?
      </div>
      <div style={{ fontSize: '12.5px', color: 'var(--text-secondary)', marginBottom: '18px', lineHeight: 1.5 }}>
        This permanently deletes <strong>&ldquo;{title}&rdquo;</strong>, all of its messages, and any uploaded
        images. This cannot be undone.
      </div>
      <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
        <button
          onClick={onCancel}
          disabled={isDeleting}
          style={{
            padding: '8px 14px',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid var(--border-light)',
            background: 'var(--bg-surface)',
            color: 'var(--text-main)',
            fontSize: '12.5px',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          Cancel
        </button>
        <button
          onClick={onConfirm}
          disabled={isDeleting}
          style={{
            padding: '8px 14px',
            borderRadius: 'var(--radius-sm)',
            border: 'none',
            background: 'var(--accent-coral)',
            color: '#fff',
            fontSize: '12.5px',
            fontWeight: 700,
            cursor: isDeleting ? 'not-allowed' : 'pointer',
            opacity: isDeleting ? 0.7 : 1,
          }}
        >
          {isDeleting ? 'Deleting…' : 'Delete'}
        </button>
      </div>
    </div>
  </div>
);
