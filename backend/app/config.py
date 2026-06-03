from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://rankkit:rankkit@localhost:5432/rankkit"
    jwt_secret: str = "dev-nextauth-secret-change-me"
    allowed_origins: str = "http://localhost:3000"
    local_data_path: str = "data/rankkit-local.json"


settings = Settings()
