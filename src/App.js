import HeatmapLayer from './HeatmapLayer';
import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, LayersControl, FeatureGroup } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
  iconUrl: require('leaflet/dist/images/marker-icon.png'),
  shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

const getUniqueChargers = (data) => {
  const uniqueMap = new Map();
  data.forEach(item => {
    const key = `${item.lat.toFixed(5)}_${item.lon.toFixed(5)}`;
    if (uniqueMap.has(key)) {
      const existing = uniqueMap.get(key);
      existing.num_chargers = Math.max(existing.num_chargers, item.num_chargers);
    } else {
      uniqueMap.set(key, { ...item });
    }
  });
  return Array.from(uniqueMap.values());
};

const renderPopupContent = (charger) => {
  const opNormalized = charger.operator.toUpperCase();
  const badgeColor = opNormalized.includes('ESB') ? '#00704A' :
                     opNormalized.includes('EASYGO') ? '#FF5A5F' : '#7f8c8d';
  return (
    <div style={{ fontFamily: 'Segoe UI, Arial, sans-serif', minWidth: '180px' }}>
      <h4 style={{ margin: '0 0 6px 0', color: '#2c3e50', fontSize: '13px', fontWeight: 'bold' }}>{charger.address}</h4>
      <div style={{ marginBottom: '6px' }}>
        <span style={{
          background: badgeColor, color: '#fff', padding: '2px 6px',
          borderRadius: '3px', fontSize: '10px', fontWeight: 'bold'
        }}>{charger.operator}</span>
      </div>
      <p style={{ margin: '4px 0', fontSize: '12px', color: '#555' }}>
        🔌 <b>Total Chargers:</b> {charger.num_chargers}
      </p>
      <p style={{ margin: '4px 0', fontSize: '11px', color: '#95a5a6' }}>
        📍 ID: {charger.id.toUpperCase()}
      </p>
    </div>
  );
};

