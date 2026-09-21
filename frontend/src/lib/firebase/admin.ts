/**
 * Firebase ADMIN SDK initialization — SERVER ONLY.
 *
 * Never import this file from a Client Component or anything bundled to the
 * browser. It reads FIREBASE_ADMIN_* secrets (private key etc.) which must
 * never be exposed with a NEXT_PUBLIC_ prefix. It is used only inside
 * Next.js Route Handlers (app/api/**\/route.ts) to:
 *   - verify a user's Firebase ID token before trusting `uid` on the server
 *   - perform privileged Cloudinary cleanup tied to Firestore ownership checks
 *
 * All normal chat CRUD (reading/writing conversations & messages) happens
 * client-side with the Firebase client SDK, gated by firestore.rules —
 * Admin SDK is intentionally NOT used for that, per the "prefer client SDK,
 * Admin only for trusted server-side ops" requirement.
 */
import { getApps, getApp, initializeApp, cert, type App } from 'firebase-admin/app';
import { getAuth, type Auth } from 'firebase-admin/auth';

function buildAdminApp(): App {
  if (getApps().length) return getApp();

  const projectId = process.env.FIREBASE_ADMIN_PROJECT_ID;
  const clientEmail = process.env.FIREBASE_ADMIN_CLIENT_EMAIL;
  // Private keys stored in .env files usually have literal "\n" sequences;
  // they must be converted back to real newlines before use.
  const privateKey = process.env.FIREBASE_ADMIN_PRIVATE_KEY?.replace(/\\n/g, '\n');

  if (!projectId || !clientEmail || !privateKey) {
    throw new Error(
      'Firebase Admin SDK is not configured. Set FIREBASE_ADMIN_PROJECT_ID, ' +
        'FIREBASE_ADMIN_CLIENT_EMAIL, and FIREBASE_ADMIN_PRIVATE_KEY in your server environment ' +
        '(never with a NEXT_PUBLIC_ prefix).'
    );
  }

  return initializeApp({
    credential: cert({ projectId, clientEmail, privateKey }),
  });
}

let cachedAuth: Auth | null = null;

/** Lazily initialized so route handlers that don't need Admin never crash the build. */
export function getAdminAuth(): Auth {
  if (!cachedAuth) {
    cachedAuth = getAuth(buildAdminApp());
  }
  return cachedAuth;
}

/**
 * Verifies the Firebase ID token sent from the client (Authorization: Bearer <token>)
 * and returns the trusted uid. Throws if the token is missing/invalid/expired.
 */
export async function requireUid(authorizationHeader: string | null): Promise<string> {
  if (!authorizationHeader?.startsWith('Bearer ')) {
    throw new Error('Missing bearer token');
  }
  const idToken = authorizationHeader.slice('Bearer '.length);
  const decoded = await getAdminAuth().verifyIdToken(idToken);
  return decoded.uid;
}
