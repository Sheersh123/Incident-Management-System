from aiokafka import AIOKafkaProducer
import json
from app.config import settings
import asyncio

class KafkaProducerWrapper:
    def __init__(self):
        self.producer = None

    async def start(self):
        self.producer = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_BROKER,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        await self.producer.start()

    async def stop(self):
        if self.producer:
            await self.producer.stop()

    async def send_signal(self, signal_data: dict):
        if not self.producer:
            await self.start()
        await self.producer.send_and_wait(settings.KAFKA_TOPIC, signal_data)

kafka_producer = KafkaProducerWrapper()
