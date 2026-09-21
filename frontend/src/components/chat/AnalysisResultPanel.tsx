'use client';

import React, { useState } from 'react';
import { EvidenceVisualizer } from '../EvidenceVisualizer';
import { SpectralIndicesDeck } from '../SpectralIndicesDeck';
import { BitemporalSwipeSlider } from '../BitemporalSwipeSlider';
import { GeospatialLoupeEnhancer } from '../GeospatialLoupeEnhancer';
import { GeospatialTelemetryHUD } from '../GeospatialTelemetryHUD';
import { DetectedObjectsDeck } from '../DetectedObjectsDeck';
import { VlmSynthesisTerminal } from '../VlmSynthesisTerminal';
import { ExecutionTraceDeck } from '../ExecutionTraceDeck';
import type { AnalysisResponse } from '@/types/satquery';

type Tab = 'matrix' | 'indices' | 'swipe' | 'hud' | 'loupe' | 'radar' | 'objects';

interface Props {
  response: AnalysisResponse | null;
  previewA: string | null;
  previewB: string | null;
  isLoading: boolean;
  onGenerateBriefing?: () => void;
  fileA?: File | null;
}

const TAB_LABELS: Record<Tab, string> = {
  matrix: '[01] EVIDENCE MATRIX',
  indices: '[02] BAND MATH (NDVI/NDWI)',
  swipe: '[03] COMPARISON SLIDER',
  loupe: '[04] 3X LOUPE & CLAHE',
  hud: '[05] HUD INSPECTOR',
  radar: '[06] TARGET DETECTIONS',
  objects: '[06] TARGET DETECTIONS',
};

export const AnalysisResultPanel: React.FC<Props> = ({ response, previewA, previewB, isLoading, onGenerateBriefing, fileA }) => {
  const [activeTab, setActiveTab] = useState<Tab>('matrix');

  const tabButton = (tab: Tab, label: string, badge?: number) => (
    <button
      key={tab}
      onClick={() => setActiveTab(tab)}
      style={{
        padding: '6px 12px',
        background: activeTab === tab ? 'var(--accent-amber-subtle)' : '#f5f0e8',
        border: `1px solid ${activeTab === tab ? 'var(--accent-amber)' : 'var(--border-subtle)'}`,
        borderRadius: '6px',
        color: activeTab === tab ? 'var(--accent-amber)' : 'var(--text-secondary)',
        fontFamily: 'var(--font-hud)',
        fontSize: '11px',
        fontWeight: 700,
        cursor: 'pointer',
        display: 'flex',
        alignItems: 'center',
        gap: '6px',
      }}
    >
      <span>{label}</span>
      {badge !== undefined && badge > 0 && (
        <span
          style={{
            background: 'var(--accent-amber)',
            color: '#fff',
            borderRadius: '10px',
            padding: '1px 6px',
            fontSize: '9.5px',
            fontWeight: 800,
          }}
        >
          {badge}
        </span>
      )}
    </button>
  );

  return (
    <div>
      {onGenerateBriefing && response && (
        <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '10px' }}>
          <button
            onClick={onGenerateBriefing}
            style={{
              padding: '6px 14px',
              background: 'var(--accent-amber-subtle)',
              border: '1px solid var(--accent-amber-border)',
              borderRadius: '6px',
              color: 'var(--accent-amber)',
              fontFamily: 'var(--font-mono)',
              fontSize: '11px',
              fontWeight: 700,
              cursor: 'pointer',
            }}
          >
            GENERATE MISSION INTELLIGENCE BRIEFING (PDF)
          </button>
        </div>
      )}

      <div style={{ display: 'flex', gap: '6px', marginBottom: '12px', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '8px', flexWrap: 'wrap' }}>
        {tabButton('matrix', TAB_LABELS.matrix)}
        {tabButton('indices', TAB_LABELS.indices)}
        {tabButton('swipe', TAB_LABELS.swipe)}
        {tabButton('loupe', TAB_LABELS.loupe)}
        {tabButton('hud', TAB_LABELS.hud)}
        {tabButton('objects', TAB_LABELS.objects, response?.detected_objects?.length)}
      </div>

      {activeTab === 'matrix' && <EvidenceVisualizer evidence={response?.evidence || null} isLoading={isLoading} />}
      {activeTab === 'indices' && <SpectralIndicesDeck fileA={fileA ?? null} previewA={previewA} onLoadBenchmarkSwath={async () => {}} />}
      {activeTab === 'swipe' && <BitemporalSwipeSlider imageBefore={previewA} imageAfter={previewB} />}
      {activeTab === 'loupe' && <GeospatialLoupeEnhancer imageSrc={previewA} />}
      {activeTab === 'hud' && <GeospatialTelemetryHUD imageSrc={previewA} />}
      {activeTab === 'objects' && (
        <DetectedObjectsDeck
          objects={response?.detected_objects || []}
          annotatedImage={response?.evidence?.slot3_reticle_or_sar || null}
          isLoading={isLoading}
        />
      )}

      <VlmSynthesisTerminal answer={response?.answer || null} confidence={response?.trace?.confidence} isLoading={isLoading} />
      <ExecutionTraceDeck trace={response?.trace || null} fullResponse={response} />
    </div>
  );
};
