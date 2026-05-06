from abc import ABC, abstractmethod
from models.incident_model import Severity
from utils.constants import RDBMS_IDENTIFIERS, CACHE_IDENTIFIERS

class AlertStrategy(ABC):
    """Abstract base class for the Alerting Strategy Pattern.
    
    Different component failures require different alert types.
    This pattern allows swapping alerting logic based on component type.
    """

    @abstractmethod
    def get_severity(self) -> Severity:
        pass

    @abstractmethod
    def get_alert_title(self, component_id: str) -> str:
        pass


class RDBMSAlertStrategy(AlertStrategy):
    """P0 — Critical: RDBMS / Database failures."""
    def get_severity(self) -> Severity:
        return Severity.P0

    def get_alert_title(self, component_id: str) -> str:
        return f"CRITICAL: RDBMS Failure on {component_id}"


class CacheAlertStrategy(AlertStrategy):
    """P2 — Warning: Cache degradation."""
    def get_severity(self) -> Severity:
        return Severity.P2

    def get_alert_title(self, component_id: str) -> str:
        return f"WARNING: Cache Degradation on {component_id}"


class DefaultAlertStrategy(AlertStrategy):
    """P1 — Default: General component failures."""
    def get_severity(self) -> Severity:
        return Severity.P1

    def get_alert_title(self, component_id: str) -> str:
        return f"ISSUE: Component {component_id} reporting errors"


def get_alert_strategy(component_id: str) -> AlertStrategy:
    """Factory function that selects the correct strategy based on component ID."""
    upper_id = component_id.upper()
    if any(identifier in upper_id for identifier in RDBMS_IDENTIFIERS):
        return RDBMSAlertStrategy()
    elif any(identifier in upper_id for identifier in CACHE_IDENTIFIERS):
        return CacheAlertStrategy()
    return DefaultAlertStrategy()
