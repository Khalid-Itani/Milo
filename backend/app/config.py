"""Server-only configuration. Never print settings or database URLs."""
import os
from pathlib import Path
from dataclasses import dataclass
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

@dataclass(repr=False)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "")
    demo_api_token: str = os.getenv("DEMO_API_TOKEN", "")
    demo_user_id: int = int(os.getenv("DEMO_USER_ID", "1"))
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    anthropic_model: str = os.getenv("ANTHROPIC_MODEL") or os.getenv("COACH_MODEL") or "claude-sonnet-5-5"
    visualize_secret_key: str = os.getenv("VISUALIZE_SECRET_KEY", "")
    visualize_api_base_url: str = os.getenv("VISUALIZE_API_BASE_URL", "https://api.visualizeme.ai")
    visualize_host_user_ref: str = os.getenv("VISUALIZE_HOST_USER_REF", "milo_demo_1")
    app_timezone: str = os.getenv("APP_TIMEZONE", "America/New_York")
    def __post_init__(self):
        ZoneInfo(self.app_timezone)
        if self.demo_user_id < 1:
            raise ValueError("DEMO_USER_ID must be positive")
settings = Settings()
