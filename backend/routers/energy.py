from fastapi import APIRouter, Depends, Query, HTTPException
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


def _validate_timeseries_params(days_raw: str, interval: str):
    if interval not in {"15m", "1h", "1d"}:
        raise HTTPException(status_code=400, detail="interval must be one of: 15m, 1h, 1d")

    if days_raw == "all":
        if interval != "1d":
            raise HTTPException(status_code=400, detail="days=all only supports interval=1d")
        return None, interval

    try:
        days = int(days_raw)
        if days <= 0:
            raise ValueError()
    except ValueError:
        raise HTTPException(status_code=400, detail="days must be a positive integer or 'all'")

    if days <= 7:
        pass  # all intervals allowed
    elif days <= 90:
        if interval == "15m":
            raise HTTPException(status_code=400, detail="days > 7 does not support interval=15m, use 1h or 1d")
    else:
        if interval != "1d":
            raise HTTPException(status_code=400, detail="days > 90 only supports interval=1d")

    return days, interval


@router.get("/api/energy/timeseries")
async def get_energy_timeseries(
    days: str = Query(default="7"),
    interval: str = Query(default="15m"),
    db: AsyncSession = Depends(get_db),
):
    days_val, interval = _validate_timeseries_params(days, interval)

    if days_val is None:
        time_filter = ""
        params = {}
    else:
        time_filter = "WHERE datetime >= NOW() - (INTERVAL '1 day' * :days)"
        params = {"days": days_val}

    if interval == "15m":
        sql = text(
            f"SELECT datetime, wind_mw, solar_mw, total_demand_mw, renewable_score "
            f"FROM renewable_energy {time_filter} "
            f"ORDER BY datetime ASC"
        )
    else:
        trunc = "hour" if interval == "1h" else "day"
        sql = text(
            f"SELECT date_trunc('{trunc}', datetime) AS datetime, "
            f"AVG(wind_mw) AS wind_mw, AVG(solar_mw) AS solar_mw, "
            f"AVG(total_demand_mw) AS total_demand_mw, AVG(renewable_score) AS renewable_score "
            f"FROM renewable_energy {time_filter} "
            f"GROUP BY date_trunc('{trunc}', datetime) "
            f"ORDER BY datetime ASC"
        )

    result = await db.execute(sql, params)
    rows = result.mappings().all()
    return [dict(row) for row in rows]
