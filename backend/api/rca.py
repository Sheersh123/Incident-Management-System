from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.redis_client import redis_client
from schemas.rca_schema import RCACreate, RCARead
from services.rca_service import RCAService

router = APIRouter(prefix="/rca", tags=["RCA"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=RCARead)
async def submit_rca(rca: RCACreate, db: Session = Depends(get_db)):
    """Submit a Root Cause Analysis for an incident.
    
    This is MANDATORY before an incident can be moved to CLOSED.
    Automatically transitions the incident to CLOSED and calculates MTTR.
    """
    result, error = RCAService.submit_rca(db, rca)

    if error:
        raise HTTPException(status_code=400, detail=error)

    # Invalidate dashboard cache after closing incident
    redis_client.delete("dashboard:incidents")

    return result
