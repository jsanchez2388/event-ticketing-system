# app/config.py
#
# PURPOSE
#   Single place where application settings are read from the environment
#   (.env file locally). Every other module imports settings from here instead
#   of hard-coding hosts, ports, or credentials.
#
# TO ADD
#   class Settings
#       Holds all configuration values. Suggested fields:
#         - postgres_host: str
#         - postgres_port: int
#         - postgres_db: str
#         - postgres_user: str
#         - postgres_password: str
#         - mongo_uri: str
#         - mongo_db: str                      (database that holds `event_content`)
#         - redis_host: str
#         - redis_port: int
#         - redis_db: int
#         - cache_ttl_seconds: int             (TTL for cached event details)
#       Options: a plain class populated with os.getenv(), or a
#       pydantic-settings BaseSettings subclass (add `pydantic-settings` and/or
#       `python-dotenv` to requirements.txt if used).
#
#   def get_settings() -> Settings
#       Returns a single shared Settings instance (e.g. cached with
#       functools.lru_cache) so the .env file is only read once.
#
# NOTES
#   - Variable names must match .env.example.
#   - Never commit real credentials; .env is already in .gitignore.
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is missing. Add it to the .env file."
    )

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB")