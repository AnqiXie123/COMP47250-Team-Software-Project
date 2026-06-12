# ML Notebooks — EcoCharge Dublin

**Author:** Anqi Xie  
**Branch:** ml  
**Role:** Spatial Analyst & ML Engineer  
**Last Updated:** June 2026  
**Status:** Interim Version — further development planned post-interim

---

## Overview

This folder contains the EDA and machine learning notebooks for the EcoCharge Dublin project (COMP47250 P15). The goal is to recommend optimal new EV charging station locations in Dublin by combining traffic demand data, existing charger supply, road network density, and renewable energy availability.

---

## Folder Structure

```
notebooks/
├── eda/
│   ├── 01_eda_ev_chargers.ipynb        # EV charger distribution analysis
│   └── 02_eda_eirgrid_renewable.ipynb  # Renewable energy time-series analysis
└── modelling/
    └── 03_kmeans_clustering.ipynb      # K-Means clustering and recommendations
```

---

## Notebooks

### EDA

**`01_eda_ev_chargers.ipynb`**
- Dataset: `dublin_ev_chargers.geojson` (133 records)
- Sources: ESB eCars (88), DLR (35), SDCC (10)
- Content: total station count, operator distribution, source area breakdown, duplicate coordinate check, density heatmap, operator comparison charts

**`02_eda_eirgrid_renewable.ipynb`**
- Dataset: EirGrid System Data 2026 (11,516 rows, Jan–Apr 2026)
- Content: wind/solar generation trends, renewable penetration analysis, `renewable_score` field validation, monthly and hourly patterns

### Modelling

**`03_kmeans_clustering.ipynb`**
- Dataset: `unified_features.csv` (223 SCATS traffic sites)
- Content: feature engineering, gap score calculation, Elbow Method, K-Means clustering, Silhouette Score evaluation, Folium map visualisation, top 10 recommended locations

---

## Methodology

### Step 1 — Gap Score Calculation
```python
gap_score = traffic_volume / (charger_count_nearby + 1)
```
Identifies locations with high demand and low supply.

### Step 2 — Priority Site Filtering
```python
# Top 20% highest gap score locations
threshold = df['gap_score'].quantile(0.80)
df_priority = df[df['gap_score'] >= threshold]
```

### Step 3 — Feature Scaling
```python
from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
scaled = scaler.fit_transform(df_priority[feature_cols])
```

### Step 4 — Elbow Method
Sweeps K from 2 to 14 to identify optimal number of clusters.

### Step 5 — K-Means Clustering
```python
kmeans = KMeans(n_clusters=10, random_state=42)
```
K=10 selected based on Elbow Method and project minimum requirement (≥10 recommended locations).

### Step 6 — Ranking
Cluster centers ranked by average gap score (descending).

---

## Current Results (Interim)

| Metric | Value |
|---|---|
| Total SCATS sites analysed | 223 |
| Priority sites (top 20% gap) | 45 |
| Number of clusters (K) | 10 |
| Silhouette Score | 0.4235 |
| Recommended new locations | 10 |

**Top 3 Priority Locations:**
| Rank | Latitude | Longitude | Avg Gap Score |
|---|---|---|---|
| 1 | 53.2766 | -6.1501 | 2120.1 |
| 2 | 53.2847 | -6.2254 | 1871.5 |
| 3 | 53.2710 | -6.1661 | 1637.8 |

---

## Planned Improvements (Post-Interim)

### 1. Weighted Priority Score
Replace simple gap score ranking with a composite score:
```python
priority_score = (
    0.6 * gap_score_normalised +
    0.3 * renewable_score +
    0.1 * road_density
)
```
This better reflects the project's renewable energy integration objective.

### 2. Refactor into Separate Notebooks
Split current notebook into:
- `01_feature_engineering.ipynb` — feature construction and scaling
- `02_gap_analysis.ipynb` — supply-demand gap analysis and visualisation
- `03_kmeans_clustering.ipynb` — clustering and recommendations

### 3. OSM Constraint Layer
Exclude geographically invalid recommendations (water bodies, parks, protected zones) using OpenStreetMap land-use tags.

### 4. Sensitivity Analysis
Adjust EV penetration rate and observe how recommendations change — linked to the dashboard scenario slider feature.

### 5. User Evaluation
Conduct structured evaluation with 3–5 urban planning stakeholders to assess recommendation quality and dashboard usability.

---

## Dependencies

```
pandas
geopandas
numpy
matplotlib
contextily
folium
scikit-learn
scipy
```

Install with:
```bash
pip install pandas geopandas numpy matplotlib contextily folium scikit-learn scipy
```

---

## Data Sources

| Dataset | Source | Records |
|---|---|---|
| EV Charger Locations | Smart Dublin + ESB eCars | 133 |
| Renewable Energy | EirGrid Smart Grid Dashboard | 11,516 |
| Unified Feature Dataset | Data pipeline (Yifei Wang) | 223 |

---

## AI Usage

GitHub Copilot and Claude were used for code completion and debugging assistance. All outputs were reviewed and validated by the author. Documented in the project AI Usage Log (Final Report Appendix A).
