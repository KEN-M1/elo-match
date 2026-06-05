from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://rankkit:rankkit@localhost:5432/rankkit"
    environment: str = "local"
    jwt_secret: str = "dev-nextauth-secret-change-me"
    allowed_origins: str = "http://localhost:3000"
    local_data_path: str = "data/rankkit-local.json"
    store_backend: str = "local"

    def validate_for_runtime(self) -> None:
        if self.store_backend not in {"local", "postgres"}:
            raise ValueError("STORE_BACKEND must be 'local' or 'postgres'.")

        if self.environment.lower() not in {"production", "prod"}:
            return

        if self.store_backend != "postgres":
            raise ValueError("STORE_BACKEND must be 'postgres' in production.")

        if self.jwt_secret == "dev-nextauth-secret-change-me" or len(self.jwt_secret) < 32:
            raise ValueError("JWT_SECRET must be set to a production secret with at least 32 characters.")


settings = Settings()
