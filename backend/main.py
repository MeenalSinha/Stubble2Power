"""
Main FastAPI Application for Stubble2Power.
Provides RESTful APIs for NASA Earth Observation, MODIS-VIIRS Harmonization,
Farmer Management, Agricultural Waste Logistics, and Economic Simulation.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.models.database import init_db
from backend.api.routes import (
    health,
    config,
    farmers,
    clustering,
    economics,
    nasa,
    harmonization,
    calendar,
    seasonal,
    anomalies,
    agriculture,
    farms,
    biomass,
    mobile_units,
    deployments,
    advanced_economics,
    environmental_lca,
    auth,
    organizations,
    user_experience,
    privacy_governance,
)
from backend.core.config.settings import app_settings
from backend.core.logging.logger import get_logger

logger = get_logger("stubble2power.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    logger.info("Initializing Stubble2Power database schema...")
    init_db()
    logger.info("Stubble2Power API operational.")
    yield
    # Shutdown actions
    logger.info("Stubble2Power API shutting down.")


app = FastAPI(
    title="Stubble2Power - Satellite Fire Intelligence & Bio-Refinery Platform",
    description=(
        "Production-grade geospatial intelligence platform addressing NASA Space Apps Challenge 09 "
        "(Harmonization of MODIS and VIIRS Hot Spots) with decentralized agricultural waste management."
    ),
    version="2.0.0",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Route Registrations
app.include_router(health.router, prefix="/api")
app.include_router(config.router, prefix="/api")
app.include_router(farmers.router, prefix="/api")
app.include_router(clustering.router, prefix="/api")
app.include_router(economics.router, prefix="/api")
app.include_router(nasa.router, prefix="/api")
app.include_router(harmonization.router, prefix="/api")
app.include_router(calendar.router, prefix="/api")
app.include_router(seasonal.router, prefix="/api")
app.include_router(anomalies.router, prefix="/api")
app.include_router(agriculture.router, prefix="/api")
app.include_router(farms.router, prefix="/api")
app.include_router(biomass.router, prefix="/api")
app.include_router(mobile_units.router, prefix="/api")
app.include_router(deployments.router, prefix="/api")
app.include_router(advanced_economics.router, prefix="/api")
app.include_router(environmental_lca.router, prefix="/api")
app.include_router(auth.router)
app.include_router(organizations.router)
app.include_router(user_experience.router)
app.include_router(privacy_governance.router)


@app.get("/")
def root():
    return {
        "message": "Welcome to Stubble2Power API",
        "docs_url": "/docs",
        "version": "2.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=app_settings.api_host, port=app_settings.api_port, reload=True)
