from fastapi import APIRouter, Depends, BackgroundTasks
from schemas.signal_schema import SignalIn
from app.kafka_producer import kafka_producer
from app.mongo_client import get_nosql_db
import datetime

router = APIRouter(prefix="/signals", tags=["Signals"])

@router.post("/")
async def ingest_signal(signal: SignalIn, background_tasks: BackgroundTasks):
    signal_dict = signal.model_dump()
    signal_dict["timestamp"] = signal_dict["timestamp"].isoformat()
    
    # 1. Push to Kafka for async processing
    await kafka_producer.send_signal(signal_dict)
    
    # 2. Store in Data Lake (Mongo) as audit log
    db = get_nosql_db()
    background_tasks.add_task(db.raw_signals.insert_one, signal_dict.copy())
    
    return {"status": "ingested", "component_id": signal.component_id}
