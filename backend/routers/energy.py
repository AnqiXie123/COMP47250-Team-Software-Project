from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from backend.database import get_db

router = APIRouter()


@router.get("/api/energy/latest")
async def get_latest_energy(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text(
        "SELECT datetime, wind_mw, solar_mw, total_demand_mw, renewable_score "
        "FROM renewable_energy "
        "ORDER BY datetime DESC "
        "LIMIT 1"
    ))
    row = result.mappings().first()
    return dict(row)
