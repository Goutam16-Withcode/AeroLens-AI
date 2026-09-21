/**
 * Firebase CLIENT SDK initialization.
 *
 * IMPORTANT: this file only ever touches `NEXT_PUBLIC_*` environment variables.
 * Firebase web "config" values (apiKey, authDomain, etc.) are not secrets — they
 * identify the project, and access is actually enforced by Firestore Security
 * Rules (see /firestore.rules) plus Firebase Auth. Never put the Admin SDK
 * service-account key here; that lives only in lib/firebase/admin.ts and is
 * used exclusively in server-only route handlers.
 *
 * This module is a singleton so every component/hook shares one initialized
 * app/auth/firestore instance instead of re-initializing on every render.
 */
import { initializeApp, getApps, getApp, type FirebaseApp } from 'firebase/app';
import { getAuth, GoogleAuthProvider, type Auth } from 'firebase/auth';
import { getFirestore, type Firestore } from 'firebase/firestore';

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
};

function assertConfigured() {
  const missing = Object.entries(firebaseConfig)
    .filter(([, v]) => !v)
    .map(([k]) => k);
  if (missing.length > 0 && typeof window !== 'undefined') {
    // Non-fatal warning only in the browser; lets the build succeed without
    // real credentials while making misconfiguration obvious at runtime.
    console.warn(
      `[firebase] Missing NEXT_PUBLIC_FIREBASE_* env vars: ${missing.join(', ')}. ` +
        'Authentication and chat history will not work until frontend/.env.local is configured.'
    );
  }
}

assertConfigured();

export const firebaseApp: FirebaseApp = getApps().length ? getApp() : initializeApp(firebaseConfig);
export const auth: Auth = getAuth(firebaseApp);
export const db: Firestore = getFirestore(firebaseApp);
export const googleProvider = new GoogleAuthProvider();

export function isFirebaseConfigured(): boolean {
  return Boolean(firebaseConfig.apiKey && firebaseConfig.projectId && firebaseConfig.appId);
}
