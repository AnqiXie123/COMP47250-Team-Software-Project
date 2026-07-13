import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import HeatmapLayer from './HeatmapLayer';
import LoginPage from './LoginPage';
import GuidanceModal from './GuidanceModal';
import EnergyChart from './EnergyChart';

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

const aggregateTrafficPoints = (data) => {
  const map = new Map();
  data.forEach(t => {
    const key = `${t.lat.toFixed(5)}_${t.lon.toFixed(5)}`;
    if (map.has(key)) {
      if (t.volume > map.get(key).volume) map.set(key, t);
    } else {
      map.set(key, t);
    }
  });
  return Array.from(map.values());
};

const getMarkerColor = (operator) => {
  const op = operator.toUpperCase();
  if (op.includes('ESB')) return 'blue';
  if (op.includes('EASYGO')) return 'green';
  if (op.includes('TESLA')) return 'violet';
  return 'grey';
};

const getOperatorLabel = (operator) => {
  const op = operator.toUpperCase();
  if (op.includes('ESB')) return "ESB eCars — Ireland's largest public charging network";
  if (op.includes('EASYGO')) return 'EasyGo — Public charging network';
  if (op.includes('TESLA')) return 'Tesla — Supercharger network';
  return 'Independent operator';
};

const LAYERS = {
  chargers: { id: 'chargers', label: 'Existing Chargers', icon: '🔌', description: 'Public EV charging stations currently in Dublin', color: '#3498db' },
  recommendations: { id: 'recommendations', label: 'Recommended New Sites', icon: '⭐', description: 'AI-suggested locations for new charging stations', color: '#e74c3c' },
  heatmap: { id: 'heatmap', label: 'Traffic Demand Heatmap', icon: '🔥', description: 'Areas with high traffic volume need more chargers', color: '#f39c12' },
  sdcc: { id: 'sdcc', label: 'SDCC Traffic Sites', icon: '🔵', description: 'South Dublin County Council traffic monitoring sites (2024)', color: '#2563eb' },
  windfarms: { id: 'windfarms', label: 'Wind Farms', icon: '💨', description: 'Ireland wind farm locations', color: '#059669' },
  energy: { id: 'energy', label: 'Renewable Energy Chart', icon: '🌱', description: 'Ireland wind & solar generation over the last 7 days', color: '#16a34a' },
};

const TILE_LAYERS = {
  standard: {
    url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    attribution: '&copy; OpenStreetMap contributors',
    label: '🗺 Standard Map'
  },
  dark: {
    url: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
    attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
    label: '🌙 Dark Mode'
  }
};

const EV_SCENARIOS = [
  { label: 'Baseline (8%)', value: 0.08 },
  { label: 'Low (5%)', value: 0.05 },
  { label: 'High (12%)', value: 0.12 },
];

