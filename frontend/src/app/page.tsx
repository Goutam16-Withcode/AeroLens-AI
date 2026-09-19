'use client';

import React, { useState } from 'react';
import { OrbitalHeader } from '../components/OrbitalHeader';
import { SensorIngestionDeck } from '../components/SensorIngestionDeck';
import { TacticalUplinkBar } from '../components/TacticalUplinkBar';
import { EvidenceVisualizer } from '../components/EvidenceVisualizer';
import { VlmSynthesisTerminal } from '../components/VlmSynthesisTerminal';
import { ExecutionTraceDeck } from '../components/ExecutionTraceDeck';
import { MissionArchiveGallery } from '../components/MissionArchiveGallery';
import { SpectralIndicesDeck } from '../components/SpectralIndicesDeck';
import { BitemporalSwipeSlider } from '../components/BitemporalSwipeSlider';
import { GeospatialTelemetryHUD } from '../components/GeospatialTelemetryHUD';
import { GeospatialLoupeEnhancer } from '../components/GeospatialLoupeEnhancer';
import { SatelliteOrbitRadar } from '../components/SatelliteOrbitRadar';
import { MissionBriefingModal } from '../components/MissionBriefingModal';
import { DetectedObjectsDeck } from '../components/DetectedObjectsDeck';
import { AnalysisResponse, BenchmarkMission } from '../types/satquery';

