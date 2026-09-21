'use client';

import React from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { LoginScreen } from './LoginScreen';

/**
 * Wraps the app: shows a lightweight loading state while Firebase resolves
 * the initial auth session, the LoginScreen if unauthenticated, or the
 * private chat UI once a user is signed in. This is the single gate that
 * guarantees unauthenticated users never see any conversation data,
 * regardless of what individual components attempt to fetch.
 */
export const AuthGate: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--text-muted)' }}>
          Establishing uplink…
        </div>
      </div>
    );
  }

  if (!user) {
    return <LoginScreen />;
  }

  return <>{children}</>;
};
