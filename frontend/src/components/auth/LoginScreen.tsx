'use client';

import React, { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';

export const LoginScreen: React.FC = () => {
  const { signInWithGoogle, signInWithEmail, signUpWithEmail, error, clearError, firebaseReady } = useAuth();
  const [mode, setMode] = useState<'signin' | 'signup'>('signin');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleEmailSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !password) return;
    setSubmitting(true);
    try {
      if (mode === 'signin') {
        await signInWithEmail(email.trim(), password);
      } else {
        await signUpWithEmail(email.trim(), password);
      }
    } catch {
      /* error already surfaced via context */
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      style={{
        position: 'relative',
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '24px',
      }}
    >
      <div className="space-canvas" />
      <div className="grid-overlay" />
      <div
        className="panel-card"
        style={{ position: 'relative', zIndex: 1, width: '100%', maxWidth: '380px', padding: '32px' }}
      >
        <div style={{ textAlign: 'center', marginBottom: '22px' }}>
          <div style={{ fontFamily: 'var(--font-hud)', fontSize: '20px', fontWeight: 700, color: 'var(--text-pure)' }}>
            🛰️ AeroLens AI
          </div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
            Sign in to access your mission chat history
          </div>
        </div>

        {!firebaseReady && (
          <div
            style={{
              background: 'var(--accent-coral-subtle)',
              border: '1px solid var(--accent-coral-border)',
              borderRadius: 'var(--radius-sm)',
              padding: '10px 12px',
              fontSize: '11.5px',
              color: 'var(--accent-coral)',
              marginBottom: '16px',
              fontFamily: 'var(--font-mono)',
            }}
          >
            Firebase is not configured yet. Set the <code>NEXT_PUBLIC_FIREBASE_*</code> variables in{' '}
            <code>frontend/.env.local</code> (see <code>.env.local.example</code>) and restart the dev server.
          </div>
        )}

        {error && (
          <div
            style={{
              background: 'var(--accent-coral-subtle)',
              border: '1px solid var(--accent-coral-border)',
              borderRadius: 'var(--radius-sm)',
              padding: '10px 12px',
              fontSize: '12px',
              color: 'var(--accent-coral)',
              marginBottom: '16px',
            }}
          >
            {error}
          </div>
        )}

        <button
          type="button"
          disabled={!firebaseReady}
          onClick={() => {
            clearError();
            signInWithGoogle().catch(() => {});
          }}
          style={{
            width: '100%',
            padding: '11px',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-light)',
            background: 'var(--bg-surface)',
            color: 'var(--text-main)',
            fontWeight: 600,
            fontSize: '13px',
            cursor: firebaseReady ? 'pointer' : 'not-allowed',
            opacity: firebaseReady ? 1 : 0.5,
            marginBottom: '16px',
          }}
        >
          Continue with Google
        </button>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', margin: '12px 0', color: 'var(--text-muted)', fontSize: '11px' }}>
          <div style={{ flex: 1, height: 1, background: 'var(--border-subtle)' }} />
          OR
          <div style={{ flex: 1, height: 1, background: 'var(--border-subtle)' }} />
        </div>

        <form onSubmit={handleEmailSubmit}>
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            style={inputStyle}
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={6}
            style={{ ...inputStyle, marginTop: '10px' }}
          />
          <button
            type="submit"
            disabled={!firebaseReady || submitting}
            style={{
              width: '100%',
              marginTop: '14px',
              padding: '11px',
              borderRadius: 'var(--radius-md)',
              border: 'none',
              background: 'var(--accent-amber)',
              color: '#fff',
              fontWeight: 700,
              fontSize: '13px',
              cursor: firebaseReady && !submitting ? 'pointer' : 'not-allowed',
              opacity: firebaseReady && !submitting ? 1 : 0.6,
            }}
          >
            {submitting ? 'Please wait…' : mode === 'signin' ? 'Sign In' : 'Create Account'}
          </button>
        </form>

        <div style={{ textAlign: 'center', marginTop: '16px', fontSize: '12px', color: 'var(--text-secondary)' }}>
          {mode === 'signin' ? "Don't have an account? " : 'Already have an account? '}
          <button
            type="button"
            onClick={() => {
              clearError();
              setMode(mode === 'signin' ? 'signup' : 'signin');
            }}
            style={{ background: 'none', border: 'none', color: 'var(--accent-amber)', fontWeight: 700, cursor: 'pointer', fontSize: '12px' }}
          >
            {mode === 'signin' ? 'Sign up' : 'Sign in'}
          </button>
        </div>
      </div>
    </div>
  );
};

const inputStyle: React.CSSProperties = {
  width: '100%',
  padding: '10px 12px',
  borderRadius: 'var(--radius-sm)',
  border: '1px solid var(--border-light)',
  background: 'var(--bg-input)',
  color: 'var(--text-main)',
  fontSize: '13px',
  outline: 'none',
};
