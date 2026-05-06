from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.redis_client import redis_client
from app.mongo_client import get_nosql_db
from models.incident_model import Incident, IncidentStatus
from services.incident_service import IncidentService
from schemas.incident_schema import IncidentRead
from utils.logger import get_logger
from typing import List
import json

logger = get_logger(__name__)

router = APIRouter(prefix="/incidents", tags=["Incidents"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/", response_model=List[IncidentRead])
async def list_incidents(db: Session = Depends(get_db)):
    """Live Feed — returns active incidents sorted by severity (P0 first).
    
    Uses Redis hot-path cache to avoid hitting Postgres on every UI refresh.
    Cache is refreshed every 5 seconds.
    """
    cache_key = "dashboard:incidents"
    cached = redis_client.get(cache_key)

    if cached:
        return json.loads(cached)

    incidents = db.query(Incident).order_by(
        Incident.severity.asc(),
        Incident.start_time.desc()
    ).all()

    # Serialize and cache in Redis for 5 seconds (hot-path)
    result = []
    for inc in incidents:
        result.append({
            "id": inc.id,
            "component_id": inc.component_id,
            "status": inc.status.value,
            "severity": inc.severity.value,
            "title": inc.title,
            "description": inc.description,
            "start_time": inc.start_time.isoformat() if inc.start_time else None,
            "end_time": inc.end_time.isoformat() if inc.end_time else None,
            "mttr_seconds": inc.mttr_seconds
        })

    redis_client.setex(cache_key, 5, json.dumps(result))
    return result


@router.get("/{incident_id}", response_model=IncidentRead)
async def get_incident(incident_id: str, db: Session = Depends(get_db)):
    """Get a single incident by ID."""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.get("/{incident_id}/signals")
async def get_incident_signals(incident_id: str, db: Session = Depends(get_db)):
    """Incident Detail — fetch raw signals from MongoDB (NoSQL / Data Lake).
    
    Returns the raw signal payloads linked to this incident's component.
    """
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    # Query MongoDB for raw signals matching this component
    nosql_db = get_nosql_db()
    cursor = nosql_db.raw_signals.find(
        {"component_id": incident.component_id},
        {"_id": 0}  # Exclude Mongo internal _id
    ).sort("timestamp", -1).limit(100)

    signals = await cursor.to_list(length=100)
    return {"incident_id": incident_id, "signal_count": len(signals), "signals": signals}


@router.patch("/{incident_id}/status")
async def update_incident_status(
    incident_id: str,
    new_status: str,
    db: Session = Depends(get_db)
):
    """Workflow Engine — transition an incident's status using the State Pattern.
    
    Valid transitions: OPEN → INVESTIGATING → RESOLVED → CLOSED
    CLOSED requires a submitted RCA (mandatory).
    """
    try:
        target_status = IncidentStatus(new_status)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status '{new_status}'. "
                   f"Must be one of: {[s.value for s in IncidentStatus]}"
        )

    incident, error = IncidentService.update_status(db, incident_id, target_status)

    if error:
        raise HTTPException(status_code=400, detail=error)

    # Invalidate dashboard cache
    redis_client.delete("dashboard:incidents")

    return {"id": incident.id, "status": incident.status.value, "message": "Status updated"}
