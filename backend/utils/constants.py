# Application Constants

# Incident Status Transitions
VALID_TRANSITIONS = {
    "OPEN": ["INVESTIGATING"],
    "INVESTIGATING": ["RESOLVED"],
    "RESOLVED": ["CLOSED"],
    "CLOSED": []  # Terminal state
}

# Root Cause Categories
RCA_CATEGORIES = [
    "SOFTWARE_BUG",
    "INFRASTRUCTURE",
    "NETWORK",
    "HUMAN_ERROR",
    "CONFIGURATION",
    "DEPENDENCY_FAILURE",
]

# Component type identifiers for Strategy Pattern
RDBMS_IDENTIFIERS = ["RDBMS", "DB", "DATABASE", "POSTGRES", "MYSQL"]
CACHE_IDENTIFIERS = ["CACHE", "REDIS", "MEMCACHE"]
QUEUE_IDENTIFIERS = ["QUEUE", "KAFKA", "RABBITMQ"]

# Retry configuration
MAX_DB_RETRIES = 3
RETRY_BACKOFF_SECONDS = 0.5
