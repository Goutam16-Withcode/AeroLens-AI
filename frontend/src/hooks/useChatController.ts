'use client';

import { useCallback, useRef, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { createConversation, touchConversation, deriveTitleFromMessage } from '@/services/conversationService';
import { saveMessage, updateMessageStatus } from '@/services/messageService';
import { uploadImage } from '@/services/cloudinaryUpload';
import { analyzeImagery } from '@/services/satqueryApi';
import type { AnalysisResponse } from '@/types/satquery';
import type { ImageRef } from '@/types/chat';

export interface SendMessageInput {
  query: string;
  fileA: File | null;
  fileB: File | null;
  modalityA: string;
  modalityB: string;
}

/** Keeps the original File objects for a turn in memory so "Retry" can re-run
 *  the analysis without asking the user to re-attach images. Cleared once
 *  the turn succeeds; capped implicitly by only tracking the latest attempt
 *  per assistant message id. This is intentionally in-memory only — it is
 *  lost on refresh, which is acceptable since a refreshed page shows the
 *  already-persisted (or already-failed, re-attachable) history. */
type RetryCache = Map<string, SendMessageInput>;

export function useChatController(activeConversationId: string | null, setActiveConversationId: (id: string) => void) {
  const { user } = useAuth();
  const [isSending, setIsSending] = useState(false);
  const [sendError, setSendError] = useState<string | null>(null);
  const retryCache = useRef<RetryCache>(new Map());

  const uploadEvidenceImages = useCallback(
    async (conversationId: string, evidence: AnalysisResponse['evidence']): Promise<ImageRef[]> => {
      const slots: { key: keyof typeof evidence; role: ImageRef['role'] }[] = [
        { key: 'slot1_original', role: 'evidence_original' },
        { key: 'slot2_attention_or_diff', role: 'evidence_attention' },
        { key: 'slot3_reticle_or_sar', role: 'evidence_reticle' },
        { key: 'slot4_after', role: 'evidence_after' },
      ];
      const uploads = await Promise.allSettled(
        slots.map(async ({ key, role }) => {
          const dataUrl = evidence[key] as string | null;
          if (!dataUrl) return null;
          const handle = uploadImage(dataUrl, { conversationId, role });
          return await handle.promise;
        })
      );
      return uploads.filter((r): r is PromiseFulfilledResult<ImageRef> => r.status === 'fulfilled' && !!r.value).map((r) => r.value);
    },
    []
  );

  const runTurn = useCallback(
    async (conversationId: string, userMessageId: string, input: SendMessageInput) => {
      if (!user) return;
      const assistantMessageId = crypto.randomUUID();
      retryCache.current.set(assistantMessageId, input);

      // Placeholder assistant message so the UI can show a loading indicator
      // tied to a real message id (needed for the retry button).
      await saveMessage(user.uid, conversationId, assistantMessageId, {
        role: 'assistant',
        content: '',
        images: [],
        status: 'pending',
      });

      try {
        const result = await analyzeImagery({
          query: input.query,
          modalityA: input.modalityA,
          modalityB: input.modalityB,
          fileA: input.fileA as File,
          fileB: input.fileB,
        });

        const evidenceImages = await uploadEvidenceImages(conversationId, result.evidence);

        await updateMessageStatus(user.uid, conversationId, assistantMessageId, {
          content: result.answer,
          images: evidenceImages,
          status: 'completed',
          metadata: {
            modalityA: input.modalityA,
            modalityB: input.modalityB,
            detected_objects: result.detected_objects,
            trace: result.trace,
            trace_markdown: result.trace_markdown,
          },
        });

        await touchConversation(user.uid, conversationId, result.answer.slice(0, 200), 2, 0);
        retryCache.current.delete(assistantMessageId);
      } catch (err) {
        // Critically: the user's original message (already saved before this
        // function runs) is never touched here, satisfying "failed AI
        // responses do not erase the user's original message."
        const message = (err as Error).message || 'AI processing failed. The ground station link may be down.';
        await updateMessageStatus(user.uid, conversationId, assistantMessageId, {
          status: 'failed',
          metadata: { errorMessage: message },
        });
        setSendError(message);
      }
    },
    [user, uploadEvidenceImages]
  );

  const sendMessage = useCallback(
    async (input: SendMessageInput) => {
      if (!user) return;
      if (!input.fileA) {
        setSendError('Primary sensor swath (Image A) is required.');
        return;
      }
      if (!input.query.trim()) {
        setSendError('Mission objective uplink query cannot be empty.');
        return;
      }
      setSendError(null);
      setIsSending(true);
      try {
        let conversationId = activeConversationId;
        if (!conversationId) {
          conversationId = await createConversation(user.uid, input.query);
          setActiveConversationId(conversationId);
        }

        const userMessageId = crypto.randomUUID();
        // Upload input images in the background; the user message is saved
        // immediately with an empty images array and backfilled once the
        // uploads resolve, so sending never blocks on Cloudinary latency.
        await saveMessage(user.uid, conversationId, userMessageId, {
          role: 'user',
          content: input.query,
          images: [],
          status: 'completed',
        });

        uploadInputImages(conversationId, input).then((images) => {
          if (images.length > 0) {
            updateMessageStatus(user!.uid, conversationId!, userMessageId, { images }).catch(() => {
              /* best-effort: history display falls back to no thumbnail if this fails */
            });
          }
        });

        await touchConversation(user.uid, conversationId, input.query.slice(0, 200), 1, 0);
        await runTurn(conversationId, userMessageId, input);
      } finally {
        setIsSending(false);
      }
    },
    [user, activeConversationId, setActiveConversationId, runTurn]
  );

  const retry = useCallback(
    async (assistantMessageId: string) => {
      const cached = retryCache.current.get(assistantMessageId);
      if (!cached || !user || !activeConversationId) {
        setSendError('This turn can no longer be retried — please resend your message with the images attached.');
        return;
      }
      setIsSending(true);
      setSendError(null);
      try {
        await updateMessageStatus(user.uid, activeConversationId, assistantMessageId, { status: 'pending' });
        const result = await analyzeImagery({
          query: cached.query,
          modalityA: cached.modalityA,
          modalityB: cached.modalityB,
          fileA: cached.fileA as File,
          fileB: cached.fileB,
        });
        const evidenceImages = await uploadEvidenceImages(activeConversationId, result.evidence);
        await updateMessageStatus(user.uid, activeConversationId, assistantMessageId, {
          content: result.answer,
          images: evidenceImages,
          status: 'completed',
          metadata: {
            modalityA: cached.modalityA,
            modalityB: cached.modalityB,
            detected_objects: result.detected_objects,
            trace: result.trace,
            trace_markdown: result.trace_markdown,
          },
        });
        retryCache.current.delete(assistantMessageId);
      } catch (err) {
        const message = (err as Error).message || 'Retry failed.';
        await updateMessageStatus(user.uid, activeConversationId, assistantMessageId, {
          status: 'failed',
          metadata: { errorMessage: message },
        });
        setSendError(message);
      } finally {
        setIsSending(false);
      }
    },
    [user, activeConversationId, uploadEvidenceImages]
  );

  return { sendMessage, retry, isSending, sendError, clearSendError: () => setSendError(null) };
}

async function uploadInputImages(conversationId: string, input: SendMessageInput): Promise<ImageRef[]> {
  const jobs: Promise<ImageRef | null>[] = [];
  if (input.fileA) {
    jobs.push(uploadImage(input.fileA, { conversationId, role: 'input_a' }).promise.catch(() => null));
  }
  if (input.fileB) {
    jobs.push(uploadImage(input.fileB, { conversationId, role: 'input_b' }).promise.catch(() => null));
  }
  const results = await Promise.all(jobs);
  return results.filter((r): r is ImageRef => !!r);
}

export { deriveTitleFromMessage };
