from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from .models import Status
from .schemas import StatsSummary, HourlyData, DailyData, MonthlyData
from datetime import datetime, timedelta
from dateutil import parser
from typing import List, Optional

class StatusService:
    @staticmethod
    def get_statuses_by_date(db: Session, date: str) -> List[Status]:
        try:
            target_date = parser.parse(date).date()
            start_of_day = target_date.strftime("%Y-%m-%d 00:00:00.000000")
            end_of_day = target_date.strftime("%Y-%m-%d 23:59:59.999999")

            return db.query(Status).filter(
                and_(
                    Status.start_time >= start_of_day,
                    Status.start_time <= end_of_day
                )
            ).order_by(Status.start_time).all()
        except Exception:
            return []

    @staticmethod
    def get_statuses_by_period(db: Session, start_date: str, end_date: str) -> List[Status]:
        try:
            start_dt = parser.parse(start_date)
            end_dt = parser.parse(end_date)

            start_str = start_dt.strftime("%Y-%m-%d %H:%M:%S.%f")
            end_str = end_dt.strftime("%Y-%m-%d %H:%M:%S.%f")

            return db.query(Status).filter(
                and_(
                    Status.start_time >= start_str,
                    Status.end_time <= end_str
                )
            ).order_by(Status.start_time).all()
        except Exception:
            return []

    @staticmethod
    def get_statistics(db: Session, start_date: Optional[str] = None, end_date: Optional[str] = None) -> StatsSummary:
        query = db.query(Status)

        if start_date and end_date:
            try:
                start_dt = parser.parse(start_date)
                end_dt = parser.parse(end_date)
                start_str = start_dt.strftime("%Y-%m-%d %H:%M:%S.%f")
                end_str = end_dt.strftime("%Y-%m-%d %H:%M:%S.%f")

                query = query.filter(
                    and_(
                        Status.start_time >= start_str,
                        Status.end_time <= end_str
                    )
                )
            except Exception:
                pass

        stats = query.with_entities(
            func.count(Status.id).label('total_records'),
            func.sum(Status.minutes_heating).label('total_heating_minutes'),
            func.avg(Status.average_indoor_temp).label('avg_indoor_temp'),
            func.avg(Status.average_outdoor_temp).label('avg_outdoor_temp'),
            func.min(Status.average_indoor_temp).label('min_indoor_temp'),
            func.max(Status.average_indoor_temp).label('max_indoor_temp'),
            func.min(Status.average_outdoor_temp).label('min_outdoor_temp'),
            func.max(Status.average_outdoor_temp).label('max_outdoor_temp')
        ).first()

        return StatsSummary(
            total_records=stats.total_records or 0,
            total_heating_minutes=stats.total_heating_minutes or 0,
            avg_indoor_temp=round(stats.avg_indoor_temp or 0, 2),
            avg_outdoor_temp=round(stats.avg_outdoor_temp or 0, 2),
            min_indoor_temp=stats.min_indoor_temp or 0,
            max_indoor_temp=stats.max_indoor_temp or 0,
            min_outdoor_temp=stats.min_outdoor_temp or 0,
            max_outdoor_temp=stats.max_outdoor_temp or 0
        )

    @staticmethod
    def get_hourly_data_by_date(db: Session, date: str) -> List[HourlyData]:
        try:
            target_date = parser.parse(date).date()
            start_of_day = target_date.strftime("%Y-%m-%d 00:00:00.000000")
            end_of_day = target_date.strftime("%Y-%m-%d 23:59:59.999999")

            statuses = db.query(Status).filter(
                and_(
                    Status.start_time >= start_of_day,
                    Status.start_time <= end_of_day
                )
            ).order_by(Status.start_time).all()

            hourly_data = {}
            for status in statuses:
                start_time = parser.parse(status.start_time)
                hour = start_time.hour

                if hour not in hourly_data:
                    hourly_data[hour] = {
                        'total_minutes': 0,
                        'indoor_temps': [],
                        'outdoor_temps': [],
                        'heating_minutes': 0
                    }

                hourly_data[hour]['heating_minutes'] += status.minutes_heating
                hourly_data[hour]['indoor_temps'].append(status.average_indoor_temp)
                hourly_data[hour]['outdoor_temps'].append(status.average_outdoor_temp)

            result = []
            for hour in range(24):
                if hour in hourly_data:
                    data = hourly_data[hour]
                    avg_indoor = sum(data['indoor_temps']) / len(data['indoor_temps'])
                    avg_outdoor = sum(data['outdoor_temps']) / len(data['outdoor_temps'])

                    result.append(HourlyData(
                        hour=hour,
                        minutes_heating=data['heating_minutes'],
                        avg_indoor_temp=round(avg_indoor, 2),
                        avg_outdoor_temp=round(avg_outdoor, 2)
                    ))
                else:
                    result.append(HourlyData(
                        hour=hour,
                        minutes_heating=0,
                        avg_indoor_temp=0.0,
                        avg_outdoor_temp=0.0
                    ))

            return result
        except Exception:
            return []

    @staticmethod
    def get_daily_data_by_month(db: Session, year: int, month: int) -> List[DailyData]:
        try:
            from calendar import monthrange

            start_of_month = datetime(year, month, 1).strftime("%Y-%m-%d 00:00:00.000000")
            _, last_day = monthrange(year, month)
            end_of_month = datetime(year, month, last_day, 23, 59, 59, 999999).strftime("%Y-%m-%d %H:%M:%S.%f")

            statuses = db.query(Status).filter(
                and_(
                    Status.start_time >= start_of_month,
                    Status.start_time <= end_of_month
                )
            ).order_by(Status.start_time).all()

            daily_data = {}
            for status in statuses:
                start_time = parser.parse(status.start_time)
                day = start_time.day

                if day not in daily_data:
                    daily_data[day] = {
                        'indoor_temps': [],
                        'outdoor_temps': [],
                        'heating_minutes': 0
                    }

                daily_data[day]['heating_minutes'] += status.minutes_heating
                daily_data[day]['indoor_temps'].append(status.average_indoor_temp)
                daily_data[day]['outdoor_temps'].append(status.average_outdoor_temp)

            result = []
            for day in range(1, last_day + 1):
                if day in daily_data:
                    data = daily_data[day]
                    avg_indoor = sum(data['indoor_temps']) / len(data['indoor_temps'])
                    avg_outdoor = sum(data['outdoor_temps']) / len(data['outdoor_temps'])

                    result.append(DailyData(
                        day=day,
                        minutes_heating=data['heating_minutes'],
                        avg_indoor_temp=round(avg_indoor, 2),
                        avg_outdoor_temp=round(avg_outdoor, 2)
                    ))
                else:
                    result.append(DailyData(
                        day=day,
                        minutes_heating=0,
                        avg_indoor_temp=0.0,
                        avg_outdoor_temp=0.0
                    ))

            return result
        except Exception:
            return []

    @staticmethod
    def get_monthly_data_by_year(db: Session, year: int) -> List[MonthlyData]:
        try:
            start_of_year = datetime(year, 1, 1).strftime("%Y-%m-%d 00:00:00.000000")
            end_of_year = datetime(year, 12, 31, 23, 59, 59, 999999).strftime("%Y-%m-%d %H:%M:%S.%f")

            statuses = db.query(Status).filter(
                and_(
                    Status.start_time >= start_of_year,
                    Status.start_time <= end_of_year
                )
            ).order_by(Status.start_time).all()

            monthly_data = {}
            for status in statuses:
                start_time = parser.parse(status.start_time)
                month = start_time.month

                if month not in monthly_data:
                    monthly_data[month] = {
                        'indoor_temps': [],
                        'outdoor_temps': [],
                        'heating_minutes': 0
                    }

                monthly_data[month]['heating_minutes'] += status.minutes_heating
                monthly_data[month]['indoor_temps'].append(status.average_indoor_temp)
                monthly_data[month]['outdoor_temps'].append(status.average_outdoor_temp)

            result = []
            for month in range(1, 13):
                if month in monthly_data:
                    data = monthly_data[month]
                    avg_indoor = sum(data['indoor_temps']) / len(data['indoor_temps'])
                    avg_outdoor = sum(data['outdoor_temps']) / len(data['outdoor_temps'])

                    result.append(MonthlyData(
                        month=month,
                        minutes_heating=data['heating_minutes'],
                        avg_indoor_temp=round(avg_indoor, 2),
                        avg_outdoor_temp=round(avg_outdoor, 2)
                    ))
                else:
                    result.append(MonthlyData(
                        month=month,
                        minutes_heating=0,
                        avg_indoor_temp=0.0,
                        avg_outdoor_temp=0.0
                    ))

            return result
        except Exception:
            return []

    @staticmethod
    def create_status(db: Session, status_data: dict) -> Status:
        status = Status(**status_data)
        db.add(status)
        db.commit()
        db.refresh(status)
        return status