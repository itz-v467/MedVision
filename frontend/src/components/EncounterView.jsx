import React, { useState } from 'react';

const EncounterView = ({ encounterId, onCitationClick }) => {
  const [isFinalized, setIsFinalized] = useState(false);

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <h3 style={{ margin: '0 0 8px' }}>Encounter: {encounterId}</h3>
        <span style={{ 
          background: isFinalized ? 'var(--success)' : 'rgba(255, 165, 0, 0.2)', 
          color: isFinalized ? '#fff' : 'orange', 
          padding: '4px 8px', 
          borderRadius: '4px', 
          fontSize: '0.85em' 
        }}>
          {isFinalized ? 'Finalized' : 'Pending Review'}
        </span>
      </div>

      <div className="summary-card">
        <h4 style={{ margin: '0 0 16px', color: 'var(--accent-purple)' }}>AI Clinical Summary</h4>
        <div className="summary-text">
          The patient presented with a persistent cough and mild dyspnea. 
          Chest X-ray reveals an area of increased opacity in the left lower lobe
          <span className="citation-marker" onClick={() => onCitationClick('xray_opacity_1')}>[1]</span>, 
          suggestive of a mild infiltrate or early pneumonia. 
          Blood work from the previous encounter shows a slightly elevated white blood cell count
          <span className="citation-marker" onClick={() => onCitationClick('lab_wbc_2')}>[2]</span>.
          
          <br /><br />
          <strong>Recommendations:</strong> Consider a short course of antibiotics and follow-up in 7 days if symptoms persist.
        </div>
      </div>

      {!isFinalized && (
        <button className="btn-primary" onClick={() => setIsFinalized(true)}>
          Approve & Finalize Summary
        </button>
      )}
    </div>
  );
};

export default EncounterView;
