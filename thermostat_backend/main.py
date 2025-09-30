import os
import asyncio
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from .routers import router
from .database import create_tables
from .home_assistant import HomeAssistantService

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Thermostat Backend API",
    description="API for managing thermostat status data",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")

home_assistant_service = None

@app.on_event("startup")
async def startup_event():
    create_tables()

    ha_url = os.getenv("HOME_ASSISTANT_URL")
    ha_token = os.getenv("HOME_ASSISTANT_TOKEN")

    if ha_url:
        global home_assistant_service
        home_assistant_service = HomeAssistantService(ha_url, ha_token)

        asyncio.create_task(home_assistant_service.start_polling(60))
        logger.info("Home Assistant polling started")
    else:
        logger.warning("HOME_ASSISTANT_URL not set, Home Assistant integration disabled")

@app.get("/")
async def root():
    return {
        "message": "Thermostat Backend API",
        "version": "1.0.0",
        "documentation": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)