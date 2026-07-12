from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from backend.database import get_db

router = APIRouter()


@router.get("/api/windfarms")
async def get_windfarms(db: AsyncSession = Depends(get_db)):
    """Return all wind farms with name, county, capacity and coordinates."""
    result = await db.execute(text(
        "SELECT name, county, capacity_mw, lat, lon FROM wind_farms ORDER BY capacity_mw DESC"
    ))
    rows = result.mappings().all()
    return [dict(row) for row in rows]


@router.get("/api/substations")
async def get_substations(
    lat: Optional[float] = Query(default=None),
    lon: Optional[float] = Query(default=None),
    radius: float = Query(default=500),
    db: AsyncSession = Depends(get_db),
):
    """Return substations. With lat/lon, filters to those within radius metres.
    Without lat/lon, returns all 7780 substations (use sparingly)."""
    if (lat is None) != (lon is None):
        raise HTTPException(status_code=400, detail="Provide both lat and lon, or neither.")
    if radius <= 0 or radius > 10000:
        raise HTTPException(status_code=400, detail="radius must be between 1 and 10000 metres.")

    if lat is not None:
        result = await db.execute(
            text(
                "SELECT name, voltage_class, lat, lon "
                "FROM substations "
                "WHERE ST_DWithin("
                "  ST_MakePoint(lon, lat)::geography,"
                "  ST_MakePoint(:lon, :lat)::geography,"
                "  :radius"
                ") "
                "ORDER BY ST_Distance("
                "  ST_MakePoint(lon, lat)::geography,"
                "  ST_MakePoint(:lon, :lat)::geography"
                ") ASC"
            ),
            {"lat": lat, "lon": lon, "radius": radius},
        )
    else:
        result = await db.execute(text(
            "SELECT name, voltage_class, lat, lon FROM substations"
        ))

    rows = result.mappings().all()
    return [dict(row) for row in rows]
