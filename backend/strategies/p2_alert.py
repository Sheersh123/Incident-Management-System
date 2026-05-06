"""P2 Alert Strategy — Warning: Cache / Non-critical failures."""
from strategies.alert_strategy import AlertStrategy
from models.incident_model import Severity

class P2AlertStrategy(AlertStrategy):
    """Used for Cache/Non-critical component failures — lower severity."""

    def get_severity(self) -> Severity:
        return Severity.P2

    def get_alert_title(self, component_id: str) -> str:
        return f"WARNING: Cache Degradation on {component_id}"
