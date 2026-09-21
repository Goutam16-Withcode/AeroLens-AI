import type { Timestamp } from 'firebase/firestore';
import type { AnalysisResponse, DetectedObject, ExecutionTrace } from './satquery';

/** A single stored image reference (Cloudinary-backed). Never store binary/base64 here. */
export interface ImageRef {
  imageUrl: string;
  publicId: string;
  fileName: string;
  format: string;
  width: number;
  height: number;
  resourceType: 'image';
  /** Which role this image played in the turn. */
  role: 'input_a' | 'input_b' | 'evidence_original' | 'evidence_attention' | 'evidence_reticle' | 'evidence_after';
}

export type MessageRole = 'user' | 'assistant' | 'system';
export type MessageStatus = 'pending' | 'completed' | 'failed';

export interface MessageMetadata {
  modalityA?: string;
  modalityB?: string;
  detected_objects?: DetectedObject[];
  trace?: ExecutionTrace | null;
  trace_markdown?: string;
  errorMessage?: string;
}

export interface ChatMessage {
  messageId: string;
  conversationId: string;
  role: MessageRole;
  content: string;
  images: ImageRef[];
  createdAt: Timestamp | null;
  status: MessageStatus;
  metadata?: MessageMetadata;
}

export interface Conversation {
  conversationId: string;
  title: string;
  createdAt: Timestamp | null;
  updatedAt: Timestamp | null;
  lastMessage: string;
  messageCount: number;
}

/** Local (optimistic) shape used before Firestore assigns server timestamps. */
export interface DraftMessage extends Omit<ChatMessage, 'createdAt'> {
  createdAt: Timestamp | null;
  clientId: string;
}

/** Bundles everything needed to render one AI turn using existing cockpit components. */
export type TurnResult = AnalysisResponse;