function LayerPanel({ activeLayers, onToggle, tileMode, onTileToggle, onHide, evScenario, onScenarioChange, scenarioActive, onResetScenario }) {
  return (
    <div style={{
      position: 'absolute', bottom: '30px', right: '10px',
      zIndex: 1000, background: 'white', borderRadius: '8px',
      boxShadow: '0 2px 12px rgba(0,0,0,0.2)', padding: '12px', minWidth: '260px',
      maxHeight: '80vh', overflowY: 'auto'
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
        <p style={{ margin: 0, fontSize: '12px', fontWeight: 'bold', color: '#2c3e50', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Map Layers</p>
        <button onClick={onHide} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '14px', color: '#95a5a6' }}>✕</button>
      </div>

      {Object.values(LAYERS).map(layer => (
        <div key={layer.id}
          onClick={() => onToggle(layer.id)}
          style={{
            display: 'flex', alignItems: 'flex-start', gap: '10px',
            padding: '8px', borderRadius: '6px', cursor: 'pointer', marginBottom: '4px',
            background: activeLayers[layer.id] ? '#f0f9ff' : '#f8f9fa',
            border: `2px solid ${activeLayers[layer.id] ? layer.color : 'transparent'}`,
            transition: 'all 0.2s'
          }}>
          <div style={{
            width: '20px', height: '20px', borderRadius: '4px', flexShrink: 0, marginTop: '2px',
            background: activeLayers[layer.id] ? layer.color : '#ddd',
            display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '11px',
            color: 'white', fontWeight: 'bold'
          }}>
            {activeLayers[layer.id] ? '✓' : ''}
          </div>
          <div>
            <p style={{ margin: 0, fontSize: '13px', fontWeight: '600', color: '#2c3e50' }}>
              {layer.icon} {layer.label}
            </p>
            <p style={{ margin: '2px 0 0 0', fontSize: '11px', color: '#7f8c8d', lineHeight: '1.3' }}>
              {layer.description}
            </p>
          </div>
        </div>
      ))}

      <hr style={{ border: '0', borderTop: '1px solid #eee', margin: '10px 0' }} />

      <p style={{ margin: '0 0 6px 0', fontSize: '11px', fontWeight: 'bold', color: '#7f8c8d', textTransform: 'uppercase' }}>EV Scenario Analysis</p>
      <p style={{ margin: '0 0 8px 0', fontSize: '11px', color: '#7f8c8d' }}>Select EV adoption rate to update recommended sites</p>
      {EV_SCENARIOS.map(s => (
        <div key={s.value}
          onClick={() => onScenarioChange(s.value)}
          style={{
            padding: '6px 8px', borderRadius: '6px', cursor: 'pointer', marginBottom: '4px',
            background: scenarioActive && evScenario === s.value ? '#fef3c7' : '#f8f9fa',
            border: `2px solid ${scenarioActive && evScenario === s.value ? '#f59e0b' : 'transparent'}`,
            fontSize: '12px', color: '#2c3e50', fontWeight: scenarioActive && evScenario === s.value ? '600' : '400'
          }}>
          {s.label}
        </div>
      ))}
      {scenarioActive && (
        <div
          onClick={onResetScenario}
          style={{
            padding: '6px 8px', borderRadius: '6px', cursor: 'pointer', marginTop: '4px',
            background: '#fee2e2', border: '2px solid #e74c3c',
            fontSize: '12px', color: '#e74c3c', fontWeight: '600', textAlign: 'center'
          }}>
          ✕ Reset to Default
        </div>
      )}

      <hr style={{ border: '0', borderTop: '1px solid #eee', margin: '10px 0' }} />

      <p style={{ margin: '0 0 6px 0', fontSize: '11px', fontWeight: 'bold', color: '#7f8c8d', textTransform: 'uppercase' }}>Map Style</p>
      {Object.entries(TILE_LAYERS).map(([key, tile]) => (
        <div key={key}
          onClick={() => onTileToggle(key)}
          style={{
            padding: '6px 8px', borderRadius: '6px', cursor: 'pointer', marginBottom: '4px',
            background: tileMode === key ? '#f0f9ff' : '#f8f9fa',
            border: `2px solid ${tileMode === key ? '#3498db' : 'transparent'}`,
            fontSize: '12px', color: '#2c3e50', fontWeight: tileMode === key ? '600' : '400'
          }}>
          {tile.label}
        </div>
      ))}

      <hr style={{ border: '0', borderTop: '1px solid #eee', margin: '10px 0' }} />

      <p style={{ margin: '0 0 6px 0', fontSize: '11px', fontWeight: 'bold', color: '#7f8c8d' }}>CHARGER OPERATORS</p>
      {[
        { color: '#2563eb', label: 'ESB eCars' },
        { color: '#16a34a', label: 'EasyGo' },
        { color: '#7c3aed', label: 'Tesla' },
        { color: '#6b7280', label: 'Other Networks' },
      ].map(({ color, label }) => (
        <div key={label} style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '3px' }}>
          <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: color }} />
          <span style={{ fontSize: '11px', color: '#555' }}>{label}</span>
        </div>
      ))}
    </div>
  );
}

