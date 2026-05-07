import requests
import time
import random

BASE_URL = "http://localhost:8000"

COMPONENTS = [
    "CACHE_CLUSTER_01",
    "RDBMS_PRIMARY",
    "AUTH_API_HOST",
    "SEARCH_INDEX_STORE",
    "ASYNC_QUEUE_WORKER"
]

def send_signal(component_id):
    payload = {
        "component_id": component_id,
        "signal_type": "ERROR",
        "payload": {"error_code": "500", "message": "Connection timeout"}
    }
    try:
        resp = requests.post(f"{BASE_URL}/signals/", json=payload)
        print(f"Sent signal for {component_id}: {resp.status_code}")
    except Exception as e:
        print(f"Error sending signal: {e}")

def simulate_burst(component_id, count=100):
    print(f"Simulating burst of {count} signals for {component_id}...")
    for _ in range(count):
        send_signal(component_id)

def simulate_outage_scenario():
    print("\n--- STARTING COMPLEX FAILURE SCENARIO ---")
    
    # 1. RDBMS Primary goes down (P0 Incident)
    print("Step 1: RDBMS Primary reporting Critical Latency spikes...")
    for _ in range(20):
        send_signal("RDBMS_PRIMARY")
    
    time.sleep(2)
    
    # 2. MCP Host starts failing due to DB dependency (Cascading failure)
    print("Step 2: MCP_HOST_01 failing due to downstream dependency...")
    for _ in range(50):
        send_signal("MCP_HOST_01")
        
    print("--- SCENARIO SEEDED ---")

if __name__ == "__main__":
    print("Starting data seeding...")
    
    # Simple random signals
    for _ in range(3):
        send_signal(random.choice(COMPONENTS))
        time.sleep(0.5)

    # Complex scenario requested by assignment
    simulate_outage_scenario()
    
    print("\nDone. Check your dashboard for the 'RDBMS_PRIMARY' and 'MCP_HOST_01' incidents.")
