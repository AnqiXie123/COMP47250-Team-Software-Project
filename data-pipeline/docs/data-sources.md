# Data Sources Feasibility Report
Date: 06-01-2026
Author: Yifei Wang

## 1. Smart Dublin Open Data Portal
- URL: https://data.smartdublin.ie

### 1a. EV Charger Locations

#### Dataset 1: Public EV Charging Points DLR
- Dataset URL: https://data.smartdublin.ie/dataset/public-ev-charging-points-dlr
- Source organisation: Dún Laoghaire-Rathdown County Council
- Format: GeoJSON (primary), CSV
- Accessible: Y (direct download, no registration required)
- Last updated: 2025-05-26
- Record count: ~30 stations
- Key fields: coordinates (lat/lon), ServiceProvider, NumChargers,
  Type, FastSlow (charging speed), InService, PublicAccess, ParkingType
- Coverage: Dún Laoghaire-Rathdown area (south Dublin)
- Status: ✅ Confirmed usable — rich fields, good spatial coverage

#### Dataset 2: Public EV Charging Points SDCC
- Dataset URL: https://data.smartdublin.ie/dataset/public-ev-charging-points-sdcc1
- Source organisation: South Dublin County Council
- Format: CSV
- Accessible: Y (direct download, no registration required)
- Last updated: 2024-03-08
- Record count: 33 stations
- Key fields: LEA (sub-district), Location (text only), Operator,
  Number_of_chargers, Type, Rating (charging power)
- Coverage: South Dublin County (Tallaght, Clondalkin, Lucan area)
- Status: ⚠️ Usable with limitations — no lat/lon coordinates;
  geocoding required before spatial analysis

#### Dataset 3: ESB EV Public Charging Network — Ireland
- Dataset URL: https://data.gov.ie/en_GB/dataset/esb-ev-public-charging-network
- Direct download: https://cdn.esb.ie/media-staging/docs/default-source/ecars/its-data-ecars-sites/its-data-ecars-sites-roi-ni.csv
- Source organisation: ESB (Electricity Supply Board), published via data.gov.ie
- Format: CSV
- Accessible: Y (direct download, no registration required)
- Last updated: 2024-12-02 (quarterly update frequency)
- Record count: 591 total (island of Ireland); 88 Dublin county records
- Key fields: Territory, County, Address, Nr. Chargers, Latitude,
  Longitude, Open Hours, connector types (CCS/CHAdeMO/AC), power output (kW)
- Coverage: Full Dublin administrative area including city centre (DCC),
  Fingal (FCC), South Dublin (SDCC), and Dún Laoghaire-Rathdown (DLR)
- Status: ✅ Confirmed usable — resolves previously identified FCC and
  DCC coverage gaps; all 88 Dublin records have complete coordinates

#### Note on Combined EV Charger Coverage
With ESB eCars (88 records), DLR GeoJSON (~30 records), and SDCC CSV
(33 records), total Dublin EV charger coverage is approximately 150
records across all four county council areas. ESB eCars will serve as
the primary dataset; DLR and SDCC provide supplementary detail.

#### Datasets Investigated but Rejected
- EVPZ Stations FCC (Fingal County Council):
  only 2 records, insufficient coverage — rejected
- EV Charging Location Points Public FCC (Fingal County Council):
  only 6 records, missing key fields — rejected
- Note: No EV charger dataset found for Dublin City Council (DCC)
  area via Smart Dublin search. ESB eCars national dataset to be
  investigated in Phase 4 as a supplementary source to improve
  Dublin-wide coverage.

#### Known Limitations
- No single dataset covers the full Dublin administrative area;
  data is fragmented across county councils
- FCC (Fingal/north Dublin) and DCC (city centre) areas currently
  lack usable open data
- SDCC dataset requires geocoding before use in spatial analysis
- DLR dataset was surveyed in 2019; some entries may be outdated
  despite the 2025 metadata update date
  
### 1b. Traffic Volume Data (Proxy for EV Charging Demand)

