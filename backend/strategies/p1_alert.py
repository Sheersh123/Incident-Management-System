"""P1 Alert Strategy — Default / General component failures."""
from strategies.alert_strategy import AlertStrategy
from models.incident_model import Severity

class P1AlertStrategy(AlertStrategy):
    """Used for general component failures — medium severity."""

    def get_severity(self) -> Severity:
        return Severity.P1

    def get_alert_title(self, component_id: str) -> str:
        return f"ISSUE: Component {component_id} reporting errors"
