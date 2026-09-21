import { NextRequest, NextResponse } from 'next/server';
import { v2 as cloudinary } from 'cloudinary';
import { requireUid } from '@/lib/firebase/admin';

cloudinary.config({
  cloud_name: process.env.CLOUDINARY_CLOUD_NAME,
  api_key: process.env.CLOUDINARY_API_KEY,
  api_secret: process.env.CLOUDINARY_API_SECRET,
});

/**
 * POST /api/cloudinary/delete
 * body EITHER:
 *   { publicId: string }                 — remove one orphaned image (e.g. user
 *                                          removed an attachment before sending,
 *                                          or a single message failed permanently)
 *   { conversationId: string }           — remove every image belonging to a
 *                                          conversation that is being permanently
 *                                          deleted (bulk prefix delete)
 *
 * Every path is authorized by checking the target path is namespaced under
 * `aerolens/users/{uid}/...` for the CALLER'S OWN verified uid — never trusts
 * a client-supplied uid, and a user can never delete another user's images.
 *
 * Because every image is namespaced under its own conversationId folder
 * (see /api/cloudinary/sign), a folder-prefix delete for one conversation can
 * never remove an image that is still referenced by messages in a different
 * conversation.
 */
export async function POST(req: NextRequest) {
  try {
    const uid = await requireUid(req.headers.get('authorization'));

    if (!process.env.CLOUDINARY_CLOUD_NAME || !process.env.CLOUDINARY_API_KEY || !process.env.CLOUDINARY_API_SECRET) {
      return NextResponse.json({ error: 'Cloudinary is not configured on the server.' }, { status: 503 });
    }

    const body = await req.json().catch(() => ({}));
    const userPrefix = `aerolens/users/${uid}/`;

    if (typeof body.publicId === 'string') {
      if (!body.publicId.startsWith(userPrefix)) {
        return NextResponse.json({ error: 'Forbidden: image does not belong to this user.' }, { status: 403 });
      }
      const result = await cloudinary.uploader.destroy(body.publicId, { resource_type: 'image' });
      return NextResponse.json({ result });
    }

    if (typeof body.conversationId === 'string' && body.conversationId) {
      const folder = `${userPrefix}conversations/${body.conversationId}`;
      await cloudinary.api.delete_resources_by_prefix(folder).catch((err: unknown) => {
        // Not fatal for the app: Firestore deletion already happened, and an
        // orphaned Cloudinary asset costs storage but is not a data leak.
        // We surface it so the caller can inform the user of a partial cleanup.
        throw err;
      });
      await cloudinary.api.delete_folder(folder).catch(() => {
        /* folder may already be empty/absent; ignore */
      });
      return NextResponse.json({ result: 'ok' });
    }

    return NextResponse.json({ error: 'Provide either publicId or conversationId.' }, { status: 400 });
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Unauthorized';
    const status = message === 'Missing bearer token' ? 401 : 500;
    return NextResponse.json({ error: message }, { status });
  }
}
