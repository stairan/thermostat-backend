# Thermostat Backend API

A FastAPI-based backend for managing thermostat status data with SQLite database.

## Features

- Query thermostat data by specific date
- Query thermostat data for a time period
- Get statistical summaries
- Calculate heating efficiency metrics
- Create new status records
- RESTful API with automatic OpenAPI documentation

## Database Schema

The `statuses` table contains:
- `id` (integer): Unique identifier, auto-increment
- `start_time` (text): Starting date/time (format: "2021-03-04 20:00:00.000000")
- `end_time` (text): Ending date/time (same format as start_time)
- `minutes_heating` (int): Number of minutes heating was on
- `average_indoor_temp` (real): Average indoor temperature during the period
- `average_outdoor_temp` (real): Average outdoor temperature during the period

## Setup

1. Install dependencies:
```bash
uv sync
```

2. Add sample data (optional):
```bash
uv run python add_sample_data.py
```

3. Start the server:
```bash
uv run python run.py
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Core Endpoints

#### Get data for one day
```
GET /api/v1/statuses/day/{date}
```
Example: `GET /api/v1/statuses/day/2024-01-01`

#### Get data for a time period
```
GET /api/v1/statuses/period?start_date={start}&end_date={end}
```
Example: `GET /api/v1/statuses/period?start_date=2024-01-01&end_date=2024-01-02`

#### Get all statuses (paginated)
```
GET /api/v1/statuses/all?limit={limit}&offset={offset}
```
Example: `GET /api/v1/statuses/all?limit=50&offset=0`

### Analytics Endpoints

#### Get statistics
```
GET /api/v1/statuses/stats?start_date={start}&end_date={end}
```
Returns total records, heating minutes, temperature averages, and min/max values.

#### Get heating efficiency
```
GET /api/v1/statuses/heating-efficiency?start_date={start}&end_date={end}
```
Calculates heating efficiency based on temperature difference and heating time.

### Data Management

#### Create new status record
```
POST /api/v1/statuses
```
Body:
```json
{
  "start_time": "2024-01-01 08:00:00.000000",
  "end_time": "2024-01-01 09:00:00.000000",
  "minutes_heating": 45,
  "average_indoor_temp": 21.5,
  "average_outdoor_temp": 5.2
}
```

### Utility Endpoints

#### Health check
```
GET /health
```

#### API information
```
GET /
```

## Documentation

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Example Usage

```bash
# Get data for January 1st, 2024
curl "http://localhost:8000/api/v1/statuses/day/2024-01-01"

# Get statistics for a date range
curl "http://localhost:8000/api/v1/statuses/stats?start_date=2024-01-01&end_date=2024-01-31"

# Create a new status record
curl -X POST "http://localhost:8000/api/v1/statuses" \
  -H "Content-Type: application/json" \
  -d '{
    "start_time": "2024-01-01 10:00:00.000000",
    "end_time": "2024-01-01 11:00:00.000000",
    "minutes_heating": 30,
    "average_indoor_temp": 22.0,
    "average_outdoor_temp": 3.5
  }'
```

## Project Structure

```
thermostat-backend/
├── thermostat_backend/
│   ├── __init__.py
│   ├── main.py           # FastAPI application
│   ├── models.py         # SQLAlchemy models
│   ├── schemas.py        # Pydantic schemas
│   ├── database.py       # Database connection
│   ├── services.py       # Business logic
│   └── routers.py        # API endpoints
├── run.py               # Development server runner
├── add_sample_data.py   # Sample data generator
├── pyproject.toml       # Project configuration
└── README.md            # This file
```