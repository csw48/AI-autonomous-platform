"""Tests for configuration"""

from app.core.config import settings


def test_settings_exist():
    """Test that settings are loaded"""
    assert settings is not None
    assert settings.app_name is not None
    assert settings.app_version is not None


def test_settings_defaults():
    """Test default settings values"""
    assert settings.app_version == "0.1.0"
    assert settings.app_name == "AI Autonomous Platform"
    assert settings.log_level == "INFO"
    assert settings.api_port == 8000
