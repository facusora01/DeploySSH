from contextlib import asynccontextmanager
import logging

import uvicorn
from fastapi import FastAPI

import app.models
from app.api.v1.router import api_router
from app.core.config import settings
from app.exceptions.handlers import (
    register_exception_handlers,
)
from app.services.scheduler import AppointmentScheduler
from app.services.whatsapp import initialize_whatsapp_client, cleanup_whatsapp

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    import os
    if os.getenv("WHATSAPP_ENABLED", "true").lower() == "true":
        try:
            await initialize_whatsapp_client()
        except Exception as e:
            logger.warning(f"⚠️ WhatsApp no disponible (dev/Docker sin display): {e}")
            logger.info("   Email y scheduler funcionarán normalmente")
    else:
        logger.info("ℹ️ WhatsApp deshabilitado (WHATSAPP_ENABLED=false)")

    scheduler = AppointmentScheduler()
    scheduler.start()
    scheduler.add_reminder_job()

    yield

    # Shutdown
    scheduler.stop()
    try:
        await cleanup_whatsapp()
    except Exception as e:
        logger.error(f"Error cerrando WhatsApp: {e}")


app = FastAPI(
    title="Appointa API",
    description="Backend para Appointa - Sistema de gestión de turnos",
    version="1.0.0",
    lifespan=lifespan,
)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        settings.frontend_url,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
register_exception_handlers(app)

app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "Appointa API is running", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(app, host=settings.host, port=settings.port)
