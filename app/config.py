"""Settings: everything that changes between your laptop and production lives in .env, not in code."""
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    provider: str          # "mock" now; "gemini" arrives in F9
    ai_service_key: str    # shared secret with the NestJS backend ("" = no check, fine for local dev)
    mock_data_dir: Path
    throttle_max_messages: int = 10       # per customer ...
    throttle_window_seconds: float = 60.0  # ... per this many seconds


def load_settings() -> Settings:
    load_dotenv(ROOT / ".env")
    return Settings(
        provider=os.getenv("AI_PROVIDER", "mock").strip().lower(),
        ai_service_key=os.getenv("AI_SERVICE_KEY", "").strip(),
        mock_data_dir=Path(os.getenv("MOCK_DATA_DIR", str(ROOT / "mock_data"))),
        throttle_max_messages=int(os.getenv("THROTTLE_MAX_MESSAGES", "10")),
        throttle_window_seconds=float(os.getenv("THROTTLE_WINDOW_SECONDS", "60")),
    )
