"""Debounce Service — Uses Redis to suppress duplicate Work Item creation.

If 100 signals arrive for the same Component ID within a 10-second window,
only ONE Work Item should be created. All 100 signals are linked to it in MongoDB.
"""
from app.redis_client import redis_client
from app.config import settings
from utils.logger import get_logger

logger = get_logger(__name__)


class DebounceService:
    """Redis-based debouncing to prevent incident noise."""

    @staticmethod
    def should_create_incident(component_id: str, signal_timestamp_ms: int) -> bool:
        """Returns True only for the FIRST signal in a debounce window.
        
        Uses Redis INCR + EXPIRE for atomic counting within a time window.
        """
        window_id = int(signal_timestamp_ms / 1000 / settings.DEBOUNCE_WINDOW_SECONDS)
        debounce_key = f"debounce:{component_id}:{window_id}"

        count = redis_client.incr(debounce_key)
        if count == 1:
            redis_client.expire(debounce_key, settings.DEBOUNCE_WINDOW_SECONDS * 2)

        if count == 1:
            logger.info(f"Debounce PASS for {component_id} (window {window_id})")
            return True
        else:
            logger.info(f"Debounce SUPPRESSED for {component_id} (count: {count})")
            return False

    @staticmethod
    def link_signal_to_incident(component_id: str, signal_timestamp_ms: int):
        """Track the signal count for a given component in the current window."""
        window_id = int(signal_timestamp_ms / 1000 / settings.DEBOUNCE_WINDOW_SECONDS)
        link_key = f"signal_count:{component_id}:{window_id}"
        redis_client.incr(link_key)
        redis_client.expire(link_key, 3600)  # Keep for 1 hour
