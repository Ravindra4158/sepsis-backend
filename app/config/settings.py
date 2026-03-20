from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    APP_NAME: str = "SepsisShield AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "sepsis_shield"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = "supersecretkey-change-in-production-32chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""
    MODEL_PATH: str = "ai_models/sepsis_model.pkl"
    MODEL_PROVIDER: str = "auto"
    MODEL_METADATA_PATH: str = ""
    MODEL_THRESHOLD_CRITICAL: int = 65
    MODEL_THRESHOLD_HIGH: int = 40
    MODEL_THRESHOLD_MODERATE: int = 20
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173,https://sepsis-forentend.vercel.app"
    CORS_ALLOW_ORIGIN_REGEX: str = r"^https://.*\.vercel\.app$"

    @property
    def cors_origins(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()
