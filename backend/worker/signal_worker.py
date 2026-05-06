"""Signal Worker — Kafka consumer that processes signals with debouncing.

Runs as a standalone process, consuming from Kafka and using Redis for
debounce state. Prints throughput metrics to console every 5 seconds.
"""
import asyncio
import json
from aiokafka import AIOKafkaConsumer
from app.config import settings
from app.redis_client import redis_client
from app.database import SessionLocal
from services.incident_service import IncidentService
from services.debounce_service import DebounceService
from services.metrics_service import MetricsService
from utils.logger import get_logger

logger = get_logger(__name__)


async def print_metrics_loop():
    """Background task: print throughput metrics to console every 5 seconds."""
    while True:
        await asyncio.sleep(5)
        throughput = MetricsService.get_throughput()
        logger.info(f"[METRICS] Signals/sec (avg 5s): {throughput:.2f}")


async def process_signals():
    """Main consumer loop — reads from Kafka and applies debouncing."""
    consumer = AIOKafkaConsumer(
        settings.KAFKA_TOPIC,
        bootstrap_servers=settings.KAFKA_BROKER,
        group_id="signal_processor_group",
        value_deserializer=lambda v: json.loads(v.decode('utf-8'))
    )

    await consumer.start()
    logger.info("Signal worker started, consuming from Kafka...")

    try:
        async for msg in consumer:
            signal_data = msg.value
            component_id = signal_data.get("component_id")

            # Record throughput metric
            MetricsService.record_signal()

            # Debouncing: only create 1 Work Item per component per window
            should_create = DebounceService.should_create_incident(
                component_id, msg.timestamp
            )

            # Always link signal to the incident in Redis
            DebounceService.link_signal_to_incident(component_id, msg.timestamp)

            if should_create:
                db = SessionLocal()
                try:
                    incident = IncidentService.create_or_update_incident(db, component_id)
                    logger.info(f"Incident {incident.id} active for {component_id}")
                finally:
                    db.close()

    finally:
        await consumer.stop()


async def main():
    """Run both the consumer and metrics printer concurrently."""
    await asyncio.gather(
        process_signals(),
        print_metrics_loop()
    )


if __name__ == "__main__":
    asyncio.run(main())
