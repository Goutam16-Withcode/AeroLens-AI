import type { AnalysisResponse, BenchmarkMission } from '@/types/satquery';

/**
 * Thin wrapper around the EXISTING, UNMODIFIED FastAPI endpoints. This is a
 * refactor-only extraction of logic that previously lived inline in
 * app/page.tsx — the request/response shapes are identical to before.
 *
 * Deliberately still sends raw File objects as multipart/form-data (exactly
 * like the original cockpit), rather than Cloudinary URLs, because the
 * backend's /api/analyze only accepts UploadFile. This is the "compatible
 * adapter in Next.js" approach called for when the existing API doesn't
 * support URL-based input, and it means zero backend changes were needed.
 */
const FASTAPI_BASE_URL = process.env.NEXT_PUBLIC_FASTAPI_URL || 'http://localhost:8000';

export async function fetchExamples(): Promise<BenchmarkMission[]> {
  const res = await fetch(`${FASTAPI_BASE_URL}/api/examples`);
  if (!res.ok) return [];
  const data = await res.json();
  return data.examples || [];
}

export interface AnalyzeParams {
  query: string;
  modalityA: string;
  modalityB: string;
  fileA: File;
  fileB?: File | null;
}

export async function analyzeImagery(params: AnalyzeParams): Promise<AnalysisResponse> {
  const formData = new FormData();
  formData.append('query', params.query);
  formData.append('modality_a', params.modalityA);
  formData.append('modality_b', params.modalityB);
  formData.append('image_a', params.fileA);
  if (params.fileB) formData.append('image_b', params.fileB);

  const res = await fetch(`${FASTAPI_BASE_URL}/api/analyze`, { method: 'POST', body: formData });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.error || 'Pipeline execution encountered an issue.');
  }
  return data as AnalysisResponse;
}

export function dataURLtoFile(dataurl: string, filename: string): File {
  const arr = dataurl.split(',');
  const mime = arr[0].match(/:(.*?);/)?.[1] || 'image/png';
  const bstr = atob(arr[1]);
  let n = bstr.length;
  const u8arr = new Uint8Array(n);
  while (n--) {
    u8arr[n] = bstr.charCodeAt(n);
  }
  return new File([u8arr], filename, { type: mime });
}
