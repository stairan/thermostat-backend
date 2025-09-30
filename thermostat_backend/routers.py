from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from .database import get_db
from .schemas import StatusResponse, StatusCreate, StatsSummary, HourlyData, DailyData, MonthlyData
from .services import StatusService
from .models import Status
from .home_assistant import HomeAssistantService

router = APIRouter()

@router.get("/statuses/day/{date}", response_model=List[StatusResponse])
async def get_statuses_by_day(
    date: str,
    db: Session = Depends(get_db)
):
    statuses = StatusService.get_statuses_by_date(db, date)
    if not statuses:
        raise HTTPException(status_code=404, detail="No data found for the specified date")
    return [StatusResponse.model_validate(status.to_dict()) for status in statuses]

@router.get("/statuses/period", response_model=List[StatusResponse])
async def get_statuses_by_period(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD HH:MM:SS.ffffff or YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD HH:MM:SS.ffffff or YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    statuses = StatusService.get_statuses_by_period(db, start_date, end_date)
    if not statuses:
        raise HTTPException(status_code=404, detail="No data found for the specified period")
    return [StatusResponse.model_validate(status.to_dict()) for status in statuses]

@router.get("/statuses/all", response_model=List[StatusResponse])
async def get_all_statuses(
    limit: Optional[int] = Query(100, description="Maximum number of records to return"),
    offset: Optional[int] = Query(0, description="Number of records to skip"),
    db: Session = Depends(get_db)
):
    statuses = db.query(Status).offset(offset).limit(limit).all()
    return [StatusResponse.model_validate(status.to_dict()) for status in statuses]

@router.get("/statuses/stats", response_model=StatsSummary)
async def get_statistics(
    start_date: Optional[str] = Query(None, description="Start date for statistics"),
    end_date: Optional[str] = Query(None, description="End date for statistics"),
    db: Session = Depends(get_db)
):
    return StatusService.get_statistics(db, start_date, end_date)

@router.post("/statuses", response_model=StatusResponse)
async def create_status(
    status: StatusCreate,
    db: Session = Depends(get_db)
):
    try:
        created_status = StatusService.create_status(db, status.model_dump())
        return StatusResponse.model_validate(created_status.to_dict())
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating status: {str(e)}")

@router.get("/statuses/heating-efficiency", response_model=List[dict])
async def get_heating_efficiency(
    start_date: Optional[str] = Query(None, description="Start date"),
    end_date: Optional[str] = Query(None, description="End date"),
    db: Session = Depends(get_db)
):
    if start_date and end_date:
        statuses = StatusService.get_statuses_by_period(db, start_date, end_date)
    else:
        statuses = db.query(Status).all()

    efficiency_data = []
    for status in statuses:
        temp_diff = status.average_indoor_temp - status.average_outdoor_temp
        efficiency = status.minutes_heating / temp_diff if temp_diff > 0 else 0

        efficiency_data.append({
            "id": status.id,
            "start_time": status.start_time,
            "temperature_difference": round(temp_diff, 2),
            "heating_minutes": status.minutes_heating,
            "heating_efficiency": round(efficiency, 2)
        })

    return efficiency_data

@router.get("/statuses/hourly/{date}", response_model=List[HourlyData])
async def get_hourly_data_by_date(
    date: str,
    db: Session = Depends(get_db)
):
    hourly_data = StatusService.get_hourly_data_by_date(db, date)
    if not hourly_data:
        raise HTTPException(status_code=404, detail="No data found for the specified date")
    return hourly_data

@router.get("/statuses/daily/{year}/{month}", response_model=List[DailyData])
async def get_daily_data_by_month(
    year: int,
    month: int,
    db: Session = Depends(get_db)
):
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="Month must be between 1 and 12")

    daily_data = StatusService.get_daily_data_by_month(db, year, month)
    if not daily_data:
        raise HTTPException(status_code=404, detail="No data found for the specified month")
    return daily_data

@router.get("/statuses/monthly/{year}", response_model=List[MonthlyData])
async def get_monthly_data_by_year(
    year: int,
    db: Session = Depends(get_db)
):
    monthly_data = StatusService.get_monthly_data_by_year(db, year)
    if not monthly_data:
        raise HTTPException(status_code=404, detail="No data found for the specified year")
    return monthly_data

@router.get("/dashboard")
async def get_dashboard_data(db: Session = Depends(get_db)):
    """Get the latest sensor readings and weather forecast for the dashboard"""
    try:
        # We need to get Home Assistant service instance
        # For now, let's create a temporary instance to get latest readings
        import os
        ha_url = os.getenv("HOME_ASSISTANT_URL", "")
        ha_token = os.getenv("HOME_ASSISTANT_TOKEN")

        if not ha_url:
            raise HTTPException(status_code=503, detail="Home Assistant integration not configured")

        ha_service = HomeAssistantService(ha_url, ha_token)
        latest_readings = ha_service.get_latest_readings(db)
        latest_forecast = ha_service.get_latest_weather_forecast(db)
        latest_power_usage = ha_service.get_latest_daily_power_usage(db)
        daily_thermostat_stats = ha_service.get_daily_thermostat_stats(db)

        dashboard_data = {
            "sensor_readings": latest_readings,
            "weather_forecast": latest_forecast,
            "daily_power_usage": latest_power_usage,
            "daily_thermostat_stats": daily_thermostat_stats
        }

        return dashboard_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving dashboard data: {str(e)}")