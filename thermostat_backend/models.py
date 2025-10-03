from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Date, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, date
from typing import Optional
import json

Base = declarative_base()

class Status(Base):
    __tablename__ = "statuses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    start_time = Column(String, nullable=False)
    end_time = Column(String, nullable=False)
    minutes_heating = Column(Integer, nullable=False)
    average_indoor_temp = Column(Float, nullable=False)
    average_outdoor_temp = Column(Float, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "minutes_heating": self.minutes_heating,
            "average_indoor_temp": self.average_indoor_temp,
            "average_outdoor_temp": self.average_outdoor_temp
        }

class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_id = Column(String, nullable=False, index=True)
    state = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "entity_id": self.entity_id,
            "state": self.state,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }

class WeatherForecast(Base):
    __tablename__ = "weather_forecasts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_id = Column(String, nullable=False, index=True, default="weather.pilisszentivan_forecast")
    forecast_data = Column(Text, nullable=False)  # JSON string of the forecast array
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "entity_id": self.entity_id,
            "forecast_data": json.loads(self.forecast_data) if self.forecast_data else [],
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }

class DailyPowerUsage(Base):
    __tablename__ = "daily_power_usage"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, unique=True, index=True)

    # Import values
    import_start_value = Column(Float, nullable=False)
    import_end_value = Column(Float, nullable=False)
    daily_import = Column(Float, nullable=False)

    # Export values
    export_start_value = Column(Float, nullable=False, default=0.0)
    export_end_value = Column(Float, nullable=False, default=0.0)
    daily_export = Column(Float, nullable=False, default=0.0)

    # Solar yield
    inverter_daily_yield = Column(Float, nullable=False, default=0.0)

    # Total usage: (inverter_daily_yield - daily_export) + daily_import
    daily_usage = Column(Float, nullable=False)

    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date.isoformat() if self.date else None,
            "daily_import": self.daily_import,
            "daily_export": self.daily_export,
            "inverter_daily_yield": self.inverter_daily_yield,
            "daily_usage": self.daily_usage,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }