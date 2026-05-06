from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class RCABase(BaseModel):
    root_cause_category: str
    fix_applied: str
    prevention_steps: str

class RCACreate(RCABase):
    incident_id: str

class RCARead(RCABase):
    id: str
    incident_id: str
    created_at: datetime

    class Config:
        from_attributes = True
