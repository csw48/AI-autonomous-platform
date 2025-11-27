"""Workflow management and execution endpoints"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.db.session import get_db
from app.services.workflow.workflow_service import WorkflowService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workflows", tags=["workflows"])


# Schemas

class WorkflowStepSchema(BaseModel):
    """Schema for a workflow step"""
    name: Optional[str] = None
    action: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    output_variable: Optional[str] = None
    condition: Optional[str] = None


class WorkflowCreateRequest(BaseModel):
    """Request to create a workflow"""
    name: str
    description: Optional[str] = None
    steps: List[WorkflowStepSchema]
    variables: Optional[Dict[str, Any]] = None
    created_by: Optional[str] = None
    template_id: Optional[int] = None


class WorkflowUpdateRequest(BaseModel):
    """Request to update a workflow"""
    name: Optional[str] = None
    description: Optional[str] = None
    steps: Optional[List[WorkflowStepSchema]] = None
    variables: Optional[Dict[str, Any]] = None
    enabled: Optional[bool] = None


class WorkflowResponse(BaseModel):
    """Response for a workflow"""
    id: int
    name: str
    description: Optional[str]
    steps: List[Dict[str, Any]]
    variables: Optional[Dict[str, Any]]
    enabled: bool
    version: int
    created_by: Optional[str]
    template_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WorkflowExecuteRequest(BaseModel):
    """Request to execute a workflow"""
    input_data: Optional[Dict[str, Any]] = None


class WorkflowExecutionResponse(BaseModel):
    """Response for workflow execution"""
    id: int
    workflow_id: int
    status: str
    current_step: int
    input_data: Optional[Dict[str, Any]]
    output_data: Optional[Dict[str, Any]]
    context: Optional[Dict[str, Any]]
    error_message: Optional[str]
    error_step: Optional[int]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_ms: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class WorkflowTemplateCreateRequest(BaseModel):
    """Request to create a workflow template"""
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    steps: List[WorkflowStepSchema]
    default_variables: Optional[Dict[str, Any]] = None
    required_variables: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    author: Optional[str] = None
    is_public: bool = False


class WorkflowTemplateResponse(BaseModel):
    """Response for a workflow template"""
    id: int
    name: str
    description: Optional[str]
    category: Optional[str]
    steps: List[Dict[str, Any]]
    default_variables: Optional[Dict[str, Any]]
    required_variables: Optional[List[str]]
    tags: Optional[List[str]]
    author: Optional[str]
    is_public: bool
    usage_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class WorkflowFromTemplateRequest(BaseModel):
    """Request to create workflow from template"""
    name: str
    variables: Optional[Dict[str, Any]] = None
    created_by: Optional[str] = None


class ActionListResponse(BaseModel):
    """Response for available actions"""
    actions: Dict[str, str]


# Workflow endpoints

@router.post("/", response_model=WorkflowResponse)
async def create_workflow(
    workflow: WorkflowCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create a new workflow"""
    try:
        service = WorkflowService(db)

        # Convert Pydantic models to dicts
        steps = [step.model_dump() for step in workflow.steps]

        result = await service.create_workflow(
            name=workflow.name,
            description=workflow.description,
            steps=steps,
            variables=workflow.variables,
            created_by=workflow.created_by,
            template_id=workflow.template_id
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[WorkflowResponse])
async def list_workflows(
    skip: int = 0,
    limit: int = 100,
    enabled_only: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """List all workflows"""
    try:
        service = WorkflowService(db)
        workflows = await service.list_workflows(
            skip=skip,
            limit=limit,
            enabled_only=enabled_only
        )
        return workflows

    except Exception as e:
        logger.error(f"Failed to list workflows: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get workflow by ID"""
    try:
        service = WorkflowService(db)
        workflow = await service.get_workflow(workflow_id)

        if not workflow:
            raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")

        return workflow

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: int,
    update: WorkflowUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Update workflow"""
    try:
        service = WorkflowService(db)

        # Convert steps to dict if provided
        steps = None
        if update.steps is not None:
            steps = [step.model_dump() for step in update.steps]

        workflow = await service.update_workflow(
            workflow_id=workflow_id,
            name=update.name,
            description=update.description,
            steps=steps,
            variables=update.variables,
            enabled=update.enabled
        )

        return workflow

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{workflow_id}")
async def delete_workflow(
    workflow_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete workflow"""
    try:
        service = WorkflowService(db)
        await service.delete_workflow(workflow_id)
        return {"message": f"Workflow {workflow_id} deleted successfully"}

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to delete workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Execution endpoints

@router.post("/{workflow_id}/execute", response_model=WorkflowExecutionResponse)
async def execute_workflow(
    workflow_id: int,
    request: WorkflowExecuteRequest,
    db: AsyncSession = Depends(get_db)
):
    """Execute a workflow"""
    try:
        service = WorkflowService(db)
        execution = await service.execute_workflow(
            workflow_id=workflow_id,
            input_data=request.input_data
        )
        return execution

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to execute workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/executions/{execution_id}", response_model=WorkflowExecutionResponse)
async def get_execution(
    execution_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get execution status and results"""
    try:
        service = WorkflowService(db)
        execution = await service.get_execution(execution_id)

        if not execution:
            raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")

        return execution

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get execution: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/executions/", response_model=List[WorkflowExecutionResponse])
async def list_executions(
    workflow_id: Optional[int] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """List workflow executions"""
    try:
        service = WorkflowService(db)
        executions = await service.list_executions(
            workflow_id=workflow_id,
            status=status,
            skip=skip,
            limit=limit
        )
        return executions

    except Exception as e:
        logger.error(f"Failed to list executions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/executions/{execution_id}/cancel")
async def cancel_execution(
    execution_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Cancel a running execution"""
    try:
        service = WorkflowService(db)
        await service.cancel_execution(execution_id)
        return {"message": f"Execution {execution_id} cancelled"}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to cancel execution: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Template endpoints

@router.post("/templates/", response_model=WorkflowTemplateResponse)
async def create_template(
    template: WorkflowTemplateCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create a workflow template"""
    try:
        service = WorkflowService(db)

        # Convert steps to dict
        steps = [step.model_dump() for step in template.steps]

        result = await service.create_template(
            name=template.name,
            description=template.description,
            category=template.category,
            steps=steps,
            default_variables=template.default_variables,
            required_variables=template.required_variables,
            tags=template.tags,
            author=template.author,
            is_public=template.is_public
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates/", response_model=List[WorkflowTemplateResponse])
async def list_templates(
    category: Optional[str] = None,
    public_only: bool = False,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """List workflow templates"""
    try:
        service = WorkflowService(db)
        templates = await service.list_templates(
            category=category,
            public_only=public_only,
            skip=skip,
            limit=limit
        )
        return templates

    except Exception as e:
        logger.error(f"Failed to list templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates/{template_id}", response_model=WorkflowTemplateResponse)
async def get_template(
    template_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get template by ID"""
    try:
        service = WorkflowService(db)
        template = await service.get_template(template_id)

        if not template:
            raise HTTPException(status_code=404, detail=f"Template {template_id} not found")

        return template

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/templates/{template_id}/create-workflow", response_model=WorkflowResponse)
async def create_workflow_from_template(
    template_id: int,
    request: WorkflowFromTemplateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create a workflow from a template"""
    try:
        service = WorkflowService(db)
        workflow = await service.create_workflow_from_template(
            template_id=template_id,
            name=request.name,
            variables=request.variables,
            created_by=request.created_by
        )
        return workflow

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create workflow from template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Utility endpoints

@router.get("/actions/list", response_model=ActionListResponse)
async def list_actions(db: AsyncSession = Depends(get_db)):
    """List all available workflow actions"""
    try:
        service = WorkflowService(db)
        actions = service.list_available_actions()
        return ActionListResponse(actions=actions)

    except Exception as e:
        logger.error(f"Failed to list actions: {e}")
        raise HTTPException(status_code=500, detail=str(e))