function dataURLtoFile(dataurl: string, filename: string): File {
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

export default function GroundStationPage() {
  const [fileA, setFileA] = useState<File | null>(null);
  const [previewA, setPreviewA] = useState<string | null>(null);
  const [modalityA, setModalityA] = useState<string>('Auto');

  const [fileB, setFileB] = useState<File | null>(null);
  const [previewB, setPreviewB] = useState<string | null>(null);
  const [modalityB, setModalityB] = useState<string>('Auto');

  const [query, setQuery] = useState<string>(
    'Describe the land cover, major objects, and overall scene composition in this remote sensing image.'
  );
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [response, setResponse] = useState<AnalysisResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Active View Tab on Right Column
  const [activeTab, setActiveTab] = useState<'matrix' | 'indices' | 'swipe' | 'hud' | 'loupe' | 'radar' | 'objects'>('matrix');

  // Mission Briefing Modal
  const [isBriefingOpen, setIsBriefingOpen] = useState<boolean>(false);

  const handleSelectMission = (mission: BenchmarkMission) => {
    setQuery(mission.query);
    setModalityA(mission.modality_a || 'Auto');
    setModalityB(mission.modality_b || 'Auto');

    if (mission.image_a_preview) {
      setPreviewA(mission.image_a_preview);
      setFileA(dataURLtoFile(mission.image_a_preview, 'sensor_a.png'));
    } else {
      setPreviewA(null);
      setFileA(null);
    }

    if (mission.image_b_preview) {
      setPreviewB(mission.image_b_preview);
      setFileB(dataURLtoFile(mission.image_b_preview, 'sensor_b.png'));
    } else {
      setPreviewB(null);
      setFileB(null);
    }
  };

  const handleSelectPreset = async (presetId: string, prompt: string) => {
    setQuery(prompt);

    // Fetch examples if needed to auto-load matching dataset pairs
    let examples: BenchmarkMission[] = [];
    try {
      const r = await fetch('http://localhost:8000/api/examples');
      if (r.ok) {
        const d = await r.json();
        examples = d.examples || [];
      }
    } catch {
      // ignore
    }

    if (presetId === 'sar_fusion') {
      setModalityA('Optical');
      setModalityB('SAR');
      setActiveTab('matrix');
      const fusionMission = examples.find((e) => e.id === 'bigearthnet_fusion' || e.category.includes('Fusion'));
      if (fusionMission && (!previewB || modalityB !== 'SAR')) {
        handleSelectMission(fusionMission);
      }
    } else if (presetId === 'bitemporal') {
      setModalityA('Optical');
      setModalityB('Optical');
      setActiveTab('swipe');
      const cdMission = examples.find((e) => e.id.includes('flood') || e.id.includes('cdvqa') || e.category.includes('Disaster') || e.category.includes('Bi-Temporal'));
      if (cdMission && !previewB) {
        handleSelectMission(cdMission);
      }
    } else if (presetId === 'multi_detect') {
      setModalityA('Optical');
      setActiveTab('objects');
      if (!previewA) {
        const vrsMission = examples.find((e) => e.id.includes('vrsbench'));
        if (vrsMission) handleSelectMission(vrsMission);
      }
    } else if (presetId === 'grounding') {
      setModalityA('Optical');
      setActiveTab('matrix');
      if (!previewA) {
        const vrsMission = examples.find((e) => e.id.includes('vrsbench'));
        if (vrsMission) handleSelectMission(vrsMission);
      }
    } else if (presetId === 'vqa') {
      setActiveTab('matrix');
      if (!previewA) {
        const rsvqaMission = examples.find((e) => e.id.includes('rsvqa'));
        if (rsvqaMission) handleSelectMission(rsvqaMission);
      }
    } else if (presetId === 'caption') {
      setActiveTab('matrix');
    } else if (presetId === 'wildfire') {
      setModalityA('Optical');
      setActiveTab('indices');
    } else if (presetId === 'maritime') {
      setModalityA('Optical');
      setActiveTab('objects');
    }
  };

  const handleTransmit = async () => {
    if (!fileA && !previewA) {
      setErrorMessage('Telemetry Alert: Primary sensor swath (Image A) is required.');
      return;
    }
    if (!query.trim()) {
      setErrorMessage('Mission objective uplink query cannot be empty.');
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);

    const formData = new FormData();
    formData.append('query', query);
    formData.append('modality_a', modalityA);
    formData.append('modality_b', modalityB);
    
    if (fileA) {
      formData.append('image_a', fileA);
    } else if (previewA) {
      formData.append('image_a', dataURLtoFile(previewA, 'sensor_a.png'));
    }

    if (fileB) {
      formData.append('image_b', fileB);
    } else if (previewB) {
      formData.append('image_b', dataURLtoFile(previewB, 'sensor_b.png'));
    }

    try {
      const res = await fetch('http://localhost:8000/api/analyze', {
        method: 'POST',
        body: formData,
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error || 'Pipeline execution encountered an issue.');
      }

      setResponse(data);
      if (data.detected_objects && data.detected_objects.length > 0) {
        setActiveTab('objects');
      }
    } catch (err: any) {
      setErrorMessage(err.message || 'Ground station downlink disconnected. Please ensure the backend is running.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ position: 'relative', minHeight: '100vh' }}>
      {/* Background Atmosphere */}
      <div className="space-canvas" />
      <div className="grid-overlay" />

      <main className="app-viewport">
        {/* Top Navbar */}
        <OrbitalHeader />

        {/* Action Bar: Briefing Generator */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', flexWrap: 'wrap', gap: '10px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--accent-amber)', display: 'inline-block' }} />
            <span>OPERATIONAL COCKPIT // 6 ADVANCED REMOTE SENSING DEVIATION TOOLS</span>
          </div>

          {response && (
            <button
              onClick={() => setIsBriefingOpen(true)}
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
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
              }}
            >
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14 2 14 8 20 8" />
                <line x1="16" y1="13" x2="8" y2="13" />
                <line x1="16" y1="17" x2="8" y2="17" />
              </svg>
              <span>GENERATE MISSION INTELLIGENCE BRIEFING (PDF)</span>
            </button>
          )}
        </div>

        {/* Error Alert */}
        {errorMessage && (
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
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#dc2626" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
              <span>{errorMessage}</span>
            </div>
            <button
              onClick={() => setErrorMessage(null)}
              style={{
                background: 'transparent',
                border: 'none',
                color: '#dc2626',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
              }}
            >
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </div>
        )}

        {/* Master 2-Column Command Grid */}
        <div className="command-grid">
          {/* Left Column: Ingestion & Control Uplink */}
          <div>
            <SensorIngestionDeck
              fileA={fileA}
              setFileA={setFileA}
              previewA={previewA}
              setPreviewA={setPreviewA}
              modalityA={modalityA}
              setModalityA={setModalityA}
              fileB={fileB}
              setFileB={setFileB}
              previewB={previewB}
              setPreviewB={setPreviewB}
              modalityB={modalityB}
              setModalityB={setModalityB}
            />

            <TacticalUplinkBar
              query={query}
              setQuery={setQuery}
              onTransmit={handleTransmit}
              isLoading={isLoading}
              onSelectPreset={handleSelectPreset}
            />

            <SatelliteOrbitRadar />
          </div>

          {/* Right Column: Multi-Feature Telemetry Hub */}
          <div>
            {/* View Tab Switcher */}
            <div
              style={{
                display: 'flex',
                gap: '6px',
                marginBottom: '12px',
                borderBottom: '1px solid var(--border-subtle)',
                paddingBottom: '8px',
                flexWrap: 'wrap',
              }}
            >
              <button
                onClick={() => setActiveTab('matrix')}
                style={{
                  padding: '6px 12px',
                  background: activeTab === 'matrix' ? 'var(--accent-amber-subtle)' : '#f5f0e8',
                  border: `1px solid ${activeTab === 'matrix' ? 'var(--accent-amber)' : 'var(--border-subtle)'}`,
                  borderRadius: '6px',
                  color: activeTab === 'matrix' ? 'var(--accent-amber)' : 'var(--text-secondary)',
                  fontFamily: 'var(--font-hud)',
                  fontSize: '11px',
                  fontWeight: 700,
                  cursor: 'pointer',
                  transition: 'all 0.18s ease',
                }}
              >
                [01] EVIDENCE MATRIX
              </button>

              <button
                onClick={() => setActiveTab('indices')}
                style={{
                  padding: '6px 12px',
                  background: activeTab === 'indices' ? 'var(--accent-amber-subtle)' : '#f5f0e8',
                  border: `1px solid ${activeTab === 'indices' ? 'var(--accent-amber)' : 'var(--border-subtle)'}`,
                  borderRadius: '6px',
                  color: activeTab === 'indices' ? 'var(--accent-amber)' : 'var(--text-secondary)',
                  fontFamily: 'var(--font-hud)',
                  fontSize: '11px',
                  fontWeight: 700,
                  cursor: 'pointer',
                  transition: 'all 0.18s ease',
                }}
              >
                [02] BAND MATH (NDVI/NDWI)
              </button>

              <button
                onClick={() => setActiveTab('swipe')}
                style={{
                  padding: '6px 12px',
                  background: activeTab === 'swipe' ? 'var(--accent-amber-subtle)' : '#f5f0e8',
                  border: `1px solid ${activeTab === 'swipe' ? 'var(--accent-amber)' : 'var(--border-subtle)'}`,
                  borderRadius: '6px',
                  color: activeTab === 'swipe' ? 'var(--accent-amber)' : 'var(--text-secondary)',
                  fontFamily: 'var(--font-hud)',
                  fontSize: '11px',
                  fontWeight: 700,
                  cursor: 'pointer',
                  transition: 'all 0.18s ease',
                }}
              >
                [03] COMPARISON SLIDER
              </button>

              <button
                onClick={() => setActiveTab('loupe')}
                style={{
                  padding: '6px 12px',
                  background: activeTab === 'loupe' ? 'var(--accent-amber-subtle)' : '#f5f0e8',
                  border: `1px solid ${activeTab === 'loupe' ? 'var(--accent-amber)' : 'var(--border-subtle)'}`,
                  borderRadius: '6px',
                  color: activeTab === 'loupe' ? 'var(--accent-amber)' : 'var(--text-secondary)',
                  fontFamily: 'var(--font-hud)',
                  fontSize: '11px',
                  fontWeight: 700,
                  cursor: 'pointer',
                  transition: 'all 0.18s ease',
                }}
              >
                [04] 3X LOUPE & CLAHE
              </button>

              <button
                onClick={() => setActiveTab('hud')}
                style={{
                  padding: '6px 12px',
                  background: activeTab === 'hud' ? 'var(--accent-amber-subtle)' : '#f5f0e8',
                  border: `1px solid ${activeTab === 'hud' ? 'var(--accent-amber)' : 'var(--border-subtle)'}`,
                  borderRadius: '6px',
                  color: activeTab === 'hud' ? 'var(--accent-amber)' : 'var(--text-secondary)',
                  fontFamily: 'var(--font-hud)',
                  fontSize: '11px',
                  fontWeight: 700,
                  cursor: 'pointer',
                  transition: 'all 0.18s ease',
                }}
              >
                [05] HUD INSPECTOR
              </button>

              <button
                onClick={() => setActiveTab('objects')}
                style={{
                  padding: '6px 12px',
                  background: activeTab === 'objects' ? 'var(--accent-amber-subtle)' : '#f5f0e8',
                  border: `1px solid ${activeTab === 'objects' ? 'var(--accent-amber)' : 'var(--border-subtle)'}`,
                  borderRadius: '6px',
                  color: activeTab === 'objects' ? 'var(--accent-amber)' : 'var(--text-secondary)',
                  fontFamily: 'var(--font-hud)',
                  fontSize: '11px',
                  fontWeight: 700,
                  cursor: 'pointer',
                  transition: 'all 0.18s ease',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                }}
              >
                <span>[06] TARGET DETECTIONS</span>
                {response?.detected_objects && response.detected_objects.length > 0 && (
                  <span
                    style={{
                      background: 'var(--accent-amber)',
                      color: '#ffffff',
                      borderRadius: '10px',
                      padding: '1px 6px',
                      fontSize: '9.5px',
                      fontWeight: 800,
                    }}
                  >
                    {response.detected_objects.length}
                  </span>
                )}
              </button>
            </div>

            {/* Tab Views */}
            {activeTab === 'matrix' && (
              <EvidenceVisualizer
                evidence={response?.evidence || null}
                isLoading={isLoading}
              />
            )}

            {activeTab === 'indices' && (
              <SpectralIndicesDeck
                fileA={fileA}
                previewA={previewA}
                onLoadBenchmarkSwath={async () => {
                  try {
                    const r = await fetch('http://localhost:8000/api/examples');
                    if (r.ok) {
                      const d = await r.json();
                      const examples = d.examples || [];
                      const m = examples.find((ex: any) => ex.image_a_preview) || examples[0];
                      if (m) handleSelectMission(m);
                    }
                  } catch (e) {
                    console.error('Failed to load benchmark swath:', e);
                  }
                }}
              />
            )}

            {activeTab === 'swipe' && (
              <BitemporalSwipeSlider
                imageBefore={previewA}
                imageAfter={previewB}
              />
            )}

            {activeTab === 'loupe' && (
              <GeospatialLoupeEnhancer
                imageSrc={previewA}
              />
            )}

            {activeTab === 'hud' && (
              <GeospatialTelemetryHUD
                imageSrc={previewA}
              />
            )}

            {activeTab === 'objects' && (
              <DetectedObjectsDeck
                objects={response?.detected_objects || []}
                annotatedImage={response?.evidence?.slot3_reticle_or_sar || null}
                isLoading={isLoading}
              />
            )}

            {/* VLM Synthesized Intelligence Terminal */}
            <VlmSynthesisTerminal
              answer={response?.answer || null}
              confidence={response?.trace?.confidence}
              isLoading={isLoading}
            />

            {/* Flight Recorder Execution Trace */}
            <ExecutionTraceDeck
              trace={response?.trace || null}
              fullResponse={response}
            />
          </div>
        </div>

        {/* Verified Mission Archive Presets */}
        <MissionArchiveGallery onSelectMission={handleSelectMission} />

        {/* Mission Briefing PDF Modal */}
        <MissionBriefingModal
          isOpen={isBriefingOpen}
          onClose={() => setIsBriefingOpen(false)}
          query={query}
          response={response}
        />

        {/* Footer */}
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
          SATQUERY AI // AUTONOMOUS MULTISPECTRAL AGENTIC VLM // NEXT.JS + FASTAPI COCKPIT
        </footer>
      </main>
    </div>
  );
}
