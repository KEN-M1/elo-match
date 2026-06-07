from urllib.parse import quote

from pydantic_settings import BaseSettings, SettingsConfigDict


DEFAULT_DATABASE_URL = "postgresql+asyncpg://rankkit:rankkit@localhost:5432/rankkit"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = DEFAULT_DATABASE_URL
    database_host: str | None = None
    database_port: int = 5432
    database_name: str | None = None
    database_user: str | None = None
    database_password: str | None = None
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

        if self.effective_database_url() == DEFAULT_DATABASE_URL:
            raise ValueError("DATABASE_URL must be set for production Postgres runtime.")

    def effective_database_url(self) -> str:
        components = [
            self.database_host,
            self.database_name,
            self.database_user,
            self.database_password,
        ]
        if not any(components):
            return self.database_url
        if not all(components):
            raise ValueError(
                "Database component settings require DATABASE_HOST, DATABASE_NAME, "
                "DATABASE_USER, and DATABASE_PASSWORD."
            )

        user = quote(self.database_user or "", safe="")
        password = quote(self.database_password or "", safe="")
        return (
            f"postgresql+asyncpg://{user}:{password}@"
            f"{self.database_host}:{self.database_port}/{self.database_name}"
        )


settings = Settings()
