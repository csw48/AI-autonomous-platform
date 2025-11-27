"""Workflow execution engine"""

import logging
import asyncio
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .actions import action_registry
from ...db.models import Workflow, WorkflowExecution, WorkflowStepExecution

logger = logging.getLogger(__name__)


class WorkflowExecutor:
    """Executes workflows step by step"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.logger = logging.getLogger(__name__)

    async def execute_workflow(
        self,
        workflow_id: int,
        input_data: Optional[Dict[str, Any]] = None
    ) -> WorkflowExecution:
        """
        Execute a workflow

        Args:
            workflow_id: ID of the workflow to execute
            input_data: Input variables for the workflow

        Returns:
            WorkflowExecution instance with results
        """
        # Get workflow
        result = await self.db.execute(
            select(Workflow).where(Workflow.id == workflow_id)
        )
        workflow = result.scalar_one_or_none()

        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        if not workflow.enabled:
            raise ValueError(f"Workflow {workflow_id} is disabled")

        # Create execution instance
        execution = WorkflowExecution(
            workflow_id=workflow_id,
            status="pending",
            input_data=input_data or {},
            context={}
        )
        self.db.add(execution)
        await self.db.commit()
        await self.db.refresh(execution)

        self.logger.info(f"Starting workflow execution {execution.id} for workflow {workflow_id}")

        # Initialize context with input data and workflow variables
        context = {}
        if workflow.variables:
            context.update(workflow.variables)
        if input_data:
            context.update(input_data)

        # Update execution status
        execution.status = "running"
        execution.started_at = datetime.utcnow()
        await self.db.commit()

        try:
            # Execute each step
            for step_index, step in enumerate(workflow.steps):
                self.logger.info(f"Executing step {step_index}: {step.get('name', 'unnamed')}")

                # Check if step should be executed based on condition
                if not self._should_execute_step(step, context):
                    self.logger.info(f"Skipping step {step_index} due to condition")
                    await self._record_step_skipped(execution.id, step_index, step)
                    continue

                # Execute the step
                try:
                    step_result = await self._execute_step(
                        execution.id,
                        step_index,
                        step,
                        context
                    )

                    # Update context with step result
                    output_var = step.get("output_variable", f"step_{step_index}_output")
                    context[output_var] = step_result

                    # Update execution context
                    execution.context = context
                    execution.current_step = step_index + 1
                    await self.db.commit()

                except Exception as step_error:
                    self.logger.error(f"Step {step_index} failed: {step_error}")
                    execution.status = "failed"
                    execution.error_message = str(step_error)
                    execution.error_step = step_index
                    execution.completed_at = datetime.utcnow()

                    if execution.started_at:
                        duration = (execution.completed_at - execution.started_at).total_seconds() * 1000
                        execution.duration_ms = int(duration)

                    await self.db.commit()
                    raise

            # Workflow completed successfully
            execution.status = "completed"
            execution.output_data = context
            execution.completed_at = datetime.utcnow()

            if execution.started_at:
                duration = (execution.completed_at - execution.started_at).total_seconds() * 1000
                execution.duration_ms = int(duration)

            await self.db.commit()

            self.logger.info(f"Workflow execution {execution.id} completed successfully")
            return execution

        except Exception as e:
            self.logger.error(f"Workflow execution {execution.id} failed: {e}")
            raise

    async def _execute_step(
        self,
        execution_id: int,
        step_index: int,
        step: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Any:
        """Execute a single workflow step"""

        action_type = step.get("action")
        if not action_type:
            raise ValueError(f"Step {step_index} missing 'action' field")

        # Get action handler
        action = action_registry.get(action_type)
        if not action:
            raise ValueError(f"Unknown action type: {action_type}")

        # Create step execution record
        step_execution = WorkflowStepExecution(
            execution_id=execution_id,
            step_index=step_index,
            step_name=step.get("name"),
            action_type=action_type,
            status="running",
            parameters=step.get("parameters", {}),
            started_at=datetime.utcnow()
        )
        self.db.add(step_execution)
        await self.db.commit()
        await self.db.refresh(step_execution)

        try:
            # Validate parameters
            parameters = step.get("parameters", {})
            action.validate_parameters(parameters)

            # Execute action
            result = await action.execute(parameters, context)

            # Update step execution
            step_execution.status = "completed"
            step_execution.output_data = result
            step_execution.completed_at = datetime.utcnow()

            if step_execution.started_at:
                duration = (step_execution.completed_at - step_execution.started_at).total_seconds() * 1000
                step_execution.duration_ms = int(duration)

            await self.db.commit()

            return result

        except Exception as e:
            step_execution.status = "failed"
            step_execution.error_message = str(e)
            step_execution.completed_at = datetime.utcnow()

            if step_execution.started_at:
                duration = (step_execution.completed_at - step_execution.started_at).total_seconds() * 1000
                step_execution.duration_ms = int(duration)

            await self.db.commit()
            raise

    async def _record_step_skipped(
        self,
        execution_id: int,
        step_index: int,
        step: Dict[str, Any]
    ):
        """Record a skipped step"""
        step_execution = WorkflowStepExecution(
            execution_id=execution_id,
            step_index=step_index,
            step_name=step.get("name"),
            action_type=step.get("action", "unknown"),
            status="skipped",
            parameters=step.get("parameters", {})
        )
        self.db.add(step_execution)
        await self.db.commit()

    def _should_execute_step(
        self,
        step: Dict[str, Any],
        context: Dict[str, Any]
    ) -> bool:
        """
        Check if a step should be executed based on conditions

        Args:
            step: Step configuration
            context: Current execution context

        Returns:
            True if step should be executed
        """
        condition = step.get("condition")
        if not condition:
            return True

        # Simple condition evaluation
        # Format: "variable == value" or "variable != value" or "variable exists"
        try:
            if " == " in condition:
                var_name, expected = condition.split(" == ", 1)
                var_name = var_name.strip()
                expected = expected.strip().strip('"\'')
                return str(context.get(var_name)) == expected

            elif " != " in condition:
                var_name, expected = condition.split(" != ", 1)
                var_name = var_name.strip()
                expected = expected.strip().strip('"\'')
                return str(context.get(var_name)) != expected

            elif " exists" in condition:
                var_name = condition.replace(" exists", "").strip()
                return var_name in context and context[var_name] is not None

            else:
                # Default: check if variable is truthy
                return bool(context.get(condition.strip()))

        except Exception as e:
            self.logger.warning(f"Condition evaluation failed: {e}, executing step")
            return True

    async def cancel_execution(self, execution_id: int):
        """Cancel a running workflow execution"""
        result = await self.db.execute(
            select(WorkflowExecution).where(WorkflowExecution.id == execution_id)
        )
        execution = result.scalar_one_or_none()

        if not execution:
            raise ValueError(f"Execution {execution_id} not found")

        if execution.status not in ["pending", "running"]:
            raise ValueError(f"Cannot cancel execution in status: {execution.status}")

        execution.status = "cancelled"
        execution.completed_at = datetime.utcnow()

        if execution.started_at:
            duration = (execution.completed_at - execution.started_at).total_seconds() * 1000
            execution.duration_ms = int(duration)

        await self.db.commit()

        self.logger.info(f"Cancelled execution {execution_id}")
