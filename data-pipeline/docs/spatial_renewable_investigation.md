# Spatial Renewable Energy Data Sources — Investigation Report
**Date:** 2026-07-06
**Author:** Yifei Wang
**Purpose:** Investigate candidate data sources to replace the current
`renewable_score` constant (national EirGrid average, 0.41 for all sites)
with a spatially differentiated feature for K-Means clustering.

---

## Background

The `unified_features_v2.csv` feature dataset currently has no spatially
variable renewable energy feature. The `renewable_score` column was removed
in June 2026 because EirGrid only publishes national-level generation data —
the same value appeared in every row, contributing zero spatial signal to
K-Means clustering (see `data-pipeline/docs/data-sources.md`, EirGrid
section).

The goal of this investigation is to find a publicly available, spatially
differentiated dataset that can approximate "renewable energy potential or
grid greenness" at the level of individual Dublin traffic monitoring sites
(~1 km² resolution or finer). Four candidate directions were evaluated.

---

## Candidate 1 — ESB Networks Substation Locations ✅ RECOMMENDED

### Rationale
ESB Networks is Ireland's licensed distribution system operator and the
primary provider of renewable energy grid infrastructure. The distance from
a traffic site to the nearest grid substation is a meaningful proxy for:
- Cost of connecting new EV charging infrastructure to the grid
- Proximity to renewable energy injection points (ESB substations are
  the nodes through which wind/solar generation enters the distribution
  network)

This produces a feature `distance_to_nearest_substation_m` with genuine
spatial variation across Dublin — unlike a national average, each of the
1039 traffic sites would get a different value based on its actual geography.

### Data Source
- **Landing page:** https://www.esbnetworks.ie/services/get-connected/renewable-connection/network-capacity-heatmap
- **Direct download (Excel, ~6.6 MB):**
  https://media.esbnetworks.ie/media/docs/default-source/publications/customer-heatmap-download-december-2025.xlsx
- **Format:** Excel (.xlsx), single sheet "Heatmap data"
- **Licence:** Published by ESB Networks (public utility), freely
  downloadable without registration
- **Update frequency:** Quarterly (filename contains version date)
- **Current version:** December 2025

### Confirmed File Structure
Columns include: `Station Name`, `Voltage Class` (LV/MV/HV),
`Installed Capacity MVA`, `Demand Available MVA`,
`Generation Available Firm MW`, `Latitude`, `Longitude`

- `Latitude` and `Longitude` columns confirmed present with WGS84
  decimal degree values
- MV/LV substation locations are exact; HV locations are approximate
  (per ESB Networks official notes on the heatmap page)

### Dublin Coverage (verified by loading the file)
| Voltage Class | Count in Dublin bounding box (lat 53.2–53.45, lon -6.5 to -6.0) |
|---|---|
| LV (Low Voltage) | 7,664 |
| MV (Medium Voltage) | 96 |
| HV 38 kV | 14 |
| HV 110 kV | 6 |
| **Total** | **7,780** |

7,780 substations across Dublin provides far more spatial resolution than
the 1,039 traffic sites — every traffic site will have a meaningfully
different nearest-substation distance.

### Proposed Feature
```
distance_to_nearest_substation_m:
  For each traffic site, compute Haversine distance to every substation
  in the Dublin bounding box, take the minimum.
  Units: metres (float).
  Lower = closer to grid infrastructure = lower connection cost.
```

Implementation: reuse the existing `haversine()` function already present
in `05_build_feature_dataset.py` and `01_clean_ev_chargers.py`.

### Limitations
- HV substation coordinates are approximate, not exact
- The dataset covers transformer capacity status, not renewable generation
  share specifically — the renewable energy interpretation is indirect
  (ESB Networks is the conduit for renewable generation, but a substation's
  proximity does not directly indicate what % of its supply is renewable)
- File must be re-downloaded quarterly if up-to-date capacity data is needed
  (for the distance feature only, a one-time snapshot is sufficient)

### Feasibility Assessment
✅ **High** — file is publicly available, already downloaded and inspected,
field names and coordinate format confirmed compatible with existing pipeline.
Estimated implementation time: ~2–3 hours for a new cleaning script
(`08_clean_esb_substations.py`) and update to `05_build_feature_dataset.py`.

---

## Candidate 2 — Met Éireann Weather Station Wind Speed ❌ NOT RECOMMENDED

### Rationale
Wind speed data from weather stations could approximate local wind energy
generation potential — areas with higher average wind speed near wind farms
or coastal zones would have higher renewable generation potential.

