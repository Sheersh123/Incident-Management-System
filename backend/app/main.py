from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from api import signals, incidents, rca, health
from app.kafka_producer import kafka_producer
from app.mongo_client import connect_to_mongo, close_mongo_connection
from app.database import engine, Base
from middleware.rate_limiter import rate_limit_middleware
from services.metrics_service import MetricsService
from utils.logger import get_logger
from fastapi.middleware.cors import CORSMiddleware
import asyncio

logger = get_logger(__name__)


async def print_metrics_loop():
    """Background task: print throughput metrics to console every 5 seconds."""
    while True:
        await asyncio.sleep(5)
        throughput = MetricsService.get_throughput()
        logger.info(f"[METRICS] Throughput: {throughput:.2f} signals/sec (avg 5s)")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting IMS Backend...")
    Base.metadata.create_all(bind=engine)
    await connect_to_mongo()
    await kafka_producer.start()

    # Launch background metrics printer
    metrics_task = asyncio.create_task(print_metrics_loop())
    logger.info("IMS Backend started successfully")

    yield

    # Shutdown
    metrics_task.cancel()
    await kafka_producer.stop()
    await close_mongo_connection()
    logger.info("IMS Backend shut down")


app = FastAPI(
    title="Incident Management System (IMS)",
    description="Mission-Critical Incident Management System for monitoring distributed infrastructure",
    version="1.0.0",
    lifespan=lifespan,
    dependencies=[Depends(rate_limit_middleware)]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(signals.router)
app.include_router(incidents.router)
app.include_router(rca.router)
app.include_router(health.router)


@app.get("/")
async def root():
    return {"message": "IMS API is running", "docs": "/docs"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
