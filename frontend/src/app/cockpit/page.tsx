'use client';

import React, { useState } from 'react';
import { OrbitalHeader } from '../../components/OrbitalHeader';
import { MissionArchiveGallery } from '../../components/MissionArchiveGallery';
import { MissionBriefingModal } from '../../components/MissionBriefingModal';
import { Sidebar } from '../../components/chat/Sidebar';
import { ChatComposer } from '../../components/chat/ChatComposer';
import { ChatMessageList } from '../../components/chat/ChatMessageList';
import { useMessages } from '@/hooks/useMessages';
import { useChatController } from '@/hooks/useChatController';
import type { AnalysisResponse } from '../../types/satquery';

export default function GroundStationPage() {
    const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
    const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
    const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
    const [briefing, setBriefing] = useState<{ query: string; response: AnalysisResponse } | null>(null);

    const { messages, loading, loadingMore, hasMore, loadOlder, error: messagesError } = useMessages(activeConversationId);
    const { sendMessage, retry, isSending, sendError, clearSendError } = useChatController(activeConversationId, setActiveConversationId);

    const handleGenerateBriefing = (response: AnalysisResponse, query: string) => setBriefing({ query, response });

    // The mission archive gallery below the composer is presentational-only
    // here for discovery; ChatComposer owns its own preset/mission-loading
    // logic so a selection always lands in the currently-open composer.
    const handleSelectMissionNoop = () => { };

    return (
        <div>
            <Sidebar
                activeConversationId={activeConversationId}
                onSelectConversation={setActiveConversationId}
                isOpen={mobileSidebarOpen}
                onClose={() => setMobileSidebarOpen(false)}
                collapsed={sidebarCollapsed}
            />

            {/* The sidebar is position:fixed (so it stays put on scroll regardless
          of page height), which takes it out of normal flow — this margin
          is what actually reserves its space next to the content. */}
            <div
                className="app-shell-content"
                style={{
                    position: 'relative',
                    minHeight: '100vh',
                    marginLeft: sidebarCollapsed ? 0 : 272,
                    transition: 'margin-left 0.18s ease',
                }}
            >
                <div className="space-canvas" />
                <div className="grid-overlay" />

                <main className="app-viewport">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
                        <button
                            className="sidebar-toggle-mobile"
                            onClick={() => setMobileSidebarOpen(true)}
                            style={{
                                display: 'none',
                                border: '1px solid var(--border-light)',
                                background: 'var(--bg-surface)',
                                borderRadius: 'var(--radius-sm)',
                                width: '34px',
                                height: '34px',
                                cursor: 'pointer',
                                fontSize: '16px',
                                flexShrink: 0,
                            }}
                            aria-label="Open conversation history"
                        >
                            ☰
                        </button>
                        <button
                            onClick={() => setSidebarCollapsed((v) => !v)}
                            style={{
                                border: '1px solid var(--border-light)',
                                background: 'var(--bg-surface)',
                                borderRadius: 'var(--radius-sm)',
                                width: '34px',
                                height: '34px',
                                cursor: 'pointer',
                                fontSize: '13px',
                                flexShrink: 0,
                            }}
                            title={sidebarCollapsed ? 'Show conversation history' : 'Hide conversation history'}
                            className="sidebar-toggle-desktop"
                        >
                            {sidebarCollapsed ? '»' : '«'}
                        </button>
                        <div style={{ flex: 1 }}>
                            <OrbitalHeader />
                        </div>
                    </div>

                    {(sendError || messagesError) && (
                        <div
                            style={{
                                background: '#fef2f2',
                                border: '1px solid #fecaca',
                                color: '#991b1b',
                                borderRadius: '8px',
                                padding: '10px 14px',
                                marginBottom: '16px',
                                fontFamily: 'var(--font-mono)',
                                fontSize: '12px',
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'center',
                            }}
                        >
                            <span>{sendError || messagesError}</span>
                            {sendError && (
                                <button onClick={clearSendError} style={{ background: 'transparent', border: 'none', color: '#dc2626', cursor: 'pointer' }}>
                                    ✕
                                </button>
                            )}
                        </div>
                    )}

                    <div className="command-grid">
                        {/* Left Column: persistent composer (unchanged ingestion/uplink UX) */}
                        <div>
                            <ChatComposer onSend={sendMessage} isSending={isSending} />
                        </div>

                        {/* Right Column: chat history for the active conversation.
                alignSelf: 'stretch' overrides the grid's align-items:start
                so this column's height always matches the left column's
                natural (content-driven) height, instead of using a
                viewport-relative height that drifts out of sync with it. */}
                        <div
                            className="panel-card"
                            style={{ alignSelf: 'stretch', minHeight: '480px', overflowY: 'auto', padding: 0 }}
                        >
                            <ChatMessageList
                                messages={messages}
                                loading={loading}
                                hasMore={hasMore}
                                loadingMore={loadingMore}
                                onLoadOlder={loadOlder}
                                onRetry={retry}
                                onGenerateBriefing={handleGenerateBriefing}
                            />
                        </div>
                    </div>

                    <MissionArchiveGallery onSelectMission={handleSelectMissionNoop} />

                    <MissionBriefingModal
                        isOpen={!!briefing}
                        onClose={() => setBriefing(null)}
                        query={briefing?.query || ''}
                        response={briefing?.response || null}
                    />

                    <footer
                        style={{
                            marginTop: '36px',
                            textAlign: 'center',
                            fontSize: '11px',
                            fontFamily: 'var(--font-mono)',
                            color: 'var(--text-muted)',
                            letterSpacing: '0.06em',
                        }}
                    >
                        AEROLENS AI // AUTONOMOUS ORBITAL EARTH OBSERVATION COCKPIT
                    </footer>
                </main>
            </div>

            <style>{`
        @media (max-width: 860px) {
          .sidebar-toggle-mobile { display: flex !important; align-items: center; justify-content: center; }
          .sidebar-toggle-desktop { display: none !important; }
          .app-shell-content { margin-left: 0 !important; }
        }
      `}</style>
        </div>
    );
}