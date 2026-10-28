from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


ENV_FILE = Path(__file__).with_name(".env")


class Settings(BaseSettings):
    """Runtime settings loaded from AIWORLD_* environment variables."""

    app_name: str = "AI World"
    app_version: str = "0.1.0"
    environment: str = "development"
    database_url: str = "sqlite+aiosqlite:///./data/local.sqlite3"
    log_level: str = "INFO"
    llm_model: str = "deepseek-chat"

    model_config = SettingsConfigDict(
        env_prefix="AIWORLD_",
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()


def ensure_runtime_directories(root: Path | None = None) -> None:
    """Create local runtime directories without touching production paths."""
    base = root or Path.cwd()
    for name in ("data", "logs", "backups"):
        (base / name).mkdir(parents=True, exist_ok=True)
