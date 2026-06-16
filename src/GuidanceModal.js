import React from 'react';

function GuidanceModal({ onClose }) {
  const steps = [
    {
      icon: '🔌',
      title: 'Existing Chargers',
      desc: 'Blue markers show all current public EV charging stations in Dublin. Click any marker to see the operator and number of chargers.'
    },
    {
      icon: '🔥',
      title: 'Traffic Demand Heatmap',
      desc: 'Red areas have high traffic volume — meaning more EVs are likely passing through but there are not enough chargers nearby.'
    },
    {
      icon: '⭐',
      title: 'Recommended New Sites',
      desc: 'Red numbered circles show the top 10 locations where new charging stations are most urgently needed, ranked by demand gap.'
    },
    {
      icon: '🗂',
      title: 'Layer Controls',
      desc: 'Use the Map Layers panel on the bottom right to show or hide each layer. You can also switch between Standard and Dark map styles.'
    },
  ];

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
      background: 'rgba(0,0,0,0.6)', zIndex: 9999,
      display: 'flex', alignItems: 'center', justifyContent: 'center'
    }}>
      <div style={{
        background: '#fff', borderRadius: '12px', padding: '32px',
        maxWidth: '480px', width: '90%', boxShadow: '0 8px 32px rgba(0,0,0,0.3)'
      }}>
        <h2 style={{ margin: '0 0 6px 0', color: '#1a252f', fontSize: '18px' }}>
          👋 Welcome to EcoCharge Dublin
        </h2>
        <p style={{ margin: '0 0 24px 0', color: '#7f8c8d', fontSize: '13px' }}>
          Here's a quick guide to help you explore the dashboard.
        </p>

        {steps.map((step, i) => (
          <div key={i} style={{
            display: 'flex', gap: '14px', marginBottom: '16px',
            padding: '12px', background: '#f8f9fa', borderRadius: '8px'
          }}>
            <div style={{ fontSize: '24px', flexShrink: 0 }}>{step.icon}</div>
            <div>
              <p style={{ margin: '0 0 4px 0', fontWeight: '600', color: '#2c3e50', fontSize: '13px' }}>{step.title}</p>
              <p style={{ margin: 0, color: '#7f8c8d', fontSize: '12px', lineHeight: '1.5' }}>{step.desc}</p>
            </div>
          </div>
        ))}

        <button
          onClick={onClose}
          style={{
            width: '100%', padding: '12px', background: '#1a252f',
            color: '#fff', border: 'none', borderRadius: '8px',
            fontSize: '14px', fontWeight: '600', cursor: 'pointer', marginTop: '8px'
          }}
        >
          Got it, start exploring →
        </button>
      </div>
    </div>
  );
}

export default GuidanceModal;