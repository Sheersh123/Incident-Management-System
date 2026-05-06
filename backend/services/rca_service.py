from sqlalchemy.orm import Session
from models.incident_model import Incident, RCA, IncidentStatus
from services.mttr_service import MTTRService
from schemas.rca_schema import RCACreate
from utils.constants import MAX_DB_RETRIES, RETRY_BACKOFF_SECONDS
from utils.logger import get_logger
from datetime import datetime
import uuid
import time

logger = get_logger(__name__)


class RCAService:

    @staticmethod
    def validate_rca(rca_data: RCACreate) -> tuple[bool, str]:
        """Validate that the RCA is complete before accepting it."""
        if not rca_data.root_cause_category or not rca_data.root_cause_category.strip():
            return False, "Root cause category is required"
        if not rca_data.fix_applied or not rca_data.fix_applied.strip():
            return False, "Fix applied description is required"
        if not rca_data.prevention_steps or not rca_data.prevention_steps.strip():
            return False, "Prevention steps are required"
        return True, ""

    @staticmethod
    def submit_rca(db: Session, rca_data: RCACreate):
        """Submit an RCA and transition the incident to CLOSED.
        
        Includes retry logic for DB resilience.
        """
        # Validate completeness
        is_valid, error = RCAService.validate_rca(rca_data)
        if not is_valid:
            return None, error

        for attempt in range(MAX_DB_RETRIES):
            try:
                incident = db.query(Incident).filter(
                    Incident.id == rca_data.incident_id
                ).first()

                if not incident:
                    return None, "Incident not found"

                if incident.status == IncidentStatus.CLOSED:
                    return None, "Incident is already closed"

                # Check if RCA already exists
                existing_rca = db.query(RCA).filter(
                    RCA.incident_id == rca_data.incident_id
                ).first()
                if existing_rca:
                    return None, "RCA already submitted for this incident"

                # Create RCA record
                new_rca = RCA(
                    id=str(uuid.uuid4()),
                    incident_id=rca_data.incident_id,
                    root_cause_category=rca_data.root_cause_category,
                    fix_applied=rca_data.fix_applied,
                    prevention_steps=rca_data.prevention_steps
                )
                db.add(new_rca)

                # Transition to CLOSED and calculate MTTR
                incident.status = IncidentStatus.CLOSED
                end_time = datetime.utcnow()
                incident.end_time = end_time
                if incident.start_time:
                    incident.mttr_seconds = MTTRService.calculate_mttr(
                        incident.start_time, end_time
                    )

                db.commit()
                db.refresh(new_rca)
                logger.info(f"RCA submitted for incident {rca_data.incident_id}, "
                           f"incident CLOSED")
                return new_rca, ""

            except Exception as e:
                db.rollback()
                wait = RETRY_BACKOFF_SECONDS * (2 ** attempt)
                logger.warning(f"RCA submission failed (attempt {attempt + 1}/"
                              f"{MAX_DB_RETRIES}): {e}. Retrying in {wait}s...")
                time.sleep(wait)
                if attempt == MAX_DB_RETRIES - 1:
                    logger.error(f"RCA submission failed after {MAX_DB_RETRIES} attempts")
                    raise
