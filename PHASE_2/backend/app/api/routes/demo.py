"""Demo API routes.

POST /api/demo/load  - load the validated workbook into session storage
POST /api/demo/reset - clear demo sessions
"""

from fastapi import APIRouter, HTTPException

from app.api.models import ApiResponse, ErrorCodes, ProjectSummary, UploadResponse, ValidationIssue
from app.core.config import settings
from app.domain.models import SprintStatus
from app.parsers import WorkbookParseError, WorkbookParser
from app.storage import store
from app.validators import ValidationError as ValidatorError, WorkbookValidator


router = APIRouter(prefix="/api/demo", tags=["Demo"])


@router.post("/load")
async def load_demo_workbook():
    """Load the validated demo workbook into session storage."""

    try:
        parser = WorkbookParser(settings.demo_workbook_path)
        project_state = parser.parse()
        validator = WorkbookValidator(project_state)
        warnings = validator.validate()
    except WorkbookParseError as e:
        raise HTTPException(
            status_code=400,
            detail=ApiResponse(
                success=False,
                error_code=ErrorCodes.PARSE_ERROR,
                message=f"Failed to load demo workbook: {str(e)}",
            ).model_dump(),
        )
    except ValidatorError as e:
        raise HTTPException(
            status_code=400,
            detail=ApiResponse(
                success=False,
                error_code=ErrorCodes.VALIDATION_ERROR,
                message=f"Demo workbook validation failed: {str(e)}",
            ).model_dump(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ApiResponse(
                success=False,
                error_code=ErrorCodes.INTERNAL_ERROR,
                message=f"Error loading demo workbook: {str(e)}",
            ).model_dump(),
        )

    session_id = store.create_session(project_state)
    completed_sprints = sum(1 for sprint in project_state.sprints if sprint.status == SprintStatus.COMPLETED)

    project_summary = ProjectSummary(
        session_id=session_id,
        project_name=project_state.project_info.project_name,
        project_manager=project_state.project_info.project_manager,
        customer=project_state.project_info.customer,
        start_date=project_state.project_info.start_date,
        target_end_date=project_state.project_info.target_end_date,
        total_sprints=len(project_state.sprints),
        total_work_items=len(project_state.work_items),
        total_resources=len(project_state.team),
        total_dependencies=len(project_state.dependencies),
        total_blockers=len(project_state.blockers),
        completed_sprints=completed_sprints,
    )

    response = UploadResponse(
        session_id=session_id,
        project_summary=project_summary,
        validation_warnings=[ValidationIssue(**warning.to_dict()) for warning in warnings],
    )

    return ApiResponse(success=True, data=response.model_dump(), message="Demo workbook loaded")


@router.post("/reset")
async def reset_demo():
    """Clear all sessions so the demo can restart from a clean state."""

    store.clear_all()
    return ApiResponse(success=True, message="Demo sessions cleared", data={"reset": True})