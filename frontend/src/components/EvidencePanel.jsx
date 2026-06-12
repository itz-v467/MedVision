import React, { useState } from 'react';

const EvidencePanel = ({ activeCitation }) => {
  const [showHeatmap, setShowHeatmap] = useState(true);

  if (!activeCitation) {
    return (
      <div style={{ color: 'var(--text-secondary)', textAlign: 'center', marginTop: '40px' }}>
        Click a citation marker in the summary to view evidence.
      </div>
    );
  }

  return (
    <div>
      <h3 style={{ margin: '0 0 16px', fontSize: '1.1rem' }}>Evidence Reference: {activeCitation}</h3>
      
      {activeCitation.startsWith('xray') ? (
        <div className="imaging-viewer">
          {/* Placeholder for actual X-Ray image */}
          <div style={{ width: '100%', height: '250px', background: '#2a2a2a', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <span style={{ color: '#555' }}>Chest X-Ray DICOM View</span>
          </div>
          
          {showHeatmap && (
             <div className="heatmap-overlay" style={{ background: 'radial-gradient(circle at 60% 70%, rgba(255,0,0,0.5) 0%, transparent 40%)' }}></div>
          )}
          
          <button className="toggle-heatmap" onClick={() => setShowHeatmap(!showHeatmap)}>
            {showHeatmap ? 'Hide Heatmap' : 'Show Heatmap'}
          </button>
        </div>
      ) : (
        <div className="evidence-panel">
          <h4 style={{ margin: '0 0 8px', color: 'var(--accent-blue)' }}>Lab Report Extract</h4>
          <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace', color: 'var(--text-secondary)' }}>
            WBC Count: 11.2 x10^3/uL (High)
            Reference Range: 4.5 - 11.0 x10^3/uL
          </pre>
        </div>
      )}
    </div>
  );
};

export default EvidencePanel;
