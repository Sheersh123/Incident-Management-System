# IMS Backend

This is the high-performance backend for the Mission-Critical Incident Management System (IMS). It is designed to handle high-throughput signals (up to 10k/sec), debounce them intelligently, and manage incident state machines and Root Cause Analysis workflows.

## Architecture & Data Flow
1. **FastAPI**: Provides robust async REST API endpoints for signals, incidents, and RCA management.
2. **Redis**: Acts as the hot-path rate limiter and debouncer. If a single component emits 100 failure signals in a minute, Redis ensures only a single Work Item is created, preventing cascade failures.
3. **Kafka**: The message broker. Signals are pushed to a Kafka topic (`signals`), allowing ingestion to remain incredibly fast and decoupled from database latency.
4. **Worker (Kafka Consumer)**: A background Python worker (`worker/signal_worker.py`) consumes from Kafka. It processes signals through the Alert Strategy Pattern, evaluating severity, and persisting them to MongoDB (raw logs) and PostgreSQL (stateful incident tracking).
5. **PostgreSQL**: The Source of Truth for incident lifecycles and RCA records.
6. **MongoDB**: Acts as a data lake for raw signal audit logs, avoiding clutter in the structured RDBMS.

## Key Design Patterns
- **Strategy Pattern (`strategies/alert_strategy.py`)**: Determines the severity of an incident based on the payload type (e.g., P0 for database failures, P2 for cache delays).
- **State Pattern (`services/incident_service.py`)**: Enforces strict transitions (OPEN -> INVESTIGATING -> RESOLVED -> CLOSED) and requires a completed RCA before the terminal CLOSED state.

## Getting Started

The recommended way to run this backend is via the root Docker Compose setup:
```bash
cd ..
docker-compose up -d --build
```

### Local Development
To run without Docker Compose (assuming PostgreSQL, Redis, MongoDB, and Kafka are running locally):
1. `python -m venv venv`
2. `.\venv\Scripts\activate` (or `source venv/bin/activate` on Linux/Mac)
3. `pip install -r requirements.txt`
4. Start API: `python app/main.py`
5. Start Worker: `python -m worker.signal_worker`
6. Seed Data: `python -m scripts.seed_data`

### Testing
Run `pytest tests/ -v` to execute the full test suite covering RCA validation, state transitions, and rate limiting.
