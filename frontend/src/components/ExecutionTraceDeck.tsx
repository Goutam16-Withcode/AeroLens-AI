'use client';

import React, { useState } from 'react';
import { ExecutionTrace, AnalysisResponse } from '../types/satquery';

interface ExecutionTraceDeckProps {
  trace: ExecutionTrace | null;
  fullResponse: AnalysisResponse | null;
}

export const ExecutionTraceDeck: React.FC<ExecutionTraceDeckProps> = ({ trace, fullResponse }) => {
  const [isOpen, setIsOpen] = useState(false);

  const downloadReport = () => {
    if (!fullResponse) return;
    const reportData = {
      app: 'SatQuery AI Autonomous Mission Intelligence',
      version: '2.0.0-PRO',
      timestamp: new Date().toISOString(),
      analysis: fullResponse.answer,
      trace: fullResponse.trace,
    };
    const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `satquery_mission_${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="panel-card">
      <div className="panel-header" style={{ marginBottom: trace ? '12px' : '0' }}>
        <div className="panel-title">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
          </svg>
          <span>FLIGHT RECORDER // EXECUTION TRACE</span>
        </div>

        {fullResponse && (
          <button
            onClick={downloadReport}
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '10.5px',
              padding: '4px 10px',
              background: 'var(--accent-amber-subtle)',
              border: '1px solid var(--accent-amber-border)',
              borderRadius: '4px',
              color: 'var(--accent-amber)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '5px',
            }}
          >
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="7 10 12 15 17 10" />
              <line x1="12" y1="15" x2="12" y2="3" />
            </svg>
            <span>EXPORT JSON</span>
          </button>
        )}
      </div>

      {trace ? (
        <div>
          {/* Quick Metrics Bar */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
              gap: '8px',
              marginBottom: '12px',
            }}
          >
            <div style={{ background: '#f8f4ec', border: '1px solid var(--border-subtle)', padding: '8px 10px', borderRadius: '6px' }}>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: '9.5px', color: 'var(--text-muted)' }}>ROUTED TASK</div>
              <div style={{ fontFamily: 'var(--font-hud)', fontSize: '12px', color: 'var(--accent-amber)', fontWeight: 600, marginTop: '2px' }}>
                {trace.task.toUpperCase()}
              </div>
            </div>

            <div style={{ background: '#f8f4ec', border: '1px solid var(--border-subtle)', padding: '8px 10px', borderRadius: '6px' }}>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: '9.5px', color: 'var(--text-muted)' }}>PIPELINE</div>
              <div style={{ fontFamily: 'var(--font-hud)', fontSize: '12px', color: 'var(--accent-emerald)', fontWeight: 600, marginTop: '2px' }}>
                {trace.tools_used.join(' → ')}
              </div>
            </div>

            <div style={{ background: '#f8f4ec', border: '1px solid var(--border-subtle)', padding: '8px 10px', borderRadius: '6px' }}>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: '9.5px', color: 'var(--text-muted)' }}>LATENCY</div>
              <div style={{ fontFamily: 'var(--font-hud)', fontSize: '12px', color: 'var(--accent-amber-bright)', fontWeight: 600, marginTop: '2px' }}>
                {trace.elapsed_seconds.toFixed(2)}s
              </div>
            </div>

            <div style={{ background: '#f8f4ec', border: '1px solid var(--border-subtle)', padding: '8px 10px', borderRadius: '6px' }}>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: '9.5px', color: 'var(--text-muted)' }}>ADAPTATION</div>
              <div style={{ fontFamily: 'var(--font-hud)', fontSize: '12px', color: 'var(--text-secondary)', fontWeight: 600, marginTop: '2px' }}>
                {trace.rs_adaptation || 'Standard'}
              </div>
            </div>
          </div>

          {/* Collapsible Detailed Terminal */}
          <div className="trace-accordion">
            <div className="trace-summary-header" onClick={() => setIsOpen(!isOpen)}>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '10.5px', color: 'var(--text-secondary)' }}>
                {isOpen ? '▲ HIDE AUDITABLE LOGS' : '▼ VIEW DETAILED TELEMETRY STACK'}
              </span>
              <span style={{ fontSize: '10.5px', color: 'var(--text-muted)' }}>{trace.timestamp}</span>
            </div>

            {isOpen && (
              <div className="trace-terminal-body">
                {JSON.stringify(
                  {
                    task: trace.task,
                    tools_used: trace.tools_used,
                    confidence: trace.confidence,
                    parameters: trace.parameters,
                    input_summary: trace.input_summary,
                    warnings: trace.warnings,
                  },
                  null,
                  2
                )}
              </div>
            )}
          </div>
        </div>
      ) : (
        <div style={{ color: 'var(--text-muted)', fontSize: '12px', fontStyle: 'italic', padding: '4px 0' }}>
          Flight recorder standing by. Telemetry logs will automatically capture upon execution.
        </div>
      )}
    </div>
  );
};
