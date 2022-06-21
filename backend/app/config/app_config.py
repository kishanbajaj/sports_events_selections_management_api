from pydantic import BaseSettings

class AppConfig(BaseSettings):
    API_STR: str = "/api"

    SECRET_KEY: str = ""
    POSTGRES_USER: str = ""
    POSTGRES_PASSWORD: str = ""
    POSTGRES_SERVER: str = "db"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = ""
    DB_MIN_CONNECTION_POOL: int = 2
    DB_MAX_CONNECTION_POOL: int = 10
    
    class Config:
        """Configs for the settings."""

        case_sensitive = True

appConfig = AppConfig()