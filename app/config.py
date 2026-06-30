import os
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./steam_tracker.db"
    STEAM_CURRENCY: int = 7
    COLLECTOR_DELAY_SECONDS: float = 5.0
    COLLECTOR_REFRESH_HOURS: int = 12
    COLLECTOR_MAX_RETRIES: int = 3
    COLLECTOR_BACKOFF_FACTOR: float = 3.0
    COLLECTOR_BASE_INTERVAL_MINUTES: int = 5
    LOG_LEVEL: str = "INFO"
    BASE_DIR: Path = Path(__file__).resolve().parent.parent

    SAVE_SOURCE_PATH: str = ""
    SAVE_DEST_PATH: str = ""
    SAVE_WATCHER_COOLDOWN_SECONDS: float = 5.0
    SAVE_WATCHER_POLL_INTERVAL: float = 10.0

    TBH_APPID: int = 3678970

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def save_source_path(self) -> Path:
        if self.SAVE_SOURCE_PATH:
            return Path(self.SAVE_SOURCE_PATH)
        return (
            Path(os.environ["USERPROFILE"])
            / "AppData" / "LocalLow" / "TesseractStudio" / "TaskbarHero" / "SaveFile_Live.es3"
        )

    @property
    def save_dest_path(self) -> Path:
        if self.SAVE_DEST_PATH:
            return Path(self.SAVE_DEST_PATH)
        return self.BASE_DIR / "SaveFile_Live.es3"


settings = Settings()
