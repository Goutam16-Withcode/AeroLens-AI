'use client';

import React, { createContext, useContext, useEffect, useMemo, useState, useCallback } from 'react';
import {
  onAuthStateChanged,
  signInWithPopup,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut as firebaseSignOut,
  setPersistence,
  browserLocalPersistence,
  type User,
} from 'firebase/auth';
import { auth, googleProvider, isFirebaseConfigured } from '@/lib/firebase/client';

interface AuthContextValue {
  user: User | null;
  /** True while Firebase determines the initial auth state (prevents flash of login screen). */
  loading: boolean;
  error: string | null;
  clearError: () => void;
  signInWithGoogle: () => Promise<void>;
  signInWithEmail: (email: string, password: string) => Promise<void>;
  signUpWithEmail: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
  firebaseReady: boolean;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

function friendlyAuthError(err: unknown): string {
  const code = (err as { code?: string })?.code || '';
  switch (code) {
    case 'auth/wrong-password':
    case 'auth/invalid-credential':
      return 'Incorrect email or password.';
    case 'auth/user-not-found':
      return 'No account found with that email.';
    case 'auth/email-already-in-use':
      return 'An account with that email already exists.';
    case 'auth/weak-password':
      return 'Password must be at least 6 characters.';
    case 'auth/invalid-email':
      return 'That email address looks invalid.';
    case 'auth/popup-closed-by-user':
      return 'Sign-in was cancelled.';
    case 'auth/network-request-failed':
      return 'Network error — check your connection and try again.';
    case 'auth/too-many-requests':
      return 'Too many attempts. Please wait a moment and try again.';
    default:
      return 'Something went wrong signing you in. Please try again.';
  }
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const firebaseReady = isFirebaseConfigured();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!firebaseReady) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- legitimate one-time bail-out when Firebase isn't configured; no subscription is ever started in this branch.
      setLoading(false);
      return;
    }
    // Persist the session across page refreshes / browser restarts.
    setPersistence(auth, browserLocalPersistence).catch(() => {
      /* non-fatal: falls back to Firebase's default persistence */
    });

    const unsubscribe = onAuthStateChanged(
      auth,
      (firebaseUser) => {
        setUser(firebaseUser);
        setLoading(false);
      },
      () => {
        // Auth listener errored (e.g. expired session token refresh failure).
        setUser(null);
        setLoading(false);
        setError('Your session could not be verified. Please sign in again.');
      }
    );
    return unsubscribe;
  }, [firebaseReady]);

  const clearError = useCallback(() => setError(null), []);

  const signInWithGoogle = useCallback(async () => {
    setError(null);
    try {
      await signInWithPopup(auth, googleProvider);
    } catch (err) {
      setError(friendlyAuthError(err));
      throw err;
    }
  }, []);

  const signInWithEmail = useCallback(async (email: string, password: string) => {
    setError(null);
    try {
      await signInWithEmailAndPassword(auth, email, password);
    } catch (err) {
      setError(friendlyAuthError(err));
      throw err;
    }
  }, []);

  const signUpWithEmail = useCallback(async (email: string, password: string) => {
    setError(null);
    try {
      await createUserWithEmailAndPassword(auth, email, password);
    } catch (err) {
      setError(friendlyAuthError(err));
      throw err;
    }
  }, []);

  const signOut = useCallback(async () => {
    setError(null);
    try {
      await firebaseSignOut(auth);
    } catch (err) {
      setError(friendlyAuthError(err));
      throw err;
    }
  }, []);

  const value = useMemo(
    () => ({ user, loading, error, clearError, signInWithGoogle, signInWithEmail, signUpWithEmail, signOut, firebaseReady }),
    [user, loading, error, clearError, signInWithGoogle, signInWithEmail, signUpWithEmail, signOut, firebaseReady]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider');
  return ctx;
}
