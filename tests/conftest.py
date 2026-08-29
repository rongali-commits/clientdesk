from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from clientdesk.app import create_app
from clientdesk.config import Settings


@pytest.fixture
def business() -> dict[str, str]:
    return {
        "name": "Test Studio",
        "short_name": "Test",
        "logo_text": "T",
        "tagline": "Clear client work",
        "primary_color": "#18281f",
        "accent_color": "#d8ff70",
        "support_email": "team@example.com",
        "welcome_message": "Everything for your project is organized here.",
        "currency": "USD",
        "privacy_url": "",
    }


def settings(tmp_path: Path, business: dict[str, str], demo: bool = True) -> Settings:
    business_file = tmp_path / "business.json"
    business_file.write_text(json.dumps(business), encoding="utf-8")
    return Settings(
        app_env="development",
        admin_token="test-admin-token-with-enough-length",
        database_path=tmp_path / "clientdesk.db",
        business_file=business_file,
        seed_demo_data=demo,
    )


@pytest.fixture
def demo_client(tmp_path: Path, business: dict[str, str]) -> TestClient:
    return TestClient(create_app(settings(tmp_path, business, demo=True)))


@pytest.fixture
def empty_client(tmp_path: Path, business: dict[str, str]) -> TestClient:
    return TestClient(create_app(settings(tmp_path, business, demo=False)))


@pytest.fixture
def admin_headers() -> dict[str, str]:
    return {"X-Admin-Token": "test-admin-token-with-enough-length"}

