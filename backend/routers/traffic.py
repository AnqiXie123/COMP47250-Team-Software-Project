from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from backend.database import get_db

router = APIRouter()


@router.get("/api/traffic")
async def get_traffic(db: AsyncSession = Depends(get_db)):
    """Return all SCATS traffic sites with lat, lon, and traffic volume."""
    result = await db.execute(text(
        "SELECT lat, lon, traffic_volume FROM traffic_sites ORDER BY traffic_volume DESC"
    ))
    rows = result.mappings().all()
    return [{"lat": row["lat"], "lon": row["lon"], "volume": row["traffic_volume"]} for row in rows]
