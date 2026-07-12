# ML Pipeline — EcoCharge Dublin

## Notebook Version History

| File | Description | Silhouette Score | Key Changes |
|---|---|---|---|
| `03_kmeans_clustering_interim.ipynb` | Interim version | 0.4235 | DLR only (223 sites), K=10, includes renewable_score as constant |
| `04_kmeans_clustering_v2.ipynb` | Expanded dataset | 0.3287 | DCC+DLR (974 sites), K=10, renewable_score removed, SDCC excluded |
| `05_kmeans_clustering_v3.ipynb` | Substation feature (full weight) | 0.2553 | Added distance_to_nearest_substation_m at weight=1.0 — degraded score due to high Dublin substation density, not adopted |
| `05_kmeans_clustering_v3_final_2.ipynb` | **Final version (current)** | **0.4356** | K=6 (Elbow+Silhouette supported), substation distance downweighted to 0.1, weighted gap_score (traffic×0.7 + road×0.3), 500m minimum spacing between recommendations, sensitivity analysis, scenario analysis |

---

## Final Model (05_kmeans_clustering_v3_final_2.ipynb)

### Features

| Feature | Role | Weight |
|---|---|---|
| `traffic_volume` | Primary demand proxy | Standard |
| `charger_count_nearby` | Existing supply | Standard |
| `road_density` | Infrastructure suitability | Standard |
| `distance_to_nearest_substation_m` | Grid accessibility proxy (ESB Networks) | 0.1× |
| `lat`, `lon` | Spatial position (WGS84) | Standard |

Excluded: `ev_penetration_proxy` (constant 0.049, zero spatial variance)

### Pipeline

```
unified_features_v3.csv (1,039 rows)
↓
Separate SDCC (65 sites, SCOOT system) → display only
↓
Weighted gap_score = (0.7 × norm_traffic + 0.3 × norm_road) / (charger_count + 1)
↓
Select Top 20% by gap_score (195 candidate sites)
↓
StandardScaler + downweight substation distance to 0.1
↓
K-Means (K=6, selected by Elbow + Silhouette)
↓
Per cluster: Top 1 + Top 2 (≥500m apart)
↓
Supplement to ≥10 if needed
↓
recommendations.csv (11 ranked sites)
```

### Key Decisions

- **K=6**: Both Elbow Method and Silhouette Score (0.4356) support this choice
- **Substation weight=0.1**: Full weight degraded Silhouette from 0.3287 to 0.2553 due to high substation density in Dublin; downweighted to retain signal without dominating clusters
- **SDCC excluded**: SCOOT vs SCATS incompatibility; mean traffic volume ~5× lower than DCC, making direct comparison unreliable
- **500m minimum spacing**: Prevents geographically duplicated recommendations within the same cluster

### Outputs

| File | Description |
|---|---|
| `recommendations.csv` | 11 ranked recommendations with reason, metadata |
| `recommendations_ev05.csv` | Scenario: EV penetration 5% (current) |
| `recommendations_ev08.csv` | Scenario: EV penetration 8% |
| `recommendations_ev12.csv` | Scenario: EV penetration 12% |
| `elbow_silhouette_v3.png` | K selection plot |
| `sensitivity_analysis.png` | K and threshold sensitivity |
| `kmeans_recommendations_v3.html` | Interactive Folium map |

### Data Sources

| Dataset | Source | Coverage |
|---|---|---|
| Traffic (DCC) | Smart Dublin SCATS | 973 sites, 2024–2025 |
| Traffic (DLR) | Smart Dublin SCATS | 1 site, 2023 |
| Traffic (SDCC) | SCOOT (display only) | 65 sites, 2024 |
| EV Chargers | ESB Networks / DLR (deduplicated) | 115 sites |
| Substations | ESB Networks Network Capacity Heatmap | 7,780 Dublin sites |
| Renewable | EirGrid (national time-series) | Dashboard visualisation only |

---

## Decision Log — Version Evolution

### v1 → Interim (03_kmeans_clustering_interim.ipynb)

**Dataset:** DLR only, 223 SCATS sites (2023)
**Features:** traffic_volume, charger_count_nearby, road_density, renewable_score (constant 0.4102), ev_penetration_proxy (constant 0.049), lat, lon
**K:** 10
**Silhouette Score:** 0.4235

**Decisions made:**
- K=10 selected via Elbow Method
- renewable_score included despite being a national constant — no spatially granular data available from EirGrid
- ev_penetration_proxy included as documented assumption (CSO 2021 national figure)

**Outputs:**
- `recommendations.csv` (10 rows)
- `kmeans_recommendations_interim.html`

**Known limitations identified:**
- DLR covers south Dublin only, not representative of full city
- renewable_score is identical for all sites — contributes no spatial information to clustering
- ev_penetration_proxy also constant — same issue

---

### Interim → v2 (04_kmeans_clustering_v2.ipynb)

**Dataset:** DCC + DLR, 974 sites
**Why expanded:** During data engineering, discovered 222 of 223 DLR sites are physically identical to DCC SCATS sensors. DCC data (2024–2025) is more recent than DLR (2023), so DCC-priority deduplication applied. Net result: 973 DCC sites + 1 DLR-only site.
**Features:** traffic_volume, charger_count_nearby, road_density, lat, lon (renewable_score removed, ev_penetration_proxy excluded)
**K:** 10
**Silhouette Score:** 0.3287