function App() {
  const [chargers, setChargers] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [trafficData, setTrafficData] = useState([]);

  useEffect(() => {
    fetch('http://127.0.0.1:8000/api/chargers')
      .then(res => res.json())
      .then(data => {
        const points = data.features.map(f => ({
          id: f.properties.id,
          lat: f.geometry.coordinates[1],
          lon: f.geometry.coordinates[0],
          address: f.properties.address,
          operator: f.properties.operator,
          num_chargers: f.properties.num_chargers,
        }));
        setChargers(points);
      })
      .catch(err => console.error('Chargers fetch failed:', err));

    fetch('http://127.0.0.1:8000/api/recommendations')
      .then(res => res.json())
      .then(data => {
        const points = data.features.map(f => ({
          id: `rec_${f.properties.rank}`,
          lat: f.geometry.coordinates[1],
          lon: f.geometry.coordinates[0],
          rank: f.properties.rank,
          gap_score: f.properties.gap_score,
        }));
        setRecommendations(points);
      })
      .catch(err => console.error('Recommendations fetch failed:', err));

    fetch('http://127.0.0.1:8000/api/traffic')
      .then(res => res.json())
      .then(data => {
        setTrafficData(data);
      })
      .catch(err => console.error('Traffic fetch failed:', err));
  }, []);

  const CLEANED_CHARGERS = getUniqueChargers(chargers);
  const heatmapPoints = trafficData.length > 0
    ? trafficData.map(t => ({
        lat: t.lat,
        lon: t.lon,
        intensity: t.volume / 3000
      }))
    : CLEANED_CHARGERS.map(c => ({
        lat: c.lat,
        lon: c.lon,
        intensity: c.num_chargers / 5
      }));

  const esbChargers = CLEANED_CHARGERS.filter(c => c.operator.toUpperCase().includes('ESB'));
  const easyGoChargers = CLEANED_CHARGERS.filter(c => c.operator.toUpperCase().includes('EASYGO'));
  const otherChargers = CLEANED_CHARGERS.filter(c =>
    !c.operator.toUpperCase().includes('ESB') && !c.operator.toUpperCase().includes('EASYGO')
  );

  return (
    <div style={{ height: '100vh', width: '100%', display: 'flex', flexDirection: 'column' }}>

      <div style={{ height: '55px', background: '#1a252f', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 20px', flexShrink: 0 }}>
        <h2 style={{ margin: 0, fontSize: '16px', fontWeight: '500' }}>
          ⚡ EcoCharge Dublin: EV Infrastructure Optimization Dashboard
        </h2>
        <span style={{ fontSize: '11px', color: chargers.length > 0 ? '#2ecc71' : '#f39c12' }}>
          {chargers.length > 0 ? '🟢 Live API Data' : '⏳ Loading...'}
        </span>
      </div>

      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>

        <div style={{
          width: '220px', background: '#1a252f', color: '#fff',
          padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px',
          flexShrink: 0, overflowY: 'auto'
        }}>
          <div>
            <p style={{ margin: '0 0 4px 0', fontSize: '11px', color: '#95a5a6', textTransform: 'uppercase' }}>Current Chargers</p>
            <p style={{ margin: 0, fontSize: '28px', fontWeight: 'bold', color: '#2ecc71' }}>{CLEANED_CHARGERS.length}</p>
          </div>
          <div>
            <p style={{ margin: '0 0 4px 0', fontSize: '11px', color: '#95a5a6', textTransform: 'uppercase' }}>Recommended Sites</p>
            <p style={{ margin: 0, fontSize: '28px', fontWeight: 'bold', color: '#e74c3c' }}>{recommendations.length}</p>
          </div>
          <div>
            <p style={{ margin: '0 0 4px 0', fontSize: '11px', color: '#95a5a6', textTransform: 'uppercase' }}>Traffic Sites</p>
            <p style={{ margin: 0, fontSize: '28px', fontWeight: 'bold', color: '#3498db' }}>{trafficData.length}</p>
          </div>
          <hr style={{ border: '0', borderTop: '1px solid #2c3e50', margin: '4px 0' }} />
          <div>
            <p style={{ margin: '0 0 8px 0', fontSize: '11px', color: '#95a5a6', textTransform: 'uppercase' }}>Top Priority Sites</p>
            {recommendations.slice(0, 5).map(r => (
              <div key={r.id} style={{ marginBottom: '10px', padding: '8px', background: '#2c3e50', borderRadius: '4px' }}>
                <p style={{ margin: '0 0 2px 0', fontSize: '12px', color: '#e74c3c', fontWeight: 'bold' }}>Rank #{r.rank}</p>
                <p style={{ margin: 0, fontSize: '11px', color: '#bdc3c7' }}>Gap Score: {r.gap_score.toFixed(0)}</p>
              </div>
            ))}
          </div>
        </div>

        <div style={{ flex: 1 }}>
          <MapContainer center={[53.3498, -6.2603]} zoom={11} style={{ height: '100%', width: '100%' }}>
            <LayersControl position="topright">
              <LayersControl.BaseLayer checked name="Standard Map">
                <TileLayer
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  attribution="&copy; OpenStreetMap contributors"
                />
              </LayersControl.BaseLayer>
              <LayersControl.BaseLayer name="Dark Mode Map">
                <TileLayer
                  url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                  attribution='&copy; OpenStreetMap contributors &copy; CARTO'
                />
              </LayersControl.BaseLayer>
              <LayersControl.Overlay checked name="ESB Networks">
                <FeatureGroup>
                  {esbChargers.map(c => (
                    <Marker key={c.id} position={[c.lat, c.lon]}>
                      <Popup>{renderPopupContent(c)}</Popup>
                    </Marker>
                  ))}
                </FeatureGroup>
              </LayersControl.Overlay>
              <LayersControl.Overlay checked name="EasyGo Networks">
                <FeatureGroup>
                  {easyGoChargers.map(c => (
                    <Marker key={c.id} position={[c.lat, c.lon]}>
                      <Popup>{renderPopupContent(c)}</Popup>
                    </Marker>
                  ))}
                </FeatureGroup>
              </LayersControl.Overlay>
              <LayersControl.Overlay checked name="Other Networks (Tesla, etc.)">
                <FeatureGroup>
                  {otherChargers.map(c => (
                    <Marker key={c.id} position={[c.lat, c.lon]}>
                      <Popup>{renderPopupContent(c)}</Popup>
                    </Marker>
                  ))}
                </FeatureGroup>
              </LayersControl.Overlay>
              <LayersControl.Overlay checked name="Recommended Sites">
                <FeatureGroup>
                  {recommendations.map(r => (
                    <Marker key={r.id} position={[r.lat, r.lon]}
                      icon={L.divIcon({
                        className: '',
                        html: `<div style="background:#e74c3c;color:white;width:24px;height:24px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:bold;font-size:11px;border:2px solid white">${r.rank}</div>`,
                        iconSize: [24, 24],
                        iconAnchor: [12, 12]
                      })}
                    >
                      <Popup>
                        <div style={{fontFamily:'Segoe UI, Arial, sans-serif', minWidth:'160px'}}>
                          <h4 style={{margin:'0 0 6px 0', color:'#e74c3c'}}>⚡ Recommended Site #{r.rank}</h4>
                          <p style={{margin:'4px 0', fontSize:'12px'}}>🚦 Gap Score: <b>{r.gap_score.toFixed(1)}</b></p>
                          <p style={{margin:'4px 0', fontSize:'11px', color:'#95a5a6'}}>Priority: #{r.rank} of 10</p>
                        </div>
                      </Popup>
                    </Marker>
                  ))}
                </FeatureGroup>
              </LayersControl.Overlay>
            </LayersControl>
            <HeatmapLayer points={heatmapPoints} />
          </MapContainer>
        </div>

      </div>
    </div>
  );
}

export default App;