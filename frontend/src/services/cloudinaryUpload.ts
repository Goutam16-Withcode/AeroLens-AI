import { auth } from '@/lib/firebase/client';
import type { ImageRef } from '@/types/chat';

export interface UploadHandle {
  promise: Promise<ImageRef>;
  cancel: () => void;
}

async function authHeader(): Promise<HeadersInit> {
  const token = await auth.currentUser?.getIdToken();
  if (!token) throw new Error('You must be signed in to upload images.');
  return { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' };
}

function dataUrlToBlob(dataUrl: string): { blob: Blob; extension: string } {
  const [meta, b64] = dataUrl.split(',');
  const mime = meta.match(/:(.*?);/)?.[1] || 'image/png';
  const binary = atob(b64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  const extension = mime.split('/')[1] || 'png';
  return { blob: new Blob([bytes], { type: mime }), extension };
}

/**
 * Uploads a File (or a base64 data URL, e.g. an AI-generated evidence image)
 * to Cloudinary via a server-signed request, reporting progress and
 * supporting cancellation/retry. Never touches the Cloudinary API secret.
 */
export function uploadImage(
  fileOrDataUrl: File | string,
  opts: { conversationId: string; role: ImageRef['role']; fileName?: string; onProgress?: (pct: number) => void }
): UploadHandle {
  const xhr = new XMLHttpRequest();
  let cancelled = false;

  const promise = (async (): Promise<ImageRef> => {
    const file: Blob =
      typeof fileOrDataUrl === 'string' ? dataUrlToBlob(fileOrDataUrl).blob : fileOrDataUrl;
    const fileName =
      opts.fileName || (typeof fileOrDataUrl === 'string' ? `${opts.role}.png` : fileOrDataUrl.name);

    const headers = await authHeader();
    const signRes = await fetch('/api/cloudinary/sign', {
      method: 'POST',
      headers,
      body: JSON.stringify({ conversationId: opts.conversationId, fileName, fileSizeBytes: file.size }),
    });
    const signData = await signRes.json();
    if (!signRes.ok) throw new Error(signData.error || 'Failed to authorize upload.');

    const { signature, timestamp, folder, apiKey, cloudName } = signData;

    const form = new FormData();
    form.append('file', file, fileName);
    form.append('api_key', apiKey);
    form.append('timestamp', String(timestamp));
    form.append('signature', signature);
    form.append('folder', folder);

    return await new Promise<ImageRef>((resolve, reject) => {
      xhr.open('POST', `https://api.cloudinary.com/v1_1/${cloudName}/image/upload`);
      xhr.upload.onprogress = (evt) => {
        if (evt.lengthComputable && opts.onProgress) {
          opts.onProgress(Math.round((evt.loaded / evt.total) * 100));
        }
      };
      xhr.onload = () => {
        if (cancelled) return;
        try {
          const res = JSON.parse(xhr.responseText);
          if (xhr.status >= 200 && xhr.status < 300) {
            resolve({
              imageUrl: res.secure_url,
              publicId: res.public_id,
              fileName,
              format: res.format,
              width: res.width,
              height: res.height,
              resourceType: 'image',
              role: opts.role,
            });
          } else {
            reject(new Error(res?.error?.message || 'Cloudinary upload failed.'));
          }
        } catch {
          reject(new Error('Cloudinary returned an unexpected response.'));
        }
      };
      xhr.onerror = () => reject(new Error('Network error during image upload.'));
      xhr.onabort = () => reject(new Error('Upload cancelled.'));
      xhr.send(form);
    });
  })();

  return {
    promise,
    cancel: () => {
      cancelled = true;
      xhr.abort();
    },
  };
}

/** Deletes a single orphaned image (e.g. user removed an attachment before sending). */
export async function deleteImageByPublicId(publicId: string): Promise<void> {
  const headers = await authHeader();
  await fetch('/api/cloudinary/delete', { method: 'POST', headers, body: JSON.stringify({ publicId }) });
}

/** Deletes every image belonging to a conversation being permanently deleted. */
export async function deleteConversationImages(conversationId: string): Promise<void> {
  const headers = await authHeader();
  const res = await fetch('/api/cloudinary/delete', { method: 'POST', headers, body: JSON.stringify({ conversationId }) });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.error || 'Failed to clean up conversation images.');
  }
}
