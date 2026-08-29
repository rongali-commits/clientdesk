from __future__ import annotations

from pathlib import Path

import pytest

from clientdesk.config import Settings


def test_production_rejects_short_admin_token(tmp_path: Path) -> None:
    settings = Settings(
        app_env="production",
        admin_token="too-short",
        database_path=tmp_path / "db.sqlite",
        business_file=tmp_path / "business.json",
        seed_demo_data=False,
    )
    with pytest.raises(ValueError, match="24 characters"):
        settings.validate()

