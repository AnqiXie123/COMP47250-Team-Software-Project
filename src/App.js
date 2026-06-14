import React from 'react';
import { MapContainer, TileLayer, Marker, Popup, LayersControl, FeatureGroup } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Leaflet default icon issues in React
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
  iconUrl: require('leaflet/dist/images/marker-icon.png'),
  shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

// Full Dublin Dataset
const RAW_CHARGERS = [
  // === ESB National Dataset ===
  {"id":"esb_0","lat":53.611523,"lon":-6.182852,"address":"Irish Rail, Railway Street, Balbriggan","operator":"ESB eCars","num_chargers":1},
  {"id":"esb_1","lat":53.310296,"lon":-6.195844,"address":"Irish Rail Booterstown DART Station, Rock Road, Blackrock","operator":"ESB eCars","num_chargers":1},
  {"id":"esb_2","lat":53.302596,"lon":-6.178974,"address":"Irish Rail Blackrock DART Station, Bath Place, Blackrock","operator":"ESB eCars","num_chargers":1},
  {"id":"esb_3","lat":53.3606289,"lon":-6.2993327,"address":"Tesco Cabra, Navan Road, Northside, Cabra","operator":"ESB eCars","num_chargers":1},
  {"id":"esb_4","lat":53.251009,"lon":-6.185082,"address":"Carrickmines Park, Glenamuck road, Carrickmines","operator":"ESB eCars","num_chargers":1},
  {"id":"esb_5","lat":53.275704,"lon":-6.103034,"address":"Irish Rail Dalkey DART Station, Ardeveehan Road, Dalkey","operator":"ESB eCars","num_chargers":1},
  {"id":"esb_6","lat":53.492693,"lon":-6.197212,"address":"Maxol Filling Station, M1 Junction 4, Donabate","operator":"ESB eCars","num_chargers":2},
  {"id":"esb_7","lat":53.5231007,"lon":-6.1023727,"address":"Tesco Rush, Whitestown Rd., Rush","operator":"ESB eCars","num_chargers":1},
  {"id":"esb_9","lat":53.4015594,"lon":-6.1799046,"address":"Tesco Clarehall, Malahide Rd, Northern Cross","operator":"ESB eCars","num_chargers":2},
  {"id":"esb_10","lat":53.3832068,"lon":-6.2163037,"address":"Tesco Artane, Artane Castle, Kilmore Rd","operator":"ESB eCars","num_chargers":2},
  {"id":"esb_11","lat":53.3830919,"lon":-6.2962494,"address":"Tesco Finglas Clearwater, Shopping Centre, Finglas","operator":"ESB eCars","num_chargers":1},
  {"id":"esb_12","lat":53.382607,"lon":-6.3810649,"address":"Tesco Blanchardstown, Roselawn Shopping Centre, Blanchardstown","operator":"ESB eCars","num_chargers":1},
  {"id":"esb_13","lat":53.3528616,"lon":-6.459997,"address":"Tesco Lucan, Shopping Centre, Hillcrest Dr, Lucan","operator":"ESB eCars","num_chargers":1},
  {"id":"esb_14","lat":53.3502421,"lon":-6.3889025,"address":"Tesco Liffey Valley, Fonthill Rd, Clondalkin","operator":"ESB eCars","num_chargers":2},
  {"id":"esb_15","lat":53.3470669,"lon":-6.2991244,"address":"Irish Rail Heuston Train Station, Dublin 8","operator":"ESB eCars","num_chargers":1},
  {"id":"esb_16","lat":53.3460323,"lon":-6.2928316,"address":"Irish Rail Heuston Train Station, St. Johns Road West","operator":"ESB eCars","num_chargers":1},
  {"id":"esb_17","lat":53.3200996,"lon":-6.3942292,"address":"Tesco Clondalkin, Boot Rd, Clondalkin","operator":"ESB eCars","num_chargers":1},
  {"id":"esb_18","lat":53.353856,"lon":-6.212747,"address":"Circle K Service Station, Promenade Road, Dublin 1","operator":"ESB eCars","num_chargers":2},
  {"id":"esb_19","lat":53.353218,"lon":-6.264812,"address":"Parnell Square West, Outside Rotunda Hospital","operator":"ESB eCars","num_chargers":1},
  {"id":"esb_20","lat":53.347479,"lon":-6.273155,"address":"Greek Street, Dublin 1","operator":"ESB eCars","num_chargers":1},
  {"id":"esb_21","lat":53.3459526,"lon":-6.2383946,"address":"Sir John Rogerson's Quay, Dublin 2","operator":"ESB eCars","num_chargers":2},
  {"id":"esb_22","lat":53.3453,"lon":-6.2513,"address":"Mark Street, Dublin 2","operator":"ESB eCars","num_chargers":1},
  {"id":"esb_23","lat":53.336699,"lon":-6.252228,"address":"Lower Pembroke Street, Dublin 2","operator":"ESB eCars","num_chargers":1},
  {"id":"esb_24","lat":53.336496,"lon":-6.242715,"address":"Mount Street Crescent, Dublin 2","operator":"ESB eCars","num_chargers":1},
  {"id":"esb_25","lat":53.335409,"lon":-6.257851,"address":"Earlsfort Terrace, Dublin 2","operator":"ESB eCars","num_chargers":1},
  {"id":"esb_26","lat":53.335203,"lon":-6.246205,"address":"Herbert Street, Dublin 2","operator":"ESB eCars","num_chargers":1},
  {"id":"esb_27","lat":53.3344,"lon":-6.24871,"address":"Court Apartments, Wilton Place, Dublin 2","operator":"ESB eCars","num_chargers":1},
  {"id":"esb_28","lat":53.333894,"lon":-6.267083,"address":"Synge Street, Dublin 2","operator":"ESB eCars","num_chargers":1},
  {"id":"esb_29","lat":53.332326,"lon":-6.255804,"address":"29 Adelaide Road, Dublin 2","operator":"ESB eCars","num_chargers":1},
  {"id":"esb_30","lat":53.3705209,"lon":-6.2094554,"address":"SuperValu Killester, Dublin 3","operator":"ESB eCars","num_chargers":2},
  {"id":"esb_31","lat":53.362913,"lon":-6.227746,"address":"Irish Rail Clontarf DART Station, Clontarf Road","operator":"ESB eCars","num_chargers":1},
  {"id":"esb_32","lat":53.360832,"lon":-6.183082,"address":"Kincora Road, Dublin 3","operator":"ESB eCars","num_chargers":1},
  {"id":"esb_33","lat":53.342945,"lon":-6.228056,"address":"Thorncastle Street, Dublin 4","operator":"ESB eCars","num_chargers":1},
  {"id":"esb_34","lat":53.338798,"lon":-6.232894,"address":"South Lotts Road, Dublin 4","operator":"ESB eCars","num_chargers":1},
  {"id":"esb_35","lat":53.322343,"lon":-6.238683,"address":"Belmont Avenue, Dublin 4","operator":"ESB eCars","num_chargers":1},
  {"id":"esb_36","lat":53.3805194,"lon":-6.1808952,"address":"SuperValu Raheny, Raheny Shopping Centre","operator":"ESB eCars","num_chargers":2},
  {"id":"esb_37","lat":53.325515,"lon":-6.252422,"address":"Chelmsford Road, Dublin 6","operator":"ESB eCars","num_chargers":1},
  {"id":"esb_38","lat":53.3210126,"lon":-6.2659235,"address":"Tesco Metro, Rathmines Rd Upper, Dublin 6","operator":"ESB eCars","num_chargers":1},
  {"id":"esb_39","lat":53.3582,"lon":-6.2672,"address":"Nelson Street, Dublin 7","operator":"ESB eCars","num_chargers":1},
  {"id":"esb_40","lat":53.354892,"lon":-6.287405,"address":"St. Joseph's Road, Dublin 7","operator":"ESB eCars","num_chargers":1},
  {"id":"esb_41","lat":53.347636,"lon":-6.285234,"address":"Liffey Street West, Dublin 7","operator":"ESB eCars","num_chargers":1},
  {"id":"esb_42","lat":53.3406684,"lon":-6.2684288,"address":"Golden Lane, Dublin 8","operator":"ESB eCars","num_chargers":1},
  {"id":"esb_43","lat":53.366828,"lon":-6.256153,"address":"Hollybank Road, Dublin 9","operator":"ESB eCars","num_chargers":1},
  {"id":"esb_44","lat":53.409487,"lon":-6.345243,"address":"GMC House, Millennium Business Park, Cappagh Road","operator":"ESB eCars","num_chargers":1},
  {"id":"esb_45","lat":53.369052,"lon":-6.276341,"address":"Finglas Road, Dublin 11","operator":"ESB eCars","num_chargers":1},
  {"id":"esb_46","lat":53.331883,"lon":-6.372194,"address":"The Plaza, Park West Road, Dublin 12","operator":"ESB eCars","num_chargers":1},
  {"id":"esb_47","lat":53.329905,"lon":-6.299208,"address":"Crumlin Road, Dublin 12","operator":"ESB eCars","num_chargers":1},
  {"id":"esb_48","lat":53.31948,"lon":-6.315448,"address":"St. Agnes Road, Dublin 12","operator":"ESB eCars","num_chargers":1},
  {"id":"esb_49","lat":53.3192906,"lon":-6.2929249,"address":"Supervalu Kimmage, Sundrive Shopping Centre","operator":"ESB eCars","num_chargers":2},
  {"id":"esb_50","lat":53.316717,"lon":-6.333704,"address":"Greenhills Road, Dublin 12","operator":"ESB eCars","num_chargers":1},
  {"id":"esb_51","lat":53.391623,"lon":-6.116236,"address":"Sutton DART Station, Station Road, Dublin 13","operator":"ESB eCars","num_chargers":1},
  {"id":"esb_52","lat":53.39066,"lon":-6.110035,"address":"SuperValu Sutton, Sutton Cross, Dublin 13","operator":"ESB eCars","num_chargers":2},
  {"id":"esb_53","lat":53.2906888,"lon":-6.2452316,"address":"Main Street, Dublin 14","operator":"ESB eCars","num_chargers":1},
  {"id":"esb_54","lat":53.286679,"lon":-6.240973,"address":"Dundrum Shopping Centre, Wyckham Way, Dublin 14","operator":"ESB eCars","num_chargers":2},
  {"id":"esb_55","lat":53.3953412,"lon":-6.3895335,"address":"Blanchardstown HPC Hub, Blanchardstown Centre","operator":"ESB eCars","num_chargers":4},
  {"id":"esb_56","lat":53.392154,"lon":-6.39283,"address":"Blanchardstown Centre, Navan Road, Dublin 15","operator":"ESB eCars","num_chargers":2},
  {"id":"esb_57","lat":53.386875,"lon":-6.374254,"address":"Mill Road, Dublin 15","operator":"ESB eCars","num_chargers":1},
  {"id":"esb_58","lat":53.377326,"lon":-6.391846,"address":"Irish Rail Coolmine Train Station, Carpenterstown Road","operator":"ESB eCars","num_chargers":1},
  {"id":"esb_59","lat":53.375177,"lon":-6.364012,"address":"Park Avenue, Castleknock, Dublin 15","operator":"ESB eCars","num_chargers":1},
  {"id":"esb_60","lat":53.2828883,"lon":-6.3190804,"address":"SuperValu Knocklyon, Knocklyon Road, Dublin 16","operator":"ESB eCars","num_chargers":2},
  {"id":"esb_61","lat":53.2749238,"lon":-6.254368,"address":"Supervalu Ballinteer, Ballinteer Ave, Dublin 16","operator":"ESB eCars","num_chargers":2},
  {"id":"esb_62","lat":53.2730493,"lon":-6.3150204,"address":"Tesco White Pines, Stocking Avenue, Dublin 16","operator":"ESB eCars","num_chargers":1},
  {"id":"esb_63","lat":53.412778,"lon":-6.216111,"address":"Circle K Service Station, Clonshaugh Road, Dublin 17","operator":"ESB eCars","num_chargers":1},
  {"id":"esb_64","lat":53.395465,"lon":-6.214452,"address":"Northside Shopping Centre, Oscar Traynor Road","operator":"ESB eCars","num_chargers":2},
  {"id":"esb_65","lat":53.280332,"lon":-6.213815,"address":"Stillorgan Luas Park & Ride, Blackthorn Drive","operator":"ESB eCars","num_chargers":3},
  {"id":"esb_66","lat":53.277164,"lon":-6.203613,"address":"Sandyford Luas Park and Ride, Blackthorn Avenue","operator":"ESB eCars","num_chargers":1},
  {"id":"esb_67","lat":53.260088,"lon":-6.149376,"address":"Bray Road, Dublin 18","operator":"ESB eCars","num_chargers":1},
  {"id":"esb_68","lat":53.252775,"lon":-6.169813,"address":"Carrickmines Luas Park and Ride, Glenamuck Road North","operator":"ESB eCars","num_chargers":2},
  {"id":"esb_69","lat":53.236875,"lon":-6.11792,"address":"Shankhill Dart Station, Shanganagh Wood, Dublin 18","operator":"ESB eCars","num_chargers":1},
  {"id":"esb_70","lat":53.285621,"lon":-6.369887,"address":"The Square Shopping Centre, Belgard Road, Dublin 24","operator":"ESB eCars","num_chargers":2},
  {"id":"esb_71","lat":53.281093,"lon":-6.469944,"address":"Main Street, Dublin 24","operator":"ESB eCars","num_chargers":1},
  {"id":"esb_72","lat":53.428658,"lon":-6.234603,"address":"Circle K Service Station, Corballis Road North, Dublin Airport","operator":"ESB eCars","num_chargers":1},
  {"id":"esb_73","lat":53.2938,"lon":-6.1348,"address":"Marine Road, Dun Laoghaire","operator":"ESB eCars","num_chargers":1},
  {"id":"esb_74","lat":53.282568,"lon":-6.143881,"address":"Park Pointe Shopping Centre, Glenageary Road Upper","operator":"ESB eCars","num_chargers":2},
  {"id":"esb_75","lat":53.251864,"lon":-6.186801,"address":"Carrickmines Park HPC Hub, Glenamuck Road","operator":"ESB eCars","num_chargers":4},
  {"id":"esb_76","lat":53.349266,"lon":-6.452681,"address":"Lucan Shopping Centre (SuperValu), Newcastle Road","operator":"ESB eCars","num_chargers":1},
  {"id":"esb_77","lat":53.520646,"lon":-6.144629,"address":"Irish Rail Rush and Lusk Train Station, Lusk","operator":"ESB eCars","num_chargers":1},
  {"id":"esb_78","lat":53.451478,"lon":-6.156156,"address":"Malahide DART Station, Railway Avenue, Malahide","operator":"ESB eCars","num_chargers":1},
  {"id":"esb_79","lat":53.451232,"lon":-6.15157,"address":"James's Terrace, Malahide","operator":"ESB eCars","num_chargers":1},
  {"id":"esb_80","lat":53.298772,"lon":-6.496403,"address":"Supervalu Newcastle, Graydon Road, Newcastle","operator":"ESB eCars","num_chargers":2},
  {"id":"esb_81","lat":53.283222,"lon":-6.421705,"address":"Citywest Shopping Centre Car Park, Saggart","operator":"ESB eCars","num_chargers":1},
  {"id":"esb_82","lat":53.578784,"lon":-6.104879,"address":"Public Parking, South Strand Road, Skerries","operator":"ESB eCars","num_chargers":1},
  {"id":"esb_83","lat":53.295343,"lon":-6.203373,"address":"Talbot Hotel Stillorgan, Stillorgan Road","operator":"ESB eCars","num_chargers":1},
  {"id":"esb_84","lat":53.290457,"lon":-6.199702,"address":"Old Dublin Road, Stillorgan","operator":"ESB eCars","num_chargers":1},
  {"id":"esb_85","lat":53.45423,"lon":-6.223713,"address":"Main Street, Swords","operator":"ESB eCars","num_chargers":1},
  {"id":"esb_86","lat":53.4539168,"lon":-6.2213287,"address":"Swords Pavilions Shopping Centre, Malahide Rd, Swords Demesne, Swords","operator":"ESB eCars","num_chargers":5},
  {"id":"esb_87","lat":53.445169,"lon":-6.21589,"address":"Tesco, Airside (R125), Swords","operator":"ESB eCars","num_chargers":1},

  // === DLR Dataset ===
  {"id":"dlr_0","lat":53.2601371,"lon":-6.1492864,"address":"Bray Road, Cabinteely, Dublin 18","operator":"ESB","num_chargers":2},
  {"id":"dlr_1","lat":53.3026354,"lon":-6.1792212,"address":"Irish Rail Blackrock DART Station, Bath Place","operator":"ESB","num_chargers":2},
  {"id":"dlr_2","lat":53.2903114,"lon":-6.1996911,"address":"Old Dublin Road, Stillorgan","operator":"ESB","num_chargers":2},
  {"id":"dlr_3","lat":53.3093008,"lon":-6.1958892,"address":"Irish Rail Booterstown DART Station, Rock Road","operator":"ESB","num_chargers":2},
  {"id":"dlr_4","lat":53.2826908,"lon":-6.1438747,"address":"Park Pointe Shopping Centre, Glenageary Road Upper","operator":"ESB","num_chargers":3},
  {"id":"dlr_5","lat":53.2756863,"lon":-6.1030219,"address":"Irish Rail Dalkey DART Station, Ardeveehan Road","operator":"ESB","num_chargers":2},
  {"id":"dlr_6","lat":53.2512608,"lon":-6.1852011,"address":"The Park Retail Centre, Carrickmines","operator":"ESB","num_chargers":2},
  {"id":"dlr_7","lat":53.2771422,"lon":-6.2036740,"address":"Sandyford Luas Park and Ride, Blackthorn Avenue","operator":"ESB","num_chargers":2},
  {"id":"dlr_8","lat":53.2803320,"lon":-6.2138150,"address":"Stillorgan Luas Park & Ride","operator":"ESB","num_chargers":2},
  {"id":"dlr_9","lat":53.2898950,"lon":-6.2441720,"address":"Main Street, Dundrum, Dublin 14","operator":"ESB","num_chargers":2},
  {"id":"dlr_10","lat":53.2938000,"lon":-6.1348000,"address":"Marine Road, Dun Laoghaire","operator":"ESB","num_chargers":2},
  {"id":"dlr_11","lat":53.2367349,"lon":-6.1176805,"address":"Shankhill Dart Station, Shanganagh Wood","operator":"ESB","num_chargers":2},
  {"id":"dlr_12","lat":53.2527750,"lon":-6.1698130,"address":"Carrickmines Luas Park and Ride, Off Glenamuck Road North","operator":"ESB","num_chargers":4},
  {"id":"dlr_13","lat":53.2947381,"lon":-6.2018214,"address":"Stillorgan Park Hotel, Stillorgan Road","operator":"ESB","num_chargers":1},
  {"id":"dlr_14","lat":53.2775529,"lon":-6.1398350,"address":"Aldi, Sallynoggin, Dublin","operator":"EasyGo","num_chargers":4},
  {"id":"dlr_15","lat":53.2774250,"lon":-6.2658470,"address":"Lidl Rathfarnham, 13 Grange Road","operator":"ESB","num_chargers":2},
  {"id":"dlr_16","lat":53.2713140,"lon":-6.2060860,"address":"Bewleys Hotel Leopardstown, Central Park","operator":"ESB","num_chargers":1},
  {"id":"dlr_17","lat":53.2953424,"lon":-6.2032922,"address":"Talbot Hotel Stillorgan, Stillorgan Road","operator":"ESB","num_chargers":3},
  {"id":"dlr_18","lat":53.3049123,"lon":-6.2064813,"address":"Radisson Blu St Helen's, Stillorgan Road","operator":"ESB","num_chargers":2},
  {"id":"dlr_19","lat":53.2833000,"lon":-6.1659200,"address":"Windsor Motors Deansgrange (Nissan)","operator":"Other","num_chargers":1},
  {"id":"dlr_20","lat":53.2966786,"lon":-6.1409639,"address":"Commissioners of Irish Lights, Harbour Road","operator":"EasyGo","num_chargers":2},
  {"id":"dlr_21","lat":53.2466244,"lon":-6.1322697,"address":"Eurofound, Wyattville Rd.","operator":"EasyGo","num_chargers":2},
  {"id":"dlr_22","lat":53.2335177,"lon":-6.1231442,"address":"Lidl Ireland, Shankhill","operator":"EasyGo","num_chargers":2},
  {"id":"dlr_23","lat":53.2754301,"lon":-6.1578633,"address":"Pottery Road, Dun Laoghaire Industrial Estate","operator":"Tesla","num_chargers":2},
  {"id":"dlr_24","lat":53.2712959,"lon":-6.2061397,"address":"Clayton Hotel Dublin - Leopardstown","operator":"Tesla","num_chargers":2},
  {"id":"dlr_25","lat":53.2879188,"lon":-6.2356596,"address":"Overend Way, D14 EE77 Dublin","operator":"Tesla","num_chargers":2},
  {"id":"dlr_26","lat":53.2826337,"lon":-6.1436962,"address":"Park Pointe Shopping Centre, Glenageary Road Upper","operator":"ESB","num_chargers":2},
  {"id":"dlr_27","lat":53.2803986,"lon":-6.2139673,"address":"Stillorgan Luas Park & Ride","operator":"ESB","num_chargers":3},
  {"id":"dlr_28","lat":53.2785246,"lon":-6.1375407,"address":"Lidl, Glenageary, Dublin","operator":"EasyGo","num_chargers":2},
  {"id":"dlr_29","lat":53.2956815,"lon":-6.1376914,"address":"Crofton Road, Dun Laoghaire","operator":"Other","num_chargers":1},
  {"id":"dlr_30","lat":53.2928196,"lon":-6.1300220,"address":"East Pier, Dun Laoghaire Harbour","operator":"Other","num_chargers":2},
  {"id":"dlr_31","lat":53.2860018,"lon":-6.2398900,"address":"Dundrum Shopping Center, Dublin","operator":"ESB","num_chargers":4},
  {"id":"dlr_32","lat":53.2719238,"lon":-6.2021433,"address":"Vodafone Ireland Ltd, Leopardstown","operator":"Other","num_chargers":2},
  {"id":"dlr_33","lat":53.2704321,"lon":-6.2051641,"address":"Central Park, Carmanhall and Leopardstown","operator":"Tesla","num_chargers":3},
  {"id":"dlr_34","lat":53.2703882,"lon":-6.2050745,"address":"Central Park, Carmanhall and Leopardstown","operator":"Other","num_chargers":3},

  // === SDCC Dataset ===
  {"id":"sdcc_0","lat":53.3134493,"lon":-6.392268,"address":"Maldron Hotel","operator":"EasyGo","num_chargers":2},
  {"id":"sdcc_1","lat":53.3144274,"lon":-6.3938866,"address":"Circle K Newlands","operator":"ESB","num_chargers":1},
  {"id":"sdcc_2","lat":53.3144274,"lon":-6.3938866,"address":"Circle K Newlands","operator":"ESB","num_chargers":1},
  {"id":"sdcc_3","lat":53.3144274,"lon":-6.3938866,"address":"Circle K Newlands","operator":"ESB","num_chargers":1},
  {"id":"sdcc_6","lat":53.3457966,"lon":-6.4742753,"address":"Lidl Adamstown","operator":"EasyGo","num_chargers":2},
  {"id":"sdcc_8","lat":53.3529587,"lon":-6.4592553,"address":"Tesco, Lucan","operator":"ESB","num_chargers":2},
  {"id":"sdcc_9","lat":53.3481848,"lon":-6.4523319,"address":"Lucan Shopping Centre","operator":"ESB","num_chargers":1},
  {"id":"sdcc_10","lat":53.3481848,"lon":-6.4523319,"address":"Lucan Shopping Centre","operator":"ESB","num_chargers":1},
  {"id":"sdcc_22","lat":53.2857114,"lon":-6.4180466,"address":"Lidl Fortunestown","operator":"EasyGo","num_chargers":2},
  {"id":"sdcc_23","lat":53.2824594,"lon":-6.4230167,"address":"Citywest Shopping Centre","operator":"ESB","num_chargers":2}
];

