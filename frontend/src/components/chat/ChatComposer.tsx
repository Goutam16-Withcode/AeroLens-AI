'use client';

import React, { useState } from 'react';
import { SensorIngestionDeck } from '../SensorIngestionDeck';
import { TacticalUplinkBar } from '../TacticalUplinkBar';
import { SatelliteOrbitRadar } from '../SatelliteOrbitRadar';
import { fetchExamples, dataURLtoFile } from '@/services/satqueryApi';
import type { BenchmarkMission } from '@/types/satquery';

interface Props {
  onSend: (input: { query: string; fileA: File | null; fileB: File | null; modalityA: string; modalityB: string }) => Promise<void>;
  isSending: boolean;
}

const DEFAULT_QUERY =
  'Execute an exhaustive, high-depth scientific intelligence evaluation of this satellite imagery: synthesize platform telemetry, radiometric channel physics, cloud microphysics, terrestrial geomorphology, and tactical hazard advisories.';

export const ChatComposer: React.FC<Props> = ({ onSend, isSending }) => {
  const [fileA, setFileA] = useState<File | null>(null);
  const [previewA, setPreviewA] = useState<string | null>(null);
  const [modalityA, setModalityA] = useState('Auto');

  const [fileB, setFileB] = useState<File | null>(null);
  const [previewB, setPreviewB] = useState<string | null>(null);
  const [modalityB, setModalityB] = useState('Auto');

  const [query, setQuery] = useState(DEFAULT_QUERY);

  const clearComposer = () => {
    setFileA(null);
    setPreviewA(null);
    setFileB(null);
    setPreviewB(null);
    setQuery(DEFAULT_QUERY);
  };

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
    }
  };

  const handleSelectPreset = async (presetId: string, prompt: string) => {
    setQuery(prompt);
    const examples = await fetchExamples();
    const byId = (id: string) => examples.find((e) => e.id.includes(id));
    if (presetId === 'sar_fusion') {
      setModalityA('Optical');
      setModalityB('SAR');
      const m = examples.find((e) => e.id === 'bigearthnet_fusion' || e.category.includes('Fusion'));
      if (m && (!previewB || modalityB !== 'SAR')) handleSelectMission(m);
    } else if (presetId === 'bitemporal') {
      setModalityA('Optical');
      setModalityB('Optical');
      const m = examples.find((e) => e.id.includes('flood') || e.category.includes('Disaster') || e.category.includes('Bi-Temporal'));
      if (m && !previewB) handleSelectMission(m);
    } else if (presetId === 'multi_detect' || presetId === 'grounding') {
      setModalityA('Optical');
      if (!previewA) {
        const m = byId('vrsbench');
        if (m) handleSelectMission(m);
      }
    } else if (presetId === 'vqa') {
      if (!previewA) {
        const m = byId('rsvqa');
        if (m) handleSelectMission(m);
      }
    }
  };

  const handleTransmit = async () => {
    if (isSending) return; // duplicate submission prevention
    if (!fileA || !query.trim()) return; // parent surfaces the specific validation message
    const submitted = { query, fileA, fileB, modalityA, modalityB };
    clearComposer();
    await onSend(submitted);
  };

  return (
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

      <TacticalUplinkBar query={query} setQuery={setQuery} onTransmit={handleTransmit} isLoading={isSending} onSelectPreset={handleSelectPreset} />

      <SatelliteOrbitRadar />
    </div>
  );
};

export { DEFAULT_QUERY };
