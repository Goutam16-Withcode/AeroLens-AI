import React from 'react';

export const SidebarSkeleton: React.FC = () => (
  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', padding: '4px 0' }}>
    {[0, 1, 2, 3, 4].map((i) => (
      <div
        key={i}
        style={{
          height: '44px',
          borderRadius: 'var(--radius-sm)',
          background: 'linear-gradient(90deg, var(--bg-secondary) 25%, var(--bg-surface) 50%, var(--bg-secondary) 75%)',
          backgroundSize: '200% 100%',
          animation: 'sidebar-shimmer 1.4s ease-in-out infinite',
          opacity: 1 - i * 0.12,
        }}
      />
    ))}
    <style>{`
      @keyframes sidebar-shimmer {
        0% { background-position: 200% 0; }
        100% { background-position: -200% 0; }
      }
    `}</style>
  </div>
);
