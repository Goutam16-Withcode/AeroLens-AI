"use client";

import React, { useEffect, useState } from "react";
import { SystemStatus } from "../types/satquery";

interface OrbitalHeaderProps {
  status: SystemStatus | null;
}

export const OrbitalHeader: React.FC<OrbitalHeaderProps> = ({ status }) => {
  const [clock, setClock] = useState<string>("");

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setClock(now.toUTCString().replace("GMT", "UTC"));
    };
    updateTime();
    const timer = setInterval(updateTime, 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <header className="sat-header">
      <div className="sat-brand-wrap">
        <div className="sat-dish-beacon">🛰️</div>
        <div className="sat-title-text">
          <h1>
            SAT<span>QUERY</span> AI // GROUND STATION
          </h1>
          <div className="sat-subkicker">
            AGENTIC MULTISPECTRAL VLM · 5 SATELLITE TOOLS · CROSS-MODAL FUSION
          </div>
        </div>
      </div>

      <div className="orbit-telemetry-bar">
        <div className="telemetry-chip emerald">
          <span className="pulse-led"></span>
          DOWNLINK: {status?.downlink_freq || "8.2 GHz [ACTIVE]"}
        </div>
        <div className="telemetry-chip gold">
          ORBIT: {status?.orbit || "LEO 540KM · SSO (98.2°)"}
        </div>
        <div className="telemetry-chip">
          DEVICE: {status?.device || "Neural Core Active"}
        </div>
        <div className="telemetry-chip">
          CLOCK: {clock || "SYNCING..."}
        </div>
      </div>
    </header>
  );
};
