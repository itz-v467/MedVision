import React, { useState } from 'react';
import '../styles/workspace.css';
import { PatientTimeline } from '../components/PatientTimeline';
import EncounterView from './EncounterView';
import EvidencePanel from './EvidencePanel';

const PhysicianWorkspace = () => {
  const [activeEncounterId, setActiveEncounterId] = useState('ENC-1001');
  const [activeCitation, setActiveCitation] = useState(null);

  const handleCitationClick = (citationId) => {
    setActiveCitation(citationId);
  };

  return (
    <div className="workspace-container">
      {/* Left Panel: Longitudinal Timeline */}
      <div className="panel">
        <h2 className="panel-header">Patient Timeline</h2>
        <PatientTimeline onSelectEncounter={setActiveEncounterId} activeId={activeEncounterId} />
      </div>

      {/* Center Panel: Encounter & AI Summary Review */}
      <div className="panel encounter-view">
        <h2 className="panel-header">Encounter Review</h2>
        <EncounterView 
          encounterId={activeEncounterId} 
          onCitationClick={handleCitationClick} 
        />
      </div>

      {/* Right Panel: Evidence & Imaging Viewer */}
      <div className="panel">
        <h2 className="panel-header">Clinical Evidence</h2>
        <EvidencePanel activeCitation={activeCitation} />
      </div>
    </div>
  );
};

export default PhysicianWorkspace;
