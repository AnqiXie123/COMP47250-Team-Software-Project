import React, { useState, useEffect } from 'react';

function EnergyChart({ onClose }) {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://127.0.0.1:8000/api/energy/timeseries?days=7&interval=1h')
      .then(res => res.json())
      .then(raw => {
        const hourly = raw.filter((_, i) => i % 4 === 0).map(d => ({
          time: new Date(d.datetime).toLocaleDateString('en-IE', { month: 'short', day: 'numeric', hour: '2-digit' }),
          wind: Math.round(d.wind_mw),
          solar: Math.round(d.solar_mw),
          score: Math.round(d.renewable_score * 100),
        }));
        setData(hourly);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const maxVal = Math.max(...data.map(d => d.wind + d.solar), 1);
  const chartWidth = 600;
  const chartHeight = 160;
  const padL = 40, padR = 10, padT = 10, padB = 30;
  const w = chartWidth - padL - padR;
  const h = chartHeight - padT - padB;

  const getX = (i) => padL + (i / (data.length - 1)) * w;
  const getY = (val) => padT + h - (val / maxVal) * h;

  const windPoints = data.map((d, i) => `${getX(i)},${getY(d.wind)}`).join(' ');
  const solarPoints = data.map((d, i) => `${getX(i)},${getY(d.solar)}`).join(' ');

  const latest = data[data.length - 1];

  return (
    <div style={{
      position: 'fixed', bottom: '20px', left: '240px',
      zIndex: 2000, background: 'white', borderRadius: '10px',
      boxShadow: '0 4px 20px rgba(0,0,0,0.25)', padding: '16px',
      width: '640px'
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <div>
          <p style={{ margin: 0, fontWeight: 'bold', fontSize: '14px', color: '#1a252f' }}>
            🌱 Ireland Renewable Energy — Last 7 Days
          </p>
          <p style={{ margin: '2px 0 0 0', fontSize: '11px', color: '#7f8c8d' }}>
            Wind and solar generation (MW) · Source: EirGrid
          </p>
        </div>
        <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '16px', color: '#95a5a6' }}>✕</button>
      </div>

      {loading ? (
        <p style={{ textAlign: 'center', color: '#95a5a6', fontSize: '13px' }}>Loading energy data...</p>
      ) : (
        <>
          <div style={{ display: 'flex', gap: '16px', marginBottom: '12px' }}>
            <div style={{ background: '#f0fdf4', borderRadius: '6px', padding: '8px 14px', flex: 1 }}>
              <p style={{ margin: 0, fontSize: '11px', color: '#7f8c8d' }}>Latest Wind</p>
              <p style={{ margin: 0, fontSize: '20px', fontWeight: 'bold', color: '#16a34a' }}>{latest?.wind} MW</p>
            </div>
            <div style={{ background: '#fffbeb', borderRadius: '6px', padding: '8px 14px', flex: 1 }}>
              <p style={{ margin: 0, fontSize: '11px', color: '#7f8c8d' }}>Latest Solar</p>
              <p style={{ margin: 0, fontSize: '20px', fontWeight: 'bold', color: '#d97706' }}>{latest?.solar} MW</p>
            </div>
            <div style={{ background: '#f0f9ff', borderRadius: '6px', padding: '8px 14px', flex: 1 }}>
              <p style={{ margin: 0, fontSize: '11px', color: '#7f8c8d' }}>Renewable Score</p>
              <p style={{ margin: 0, fontSize: '20px', fontWeight: 'bold', color: '#0284c7' }}>{latest?.score}%</p>
            </div>
          </div>

          <svg width={chartWidth} height={chartHeight} style={{ display: 'block' }}>
            {[0, 0.25, 0.5, 0.75, 1].map(t => {
              const y = padT + h * (1 - t);
              return (
                <g key={t}>
                  <line x1={padL} y1={y} x2={chartWidth - padR} y2={y} stroke="#f0f0f0" strokeWidth="1" />
                  <text x={padL - 4} y={y + 4} fontSize="9" fill="#aaa" textAnchor="end">{Math.round(maxVal * t)}</text>
                </g>
              );
            })}
            <polyline points={windPoints} fill="none" stroke="#16a34a" strokeWidth="2" />
            <polyline points={solarPoints} fill="none" stroke="#d97706" strokeWidth="2" />
            {data.filter((_, i) => i % 8 === 0).map((d, i) => {
              const idx = i * 8;
              return (
                <text key={i} x={getX(idx)} y={chartHeight - 4} fontSize="9" fill="#aaa" textAnchor="middle">
                  {d.time.split(',')[0]}
                </text>
              );
            })}
          </svg>

          <div style={{ display: 'flex', gap: '16px', marginTop: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <div style={{ width: '16px', height: '3px', background: '#16a34a', borderRadius: '2px' }} />
              <span style={{ fontSize: '11px', color: '#555' }}>Wind Generation</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <div style={{ width: '16px', height: '3px', background: '#d97706', borderRadius: '2px' }} />
              <span style={{ fontSize: '11px', color: '#555' }}>Solar Generation</span>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export default EnergyChart;