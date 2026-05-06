from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from models.incident_model import IncidentStatus, Severity

class IncidentBase(BaseModel):
    component_id: str
    status: IncidentStatus
    severity: Severity
    title: str
    description: str

class IncidentCreate(IncidentBase):
    pass

class IncidentRead(IncidentBase):
    id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    mttr_seconds: Optional[float] = None

    class Config:
        from_attributes = True
