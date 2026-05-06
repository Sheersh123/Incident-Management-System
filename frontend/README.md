# Mission-Critical IMS Dashboard

This is the frontend dashboard for the Incident Management System (IMS). It provides real-time monitoring of high-throughput system signals and interactive management of the Root Cause Analysis (RCA) workflow.

## Features
- **Live Feed**: Monitors active and resolved incidents using real-time HTTP polling.
- **Incident State Management**: Transition incidents from OPEN -> INVESTIGATING -> RESOLVED.
- **RCA Modal**: Submit detailed Root Cause Analysis before allowing an incident to be CLOSED.
- **Raw Signals Inspection**: Allows operators to drill down into raw MongoDB-stored signals directly from the UI.
- **Premium Design**: Dynamic, glassmorphic UI using Framer Motion and Lucide icons.

## Tech Stack
- React 19 + Vite
- Axios for API requests
- Framer Motion for animations
- Lucide React for iconography

## Getting Started

### Via Docker Compose (Recommended)
This frontend is configured to run alongside the backend via Docker Compose. From the root `backend` directory, run:
```bash
docker-compose up -d --build
```
The dashboard will be available at [http://localhost:5173](http://localhost:5173).

### Local Development
To run this frontend standalone:
```bash
npm install
npm run dev
```
(Ensure the FastAPI backend is running on `http://localhost:8000`).
