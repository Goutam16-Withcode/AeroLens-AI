'use client';

import React, { useState } from 'react';
import { OrbitalHeader } from '../components/OrbitalHeader';
import { SensorIngestionDeck } from '../components/SensorIngestionDeck';
import { TacticalUplinkBar } from '../components/TacticalUplinkBar';
import { EvidenceVisualizer } from '../components/EvidenceVisualizer';
import { VlmSynthesisTerminal } from '../components/VlmSynthesisTerminal';
import { ExecutionTraceDeck } from '../components/ExecutionTraceDeck';
import { MissionArchiveGallery } from '../components/MissionArchiveGallery';
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

  const handleSelectMission = (mission: BenchmarkMission) => {
    setQuery(mission.query);
    setModalityA(mission.modality_a || 'Auto');
    setModalityB(mission.modality_b || 'Auto');

    if (mission.image_a_preview) {
      setPreviewA(mission.image_a_preview);
      setFileA(dataURLtoFile(mission.image_a_preview, 'sensor_a.png'));
    }

    if (mission.image_b_preview) {
      setPreviewB(mission.image_b_preview);
      setFileB(dataURLtoFile(mission.image_b_preview, 'sensor_b.png'));
    } else {
      setPreviewB(null);
      setFileB(null);
    }

    window.scrollTo({ top: 100, behavior: 'smooth' });
  };

  const handleTransmit = async () => {
    if (!fileA) {
      setErrorMessage('Please ingest primary Sensor A swath or select a verified benchmark mission preset below.');
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
    formData.append('image_a', fileA);
    if (fileB) {
      formData.append('image_b', fileB);
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

        {/* Error Alert */}
        {errorMessage && (
          <div
            style={{
              background: 'rgba(244, 63, 94, 0.1)',
              border: '1px solid rgba(244, 63, 94, 0.25)',
              color: '#fecdd3',
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
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#f43f5e" strokeWidth="2">
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
                color: '#f43f5e',
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
            />
          </div>

          {/* Right Column: Multi-Spectral Matrix & Intelligence Terminal */}
          <div>
            <EvidenceVisualizer
              evidence={response?.evidence || null}
              isLoading={isLoading}
            />

            <VlmSynthesisTerminal
              answer={response?.answer || null}
              confidence={response?.trace?.confidence}
              isLoading={isLoading}
            />

            <ExecutionTraceDeck
              trace={response?.trace || null}
              fullResponse={response}
            />
          </div>
        </div>

        {/* Verified Mission Archive Presets */}
        <MissionArchiveGallery onSelectMission={handleSelectMission} />

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
