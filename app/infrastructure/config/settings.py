from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # App
    APP_NAME: str = "FishInventoryAPI"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "API de Inventario para Negocio de Compra y Venta de Pescado"
    DEBUG: bool = False

    # Database
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_NAME: str = "fish_inventory_db"
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_SSL_CA: str = ""          # <-- NUEVO

    # JWT
    JWT_SECRET: str = "change_me_to_a_very_long_secret_key_in_production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_EXPIRE_DAYS: int = 7

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            f"?charset=utf8mb4"
        )

    @property
    def database_url_alembic(self) -> str:
        return self.database_url

    @property                     # <-- NUEVO
    def db_connect_args(self) -> dict:
        if not self.DB_SSL_CA:
            return {}
        # settings.py está en app/infrastructure/config/ -> la raíz está 3 niveles arriba
        project_root = Path(__file__).resolve().parents[3]
        ca_path = (project_root / self.DB_SSL_CA).resolve()
        return {"ssl": {"ca": str(ca_path)}}


@lru_cache
def get_settings() -> Settings:
    return Settings()