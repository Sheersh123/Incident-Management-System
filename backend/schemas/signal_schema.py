from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict, Any

class SignalIn(BaseModel):
    component_id: str = Field(..., example="CACHE_CLUSTER_01")
    signal_type: str = Field(..., example="LATENCY_SPIKE")
    payload: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