#### Dataset 1: Traffic Volumes from SCATS — DLR 2023
- Dataset URL: https://data.smartdublin.ie/dataset/traffic-volumes-from-scats-traffic-management-system-2023
- Source organisation: Dún Laoghaire-Rathdown County Council
- Format: CSV (one file per month)
- Accessible: Y (direct download, no registration required)
- Last updated: 2025-06-19
- Coverage: Dún Laoghaire-Rathdown area, full year 2023 (12 months)
- Temporal resolution: Hourly
- Record count: ~2.4 million rows per month
- Key fields: End_Time, Region, Site, Detector, Sum_Volume, Avg_Volume
- Note: Site field must be joined with a separate site location
  file to obtain coordinates
- Status: ✅ Primary traffic data source for DLR area

#### Supplementary: SCATS Site Location Data — DLR
- Dataset URL: https://data.smartdublin.ie/dataset/traffic-signals-and-scats-sites-locations-dlr
- Format: CSV
- Accessible: Y (direct download)
- Record count: 290 sites
- Key fields: Site_ID, Location, Lat, Long
- Usage: joined with SCATS volume data to add coordinates
- Status: ✅ Downloaded and used in 03_clean_traffic_data.py

#### Dataset 2: Traffic Volumes from SCATS — DCC 2025
- Dataset URL (Jan–Jun): https://data.smartdublin.ie/dataset/dcc-scats-detector-volume-jan-jun-2025
- Dataset URL (Jul–Dec): https://data.smartdublin.ie/dataset/dcc-scats-detector-volume-jul-dec-2025
- Source organisation: Dublin City Council
- Format: CSV (monthly)
- Accessible: Y (ZIP download per month)
- Last updated: 2026-02-12
- Coverage: Dublin City area, available months: Dec 2024, Mar, Apr,
  May, Aug 2025 (other months not published by DCC)
- Temporal resolution: Hourly
- Record count: ~5.4–12 million rows per month (varies by month)
- Key fields: End_Time, Region, Site, Detector, Sum_Volume,
  Avg_Volume, Weighted_Avg, Weighted_Var, Weighted_Std_Dev
- Status: ✅ Primary traffic data source for DCC city centre area;
  processed in 06_clean_traffic_dcc.py

#### Supplementary: SCATS Site Location Data — DCC
- Dataset URL: https://data.smartdublin.ie/dataset/traffic-signals-and-scats-sites-locations-dcc
- Direct download (CSV): https://data.smartdublin.ie/dataset/5fd277d3-4ece-45b7-982a-b6116c45470b/resource/f64c93a1-2bce-42d0-8a8b-b41c95546d8a/download/dcc-traffic-scats-signals-google-maps-1.csv
- Source organisation: Dublin City Council
- Format: CSV
- Accessible: Y (direct download)
- Record count: 1,205 sites
- Key fields: Site_ID, Location, Lat, Long
- Update (06-29-2026): Originally assumed to be bundled inside the
  monthly volume ZIP downloads (see prior note below); this was
  incorrect. The site location data is published as a separate,
  independent dataset and was not found during the initial Phase 1
  search. It has since been located and is used in
  06_clean_traffic_dcc.py. Site_ID joins directly against the
  numeric Site column in the volume data (e.g. Site_ID 58 = "Dorset
  St / Frederick St / Blessington St", confirmed against
  SCATSMarch2025.csv).
- Coordinate match rate: 95.1% of volume rows (3,010,817 /
  3,164,738); 117 unique site_ids have no matching location record
- Status: ✅ Downloaded and used in 06_clean_traffic_dcc.py

#### Update (06-29-2026): DCC and DLR coverage overlap discovered
While merging DLR (03 output) and DCC (06 output) in
05_build_feature_dataset.py, a direct check against the real site
coordinates (see check_dlr_dcc_overlap.py) found that **222 of
DLR's 223 sites share the exact same site_id as a DCC site, at 0m
apart** — i.e. the same physical SCATS sensor. DCC's administrative
coverage is far larger than initially assumed during Phase 1 (it is
not limited to the city centre; it extends into areas such as
Terenure, Crumlin, and Drumcondra, well beyond what "city centre"
suggested). DLR's coverage area sits almost entirely *inside* DCC's.

This means the two datasets are not independent/complementary in
the way the Phase 1 feasibility write-up assumed — they substantially
describe the same physical sensors, reported by different councils
for different time periods (DLR: 2023 full year; DCC: 5 months of
2024-2025). The deduplication rule used in 05 keeps the DCC value
(more recent) where both exist; see 05_build_feature_dataset.py's
docstring for the full reasoning.

