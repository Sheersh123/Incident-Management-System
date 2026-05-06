"""MTTR Service — Calculates Mean Time To Repair for incidents."""
from datetime import datetime
from utils.logger import get_logger

logger = get_logger(__name__)


class MTTRService:
    """Calculates MTTR = end_time (RCA submission) - start_time (first signal)."""

    @staticmethod
    def calculate_mttr(start_time: datetime, end_time: datetime = None) -> float:
        """Calculate MTTR in seconds between incident start and resolution.
        
        Args:
            start_time: When the first signal was received.
            end_time: When the RCA was submitted (defaults to now).
            
        Returns:
            MTTR in seconds as a float.
        """
        if end_time is None:
            end_time = datetime.utcnow()
        
        diff = end_time - start_time
        mttr_seconds = diff.total_seconds()
        
        logger.info(f"MTTR calculated: {mttr_seconds:.2f}s "
                     f"(start: {start_time.isoformat()}, end: {end_time.isoformat()})")
        return mttr_seconds
