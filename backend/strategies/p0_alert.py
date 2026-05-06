"""P0 Alert Strategy — Critical: RDBMS / Database failures."""
from strategies.alert_strategy import AlertStrategy
from models.incident_model import Severity

class P0AlertStrategy(AlertStrategy):
    """Used for RDBMS/Database component failures — highest severity."""

    def get_severity(self) -> Severity:
        return Severity.P0

    def get_alert_title(self, component_id: str) -> str:
        return f"CRITICAL: RDBMS Failure on {component_id}"
