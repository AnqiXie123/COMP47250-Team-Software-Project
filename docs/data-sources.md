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

#### Dataset 2: Traffic Volumes from SCATS — DCC 2025
- Dataset URL (Jan–Jun): https://data.smartdublin.ie/dataset/dcc-scats-detector-volume-jan-jun-2025
- Dataset URL (Jul–Dec): https://data.smartdublin.ie/dataset/dcc-scats-detector-volume-jul-dec-2025
- Source organisation: Dublin City Council
- Format: CSV (monthly) + SCATS Site Location file (with LAT/LONG)
- Accessible: Y (ZIP download per month)
- Last updated: 2026-02-12
- Coverage: Dublin City area, available months: Jan, Mar, Apr, May,
  Jul, Aug 2025 (some months missing)
- Temporal resolution: Hourly
- Record count: ~5.4 million rows per month
- Key fields: End_Time, Region, Site, Detector, Sum_Volume,
  Avg_Volume, Weighted_Avg, Weighted_Var, Weighted_Std_Dev
- Note: Site Location file included in ZIP provides LAT/LONG
  coordinates; this must be joined with volume data for
  spatial analysis
- Status: ✅ Primary traffic data source for DCC city centre area

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
  north Dublin) area
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
