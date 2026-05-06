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

if __name__ == "__main__":
    print("Starting data seeding...")
    # 1. Send some random signals
    for _ in range(5):
        send_signal(random.choice(COMPONENTS))
        time.sleep(1)

    # 2. Simulate a burst to test debouncing (should only create 1 incident)
    simulate_burst("CACHE_CLUSTER_01", 100)
    
    # 3. Simulate another burst for a different component
    simulate_burst("RDBMS_PRIMARY", 50)
    
    print("Done.")