**Decisions made:**
- renewable_score removed — constant value provides zero spatial variance, confirmed no contribution to clustering
- SDCC (65 sites, SCOOT system) investigated but excluded from clustering — mean traffic volume ~5× lower than DCC (142 vs 701), root cause unclear (genuine low traffic vs system incompatibility), retained as display-only map layer
- Score decrease from 0.4235 to 0.3287 expected — 4× more sites over larger geographic area naturally reduces cluster cohesion

**Outputs:**
- `recommendations.csv` (10 rows)
- `kmeans_recommendations_v2.html`
- `elbow_silhouette_v2.png`

---

### v2 → v3 (05_kmeans_clustering_v3.ipynb)

**Dataset:** Same 974 sites, now with distance_to_nearest_substation_m added
**Why added:** Project name includes "Renewable Energy" — needed a spatially differentiated renewable-related feature. Investigated 4 alternatives:
- Met Éireann weather stations: only 2 in Dublin, insufficient spatial variance
- OSM land use: demand-side feature, not supply-side renewable proxy
- CSO population density: no logical connection to renewable supply
- ESB Networks substations: 7,780 Dublin locations, genuine spatial variance — selected

**Features:** traffic_volume, charger_count_nearby, road_density, distance_to_nearest_substation_m (weight=1.0), lat, lon
**K:** 10
**Silhouette Score:** 0.2553

**Problem identified:**
Dublin substation density is extremely high — 75th percentile distance is only 109m, meaning nearly all sites are very close to a substation. At full weight, the feature splits data into two groups ("very close" vs "slightly further"), causing K=2 to dominate with Silhouette=0.4604 while K=10 drops to 0.2553. Feature degrades clustering rather than improving it.

**Decision:** Do not adopt this version. Investigate downweighting instead.

**Outputs:**
- `elbow_silhouette_v3.png` (shows problematic K=2 spike)

---

### v3 → v3 Final (05_kmeans_clustering_v3_final_2.ipynb)

**Dataset:** Same 974 sites
**Features:** traffic_volume, charger_count_nearby, road_density, distance_to_nearest_substation_m (weight=0.1), lat, lon
**K:** 6
**Silhouette Score:** 0.4356

**Decisions made:**

**1. Substation distance downweighted to 0.1**
Tested weights 1.0, 0.5, 0.3, 0.1 at K=10:

| Weight | Silhouette |
|---|---|
| 1.0 | 0.2553 |
| 0.5 | 0.2828 |
| 0.3 | 0.3208 |
| **0.1** | **0.3254** |

Weight=0.1 recovers clustering quality to near-v2 baseline while retaining the feature as a grid accessibility signal.

**2. K changed from 10 to 6**
Re-ran elbow and silhouette with updated weighted features:
- Elbow Method: inflection point at K=5–6
- Silhouette Score: peaks at K=6 (0.4356), highest across all K=2–15

K=6 is mathematically optimal. To still meet the ≥10 recommendation requirement, each cluster selects up to 2 candidate sites.

**3. Weighted gap_score**
Upgraded from `traffic / (charger + 1)` to:

```
gap_score = (0.7 × norm_traffic + 0.3 × norm_road) / (charger_count + 1)
```

road_density added as secondary demand signal. Weights chosen to keep traffic as primary driver while incorporating infrastructure suitability.

**4. 500m minimum spacing constraint**
Per cluster: select highest gap_score site, then select second site only if ≥500m away. Prevents geographically duplicated recommendations within the same cluster. If total < 10, supplement from remaining candidates subject to same distance constraint.

**5. Explainability added**
Each recommendation auto-annotated with human-readable reason based on feature values relative to dataset distribution (e.g. "Recommended due to: high traffic volume, no existing chargers nearby").

**6. Sensitivity analysis added**
- Group A: K=5/6/7 — confirms K=6 is optimal
- Group B: Top 10%/20%/30% candidate pool — recommendations fully stable across all thresholds (overlap=11/11)

**7. Scenario analysis added**
Pre-computed recommendations for EV penetration 5%/8%/12%, aligned with Ireland's Draft National EV Charging Infrastructure Strategy 2026–2028 (Climate Action Plan target: 30% EV by 2030).

**Outputs:**
- `recommendations.csv` (11 rows, includes reason, k_value, candidate_percentile, minimum_spacing_m)
- `recommendations_ev05.csv` — EV penetration 5%
- `recommendations_ev08.csv` — EV penetration 8%
- `recommendations_ev12.csv` — EV penetration 12%
- `elbow_silhouette_v3.png`
- `sensitivity_analysis.png`
- `kmeans_recommendations_v3.html`

---

## Limitations and Assumptions

| Item | Limitation |
|---|---|
| Traffic data | SCATS proxy for EV demand; no direct charging demand data available |
| Renewable score | EirGrid publishes national-level data only; no spatial differentiation possible |
| Substation distance | Grid accessibility proxy only; does not imply renewable capacity or green energy supply |
| EV penetration | CSO national figure (4.9%) applied uniformly; no county-level breakdown available |
| SDCC data | SCOOT vs SCATS incompatibility; excluded from clustering, display only |
| Coordinates | WGS84 decimal degrees; not projected to metric CRS (EPSG:2157) |
| Scenario analysis | Proportional traffic scaling may not change site ranking; shows demand magnitude shift under different adoption assumptions |
 
