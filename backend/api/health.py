from fastapi import APIRouter
from app.redis_client import redis_client
from services.metrics_service import MetricsService
from app.database import SessionLocal
from models.incident_model import Incident, IncidentStatus
from utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    """Observability — health endpoint with throughput metrics."""
    throughput = MetricsService.get_throughput()

    # Quick connectivity checks
    redis_ok = True
    try:
        redis_client.ping()
    except Exception:
        redis_ok = False

    db_ok = True
    try:
        db = SessionLocal()
        db.execute("SELECT 1" if hasattr(db, 'execute') else None)
        db.close()
    except Exception:
        db_ok = False

    return {
        "status": "healthy" if (redis_ok and db_ok) else "degraded",
        "components": {
            "redis": "up" if redis_ok else "down",
            "postgres": "up" if db_ok else "down",
        },
        "metrics": {
            "signals_per_sec_avg_5s": round(throughput, 2)
        }
    }


@router.get("/aggregations")
async def get_aggregations():
    """Time-series aggregations — signal counts per component over recent windows.
    
    Uses Redis keys to provide time-bucketed signal counts.
    """
    import time
    current_time = int(time.time())
    buckets = []

    # Get the last 12 five-second windows (1 minute of data)
    for i in range(12):
        ts = current_time - (i * 5)
        bucket_signals = 0
        for j in range(5):
            key = f"throughput:{ts - j}"
            val = redis_client.get(key)
            if val:
                bucket_signals += int(val)

        buckets.append({
            "window_start": ts - 4,
            "window_end": ts,
            "signal_count": bucket_signals
        })

    # Per-component counts from debounce keys
    component_counts = {}
    for key in redis_client.scan_iter("signal_count:*"):
        parts = key.split(":")
        if len(parts) >= 2:
            comp = parts[1]
            val = redis_client.get(key)
            if val:
                component_counts[comp] = component_counts.get(comp, 0) + int(val)

    return {
        "time_series": buckets,
        "per_component": component_counts
    }
