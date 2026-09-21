'use client';

import { useEffect, useState, useCallback } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import {
  subscribeToConversations,
  renameConversation,
  deleteConversationDeep,
} from '@/services/conversationService';
import { deleteConversationImages } from '@/services/cloudinaryUpload';
import type { Conversation } from '@/types/chat';

export function useConversations() {
  const { user } = useAuth();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- clears stale data synchronously when the user signs out; no subscription is started in this branch.
      setConversations([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    const unsubscribe = subscribeToConversations(
      user.uid,
      (items) => {
        setConversations(items);
        setLoading(false);
        setError(null);
      },
      (err) => {
        setError(err.message || 'Could not load conversation history.');
        setLoading(false);
      }
    );
    return unsubscribe;
  }, [user]);

  const rename = useCallback(
    async (conversationId: string, title: string) => {
      if (!user) return;
      await renameConversation(user.uid, conversationId, title);
    },
    [user]
  );

  /**
   * Deletes the Firestore records first (so the UI updates immediately),
   * then attempts Cloudinary cleanup. If Cloudinary cleanup fails (e.g.
   * network issue, misconfiguration), the conversation is still gone from
   * the user's history — we surface the storage-cleanup failure separately
   * rather than blocking or reverting the deletion the user asked for.
   */
  const remove = useCallback(
    async (conversationId: string): Promise<{ storageCleanupFailed: boolean }> => {
      if (!user) return { storageCleanupFailed: false };
      await deleteConversationDeep(user.uid, conversationId);
      try {
        await deleteConversationImages(conversationId);
        return { storageCleanupFailed: false };
      } catch {
        return { storageCleanupFailed: true };
      }
    },
    [user]
  );

  return { conversations, loading, error, rename, remove };
}
