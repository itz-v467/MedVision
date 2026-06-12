import React from 'react';

const DUMMY_TIMELINE = [
  { id: 'ENC-1001', date: 'Oct 12, 2026', type: 'Chest X-Ray', description: 'Follow-up on persistent cough.' },
  { id: 'ENC-1002', date: 'Sep 05, 2026', type: 'Lab Report', description: 'Routine blood work, CBC.' },
  { id: 'ENC-1003', date: 'Jan 22, 2026', type: 'Initial Consult', description: 'Patient presented with mild dyspnea.' }
];

const PatientTimeline = ({ onSelectEncounter, activeId }) => {
  return (
    <div>
      {DUMMY_TIMELINE.map(item => (
        <div key={item.id} className="timeline-item">
          <div className="timeline-date">{item.date}</div>
          <div 
            className="timeline-content" 
            onClick={() => onSelectEncounter(item.id)}
            style={{ borderColor: activeId === item.id ? 'var(--accent-blue)' : '' }}
          >
            <strong>{item.type}</strong>
            <p style={{ margin: '4px 0 0', fontSize: '0.9em', color: 'var(--text-secondary)' }}>
              {item.description}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
};

export { PatientTimeline };
