from sqlalchemy import Column, String, DateTime, JSON, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import uuid
from app.database import Base

class IncidentStatus(enum.Enum):
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"

class Severity(enum.Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"

class Incident(Base):
    __tablename__ = "incidents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    component_id = Column(String, index=True)
    status = Column(SQLEnum(IncidentStatus), default=IncidentStatus.OPEN)
    severity = Column(SQLEnum(Severity))
    title = Column(String)
    description = Column(String)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    mttr_seconds = Column(JSON, nullable=True) # Storing calculation details
    
    rca = relationship("RCA", back_populates="incident", uselist=False)

class RCA(Base):
    __tablename__ = "rca_records"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_id = Column(String, ForeignKey("incidents.id"), unique=True)
    root_cause_category = Column(String) # Dropdown value
    fix_applied = Column(String)
    prevention_steps = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    incident = relationship("Incident", back_populates="rca")