// Preserve specific brand types during overlay resolution
const getUniqueChargers = (data) => {
  const uniqueMap = new Map();
  data.forEach(item => {
    const key = `${item.lat.toFixed(5)}_${item.lon.toFixed(5)}`;
    if (uniqueMap.has(key)) {
      const existing = uniqueMap.get(key);
      existing.num_chargers = Math.max(existing.num_chargers, item.num_chargers);
      const currentOp = item.operator.toUpperCase();
      if ((existing.operator.toUpperCase() === 'ESB' || existing.operator.toUpperCase() === 'ESB ECARS') && 
          (!currentOp.includes('ESB'))) {
        existing.operator = item.operator;
      }
    } else {
      uniqueMap.set(key, { ...item });
    }
  });
  return Array.from(uniqueMap.values());
};

const CLEANED_CHARGERS = getUniqueChargers(RAW_CHARGERS);

// Stylized English Popup Component
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
      <hr style={{ border: '0', borderTop: '1px solid #eee', margin: '8px 0' }} />
      <button 
        onClick={() => alert(`Analyzing gaps for: ${charger.address}`)}
        style={{
          width: '100%', background: '#34495e', color: '#fff', border: '0',
          padding: '5px', borderRadius: '4px', cursor: 'pointer', fontSize: '11px'
        }}
      >
        View Supply-Demand Gap
      </button>
    </div>
  );
};

