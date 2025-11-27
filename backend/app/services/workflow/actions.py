"""Workflow action base classes and registry"""

import logging
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type

logger = logging.getLogger(__name__)


class BaseAction(ABC):
    """Base class for all workflow actions"""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @property
    @abstractmethod
    def action_type(self) -> str:
        """Return the action type identifier"""
        pass

    @abstractmethod
    async def execute(
        self,
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute the action with given parameters and context

        Args:
            parameters: Action-specific parameters
            context: Workflow execution context with variables

        Returns:
            Dict containing the action result
        """
        pass

    def validate_parameters(self, parameters: Dict[str, Any]) -> None:
        """
        Validate action parameters

        Args:
            parameters: Parameters to validate

        Raises:
            ValueError: If parameters are invalid
        """
        pass

    def resolve_variables(self, value: Any, context: Dict[str, Any]) -> Any:
        """
        Resolve variables in value using context

        Supports {{variable}} syntax for variable substitution

        Args:
            value: Value that may contain variable references
            context: Context with variable values

        Returns:
            Value with variables resolved
        """
        if isinstance(value, str):
            # Find all {{variable}} patterns
            pattern = r'\{\{([^}]+)\}\}'

            def replacer(match):
                var_name = match.group(1).strip()
                # Support nested access like {{response.data.value}}
                parts = var_name.split('.')
                result = context

                try:
                    for part in parts:
                        if isinstance(result, dict):
                            result = result.get(part)
                        elif hasattr(result, part):
                            result = getattr(result, part)
                        else:
                            return match.group(0)  # Return original if not found

                    return str(result) if result is not None else match.group(0)
                except Exception:
                    return match.group(0)  # Return original on error

            return re.sub(pattern, replacer, value)

        elif isinstance(value, dict):
            return {k: self.resolve_variables(v, context) for k, v in value.items()}

        elif isinstance(value, list):
            return [self.resolve_variables(item, context) for item in value]

        return value

    def get_description(self) -> str:
        """Get action description for UI display"""
        return self.__doc__ or f"{self.action_type} action"


class ActionRegistry:
    """Registry for workflow actions"""

    def __init__(self):
        self._actions: Dict[str, Type[BaseAction]] = {}
        self.logger = logging.getLogger(__name__)

    def register(self, action_class: Type[BaseAction]) -> None:
        """
        Register an action class

        Args:
            action_class: Action class to register
        """
        instance = action_class()
        action_type = instance.action_type

        if action_type in self._actions:
            self.logger.warning(f"Overwriting existing action: {action_type}")

        self._actions[action_type] = action_class
        self.logger.info(f"Registered action: {action_type}")

    def get(self, action_type: str) -> Optional[BaseAction]:
        """
        Get an action instance by type

        Args:
            action_type: Type of action to get

        Returns:
            Action instance or None if not found
        """
        action_class = self._actions.get(action_type)
        if action_class:
            return action_class()
        return None

    def list_actions(self) -> Dict[str, str]:
        """
        List all registered actions with descriptions

        Returns:
            Dict mapping action_type to description
        """
        result = {}
        for action_type, action_class in self._actions.items():
            instance = action_class()
            result[action_type] = instance.get_description()
        return result

    def is_registered(self, action_type: str) -> bool:
        """Check if an action type is registered"""
        return action_type in self._actions


# Global action registry instance
action_registry = ActionRegistry()