function App() {
  const [loggedIn, setLoggedIn] = useState(false);
  const [showGuide, setShowGuide] = useState(false);
  const [chargers, setChargers] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [scenarioRecs, setScenarioRecs] = useState([]);
  const [trafficData, setTrafficData] = useState([]);
  const [sdccData, setSdccData] = useState([]);
  const [windFarms, setWindFarms] = useState([]);
  const [energyData, setEnergyData] = useState([]);
  const [evScenario, setEvScenario] = useState(null);
  const [scenarioLoading, setScenarioLoading] = useState(false);
  const [activeLayers, setActiveLayers] = useState({
    chargers: true,
    recommendations: true,
    heatmap: false,
    sdcc: false,
    windfarms: false,
    energy: false,
  });
  const [tileMode, setTileMode] = useState('standard');
  const [showSidebar, setShowSidebar] = useState(true);
  const [showLayerPanel, setShowLayerPanel] = useState(true);

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
          traffic_volume: f.properties.traffic_volume,
          charger_count_nearby: f.properties.charger_count_nearby,
          road_density: f.properties.road_density,
          traffic_source: f.properties.traffic_source,
          reason: f.properties.reason,
          distance_to_nearest_substation_m: f.properties.distance_to_nearest_substation_m,
        }));
        setRecommendations(points);
      })
      .catch(err => console.error('Recommendations fetch failed:', err));

    fetch('http://127.0.0.1:8000/api/traffic')
      .then(res => res.json())
      .then(data => setTrafficData(data))
      .catch(err => console.error('Traffic fetch failed:', err));

    fetch('http://127.0.0.1:8000/api/traffic?source=SDCC')
      .then(res => res.json())
      .then(data => setSdccData(data))
      .catch(err => console.error('SDCC fetch failed:', err));

    fetch('http://127.0.0.1:8000/api/windfarms')
      .then(res => res.json())
      .then(data => setWindFarms(data))
      .catch(err => console.error('Windfarms fetch failed:', err));

    fetch('http://127.0.0.1:8000/api/energy/timeseries?days=7&interval=1h')
      .then(res => res.json())
      .then(data => setEnergyData(data))
      .catch(err => console.error('Energy fetch failed:', err));
  }, []);

  const handleScenarioChange = (value) => {
    setEvScenario(value);
    setScenarioLoading(true);
    fetch(`http://127.0.0.1:8000/api/scenario?ev_penetration=${value}`)
      .then(res => res.json())
      .then(data => {
        const points = data.features.map(f => ({
          id: `scenario_${f.properties.rank}`,
          lat: f.geometry.coordinates[1],
          lon: f.geometry.coordinates[0],
          rank: f.properties.rank,
          gap_score: f.properties.gap_score,
          ev_penetration: f.properties.ev_penetration,
        }));
        setScenarioRecs(points);
        setScenarioLoading(false);
      })
      .catch(err => {
        console.error('Scenario fetch failed:', err);
        setScenarioLoading(false);
      });
  };

  const handleResetScenario = () => {
    setScenarioRecs([]);
    setEvScenario(null);
  };

  const toggleLayer = (layerId) => {
    setActiveLayers(prev => ({ ...prev, [layerId]: !prev[layerId] }));
  };

  const CLEANED_CHARGERS = getUniqueChargers(chargers);
  const heatmapPoints = aggregateTrafficPoints(trafficData).map(t => ({
    lat: t.lat, lon: t.lon, intensity: t.volume / 3000
  }));
  const aggregatedSdcc = aggregateTrafficPoints(sdccData);
  const displayedRecs = scenarioRecs.length > 0 ? scenarioRecs : recommendations;
  const scenarioActive = scenarioRecs.length > 0;

  if (!loggedIn) {
    return <LoginPage onEnter={() => { setLoggedIn(true); setShowGuide(true); }} />;
  }

  return (
    <div style={{ height: '100vh', width: '100%', display: 'flex', flexDirection: 'column' }}>

      {showGuide && <GuidanceModal onClose={() => setShowGuide(false)} />}
      {activeLayers.energy && <EnergyChart data={energyData} onClose={() => toggleLayer('energy')} />}

      {/* Header */}
      <div style={{ height: '55px', background: '#1a252f', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 20px', flexShrink: 0 }}>
        <h2 style={{ margin: 0, fontSize: '16px', fontWeight: '500' }}>
          ⚡ EcoCharge Dublin — EV Infrastructure Planning Dashboard
        </h2>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            onClick={() => setShowSidebar(v => !v)}
            style={{ background: '#2c3e50', border: 'none', color: '#fff', padding: '4px 10px', borderRadius: '4px', cursor: 'pointer', fontSize: '12px' }}>
            {showSidebar ? '◀ Hide Panel' : '▶ Show Panel'}
          </button>
          <button
            onClick={() => setShowLayerPanel(v => !v)}
            style={{ background: '#2c3e50', border: 'none', color: '#fff', padding: '4px 10px', borderRadius: '4px', cursor: 'pointer', fontSize: '12px' }}>
            {showLayerPanel ? '🗂 Hide Layers' : '🗂 Show Layers'}
          </button>
          <button
            onClick={() => setShowGuide(true)}
            style={{ background: '#2c3e50', border: 'none', color: '#fff', padding: '4px 10px', borderRadius: '4px', cursor: 'pointer', fontSize: '12px' }}>
            ❓ Guide
          </button>
          <span style={{ fontSize: '11px', color: chargers.length > 0 ? '#2ecc71' : '#f39c12' }}>
            {chargers.length > 0 ? '🟢 Live Data' : '⏳ Loading...'}
          </span>
        </div>
      </div>

      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>

        {/* Sidebar */}
        {showSidebar && (
          <div style={{
            width: '220px', background: '#1a252f', color: '#fff',
            padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px',
            flexShrink: 0, overflowY: 'auto'
          }}>
            <div>
              <p style={{ margin: '0 0 4px 0', fontSize: '11px', color: '#95a5a6', textTransform: 'uppercase' }}>Existing Chargers</p>
              <p style={{ margin: 0, fontSize: '28px', fontWeight: 'bold', color: '#2ecc71' }}>{CLEANED_CHARGERS.length}</p>
            </div>
            <div>
              <p style={{ margin: '0 0 4px 0', fontSize: '11px', color: '#95a5a6', textTransform: 'uppercase' }}>Recommended New Sites</p>
              <p style={{ margin: 0, fontSize: '28px', fontWeight: 'bold', color: '#e74c3c' }}>{displayedRecs.length}</p>
            </div>
            <div>
              <p style={{ margin: '0 0 4px 0', fontSize: '11px', color: '#95a5a6', textTransform: 'uppercase' }}>Traffic Monitoring Sites</p>
              <p style={{ margin: 0, fontSize: '28px', fontWeight: 'bold', color: '#3498db' }}>{trafficData.length}</p>
            </div>
            {scenarioActive && (
              <div style={{ padding: '8px', background: '#f59e0b20', borderRadius: '4px', border: '1px solid #f59e0b' }}>
                <p style={{ margin: 0, fontSize: '11px', color: '#f59e0b', fontWeight: 'bold' }}>
                  📊 Scenario: EV {(evScenario * 100).toFixed(0)}%
                </p>
              </div>
            )}
            <hr style={{ border: '0', borderTop: '1px solid #2c3e50', margin: '4px 0' }} />
            <div>
              <p style={{ margin: '0 0 8px 0', fontSize: '11px', color: '#95a5a6', textTransform: 'uppercase' }}>Top Priority New Sites</p>
              {displayedRecs.slice(0, 5).map(r => (
                <div key={r.id} style={{ marginBottom: '10px', padding: '8px', background: '#2c3e50', borderRadius: '4px' }}>
                  <p style={{ margin: '0 0 2px 0', fontSize: '12px', color: scenarioActive ? '#f59e0b' : '#e74c3c', fontWeight: 'bold' }}>
                    {scenarioActive ? '📊' : '⭐'} Rank #{r.rank}
                  </p>
                  <p style={{ margin: 0, fontSize: '11px', color: '#bdc3c7' }}>Gap Score: {r.gap_score.toFixed(2)}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Map */}
        <div style={{ flex: 1, position: 'relative' }}>
          {scenarioLoading && (
            <div style={{
              position: 'absolute', top: '10px', left: '50%', transform: 'translateX(-50%)',
              zIndex: 2000, background: '#1a252f', color: '#fff', padding: '6px 14px',
              borderRadius: '20px', fontSize: '12px'
            }}>
              ⏳ Loading scenario...
            </div>
          )}
          <MapContainer center={[53.3498, -6.2603]} zoom={11} style={{ height: '100%', width: '100%' }}>
            <TileLayer
              url={TILE_LAYERS[tileMode].url}
              attribution={TILE_LAYERS[tileMode].attribution}
            />

            {activeLayers.chargers && CLEANED_CHARGERS.map(c => (
              <Marker
                key={c.id}
                position={[c.lat, c.lon]}
                icon={new L.Icon({
                  iconUrl: `https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-${getMarkerColor(c.operator)}.png`,
                  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
                  iconSize: [15, 25],
                  iconAnchor: [7, 25],
                  popupAnchor: [1, -20],
                  shadowSize: [25, 25]
                })}
              >
                <Popup>
                  <div style={{ fontFamily: 'Segoe UI, Arial, sans-serif', minWidth: '180px' }}>
                    <h4 style={{ margin: '0 0 6px 0', color: '#2c3e50', fontSize: '13px' }}>🔌 {c.address}</h4>
                    <p style={{ margin: '4px 0', fontSize: '12px' }}><b>Operator:</b> {c.operator}</p>
                    <p style={{ margin: '4px 0', fontSize: '11px', color: '#7f8c8d' }}>{getOperatorLabel(c.operator)}</p>
                    <p style={{ margin: '4px 0', fontSize: '12px' }}><b>Chargers available:</b> {c.num_chargers}</p>
                  </div>
                </Popup>
              </Marker>
            ))}

            {activeLayers.recommendations && displayedRecs.map(r => (
              <Marker
                key={r.id}
                position={[r.lat, r.lon]}
                icon={L.divIcon({
                  className: '',
                  html: `<div style="background:${scenarioActive ? '#f59e0b' : '#e74c3c'};color:white;width:30px;height:30px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:bold;font-size:13px;border:3px solid white;box-shadow:0 2px 6px rgba(0,0,0,0.4)">${r.rank}</div>`,
                  iconSize: [30, 30],
                  iconAnchor: [15, 15]
                })}
              >
                <Popup>
                  <div style={{ fontFamily: 'Segoe UI, Arial, sans-serif', minWidth: '220px' }}>
                    <h4 style={{ margin: '0 0 8px 0', color: scenarioActive ? '#f59e0b' : '#e74c3c', fontSize: '14px' }}>
                      {scenarioActive ? '📊' : '⭐'} Recommended New Charging Site
                    </h4>
                    {scenarioActive && (
                      <p style={{ margin: '4px 0', fontSize: '11px', color: '#f59e0b', fontWeight: 'bold' }}>
                        Scenario: EV Penetration {(r.ev_penetration * 100).toFixed(0)}%
                      </p>
                    )}
                    <p style={{ margin: '4px 0', fontSize: '12px' }}><b>Priority Rank:</b> #{r.rank}</p>
                    <p style={{ margin: '4px 0', fontSize: '12px' }}><b>Gap Score:</b> {r.gap_score.toFixed(3)}</p>
                    {r.traffic_volume !== undefined && (
                      <p style={{ margin: '4px 0', fontSize: '12px' }}><b>Traffic Volume:</b> {r.traffic_volume.toFixed(0)}</p>
                    )}
                    {r.charger_count_nearby !== undefined && (
                      <p style={{ margin: '4px 0', fontSize: '12px' }}><b>Nearby Chargers:</b> {r.charger_count_nearby.toFixed(0)}</p>
                    )}
                    {r.road_density !== undefined && (
                      <p style={{ margin: '4px 0', fontSize: '12px' }}><b>Road Density:</b> {r.road_density}</p>
                    )}
                    {r.distance_to_nearest_substation_m !== undefined && (
                      <p style={{ margin: '4px 0', fontSize: '12px' }}><b>Distance to Substation:</b> {r.distance_to_nearest_substation_m}m</p>
                    )}
                    {r.traffic_source && (
                      <p style={{ margin: '4px 0', fontSize: '11px', color: '#7f8c8d' }}><b>Data Source:</b> {r.traffic_source}</p>
                    )}
                    {r.reason && (
                      <p style={{ margin: '8px 0 0 0', fontSize: '11px', color: '#059669', lineHeight: '1.4', fontStyle: 'italic' }}>
                        {r.reason}
                      </p>
                    )}
                  </div>
                </Popup>
              </Marker>
            ))}

            {activeLayers.sdcc && aggregatedSdcc.map((s, i) => (
              <Marker
                key={`sdcc_${i}`}
                position={[s.lat, s.lon]}
                icon={L.divIcon({
                  className: '',
                  html: `<div style="width:12px;height:12px;border-radius:50%;background:white;border:3px solid #2563eb;box-shadow:0 1px 3px rgba(0,0,0,0.4)"></div>`,
                  iconSize: [12, 12],
                  iconAnchor: [6, 6]
                })}
              >
                <Popup>
                  <div style={{ fontFamily: 'Segoe UI, Arial, sans-serif', minWidth: '160px' }}>
                    <h4 style={{ margin: '0 0 6px 0', color: '#2563eb', fontSize: '13px' }}>🔵 SDCC Traffic Site</h4>
                    <p style={{ margin: '4px 0', fontSize: '12px' }}><b>Traffic Volume:</b> {s.volume.toFixed(0)}</p>
                    <p style={{ margin: '4px 0', fontSize: '11px', color: '#7f8c8d' }}>South Dublin County Council · 2024</p>
                  </div>
                </Popup>
              </Marker>
            ))}

            {activeLayers.windfarms && windFarms.map((w, i) => (
              <Marker
                key={`wf_${i}`}
                position={[w.lat, w.lon]}
                icon={L.divIcon({
                  className: '',
                  html: `<div style="width:14px;height:14px;border-radius:50%;background:#059669;border:2px solid white;box-shadow:0 1px 3px rgba(0,0,0,0.4);display:flex;align-items:center;justify-content:center;font-size:8px;">💨</div>`,
                  iconSize: [14, 14],
                  iconAnchor: [7, 7]
                })}
              >
                <Popup>
                  <div style={{ fontFamily: 'Segoe UI, Arial, sans-serif', minWidth: '180px' }}>
                    <h4 style={{ margin: '0 0 6px 0', color: '#059669', fontSize: '13px' }}>💨 {w.name}</h4>
                    <p style={{ margin: '4px 0', fontSize: '12px' }}><b>County:</b> {w.county}</p>
                    {w.capacity_mw && (
                      <p style={{ margin: '4px 0', fontSize: '12px' }}><b>Capacity:</b> {w.capacity_mw} MW</p>
                    )}
                  </div>
                </Popup>
              </Marker>
            ))}

            {activeLayers.heatmap && <HeatmapLayer points={heatmapPoints} />}

          </MapContainer>

          {showLayerPanel && (
            <LayerPanel
              activeLayers={activeLayers}
              onToggle={toggleLayer}
              tileMode={tileMode}
              onTileToggle={setTileMode}
              onHide={() => setShowLayerPanel(false)}
              evScenario={evScenario}
              onScenarioChange={handleScenarioChange}
              scenarioActive={scenarioActive}
              onResetScenario={handleResetScenario}
            />
          )}
        </div>

      </div>
    </div>
  );
}

export default App;