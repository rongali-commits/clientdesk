from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

PACKAGE_DIR = Path(__file__).parent
PROJECT_DIR = PACKAGE_DIR.parent.parent


@dataclass(frozen=True)
class Settings:
    app_env: str
    admin_token: str
    database_path: Path
    business_file: Path
    seed_demo_data: bool

    @classmethod
    def from_env(cls) -> Settings:
        load_dotenv()
        app_env = os.getenv("APP_ENV", "development").strip().lower()
        return cls(
            app_env=app_env,
            admin_token=os.getenv("ADMIN_TOKEN", "development-admin-token"),
            database_path=Path(
                os.getenv("DATABASE_PATH", str(PROJECT_DIR / "runtime" / "clientdesk.db"))
            ),
            business_file=Path(
                os.getenv("BUSINESS_FILE", str(PROJECT_DIR / "data" / "business.json"))
            ),
            seed_demo_data=os.getenv("SEED_DEMO_DATA", "true").lower()
            in {"1", "true", "yes"},
        )

    def validate(self) -> None:
        if self.app_env == "production" and len(self.admin_token) < 24:
            raise ValueError("ADMIN_TOKEN must contain at least 24 characters in production")
        self.database_path.parent.mkdir(parents=True, exist_ok=True)

    def load_business(self) -> dict[str, Any]:
        if not self.business_file.exists():
            fallback = PACKAGE_DIR / "defaults" / "business.json"
            if fallback.exists():
                return json.loads(fallback.read_text(encoding="utf-8"))
            raise FileNotFoundError(f"Business configuration not found: {self.business_file}")
        return json.loads(self.business_file.read_text(encoding="utf-8"))

