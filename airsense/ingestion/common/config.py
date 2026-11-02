from pathlib import Path
import os
import yaml
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

def get_setting(name: str, default: str | None = None) -> str | None:
    return os.getenv(name, default)

def load_cities() -> list[dict]:
    path = PROJECT_ROOT / "config" / "cities.yaml"
    with path.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}
    return [city for city in config.get("cities", []) if city.get("enabled", True)]
