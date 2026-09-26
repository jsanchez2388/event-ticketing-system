# app/config.py
#
# PURPOSE
#   Single place where application settings are read from the environment file.
#   Every other module imports settings from here instead of hard-coding hosts, ports, or credentials.

import os
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()

class Settings:
    def __init__(self) -> None:
        self.POSTGRES_CONNECTION_STRING: str | None = os.getenv("POSTGRES_CONNECTION_STRING")
        self.MONGO_URI: str | None = os.getenv("MONGO_URI")
        self.MONGO_DB: str | None = os.getenv("MONGO_DB")

        self.REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
        self.REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))
        self.REDIS_DB: int = int(os.getenv("REDIS_DB", 0))
        self.CACHE_TTL_SECONDS: int = int(os.getenv("CACHE_TTL_SECONDS", 300))

        self.EVENT_CONTENT_COLLECTION: str = "event_content"

    def require(self, name: str) -> str:
        value = getattr(self, name)

        if not value:
            raise RuntimeError(f"{name} is missing. Add it to the .env file.")

        return value

@lru_cache()
def get_settings() -> Settings:
    """
    Return the application settings, cached to avoid re-reading the environment file.
    """
    return Settings()