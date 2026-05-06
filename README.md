# 🚨 Mission-Critical Incident Management System (IMS)

A resilient, distributed incident management system designed to monitor complex infrastructure stacks and manage failure mediation workflows at scale.

---

## 📐 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          INCIDENT MANAGEMENT SYSTEM                        │
│                                                                             │
│  ┌──────────────┐     ┌─────────┐     ┌──────────────────┐                │
│  │  Frontend     │────▶│ FastAPI │◀───▶│  PostgreSQL       │                │
│  │  React/Vite   │     │ Backend │     │  (Source of Truth) │                │
│  │  Dashboard    │     │         │     │  Work Items + RCA  │                │
│  └──────────────┘     │         │     └──────────────────┘                │
│                        │ Rate    │                                          │
│  ┌──────────────┐     │ Limited │     ┌──────────────────┐                │
│  │  Signal       │────▶│ /signals│────▶│  Kafka             │                │
│  │  Producers    │     │         │     │  (Message Broker)  │                │
│  │  (10k sig/s)  │     │         │     └────────┬─────────┘                │
│  └──────────────┘     │ /health │              │                           │
│                        │ /incidents│            ▼                           │
│                        │ /rca    │     ┌──────────────────┐                │
│                        └─────────┘     │  Background       │                │
│                              │         │  Worker            │                │
│                              │         │  (Debouncing +     │                │
│                              ▼         │   State Machine)   │                │
│                        ┌─────────┐     └────────┬─────────┘                │
│                        │  Redis   │◀────────────┘                           │
│                        │ (Cache + │     ┌──────────────────┐                │
│                        │ Debounce │     │  MongoDB           │                │
│                        │ Hot-Path)│     │  (Data Lake /      │                │
│                        └─────────┘     │   Audit Log)       │                │
│                                         └──────────────────┘                │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 🧱 Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **API** | FastAPI (Python) | High-performance async REST API |
| **Message Broker** | Apache Kafka | Decoupled signal ingestion, backpressure management |
| **RDBMS** | PostgreSQL | Source of Truth for Work Items & RCA records |
| **NoSQL** | MongoDB | Data Lake for raw signal audit logs |
| **Cache** | Redis | Hot-path dashboard cache, debounce state, rate limiting |
| **Frontend** | React + Vite | Real-time incident dashboard |
| **Infrastructure** | Docker Compose | Full-stack orchestration |

## 🎨 Design Patterns

### Strategy Pattern — Alerting
Different component failures trigger different severity levels:
- **P0 (Critical)**: RDBMS / Database failures → `strategies/p0_alert.py`
- **P1 (Warning)**: General component failures → `strategies/p1_alert.py`
- **P2 (Info)**: Cache degradation → `strategies/p2_alert.py`

### State Pattern — Incident Lifecycle
```
OPEN → INVESTIGATING → RESOLVED → CLOSED
```
- Each transition is validated via `IncidentStateMachine`
- **CLOSED is a terminal state** — no further transitions allowed
- **Mandatory RCA**: System rejects CLOSED transition without a submitted RCA

## 🔄 Backpressure & Resilience Strategy

### How we handle 10,000 signals/sec:

1. **Kafka as Buffer**: Signals are immediately pushed to Kafka, decoupling ingestion from processing. If the DB is slow, signals queue in Kafka instead of crashing the API.
2. **Redis Rate Limiting**: 600k signals/min limit on the ingestion API to prevent cascading failures.
3. **Debouncing**: If 100 signals arrive for the same component within 10 seconds, only ONE Work Item is created. Redis atomic counters (`INCR` + `EXPIRE`) ensure thread-safe deduplication.
4. **Retry Logic**: All DB writes use exponential backoff (3 retries) to survive transient failures.
5. **Hot-Path Caching**: Dashboard reads from Redis cache (5s TTL) instead of hitting PostgreSQL on every poll.

## 🚀 Getting Started

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Node.js 18+

### Option 1: Docker Compose (Recommended)
```bash
cd backend
docker-compose up -d
```
This starts: PostgreSQL, MongoDB, Redis, Kafka, Zookeeper, Backend API, and Worker.

### Option 2: Local Development

**1. Start Infrastructure:**
```bash
cd backend
docker-compose up -d postgres mongodb redis zookeeper kafka
```

**2. Start Backend:**
```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
python app/main.py
```

**3. Start Worker (separate terminal):**
```bash
cd backend
python -m worker.signal_worker
```

**4. Start Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**5. Seed Sample Data:**
```bash
cd backend
python -m scripts.seed_data
```

### API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/signals/` | Ingest a signal |
| GET | `/incidents/` | List all incidents (cached) |
| GET | `/incidents/{id}` | Get incident detail |
| GET | `/incidents/{id}/signals` | Get raw signals from MongoDB |
| PATCH | `/incidents/{id}/status?new_status=X` | Transition incident state |
| POST | `/rca/` | Submit RCA & close incident |
| GET | `/health` | Health check + throughput metrics |
| GET | `/aggregations` | Time-series signal aggregations |

## 🧪 Testing

```bash
cd backend
pytest tests/ -v
```

Tests cover:
- RCA validation (empty fields, whitespace)
- RCA submission (nonexistent incident, already closed)
- State Pattern transitions (valid/invalid)
- Mandatory RCA enforcement before CLOSED

## 📁 Project Structure
```
incident-management-system/
├── backend/
│   ├── api/                    # FastAPI route handlers
│   │   ├── signals.py          # Signal ingestion endpoint
│   │   ├── incidents.py        # Incident CRUD + status transitions
│   │   ├── rca.py              # RCA submission endpoint
│   │   └── health.py           # Health + aggregation endpoints
│   ├── app/                    # Core application setup
│   │   ├── main.py             # FastAPI app + lifespan events
│   │   ├── config.py           # Pydantic settings
│   │   ├── database.py         # PostgreSQL connection
│   │   ├── redis_client.py     # Redis connection
│   │   ├── mongo_client.py     # MongoDB connection
│   │   ├── kafka_producer.py   # Kafka producer
│   │   └── kafka_consumer.py   # Kafka consumer
│   ├── models/                 # SQLAlchemy ORM models
│   ├── schemas/                # Pydantic request/response schemas
│   ├── services/               # Business logic
│   │   ├── incident_service.py # State Machine + incident CRUD
│   │   ├── rca_service.py      # RCA validation + submission
│   │   ├── debounce_service.py # Redis-based signal debouncing
│   │   ├── mttr_service.py     # MTTR calculation
│   │   └── metrics_service.py  # Throughput tracking
│   ├── strategies/             # Strategy Pattern implementations
│   │   ├── alert_strategy.py   # Base class + factory
│   │   ├── p0_alert.py         # RDBMS failures (Critical)
│   │   ├── p1_alert.py         # General failures (Warning)
│   │   └── p2_alert.py         # Cache failures (Info)
│   ├── middleware/              # Rate limiting
│   ├── worker/                 # Kafka consumer worker
│   ├── tests/                  # Unit tests
│   ├── scripts/                # Sample data seeder
│   ├── utils/                  # Logger, constants
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx             # Main dashboard component
│   │   ├── index.css           # Premium dark theme CSS
│   │   └── main.jsx            # React entry point
│   └── package.json
└── README.md
```
