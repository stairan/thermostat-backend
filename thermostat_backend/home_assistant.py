import httpx
import asyncio
import logging
import json
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from .models import SensorReading, WeatherForecast, DailyPowerUsage, Status
from .database import SessionLocal

logger = logging.getLogger(__name__)

class HomeAssistantService:
    def __init__(self, base_url: str, access_token: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.access_token = access_token
        self.target_entities = [
            "sensor.balcony_humidity",
            "sensor.balcony_pressure",
            "sensor.balcony_temperature",
            "sensor.bathroom_big_humidity",
            "sensor.bathroom_big_temperature",
            "sensor.bathroom_small_humidity",
            "sensor.bathroom_small_temperature",
            "sensor.bedroom_humidity",
            "sensor.bedroom_temperature",
            "sensor.entrance_humidity",
            "sensor.entrance_temperature",
            "sensor.living_room_humidity",
            "sensor.living_room_temperature",
            "sensor.second_floor_humidity",
            "sensor.second_floor_temperature",
            "sensor.working_room_humidity",
            "sensor.working_room_temperature",
            "sensor.pantry_temperature",
            "sensor.pantry_humidity",
            "sensor.sun_next_setting",
            "sensor.sun_next_rising",
            "sensor.pilisszentivan_condition",
            "sensor.pilisszentivan_temperature",
            "sensor.inverter_daily_yield"
        ]

    async def fetch_states(self) -> List[Dict[str, Any]]:
        """Fetch all states from Home Assistant API"""
        headers = {}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/states",
                    headers=headers,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"HTTP error fetching states: {e}")
                return []
            except Exception as e:
                logger.error(f"Unexpected error fetching states: {e}")
                return []

    async def filter_target_entities(self, states: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter states to only include target entities"""
        filtered_states = []
        for state in states:
            if state.get("entity_id") in self.target_entities:
                filtered_states.append({
                    "entity_id": state["entity_id"],
                    "state": state["state"]
                })
        return filtered_states

    def save_sensor_readings(self, readings: List[Dict[str, Any]]) -> None:
        """Save or update sensor readings to database (only latest values)"""
        db = SessionLocal()
        try:
            timestamp = datetime.utcnow()
            for reading in readings:
                # Check if reading already exists for this entity
                existing = db.query(SensorReading).filter(
                    SensorReading.entity_id == reading["entity_id"]
                ).first()

                if existing:
                    # Update existing record
                    existing.state = reading["state"]
                    existing.timestamp = timestamp
                else:
                    # Create new record
                    sensor_reading = SensorReading(
                        entity_id=reading["entity_id"],
                        state=reading["state"],
                        timestamp=timestamp
                    )
                    db.add(sensor_reading)

            db.commit()
            logger.info(f"Updated {len(readings)} sensor readings")
        except Exception as e:
            logger.error(f"Error saving sensor readings: {e}")
            db.rollback()
        finally:
            db.close()

    async def fetch_weather_forecast(self) -> Optional[List[Dict[str, Any]]]:
        """Fetch weather forecast from Home Assistant API"""
        headers = {
            "Content-Type": "application/json"
        }
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"

        body = {
            "entity_id": "weather.pilisszentivan_forecast",
            "type": "hourly"
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/services/weather/get_forecasts?return_response",
                    headers=headers,
                    json=body,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()

                # Navigate through the response structure
                service_response = data.get("service_response", {})
                forecast_entity = service_response.get("weather.pilisszentivan_forecast", {})
                forecast_array = forecast_entity.get("forecast", [])

                logger.info(f"Fetched {len(forecast_array)} weather forecast entries")
                return forecast_array

            except httpx.HTTPError as e:
                logger.error(f"HTTP error fetching weather forecast: {e}")
                return None
            except Exception as e:
                logger.error(f"Unexpected error fetching weather forecast: {e}")
                return None

    def save_weather_forecast(self, forecast_data: List[Dict[str, Any]]) -> None:
        """Save or update weather forecast to database (only current forecast)"""
        if not forecast_data:
            return

        db = SessionLocal()
        try:
            timestamp = datetime.utcnow()
            entity_id = "weather.pilisszentivan_forecast"

            # Check if forecast already exists
            existing = db.query(WeatherForecast).filter(
                WeatherForecast.entity_id == entity_id
            ).first()

            if existing:
                # Update existing forecast
                existing.forecast_data = json.dumps(forecast_data)
                existing.timestamp = timestamp
                logger.info(f"Updated weather forecast with {len(forecast_data)} entries")
            else:
                # Create new forecast
                weather_forecast = WeatherForecast(
                    entity_id=entity_id,
                    forecast_data=json.dumps(forecast_data),
                    timestamp=timestamp
                )
                db.add(weather_forecast)
                logger.info(f"Saved new weather forecast with {len(forecast_data)} entries")

            db.commit()
        except Exception as e:
            logger.error(f"Error saving weather forecast: {e}")
            db.rollback()
        finally:
            db.close()

    async def fetch_daily_power_usage(self) -> Optional[float]:
        """Fetch daily power usage from Home Assistant API"""
        headers = {}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"

        today = date.today().strftime("%Y-%m-%d")
        params = {
            "filter_entity_id": "sensor.p1_meter_total_energy_import",
            "minimal_response": "",
            "significant_changes_only": ""
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/history/period/{today}",
                    headers=headers,
                    params=params,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()

                # Data is an array of arrays, we need the first (and likely only) inner array
                if not data or not isinstance(data, list) or len(data) == 0:
                    logger.warning("No history data received for power usage")
                    return None

                history_entries = data[0]  # Get the first array
                if not history_entries or len(history_entries) < 2:
                    logger.warning("Not enough history entries for power usage calculation")
                    return None

                # Get first and last entries
                first_entry = history_entries[0]
                last_entry = history_entries[-1]

                try:
                    start_value = float(first_entry["state"])
                    end_value = float(last_entry["state"])
                    daily_usage = end_value - start_value

                    logger.info(f"Power usage calculation: {end_value} - {start_value} = {daily_usage}")
                    return start_value, end_value, daily_usage

                except (ValueError, KeyError) as e:
                    logger.error(f"Error parsing power usage values: {e}")
                    return None

            except httpx.HTTPError as e:
                logger.error(f"HTTP error fetching daily power usage: {e}")
                return None
            except Exception as e:
                logger.error(f"Unexpected error fetching daily power usage: {e}")
                return None

    def save_daily_power_usage(self, start_value: float, end_value: float, daily_usage: float) -> None:
        """Save daily power usage to database"""
        db = SessionLocal()
        try:
            today = date.today()
            timestamp = datetime.utcnow()

            # Check if we already have data for today, update if exists
            existing = db.query(DailyPowerUsage).filter(DailyPowerUsage.date == today).first()

            if existing:
                existing.start_value = start_value
                existing.end_value = end_value
                existing.daily_usage = daily_usage
                existing.timestamp = timestamp
                logger.info(f"Updated daily power usage for {today}: {daily_usage} kWh")
            else:
                power_usage = DailyPowerUsage(
                    date=today,
                    entity_id="sensor.p1_meter_total_energy_import",
                    start_value=start_value,
                    end_value=end_value,
                    daily_usage=daily_usage,
                    timestamp=timestamp
                )
                db.add(power_usage)
                logger.info(f"Saved new daily power usage for {today}: {daily_usage} kWh")

            db.commit()
        except Exception as e:
            logger.error(f"Error saving daily power usage: {e}")
            db.rollback()
        finally:
            db.close()

    async def collect_and_save_data(self) -> None:
        """Main method to collect data from Home Assistant and save to database"""
        try:
            logger.info("Fetching states from Home Assistant...")
            states = await self.fetch_states()

            if not states:
                logger.warning("No states received from Home Assistant")
            else:
                filtered_states = await self.filter_target_entities(states)

                if not filtered_states:
                    logger.warning("No target entities found in states")
                else:
                    self.save_sensor_readings(filtered_states)
                    logger.info(f"Successfully collected and saved {len(filtered_states)} sensor readings")

            # Fetch weather forecast
            logger.info("Fetching weather forecast from Home Assistant...")
            forecast_data = await self.fetch_weather_forecast()

            if forecast_data:
                self.save_weather_forecast(forecast_data)
                logger.info("Successfully collected and saved weather forecast")
            else:
                logger.warning("No weather forecast data received")

            # Fetch daily power usage
            logger.info("Fetching daily power usage from Home Assistant...")
            power_usage_data = await self.fetch_daily_power_usage()

            if power_usage_data:
                start_value, end_value, daily_usage = power_usage_data
                self.save_daily_power_usage(start_value, end_value, daily_usage)
                logger.info("Successfully collected and saved daily power usage")
            else:
                logger.warning("No daily power usage data received")

        except Exception as e:
            logger.error(f"Error in collect_and_save_data: {e}")

    async def start_polling(self, interval_seconds: int = 60) -> None:
        """Start polling Home Assistant every interval_seconds"""
        logger.info(f"Starting Home Assistant polling every {interval_seconds} seconds")
        while True:
            await self.collect_and_save_data()
            await asyncio.sleep(interval_seconds)

    def get_latest_readings(self, db: Session) -> List[Dict[str, Any]]:
        """Get the latest reading for each target entity"""
        latest_readings = []
        for entity_id in self.target_entities:
            latest = db.query(SensorReading).filter(
                SensorReading.entity_id == entity_id
            ).order_by(SensorReading.timestamp.desc()).first()

            if latest:
                latest_readings.append(latest.to_dict())

        return latest_readings

    def get_latest_weather_forecast(self, db: Session) -> Optional[Dict[str, Any]]:
        """Get the latest weather forecast"""
        latest_forecast = db.query(WeatherForecast).order_by(
            WeatherForecast.timestamp.desc()
        ).first()

        if latest_forecast:
            return latest_forecast.to_dict()
        return None

    def get_latest_daily_power_usage(self, db: Session) -> Optional[Dict[str, Any]]:
        """Get the latest daily power usage"""
        latest_power_usage = db.query(DailyPowerUsage).order_by(
            DailyPowerUsage.date.desc()
        ).first()

        if latest_power_usage:
            return latest_power_usage.to_dict()
        return None

    def get_daily_thermostat_stats(self, db: Session) -> Optional[Dict[str, Any]]:
        """Get today's thermostat statistics from the statuses table"""
        from sqlalchemy import func
        from dateutil import parser

        today = date.today()
        start_of_day = today.strftime("%Y-%m-%d 00:00:00.000000")
        end_of_day = today.strftime("%Y-%m-%d 23:59:59.999999")

        # Get all status records for today
        today_statuses = db.query(Status).filter(
            Status.start_time >= start_of_day,
            Status.start_time <= end_of_day
        ).all()

        if not today_statuses:
            return None

        # Calculate statistics
        total_heating_minutes = sum(status.minutes_heating for status in today_statuses)
        total_indoor_temp = sum(status.average_indoor_temp for status in today_statuses)
        total_outdoor_temp = sum(status.average_outdoor_temp for status in today_statuses)
        count = len(today_statuses)

        avg_indoor_temp = round(total_indoor_temp / count, 2) if count > 0 else 0.0
        avg_outdoor_temp = round(total_outdoor_temp / count, 2) if count > 0 else 0.0

        return {
            "date": today.isoformat(),
            "total_heating_minutes": total_heating_minutes,
            "avg_indoor_temp": avg_indoor_temp,
            "avg_outdoor_temp": avg_outdoor_temp,
            "records_count": count
        }