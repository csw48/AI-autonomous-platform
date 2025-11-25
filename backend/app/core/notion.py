"""Notion API integration for task tracking"""

import logging
from typing import Optional, Dict, Any
from notion_client import Client
from notion_client.errors import APIResponseError

from .config import settings

logger = logging.getLogger(__name__)


class NotionIntegration:
    """Handles Notion API operations for task tracking"""

    def __init__(self):
        self.client: Optional[Client] = None
        self.database_id = settings.notion_database_id

        if settings.notion_api_key and settings.notion_database_id:
            try:
                self.client = Client(auth=settings.notion_api_key)
                logger.info("Notion integration initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Notion client: {e}")
                self.client = None
        else:
            logger.warning(
                "Notion API key or database ID not provided. "
                "Notion integration will be disabled."
            )

    def is_enabled(self) -> bool:
        """Check if Notion integration is enabled"""
        return self.client is not None

    def update_task_status(self, task_name: str, status: str) -> bool:
        """
        Update task status in Notion database

        Args:
            task_name: Name of the task to update
            status: New status (e.g., "In Progress", "Done", "Completed")

        Returns:
            True if update was successful, False otherwise
        """
        if not self.is_enabled():
            logger.warning(
                f"Notion integration disabled. Cannot update task '{task_name}' to '{status}'"
            )
            return False

        try:
            # Query database for the task
            response = self.client.databases.query(
                database_id=self.database_id,
                filter={
                    "property": "Name",
                    "title": {
                        "contains": task_name
                    }
                }
            )

            if not response.get("results"):
                logger.warning(f"Task '{task_name}' not found in Notion database")
                return False

            # Update the first matching task
            page_id = response["results"][0]["id"]
            self.client.pages.update(
                page_id=page_id,
                properties={
                    "Status": {
                        "status": {
                            "name": status
                        }
                    }
                }
            )

            logger.info(f"Successfully updated task '{task_name}' to status '{status}'")
            return True

        except APIResponseError as e:
            logger.error(f"Notion API error updating task '{task_name}': {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error updating task '{task_name}': {e}")
            return False

    def log_milestone(self, milestone_name: str, details: Dict[str, Any]) -> bool:
        """
        Log milestone completion to Notion

        Args:
            milestone_name: Name of the milestone
            details: Additional details about the milestone

        Returns:
            True if logging was successful, False otherwise
        """
        if not self.is_enabled():
            logger.warning(
                f"Notion integration disabled. Cannot log milestone '{milestone_name}'"
            )
            return False

        try:
            # Create a new page in the database
            self.client.pages.create(
                parent={"database_id": self.database_id},
                properties={
                    "Name": {
                        "title": [
                            {
                                "text": {
                                    "content": f"Milestone: {milestone_name}"
                                }
                            }
                        ]
                    },
                    "Status": {
                        "status": {
                            "name": "Done"
                        }
                    }
                }
            )

            logger.info(f"Successfully logged milestone '{milestone_name}'")
            return True

        except APIResponseError as e:
            logger.error(f"Notion API error logging milestone '{milestone_name}': {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error logging milestone '{milestone_name}': {e}")
            return False


# Global instance
notion = NotionIntegration()