**Implication for FCC investigation:** given that DCC's true coverage
was significantly underestimated on first search, it may be worth
re-investigating whether an FCC (Fingal) traffic/charger dataset
exists under a less obvious name or administrative grouping, rather
than concluding none exists based on the Phase 1 search alone.

#### Dataset 3: Traffic Flow Data — SDCC Apr–Sep 2024
- Dataset URL: https://data.smartdublin.ie/dataset/traffic-flow-data-01-april-to-19-september-2024-sdcc
- Source organisation: South Dublin County Council
- Format: GeoJSON (geometry null — no spatial coordinates embedded)
- Accessible: Y (direct download)
- Last updated: 2024-11-27
- Coverage: South Dublin County, April to September 2024
- Temporal resolution: 15 minutes
- Key fields: site, date, start_time, end_time, flow, flow_pc,
  cong (congestion), dsat (degree of saturation)
- Note: geometry field is null for all records; site ID (e.g.
  N01111A) must be matched against a separate SDCC site
  location table to obtain coordinates — this table has not
  yet been found and should be investigated in Phase 2
- Status: ⚠️ Usable data values but requires site location
  lookup for spatial analysis

#### Update (06-29-2026): Site location file found and verified complete
The site location file referenced as "not yet found" above has been
located: "Traffic Data Site Names SDCC" on South Dublin County
Council's own ArcGIS Hub portal (not on data.smartdublin.ie directly
— that page only lists/describes the dataset and links out to the
real host). Direct CSV download confirmed via two independent
fetches to return identical content (37 physical sites, 65 detection
points after accounting for multiple directions per junction) —
this is the network's true full extent, not a truncated download.
South Dublin's SCOOT network is far smaller than DCC's or DLR's
SCATS networks, concentrated on motorway junctions (M50, N4, N81)
and a handful of arterial roads rather than dense urban junctions.

