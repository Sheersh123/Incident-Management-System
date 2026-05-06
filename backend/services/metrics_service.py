from app.redis_client import redis_client
import time

class MetricsService:
    @staticmethod
    def get_throughput():
        # Using Redis to track signals per second for the last 5 seconds
        current_time = int(time.time())
        total_signals = 0
        for i in range(5):
            key = f"throughput:{current_time - i}"
            val = redis_client.get(key)
            if val:
                total_signals += int(val)
        
        return total_signals / 5.0 # Average signals/sec over 5s

    @staticmethod
    def record_signal():
        current_time = int(time.time())
        key = f"throughput:{current_time}"
        redis_client.incr(key)
        redis_client.expire(key, 60)
