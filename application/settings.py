from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = ["settings", "Settings"]


class Settings(BaseSettings):
    # Telegram
    api_id: int
    api_hash: str

    # Parser
    delay: int = 1  # sec
    channels_dir: Path = Path("./data/channels")
    sessions_dir: Path = Path("./data/sessions")

    downloads_retry: int = 5
    need_remove_folder: bool = False

    # S3
    s3_needs: bool = False
    s3_endpoint_url: str | None
    s3_bucket: str | None
    s3_access_key_id: str | None
    s3_secret_access_key: str | None
    s3_region: str | None = "us-east-1"
    s3_uploading_retry: int = 5

    model_config = SettingsConfigDict(case_sensitive=False, extra="ignore")


settings = Settings()

settings.sessions_dir.mkdir(parents=True, exist_ok=True)
settings.channels_dir.mkdir(parents=True, exist_ok=True)