**Unit caveat:** SDCC's `flow` field is a SCOOT-modelled demand
estimate ("a representation of demand built up over several minutes
by the SCOOT model" per the source's own field description), not a
direct vehicle count like SCATS's `sum_volume`. Real data shows
SDCC's flow values (mean ~142) are roughly 5x smaller than DCC's
sum_volume (mean ~700) — this may reflect a genuine traffic
difference, a measurement methodology difference, or both. Flagged
via the `traffic_source` column in the unified feature dataset;
not resolved, decision on how to handle left to the ML teammate.

#### Dataset 4: Traffic Counts — Cordon Count DCC, November 2019
- Dataset URL: https://data.smartdublin.ie/dataset/traffic-volumes
- Source organisation: Dublin City Council
- Format: CSV (count data) + CSV (site locations with LAT/LONG)
- Accessible: Y (direct download)
- Last updated: 2025-06-19
- Coverage: 33 entry points into Dublin City Centre cordon
- Temporal resolution: 15 minutes (single survey period)
- Key fields: SiteNumber, Direction, CountType, CountValue, Date,
  Time; location file provides LatitudeX, LongitudeY
- Note: One-off annual survey data from November 2019 only;
  not continuous sensor data. Useful as supplementary
  reference for city centre entry point traffic patterns
- Status: ⚠️ Supplementary reference only — not suitable as
  primary traffic data due to single time point

#### Known Limitations
- No continuous traffic volume data found for FCC (Fingal /
  north Dublin) area. Re-searched on 06-29-2026 (Smart Dublin,
  data.gov.ie, and Fingal's own open data portal data.fingal.ie)
  after discovering DCC's site location file had been missed on
  first search — confirmed FCC has not published a SCATS-equivalent
  traffic volume dataset or site location file under any name found.
  Existing FCC traffic-adjacent data (3 cycle counters, parking
  fines, a single park's vehicle count at Ardgillan Demesne) cannot
  substitute for junction-level traffic volume. Treated as a
  confirmed data gap, not an unexplored one.
- SDCC and DLR SCATS data require joining with separate site
  location files to enable spatial analysis
- DCC 2025 SCATS data has gaps (several months missing from
  both half-year datasets)
- All traffic datasets serve as proxy for EV charging demand,
  as direct EV charging session data is not publicly available
  
## 2. EirGrid Smart Grid Dashboard
- URL: https://www.smartgriddashboard.com
- Data download page: https://www.eirgrid.ie/grid/system-and-renewable-data-reports

### Dataset: System Data Quarterly Hourly — 2026
- Download URL: https://cms.eirgrid.ie/sites/default/files/publications/System-Data-Qtr-Hourly-2026-V4.xlsx
- Format: Excel (.xlsx), single sheet
- Accessible: Y (direct download, no registration required)
- Coverage: Republic of Ireland (IE) + Northern Ireland (NI) +
  All Island (AI) aggregates
- Temporal resolution: 15 minutes
- Date range: 2026-01-01 to 2026-04-30 (as of access date 2026-05-31;
  file updated periodically — re-download recommended)
- Record count: 11,516 rows
- Key fields for this project:
  - IE Wind Generation (MW) — actual wind power output
  - IE Solar Generation (MW) — actual solar power output
  - IE Wind Availability / IE Solar Availability (MW) — capacity
  - IE Wind Penetration / IE Solar Penetration (%) — grid share
- Note: File is versioned (V4 at time of access) and updated
  regularly; re-download recommended before final analysis.
  Solar energy reporting for Ireland began April 2023 per
  dataset notes; earlier solar values may be unreliable.
- Contact for queries: RenewableReports@EirGrid.com
- Status: ✅ Confirmed usable — correct format, sufficient
  temporal resolution, directly downloadable

### Known Limitations
- Data covers Ireland as a whole, not Dublin specifically;
  no sub-regional renewable generation breakdown available
  from this source
- This is a national-level dataset; the 'greenness' overlay
  for Dublin will be derived from national IE figures as a
  reasonable proxy, which is a documented assumption
- Old API endpoint (smartgriddashboard.com/DashboardService.svc)
  returns HTTP 503 and is no longer accessible
  
## 3. Central Statistics Office (CSO) Ireland
- URL: https://www.cso.ie
- PxStat database: https://data.cso.ie

### Dataset 1: TEM12 — New Vehicles Licensed by Month, Taxation Class
and Fuel Type (National)
- PxStat URL: https://data.cso.ie/table/TEM12
- Format: Interactive table with CSV/JSON download + REST API
- API endpoint: https://ws.cso.ie/public/api.restful/PxStat.Data.Cube_API.ReadDataset/TEM12/CSV/1.0/en
- Accessible: Y (no registration required)
- Last updated: 12/05/2026
- Coverage: Republic of Ireland, national level
- Date range: January 2015 – April 2026 (updated monthly)
- Key fields: Month, Type of Vehicle Registration,
  Type of Fuel (incl. Electric, Hybrid, PHEV), count
- Status: ✅ Confirmed usable — API accessible, Electric fuel
  type available, monthly granularity

### Dataset 2: TEM27 — New and Secondhand Vehicles by Taxation Class,
Fuel Type and Year (National)
- PxStat URL: https://data.cso.ie/table/TEM27
- Format: Interactive table with CSV/JSON download + REST API
- Accessible: Y (no registration required)
- Last updated: 15/01/2026
- Coverage: Republic of Ireland, national level
- Date range: 2010 – 2025 (annual)
- Key fields: Year, Taxation Class, Type of Fuel (incl. Electric,
  Hybrid), count
- Status: ✅ Confirmed usable — annual EV totals by fuel type

### Dataset 3: Sustainable Mobility and Transport 2021 (Reference)
- URL: https://www.cso.ie/en/releasesandpublications/ep/p-smt/sustainablemobilityandtransport2021/electricvehicles/
- Format: Statistical report with Excel tables
- Key finding: EV ownership in Dublin (4.9%) is approximately
  twice the national average outside Dublin (2.5%), providing
  a county-level weighting factor for demand modelling
- Status: ✅ Used as reference — Dublin EV penetration
  weighting coefficient

### Known Limitations
- No PxStat API table provides EV licensing counts broken down
  by county and fuel type simultaneously; county-level data
  is only available in ad-hoc Excel attachments within
  individual monthly report pages
- National-level figures (TEM12, TEM27) will be used as the
  primary EV penetration proxy, adjusted using the Dublin
  weighting coefficient from the 2021 survey
- CSO data covers new vehicle licensing only; total EV stock
  on the road requires separate estimation

## 4. OpenStreetMap via Overpass API
- URL: https://overpass-turbo.eu (visual testing interface)
- API endpoint: https://overpass-api.de/api/interpreter

### Dataset: Dublin Road Network and Land-use Data
- Format: JSON (via API query), exportable to GeoJSON
- Accessible: Y (no registration, no API key required)
- Coverage: Dublin City Council administrative area
  (admin_level = 7)
- Licence: Open Database Licence (ODbL) — free to use
  with attribution
- Query tested:
  [out:json][timeout:60];
  area["name"="Dublin"]["admin_level"="7"]->.searchArea;
  way["highway"](area.searchArea);
  out body; >; out skel qt;
- Query result: 184,294 nodes, 46,260 ways — confirmed
  full road network coverage of Dublin city centre
- Key data available:
  - Road network (all highway types)
  - Land-use zoning (amenity, landuse tags)
  - Points of interest
- Note: Data volume is approximately 30MB for full road
  network query; in Phase 2, query should be scoped to
  specific highway types (e.g. primary, secondary, tertiary)
  to reduce payload size for the pipeline
- Status: ✅ Confirmed usable — API responsive, Dublin
  coverage verified, GeoJSON export available

### Known Limitations
- OSM data is community-maintained; completeness and
  accuracy may vary by area
- Large queries (full road network) return ~30MB;
  pipeline implementation should filter by road type
  to manage data volume

## 5. Spatial Renewable Energy Data

### Dataset 1: ESB Networks Network Capacity Heatmap
- Landing page: https://www.esbnetworks.ie/services/get-connected/renewable-connection/network-capacity-heatmap
- Direct download: https://media.esbnetworks.ie/media/docs/default-source/publications/customer-heatmap-download-december-2025.xlsx
- Source organisation: ESB Networks (Ireland's licensed electricity distribution operator)
- Format: Excel (.xlsx), sheet "Heatmap data"
- Accessible: Y (free, no registration required)
- Update frequency: Quarterly
- Current version: December 2025
- Coverage: All of Ireland, LV/MV/HV substations with coordinates
- Dublin records: 7,780 substations (LV: 7,664 / MV: 96 / HV: 20)
- Key fields: Station Name, Voltage Class, Latitude, Longitude
- Note: MV/LV coordinates are exact; HV coordinates are approximate
  per ESB Networks' own documentation. Coordinates are WGS84.
- Status: ✅ Downloaded and used in 08_clean_esb_substations.py to
  produce output/dublin_substations.csv. Feature
  distance_to_nearest_substation_m computed in
  05_build_feature_dataset.py but retained as reference field only —
  Dublin's grid density (almost all sites within 100m of a substation)
  makes this feature unsuitable for K-Means clustering. See
  docs/spatial_renewable_investigation.md for full evaluation.

### Dataset 2: SEAI Wind Farms Connected
- Landing page: https://data.gov.ie/dataset/wind-farms-in-ireland
- Direct download: https://seaiopendata.blob.core.windows.net/wind/WindFarmsConnectedJune2022.csv
- Source organisation: Sustainable Energy Authority of Ireland (SEAI)
- Format: CSV
- Accessible: Y (CC BY 4.0, free)
- Last updated: July 2022 (annual updates per SEAI)
- Coverage: All connected wind farms in Ireland (ex Northern Ireland)
- Record count: 313 wind farms, no missing coordinates
- Key fields: Windfarm_Name, County, Installed_Capacity__MW_,
  Nat_Grid_E__substation_, Nat_Grid_N__substation_
- Note: Coordinates are in Irish Grid (EPSG:29902), not WGS84 —
  converted using pyproj in 09_clean_wind_farms.py
- Status: ✅ Downloaded and used in 09_clean_wind_farms.py to produce
  output/ireland_wind_farms.csv. Feature distance_to_nearest_windfarm_km
  computed in 05_build_feature_dataset.py as the primary spatial
  renewable proxy for K-Means clustering (range 0.07–22.3km across
  Dublin sites). See docs/spatial_renewable_investigation.md for
  full evaluation.

### Known Limitations
- ESB substation data provides grid infrastructure proximity but not
  renewable generation share specifically — interpretation as a
  renewable proxy is indirect
- SEAI wind farm dataset was last updated July 2022; new wind farms
  connected since then are not included
- Wind farm coordinates use substation grid references where direct
  wind farm coordinates were unavailable (per SEAI's own notes)
