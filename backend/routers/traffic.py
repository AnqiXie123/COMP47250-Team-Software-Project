from fastapi import APIRouter, Depends, Query
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from backend.database import get_db

router = APIRouter()

VALID_SOURCES = {"DCC", "DLR", "SDCC"}


@router.get("/api/traffic")
async def get_traffic(
    source: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Return traffic sites. Optionally filter by ?source=DCC|DLR|SDCC."""
    if source is not None:
        result = await db.execute(
            text("SELECT lat, lon, traffic_volume, traffic_source "
                 "FROM traffic_sites WHERE traffic_source = :source "
                 "ORDER BY traffic_volume DESC"),
            {"source": source.upper()}
        )
    else:
        result = await db.execute(text(
            "SELECT lat, lon, traffic_volume, traffic_source "
            "FROM traffic_sites ORDER BY traffic_volume DESC"
        ))
    rows = result.mappings().all()
    return [
        {"lat": row["lat"], "lon": row["lon"], "volume": row["traffic_volume"], "source": row["traffic_source"]}
        for row in rows
    ]
