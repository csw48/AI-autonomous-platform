"""Tests for Notion integration"""

import pytest
from unittest.mock import Mock, patch

from app.core.notion import NotionIntegration


def test_notion_integration_disabled_without_credentials():
    """Test that Notion integration is disabled without credentials"""
    with patch("app.core.notion.settings") as mock_settings:
        mock_settings.notion_api_key = ""
        mock_settings.notion_database_id = ""

        notion = NotionIntegration()

        assert not notion.is_enabled()


def test_update_task_status_disabled():
    """Test that update_task_status returns False when disabled"""
    with patch("app.core.notion.settings") as mock_settings:
        mock_settings.notion_api_key = ""
        mock_settings.notion_database_id = ""

        notion = NotionIntegration()
        result = notion.update_task_status("Test Task", "Done")

        assert result is False


def test_log_milestone_disabled():
    """Test that log_milestone returns False when disabled"""
    with patch("app.core.notion.settings") as mock_settings:
        mock_settings.notion_api_key = ""
        mock_settings.notion_database_id = ""

        notion = NotionIntegration()
        result = notion.log_milestone("Test Milestone", {"detail": "test"})

        assert result is False
