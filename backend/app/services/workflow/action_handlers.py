"""Workflow action handlers"""

import logging
import httpx
from typing import Any, Dict, Optional

from .actions import BaseAction, action_registry
from ..llm_service import llm_service
from ..indexing_service import indexing_service
from ..notion_service import notion_service

logger = logging.getLogger(__name__)


class LLMQueryAction(BaseAction):
    """Query LLM with a prompt"""

    @property
    def action_type(self) -> str:
        return "llm_query"

    def validate_parameters(self, parameters: Dict[str, Any]) -> None:
        """Validate LLM query parameters"""
        if "prompt" not in parameters:
            raise ValueError("LLM query action requires 'prompt' parameter")

    async def execute(
        self,
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute LLM query

        Parameters:
            - prompt (str): The prompt to send to the LLM
            - system_prompt (str, optional): System prompt for the LLM
            - temperature (float, optional): Temperature for generation (0.0-1.0)
            - max_tokens (int, optional): Maximum tokens to generate

        Returns:
            Dict with 'response' key containing the LLM response
        """
        self.validate_parameters(parameters)

        # Resolve variables in prompt
        prompt = self.resolve_variables(parameters["prompt"], context)
        system_prompt = self.resolve_variables(
            parameters.get("system_prompt", "You are a helpful AI assistant."),
            context
        )
        temperature = parameters.get("temperature", 0.7)
        max_tokens = parameters.get("max_tokens", 1000)

        self.logger.info(f"Executing LLM query with prompt: {prompt[:100]}...")

        try:
            response = await llm_service.generate_response(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )

            return {
                "response": response,
                "tokens_used": len(response.split())  # Approximate
            }

        except Exception as e:
            self.logger.error(f"LLM query failed: {e}")
            raise


class DocumentSearchAction(BaseAction):
    """Search documents using vector similarity"""

    @property
    def action_type(self) -> str:
        return "doc_search"

    def validate_parameters(self, parameters: Dict[str, Any]) -> None:
        """Validate document search parameters"""
        if "query" not in parameters:
            raise ValueError("Document search action requires 'query' parameter")

    async def execute(
        self,
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute document search

        Parameters:
            - query (str): Search query
            - limit (int, optional): Maximum number of results (default: 5)
            - min_similarity (float, optional): Minimum similarity threshold (default: 0.7)

        Returns:
            Dict with 'results' containing list of matching documents
        """
        self.validate_parameters(parameters)

        query = self.resolve_variables(parameters["query"], context)
        limit = parameters.get("limit", 5)
        min_similarity = parameters.get("min_similarity", 0.7)

        self.logger.info(f"Searching documents for: {query}")

        try:
            results = await indexing_service.search_documents(
                query=query,
                limit=limit,
                min_similarity=min_similarity
            )

            return {
                "results": results,
                "count": len(results)
            }

        except Exception as e:
            self.logger.error(f"Document search failed: {e}")
            raise


class NotionUpdateAction(BaseAction):
    """Update Notion database entry"""

    @property
    def action_type(self) -> str:
        return "notion_update"

    def validate_parameters(self, parameters: Dict[str, Any]) -> None:
        """Validate Notion update parameters"""
        if "task_id" not in parameters or "properties" not in parameters:
            raise ValueError("Notion update action requires 'task_id' and 'properties' parameters")

    async def execute(
        self,
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute Notion update

        Parameters:
            - task_id (str): Notion task ID to update
            - properties (dict): Properties to update

        Returns:
            Dict with update status
        """
        self.validate_parameters(parameters)

        task_id = self.resolve_variables(parameters["task_id"], context)
        properties = self.resolve_variables(parameters["properties"], context)

        self.logger.info(f"Updating Notion task: {task_id}")

        try:
            await notion_service.update_task(task_id, properties)

            return {
                "status": "success",
                "task_id": task_id,
                "updated_properties": list(properties.keys())
            }

        except Exception as e:
            self.logger.error(f"Notion update failed: {e}")
            raise


class HTTPRequestAction(BaseAction):
    """Make HTTP request"""

    @property
    def action_type(self) -> str:
        return "http_request"

    def validate_parameters(self, parameters: Dict[str, Any]) -> None:
        """Validate HTTP request parameters"""
        if "url" not in parameters:
            raise ValueError("HTTP request action requires 'url' parameter")
        if "method" not in parameters:
            raise ValueError("HTTP request action requires 'method' parameter")

    async def execute(
        self,
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute HTTP request

        Parameters:
            - url (str): Request URL
            - method (str): HTTP method (GET, POST, PUT, DELETE, etc.)
            - headers (dict, optional): Request headers
            - body (dict, optional): Request body (for POST/PUT)
            - timeout (int, optional): Request timeout in seconds (default: 30)

        Returns:
            Dict with response data
        """
        self.validate_parameters(parameters)

        url = self.resolve_variables(parameters["url"], context)
        method = parameters["method"].upper()
        headers = self.resolve_variables(parameters.get("headers", {}), context)
        body = self.resolve_variables(parameters.get("body"), context)
        timeout = parameters.get("timeout", 30)

        self.logger.info(f"Making {method} request to {url}")

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                if method == "GET":
                    response = await client.get(url, headers=headers)
                elif method == "POST":
                    response = await client.post(url, headers=headers, json=body)
                elif method == "PUT":
                    response = await client.put(url, headers=headers, json=body)
                elif method == "DELETE":
                    response = await client.delete(url, headers=headers)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                response.raise_for_status()

                # Try to parse JSON response
                try:
                    response_data = response.json()
                except Exception:
                    response_data = response.text

                return {
                    "status_code": response.status_code,
                    "data": response_data,
                    "headers": dict(response.headers)
                }

        except Exception as e:
            self.logger.error(f"HTTP request failed: {e}")
            raise


class DataTransformAction(BaseAction):
    """Transform data using Python expressions"""

    @property
    def action_type(self) -> str:
        return "data_transform"

    def validate_parameters(self, parameters: Dict[str, Any]) -> None:
        """Validate data transform parameters"""
        if "operations" not in parameters:
            raise ValueError("Data transform action requires 'operations' parameter")

    async def execute(
        self,
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute data transformation

        Parameters:
            - operations (list): List of transformation operations
              Each operation is a dict with:
                - type: 'extract', 'filter', 'map', 'combine'
                - source: Variable name to transform
                - target: Variable name for result
                - expression: Transformation expression

        Returns:
            Dict with transformed data
        """
        self.validate_parameters(parameters)

        operations = parameters["operations"]
        result = {}

        self.logger.info(f"Executing {len(operations)} data transformations")

        try:
            for op in operations:
                op_type = op.get("type")
                source = op.get("source")
                target = op.get("target")

                if op_type == "extract":
                    # Extract field from source
                    path = op.get("path", "").split(".")
                    data = context.get(source)

                    for part in path:
                        if isinstance(data, dict):
                            data = data.get(part)
                        elif isinstance(data, list) and part.isdigit():
                            data = data[int(part)]
                        else:
                            data = None
                            break

                    result[target] = data

                elif op_type == "filter":
                    # Filter list based on condition
                    source_data = context.get(source, [])
                    condition = op.get("condition", "")

                    # Simple filtering (can be extended)
                    filtered = []
                    for item in source_data:
                        # Basic condition evaluation
                        if self._evaluate_condition(item, condition):
                            filtered.append(item)

                    result[target] = filtered

                elif op_type == "map":
                    # Map over list
                    source_data = context.get(source, [])
                    field = op.get("field")

                    mapped = [item.get(field) if isinstance(item, dict) else item
                             for item in source_data]

                    result[target] = mapped

                elif op_type == "combine":
                    # Combine multiple sources
                    sources = op.get("sources", [])
                    combined = {}

                    for src in sources:
                        data = context.get(src)
                        if isinstance(data, dict):
                            combined.update(data)

                    result[target] = combined

            return result

        except Exception as e:
            self.logger.error(f"Data transformation failed: {e}")
            raise

    def _evaluate_condition(self, item: Any, condition: str) -> bool:
        """
        Simple condition evaluator (can be extended)

        Currently supports basic comparisons
        """
        # For now, return True (can be extended with safe eval)
        return True


# Register all actions
action_registry.register(LLMQueryAction)
action_registry.register(DocumentSearchAction)
action_registry.register(NotionUpdateAction)
action_registry.register(HTTPRequestAction)
action_registry.register(DataTransformAction)
