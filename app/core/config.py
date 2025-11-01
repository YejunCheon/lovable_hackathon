from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

# Build an absolute path to the .env file from the project root
# This assumes config.py is in app/core/
# So, we go up two directories to find the project root where .env is.
env_path = Path(__file__).parent.parent.parent / ".env"

class Settings(BaseSettings):
    GEMINI_API_KEY: str
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str

    # Qdrant settings
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str | None = None
    QDRANT_COLLECTION_NAME: str = "candidates"

    # Supabase settings
    SUPABASE_URL: str
    SUPABASE_KEY: str

    model_config = SettingsConfigDict(env_file=str(env_path)) # Use absolute path

settings = Settings()
