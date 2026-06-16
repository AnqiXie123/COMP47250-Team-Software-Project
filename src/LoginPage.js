import React from 'react';

function LoginPage({ onEnter }) {
  return (
    <div style={{
      height: '100vh', width: '100%', background: '#1a252f',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      flexDirection: 'column'
    }}>
      <div style={{
        background: '#2c3e50', borderRadius: '12px', padding: '48px 40px',
        maxWidth: '420px', width: '90%', textAlign: 'center',
        boxShadow: '0 8px 32px rgba(0,0,0,0.4)'
      }}>
        <div style={{ fontSize: '48px', marginBottom: '16px' }}>⚡</div>
        <h1 style={{ color: '#fff', fontSize: '22px', margin: '0 0 8px 0', fontWeight: '600' }}>
          EcoCharge Dublin
        </h1>
        <p style={{ color: '#95a5a6', fontSize: '14px', margin: '0 0 32px 0', lineHeight: '1.5' }}>
          A data-driven dashboard to help city planners identify where new EV charging stations are needed most across Dublin.
        </p>
        <button
          onClick={onEnter}
          style={{
            width: '100%', padding: '14px', background: '#2ecc71',
            color: '#fff', border: 'none', borderRadius: '8px',
            fontSize: '16px', fontWeight: '600', cursor: 'pointer',
            marginBottom: '16px', transition: 'background 0.2s'
          }}
          onMouseOver={e => e.target.style.background = '#27ae60'}
          onMouseOut={e => e.target.style.background = '#2ecc71'}
        >
          Enter Dashboard →
        </button>
        <p style={{ color: '#7f8c8d', fontSize: '11px', margin: 0 }}>
          Data sourced from Smart Dublin · EirGrid · ESB eCars · OSM
        </p>
      </div>
    </div>
  );
}

export default LoginPage;