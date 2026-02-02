"""Unit tests for services."""
import pytest
from app.core.config import settings
from app.workflows.activities.planning import _calculate_time


class TestSettings:
    def test_settings_loaded(self):
        assert settings.DATABASE_URL is not None
        assert settings.TEMPORAL_HOST is not None


class TestPlanningHelpers:
    def test_calculate_time_small_repo(self):
        info = {"size": 500}
        t = _calculate_time(info)
        assert 30 <= t <= 300

    def test_calculate_time_large_repo(self):
        info = {"size": 50000}
        t = _calculate_time(info)
        assert t >= 60  # large repos take more time
