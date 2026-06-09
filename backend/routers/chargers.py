from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from backend.database import get_db

router = APIRouter()


@router.get("/api/chargers")
async def get_chargers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text(
        "SELECT id, lat, lon, address, operator, num_chargers, source_area, open_hours "
        "FROM ev_chargers"
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