### Data Source
- **Landing page:** https://www.met.ie/climate/available-data
- **Open data portal:** https://www.met.ie/about-us/specialised-services/open-data
- **Format:** CSV, CC BY 4.0 licence, free download

### Critical Limitation
Met Éireann operates **25 synoptic weather stations across all of Ireland**.
Within the Dublin area, there are only **two stations**:
- **CASEMENT** (Baldonnel, Dublin, records from 1964)
- **PHOENIX PARK** (Dublin, records from 2003)

With only 2 stations for 1,039 traffic sites, every site's nearest-station
assignment would be either "Phoenix Park" or "Casement" — this produces
essentially a binary feature that splits Dublin roughly north/south at most.
This is the same fundamental problem as the EirGrid national average: it
lacks meaningful spatial granularity within Dublin.

### Feasibility Assessment
❌ **Low** — data is accessible but the station density is far too sparse to
produce a spatially meaningful feature at the scale required. Not recommended
unless a denser network of automatic weather stations (AWS) with public API
access is identified in a future investigation.

---

## Candidate 3 — OSM Land Use Classification ⚠️ LOW PRIORITY

### Rationale
OpenStreetMap `landuse` tags (residential, commercial, industrial, retail,
greenspace, etc.) could indicate where EV demand is highest and indirectly
suggest renewable suitability (e.g. large commercial/industrial zones often
have on-site renewable generation; greenspace areas have low demand).

### Data Source
Already available via the Overpass API used in `04_fetch_osm_roads.py` —
adding `landuse` to the query requires only minor script modification, no
new data source needed.

### Limitation
Land use type is a proxy for *demand* characteristics, not for renewable
energy *supply*. It is less directly connected to the project's renewable
energy theme than the ESB substation distance. Useful as a supplementary
feature but not as a primary replacement for `renewable_score`.

### Feasibility Assessment
⚠️ **Medium** — technically easy (modifies existing script), but conceptual
link to renewable energy is weaker than Candidate 1. Recommended as a
secondary addition after Candidate 1 is implemented, not as the primary
spatial renewable proxy.

---

## Candidate 4 — CSO Census Small Area Population Density ❌ LOW PRIORITY

### Rationale
Population density at fine spatial resolution could weight EV charging
demand. Note: CSO is already used in this project for EV penetration rate
(the national `ev_penetration_proxy = 0.049` constant in
`unified_features_v2.csv`), but that is a county-level aggregate —
not spatially differentiated.

### Data Source
- **CSO Small Area Population Statistics (SAPS):**
  https://www.cso.ie/en/census/census2022/

### Limitation
Population density describes *demand-side* characteristics (where people
live), not *supply-side* renewable energy potential. The conceptual fit
with the project's renewable energy angle is weak. Implementation requires
spatial join with CSO Small Area boundary polygons (more complex than a
simple point-to-point distance calculation).

### Feasibility Assessment
❌ **Low priority** — not recommended for this phase. The project already
uses a CSO-derived EV penetration figure; adding population density would
require significant additional spatial join work for limited thematic gain.

---

## Summary and Recommendation

| Candidate | Spatial Resolution in Dublin | Thematic Fit | Feasibility | Decision |
|---|---|---|---|---|
| ESB Networks substations | 7,780 points | High (grid infra) | High | ✅ Proceed |
| Met Éireann wind stations | 2 points | Medium (wind) | Low | ❌ Skip |
| OSM land use | High (polygon) | Medium (demand proxy) | High | ⚠️ Secondary |
| CSO population density | Medium (small area) | Low (demand proxy) | Medium | ❌ Skip |

**Recommended next step:** Implement `08_clean_esb_substations.py` to extract
Dublin substation coordinates from the ESB Networks heatmap Excel file, then
update `05_build_feature_dataset.py` to compute `distance_to_nearest_substation_m`
for each traffic site and include it in `unified_features_v3.csv`.

The ML teammate should then evaluate whether this new spatial feature improves
the K-Means Silhouette Score and produces more geographically meaningful
cluster boundaries compared to the version without any renewable spatial feature.

---

## Files Referenced
- ESB Networks heatmap Excel: `raw/customer-heatmap-december-2025.xlsx`
  (manual download required — see landing page link above)
- Current feature dataset: `output/unified_features_v2.csv`
- Pipeline script to update: `data-pipeline/05_build_feature_dataset.py`
