from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from backend.database import get_db

router = APIRouter()

VALID_EV_PENETRATIONS = {0.05, 0.08, 0.12}


@router.get("/api/recommendations")
async def get_recommendations(db: AsyncSession = Depends(get_db)):
    """Return all recommended new EV charger locations, ranked by gap score."""
    result = await db.execute(text(
        "SELECT rank, lat, lon, cluster, gap_score, traffic_volume, "
        "charger_count_nearby, road_density, distance_to_nearest_substation_m, "
        "traffic_source, reason, k_value, candidate_percentile, minimum_spacing_m "
        "FROM recommendations "
        "ORDER BY rank ASC"
    ))
    rows = result.mappings().all()
    features = [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [row["lon"], row["lat"]]},
            "properties": {k: v for k, v in row.items() if k not in ("lat", "lon")},
        }
        for row in rows
    ]
    return {"type": "FeatureCollection", "count": len(features), "features": features}


@router.get("/api/scenario")
async def get_scenario(
    ev_penetration: float = Query(..., description="EV penetration rate: 0.05, 0.08, or 0.12"),
    db: AsyncSession = Depends(get_db),
):
    """Return scenario recommendations for a given EV penetration rate."""
    if ev_penetration not in VALID_EV_PENETRATIONS:
        raise HTTPException(status_code=400, detail="ev_penetration must be one of: 0.05, 0.08, 0.12")

    result = await db.execute(
        text("SELECT rank, lat, lon, cluster, gap_score, ev_penetration, k_value, candidate_percentile "
             "FROM scenario_recommendations WHERE ev_penetration = :ev "
             "ORDER BY rank ASC"),
        {"ev": ev_penetration}
    )
    rows = result.mappings().all()
    features = [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [row["lon"], row["lat"]]},
            "properties": {k: v for k, v in row.items() if k not in ("lat", "lon")},
        }
        for row in rows
    ]
    return {"type": "FeatureCollection", "count": len(features), "features": features}
