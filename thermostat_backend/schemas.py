from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

class StatusResponse(BaseModel):
    id: int
    start_time: str
    end_time: str
    minutes_heating: int
    average_indoor_temp: float
    average_outdoor_temp: float

    class Config:
        from_attributes = True

class StatusCreate(BaseModel):
    start_time: str = Field(..., description="Start time in format: 2021-03-04 20:00:00.000000")
    end_time: str = Field(..., description="End time in format: 2021-03-04 21:00:00.000000")
    minutes_heating: int = Field(..., ge=0, description="Minutes heating was on")
    average_indoor_temp: float = Field(..., description="Average indoor temperature")
    average_outdoor_temp: float = Field(..., description="Average outdoor temperature")

class HourlyData(BaseModel):
    hour: int = Field(..., description="Hour of the day (0-23)")
    minutes_heating: int = Field(..., description="Total minutes heating was on during this hour")
    avg_indoor_temp: float = Field(..., description="Average indoor temperature during this hour")
    avg_outdoor_temp: float = Field(..., description="Average outdoor temperature during this hour")

class DailyData(BaseModel):
    day: int = Field(..., description="Day of the month (1-31)")
    minutes_heating: int = Field(..., description="Total minutes heating was on during this day")
    avg_indoor_temp: float = Field(..., description="Average indoor temperature during this day")
    avg_outdoor_temp: float = Field(..., description="Average outdoor temperature during this day")

class MonthlyData(BaseModel):
    month: int = Field(..., description="Month of the year (1-12)")
    minutes_heating: int = Field(..., description="Total minutes heating was on during this month")
    avg_indoor_temp: float = Field(..., description="Average indoor temperature during this month")
    avg_outdoor_temp: float = Field(..., description="Average outdoor temperature during this month")

class StatsSummary(BaseModel):
    total_records: int
    total_heating_minutes: int
    avg_indoor_temp: float
    avg_outdoor_temp: float
    min_indoor_temp: float
    max_indoor_temp: float
    min_outdoor_temp: float
    max_outdoor_temp: float