import { NextRequest, NextResponse } from 'next/server';
import { v2 as cloudinary } from 'cloudinary';
import { requireUid } from '@/lib/firebase/admin';

// Server-only Cloudinary config. CLOUDINARY_API_SECRET must never carry a
// NEXT_PUBLIC_ prefix and must never be sent to the browser.
cloudinary.config({
  cloud_name: process.env.CLOUDINARY_CLOUD_NAME,
  api_key: process.env.CLOUDINARY_API_KEY,
  api_secret: process.env.CLOUDINARY_API_SECRET,
});

const ALLOWED_FORMATS = new Set(['png', 'jpg', 'jpeg', 'webp']);
const MAX_UPLOAD_MB = 25;

/**
 * POST /api/cloudinary/sign
 * body: { conversationId: string, fileName: string, fileSizeBytes: number }
 *
 * Returns a signature scoped to a folder derived from the CALLER'S OWN uid
 * (taken from their verified ID token, never from client input), so a user
 * can never forge an upload into another user's folder, and cannot smuggle
 * an arbitrary Cloudinary public_id.
 */
export async function POST(req: NextRequest) {
  try {
    const uid = await requireUid(req.headers.get('authorization'));

    if (!process.env.CLOUDINARY_CLOUD_NAME || !process.env.CLOUDINARY_API_KEY || !process.env.CLOUDINARY_API_SECRET) {
      return NextResponse.json({ error: 'Cloudinary is not configured on the server.' }, { status: 503 });
    }

    const body = await req.json().catch(() => ({}));
    const conversationId: string = body.conversationId;
    const fileName: string = body.fileName || 'upload';
    const fileSizeBytes: number = Number(body.fileSizeBytes) || 0;

    if (!conversationId || typeof conversationId !== 'string') {
      return NextResponse.json({ error: 'conversationId is required.' }, { status: 400 });
    }

    const ext = (fileName.split('.').pop() || '').toLowerCase();
    if (ext && !ALLOWED_FORMATS.has(ext)) {
      return NextResponse.json({ error: `Unsupported file type: .${ext}. Allowed: PNG, JPG, WEBP.` }, { status: 400 });
    }
    if (fileSizeBytes > MAX_UPLOAD_MB * 1024 * 1024) {
      return NextResponse.json({ error: `File exceeds the ${MAX_UPLOAD_MB}MB upload limit.` }, { status: 400 });
    }

    // Folder is fully server-derived: aerolens/users/{uid}/conversations/{conversationId}/
    const folder = `aerolens/users/${uid}/conversations/${conversationId}`;
    const timestamp = Math.round(Date.now() / 1000);

    const paramsToSign: Record<string, string | number> = { timestamp, folder };
    const signature = cloudinary.utils.api_sign_request(paramsToSign, process.env.CLOUDINARY_API_SECRET);

    return NextResponse.json({
      signature,
      timestamp,
      folder,
      apiKey: process.env.CLOUDINARY_API_KEY,
      cloudName: process.env.CLOUDINARY_CLOUD_NAME,
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Unauthorized';
    return NextResponse.json({ error: message }, { status: 401 });
  }
}
