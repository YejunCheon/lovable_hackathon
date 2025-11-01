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

    model_config = SettingsConfigDict(env_file=str(env_path)) # Use absolute path

settings = Settings()
