#!/usr/bin/env python3

from thermostat_backend.database import SessionLocal, create_tables
from thermostat_backend.models import Status
from datetime import datetime, timedelta
import random

def add_sample_data():
    create_tables()
    db = SessionLocal()

    try:
        start_date = datetime(2024, 1, 1, 8, 0, 0)

        sample_data = []
        for i in range(30):
            current_start = start_date + timedelta(days=i)
            current_end = current_start + timedelta(hours=1)

            outdoor_temp = round(random.uniform(-10, 25), 1)
            indoor_temp = round(random.uniform(18, 24), 1)
            heating_minutes = random.randint(15, 60)

            sample_data.append({
                "start_time": current_start.strftime("%Y-%m-%d %H:%M:%S.%f"),
                "end_time": current_end.strftime("%Y-%m-%d %H:%M:%S.%f"),
                "minutes_heating": heating_minutes,
                "average_indoor_temp": indoor_temp,
                "average_outdoor_temp": outdoor_temp
            })

        for i in range(len(sample_data)):
            for j in range(random.randint(8, 16)):
                data = sample_data[i].copy()
                hour_offset = j
                start_dt = datetime.strptime(data["start_time"], "%Y-%m-%d %H:%M:%S.%f") + timedelta(hours=hour_offset)
                end_dt = start_dt + timedelta(hours=1)

                data["start_time"] = start_dt.strftime("%Y-%m-%d %H:%M:%S.%f")
                data["end_time"] = end_dt.strftime("%Y-%m-%d %H:%M:%S.%f")
                data["minutes_heating"] = random.randint(5, 60)
                data["average_indoor_temp"] = round(random.uniform(18, 24), 1)
                data["average_outdoor_temp"] = round(random.uniform(-10, 25), 1)

                status = Status(**data)
                db.add(status)

        db.commit()
        print(f"Added sample data successfully!")

        count = db.query(Status).count()
        print(f"Total records in database: {count}")

    except Exception as e:
        print(f"Error adding sample data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_sample_data()