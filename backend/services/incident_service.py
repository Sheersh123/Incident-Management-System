from sqlalchemy.orm import Session
from models.incident_model import Incident, IncidentStatus, Severity, RCA
from strategies.alert_strategy import get_alert_strategy
from services.mttr_service import MTTRService
from utils.constants import VALID_TRANSITIONS, MAX_DB_RETRIES, RETRY_BACKOFF_SECONDS
from utils.logger import get_logger
from datetime import datetime
import uuid
import time

logger = get_logger(__name__)


class IncidentStateMachine:
    """State Pattern — enforces valid transitions for incident lifecycle.
    
    OPEN → INVESTIGATING → RESOLVED → CLOSED
    """

    @staticmethod
    def can_transition(current_status: IncidentStatus, new_status: IncidentStatus) -> bool:
        allowed = VALID_TRANSITIONS.get(current_status.value, [])
        return new_status.value in allowed

    @staticmethod
    def validate_close(incident: Incident) -> tuple[bool, str]:
        """Check if an incident can move to CLOSED — requires RCA."""
        if not incident.rca:
            return False, "Cannot close incident without a submitted RCA"
        return True, ""


class IncidentService:

    @staticmethod
    def create_or_update_incident(db: Session, component_id: str):
        """Create a new incident or return the existing active one.
        
        Uses retry logic with exponential backoff for DB resilience.
        """
        for attempt in range(MAX_DB_RETRIES):
            try:
                existing_incident = db.query(Incident).filter(
                    Incident.component_id == component_id,
                    Incident.status.in_([IncidentStatus.OPEN, IncidentStatus.INVESTIGATING])
                ).first()

                if existing_incident:
                    return existing_incident

                strategy = get_alert_strategy(component_id)
                new_incident = Incident(
                    id=str(uuid.uuid4()),
                    component_id=component_id,
                    title=strategy.get_alert_title(component_id),
                    severity=strategy.get_severity(),
                    status=IncidentStatus.OPEN,
                    description=f"Automated incident created for {component_id}",
                    start_time=datetime.utcnow()
                )
                db.add(new_incident)
                db.commit()
                db.refresh(new_incident)
                logger.info(f"Created incident {new_incident.id} for {component_id}")
                return new_incident

            except Exception as e:
                db.rollback()
                wait = RETRY_BACKOFF_SECONDS * (2 ** attempt)
                logger.warning(f"DB write failed (attempt {attempt + 1}/{MAX_DB_RETRIES}): {e}. "
                               f"Retrying in {wait}s...")
                time.sleep(wait)
                if attempt == MAX_DB_RETRIES - 1:
                    logger.error(f"DB write failed after {MAX_DB_RETRIES} attempts for {component_id}")
                    raise

    @staticmethod
    def update_status(db: Session, incident_id: str, new_status: IncidentStatus):
        """Transition an incident to a new status with State Pattern validation."""
        incident = db.query(Incident).filter(Incident.id == incident_id).first()
        if not incident:
            return None, "Incident not found"

        # State Pattern: enforce valid transitions
        if not IncidentStateMachine.can_transition(incident.status, new_status):
            return None, (f"Invalid transition: {incident.status.value} → {new_status.value}. "
                         f"Allowed: {VALID_TRANSITIONS.get(incident.status.value, [])}")

        # Mandatory RCA check before CLOSED
        if new_status == IncidentStatus.CLOSED:
            can_close, reason = IncidentStateMachine.validate_close(incident)
            if not can_close:
                return None, reason

        incident.status = new_status
        if new_status in (IncidentStatus.RESOLVED, IncidentStatus.CLOSED):
            incident.end_time = datetime.utcnow()
            if incident.start_time:
                incident.mttr_seconds = MTTRService.calculate_mttr(incident.start_time, incident.end_time)

        db.commit()
        db.refresh(incident)
        logger.info(f"Incident {incident_id} transitioned to {new_status.value}")
        return incident, ""
