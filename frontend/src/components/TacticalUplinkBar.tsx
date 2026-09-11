"use client";

import React from "react";

interface TacticalUplinkBarProps {
  query: string;
  setQuery: (q: string) => void;
  onTransmit: () => void;
  isLoading: boolean;
}

export const TacticalUplinkBar: React.FC<TacticalUplinkBarProps> = ({
  query,
  setQuery,
  onTransmit,
  isLoading,
}) => {
  const chips = [
    { label: "🛰️ VQA Scene Inquiry", prompt: "Is a residential building present in this scene?" },
    { label: "📝 Land-Cover Caption", prompt: "Describe the land cover, major objects, and overall scene composition in this remote sensing image." },
    { label: "🎯 Target Grounding", prompt: "Locate and highlight all parked airplanes with a bounding box." },
    { label: "🚨 Bi-Temporal Delta", prompt: "What structural and land-cover changes occurred between these two observation dates?" },
    { label: "📡 Optical-SAR Fusion", prompt: "Use both the optical and SAR images together to identify water boundaries and built-up areas beneath clouds." },
  ];

  return (
    <div className="hud-deck-card">
      <div className="hud-panel-title">
        <span>[02]</span> TARGET UPLINK CONSOLE (5 SATELLITE TOOLS & PRESET COMMANDS)
      </div>

      <div className="query-chips-wrap">
        {chips.map((chip, idx) => (
          <button
            key={idx}
            className="sat-chip-btn"
            onClick={() => setQuery(chip.prompt)}
          >
            {chip.label}
          </button>
        ))}
      </div>

      <textarea
        className="query-textarea"
        placeholder="Uplink geospatial target query (e.g., 'Describe the land cover in this image', 'What changed between these two dates?', 'Use optical and SAR images together to identify built-up areas')..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        rows={3}
      />

      <button
        className="transmit-btn"
        onClick={onTransmit}
        disabled={isLoading || !query.trim()}
      >
        {isLoading ? "🛰️ EXECUTING SATELLITE AGENT & VLM PIPELINE..." : "TRANSMIT SATELLITE UPLINK 📡 [EXECUTE]"}
      </button>
    </div>
  );
};
