# Design Process & Specification Plans

## 1. Initial Prompt & Conceptualization
The project was initiated with a focus on building a **mission-critical distributed system**. The primary objective was to ensure that the "Signals" (raw error events) never overwhelm the "Storage" (Source of Truth), while still providing real-time visibility to engineers.

### Key Conceptual Goals:
*   **Decoupling**: Use a Message Broker (Kafka) to ensure the API stays responsive under load.
*   **Deduplication**: Prevent "Alert Fatigue" by debouncing high-frequency signals at the worker level.
*   **Transactional Integrity**: Ensure that incident state changes and RCA submissions are atomic and persistent.

## 2. Design Pattern Selection
To meet the "LLD" requirements of the assignment, the following patterns were selected:

### 2.1. Strategy Pattern (Alerting)
*   **Reasoning**: Different components have different criticality. Hard-coding severity checks would make the system brittle.
*   **Implementation**: A `StrategyFactory` instantiates the correct alerting logic (P0/P1/P2) based on the `component_id`. This allows for adding new component types without modifying the core worker logic.

### 2.2. State Pattern (Lifecycle)
*   **Reasoning**: Managing transitions between `OPEN`, `INVESTIGATING`, `RESOLVED`, and `CLOSED` involves complex business rules (e.g., MTTR calculation on resolve, mandatory RCA on close).
*   **Implementation**: Each state is a dedicated class that defines valid next-state transitions. This prevents illegal transitions like moving an incident from `OPEN` directly to `CLOSED` without an RCA.

## 3. Data Flow Specification
1.  **Ingestion**: FastAPI receives JSON signal → Validates Schema → Publishes to Kafka `incident_signals` topic.
2.  **Buffering**: Kafka handles backpressure. If the worker slows down, Kafka stores the messages safely.
3.  **Processing**: Worker consumes Kafka → Checks Redis for existing debounce window → If new, creates Postgres record → Always logs raw payload to MongoDB.
4.  **Dashboard**: React polls (or uses WebSockets) to fetch the latest state from the Redis "Hot Path" cache.

## 4. Resilience Plans
*   **Rate Limiting**: Implemented a sliding window limiter in Redis to protect the Ingestion API.
*   **Graceful Shutdown**: All services (FastAPI, Worker) handle SIGTERM to ensure Kafka offsets are committed and DB connections are closed cleanly.
*   **Schema Safety**: Pydantic models ensure that malformed signals are rejected at the edge, before entering the system.

---