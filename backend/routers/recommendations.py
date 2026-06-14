from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from backend.database import get_db

router = APIRouter()


@router.get("/api/recommendations")
async def get_recommendations(db: AsyncSession = Depends(get_db)):
    """Return all recommended new EV charger locations, ranked by gap score."""
    result = await db.execute(text(
        "SELECT rank, lat, lon, cluster_id, gap_score, traffic_volume, "
        "charger_count_nearby, renewable_score "
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