function App() {
  const esbChargers = CLEANED_CHARGERS.filter(c => c.operator.toUpperCase().includes('ESB'));
  const easyGoChargers = CLEANED_CHARGERS.filter(c => c.operator.toUpperCase().includes('EASYGO'));
  const otherChargers = CLEANED_CHARGERS.filter(c => 
    !c.operator.toUpperCase().includes('ESB') && !c.operator.toUpperCase().includes('EASYGO')
  );

  return (
    <div style={{ height: '100vh', width: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* English Header Panel */}
      <div style={{ height: '55px', background: '#1a252f', color: '#fff', display: 'flex', alignItems: 'center', padding: '0 20px', zIndex: 1000 }}>
        <h2 style={{ margin: 0, fontSize: '16px', fontWeight: '500' }}>
          ⚡ EcoCharge Dublin: EV Infrastructure Optimization Dashboard
        </h2>
      </div>

      {/* Map Content View */}
      <div style={{ flex: 1, width: '100%' }}>
        <MapContainer center={[53.3498, -6.2603]} zoom={11} style={{ height: '100%', width: '100%' }}>          
          <LayersControl position="topright">     
            <LayersControl.BaseLayer checked name="Standard Map">
              <TileLayer
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                attribution="&copy; <a href='https://openstreetmap.org'>OpenStreetMap</a>"
              />
            </LayersControl.BaseLayer>

            <LayersControl.BaseLayer name="Dark Mode Map">
              <TileLayer
                url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
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
          </LayersControl>

        </MapContainer>
      </div>
    </div>
  );
}

export default App;