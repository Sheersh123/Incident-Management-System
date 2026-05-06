from pydantic_settings import BaseSettings
class Settings(BaseSettings):
    POSTGRES_URL: str
    MONGO_URL: str
    REDIS_URL: str
    KAFKA_BROKER: str
    KAFKA_TOPIC: str = "incident_signals"
    RATE_LIMIT_PER_MINUTE: int = 600000
    DEBOUNCE_WINDOW_SECONDS: int = 10
    DEBOUNCE_THRESHOLD: int = 100

    class Config:
        env_file = ".env"
settings = Settings()