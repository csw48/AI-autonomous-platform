"""Workflow management service"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

from .executor import WorkflowExecutor
from .actions import action_registry
from ...db.models import (
    Workflow,
    WorkflowExecution,
    WorkflowStepExecution,
    WorkflowTemplate
)

logger = logging.getLogger(__name__)


class WorkflowService:
    """Service for managing workflows"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.executor = WorkflowExecutor(db)
        self.logger = logging.getLogger(__name__)

    # Workflow CRUD

    async def create_workflow(
        self,
        name: str,
        steps: List[Dict[str, Any]],
        description: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
        created_by: Optional[str] = None,
        template_id: Optional[int] = None
    ) -> Workflow:
        """Create a new workflow"""

        # Validate steps
        self._validate_workflow_steps(steps)

        workflow = Workflow(
            name=name,
            description=description,
            steps=steps,
            variables=variables,
            created_by=created_by,
            template_id=template_id,
            enabled=True,
            version=1
        )

        self.db.add(workflow)
        await self.db.commit()
        await self.db.refresh(workflow)

        self.logger.info(f"Created workflow {workflow.id}: {name}")
        return workflow

    async def get_workflow(self, workflow_id: int) -> Optional[Workflow]:
        """Get workflow by ID"""
        result = await self.db.execute(
            select(Workflow).where(Workflow.id == workflow_id)
        )
        return result.scalar_one_or_none()

    async def list_workflows(
        self,
        skip: int = 0,
        limit: int = 100,
        enabled_only: bool = False
    ) -> List[Workflow]:
        """List workflows"""
        query = select(Workflow).order_by(desc(Workflow.created_at))

        if enabled_only:
            query = query.where(Workflow.enabled == True)

        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_workflow(
        self,
        workflow_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        steps: Optional[List[Dict[str, Any]]] = None,
        variables: Optional[Dict[str, Any]] = None,
        enabled: Optional[bool] = None
    ) -> Workflow:
        """Update workflow"""
        workflow = await self.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        if name is not None:
            workflow.name = name
        if description is not None:
            workflow.description = description
        if steps is not None:
            self._validate_workflow_steps(steps)
            workflow.steps = steps
            workflow.version += 1
        if variables is not None:
            workflow.variables = variables
        if enabled is not None:
            workflow.enabled = enabled

        await self.db.commit()
        await self.db.refresh(workflow)

        self.logger.info(f"Updated workflow {workflow_id}")
        return workflow

    async def delete_workflow(self, workflow_id: int):
        """Delete workflow"""
        workflow = await self.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        await self.db.delete(workflow)
        await self.db.commit()

        self.logger.info(f"Deleted workflow {workflow_id}")

    # Workflow execution

    async def execute_workflow(
        self,
        workflow_id: int,
        input_data: Optional[Dict[str, Any]] = None
    ) -> WorkflowExecution:
        """Execute a workflow"""
        return await self.executor.execute_workflow(workflow_id, input_data)

    async def get_execution(self, execution_id: int) -> Optional[WorkflowExecution]:
        """Get execution by ID with step details"""
        result = await self.db.execute(
            select(WorkflowExecution)
            .options(selectinload(WorkflowExecution.step_executions))
            .where(WorkflowExecution.id == execution_id)
        )
        return result.scalar_one_or_none()

    async def list_executions(
        self,
        workflow_id: Optional[int] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[WorkflowExecution]:
        """List workflow executions"""
        query = select(WorkflowExecution).order_by(desc(WorkflowExecution.created_at))

        if workflow_id is not None:
            query = query.where(WorkflowExecution.workflow_id == workflow_id)

        if status is not None:
            query = query.where(WorkflowExecution.status == status)

        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def cancel_execution(self, execution_id: int):
        """Cancel a running execution"""
        await self.executor.cancel_execution(execution_id)

    # Templates

    async def create_template(
        self,
        name: str,
        steps: List[Dict[str, Any]],
        description: Optional[str] = None,
        category: Optional[str] = None,
        default_variables: Optional[Dict[str, Any]] = None,
        required_variables: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        author: Optional[str] = None,
        is_public: bool = False
    ) -> WorkflowTemplate:
        """Create a workflow template"""

        # Validate steps
        self._validate_workflow_steps(steps)

        template = WorkflowTemplate(
            name=name,
            description=description,
            category=category,
            steps=steps,
            default_variables=default_variables,
            required_variables=required_variables,
            tags=tags,
            author=author,
            is_public=is_public,
            usage_count=0
        )

        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)

        self.logger.info(f"Created template {template.id}: {name}")
        return template

    async def get_template(self, template_id: int) -> Optional[WorkflowTemplate]:
        """Get template by ID"""
        result = await self.db.execute(
            select(WorkflowTemplate).where(WorkflowTemplate.id == template_id)
        )
        return result.scalar_one_or_none()

    async def list_templates(
        self,
        category: Optional[str] = None,
        public_only: bool = False,
        skip: int = 0,
        limit: int = 100
    ) -> List[WorkflowTemplate]:
        """List workflow templates"""
        query = select(WorkflowTemplate).order_by(desc(WorkflowTemplate.usage_count))

        if category:
            query = query.where(WorkflowTemplate.category == category)

        if public_only:
            query = query.where(WorkflowTemplate.is_public == True)

        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create_workflow_from_template(
        self,
        template_id: int,
        name: str,
        variables: Optional[Dict[str, Any]] = None,
        created_by: Optional[str] = None
    ) -> Workflow:
        """Create a workflow from a template"""
        template = await self.get_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")

        # Merge default variables with provided variables
        workflow_variables = {}
        if template.default_variables:
            workflow_variables.update(template.default_variables)
        if variables:
            workflow_variables.update(variables)

        # Create workflow
        workflow = await self.create_workflow(
            name=name,
            steps=template.steps,
            description=template.description,
            variables=workflow_variables,
            created_by=created_by,
            template_id=template_id
        )

        # Increment template usage count
        template.usage_count += 1
        await self.db.commit()

        self.logger.info(f"Created workflow {workflow.id} from template {template_id}")
        return workflow

    # Utilities

    def _validate_workflow_steps(self, steps: List[Dict[str, Any]]):
        """Validate workflow steps"""
        if not steps:
            raise ValueError("Workflow must have at least one step")

        for i, step in enumerate(steps):
            if "action" not in step:
                raise ValueError(f"Step {i} missing 'action' field")

            action_type = step["action"]
            if not action_registry.is_registered(action_type):
                raise ValueError(f"Unknown action type in step {i}: {action_type}")

            # Validate parameters if action is registered
            action = action_registry.get(action_type)
            if action:
                try:
                    action.validate_parameters(step.get("parameters", {}))
                except ValueError as e:
                    raise ValueError(f"Step {i} validation failed: {e}")

    def list_available_actions(self) -> Dict[str, str]:
        """List all available action types"""
        return action_registry.list_actions()
