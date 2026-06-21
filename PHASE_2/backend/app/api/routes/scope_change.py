"""Scope change API routes.

POST /api/scope-change - apply a scope reduction to one or more work items.
"""

from fastapi import APIRouter, HTTPException, Query

from app.api.models import ApiResponse, ErrorCodes
from app.api.models_phase3 import ScopeChangeRequest, ScopeChangeResponse
from app.domain.models import WorkItemStatus
from app.engines.critical_path_engine import CriticalPathEngine
from app.engines.dependency_engine import DependencyGraphEngine
from app.engines.forecast_engine import ForecastEngine
from app.engines.impact_scoring_engine import ImpactScoringEngine
from app.engines.metrics_engine import MetricsEngine
from app.engines.monte_carlo_engine import MonteCarloEngine
from app.engines.risk_engine import RiskEngine
from app.engines.spillover_engine import SpilloverAnalysisEngine
from app.storage import store


router = APIRouter(prefix="/api", tags=["Scope"])


@router.post("/scope-change")
async def apply_scope_change(
    session_id: str = Query(..., description="Session ID"),
    request: ScopeChangeRequest = ..., 
):
    """Apply a scope reduction and return updated forecast/risk analysis."""

    try:
        session = store.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=404,
                detail=ApiResponse(
                    success=False,
                    error_code=ErrorCodes.SESSION_NOT_FOUND,
                    message=f"Session {session_id} not found",
                ).model_dump(),
            )

        project_state = session.project_state
        work_item_map = {item.item_id: item for item in project_state.work_items}
        descoped_item_ids = []

        for item_id in request.item_ids:
            work_item = work_item_map.get(item_id)
            if not work_item:
                raise HTTPException(
                    status_code=404,
                    detail=ApiResponse(
                        success=False,
                        error_code=ErrorCodes.VALIDATION_ERROR,
                        message=f"Work item {item_id} not found in session {session_id}",
                    ).model_dump(),
                )

            work_item.status = WorkItemStatus.COMPLETED
            work_item.is_scope_changed = True
            work_item.scope_change_reason = request.reason or "Scope reduced via API"
            work_item.remaining_effort_hrs = 0.0
            work_item.current_estimate_hrs = 0.0
            work_item.actual_effort_hrs = min(work_item.actual_effort_hrs, work_item.estimated_effort_hrs)
            work_item.progress_pct = 1.0
            descoped_item_ids.append(item_id)

        session.descoped_item_ids.update(descoped_item_ids)

        metrics = MetricsEngine(project_state).calculate()
        dag = DependencyGraphEngine(project_state).build_dag()
        cp_result = CriticalPathEngine(project_state, dag).analyze()
        spillover = SpilloverAnalysisEngine(project_state, metrics.average_item_effort).analyze()
        forecast = ForecastEngine(project_state, metrics, cp_result, spillover).calculate()
        monte_carlo = MonteCarloEngine(
            project_state=project_state,
            metrics=metrics,
            cp_result=cp_result,
            spillover=spillover,
            simulation_count=1000,
        ).calculate()
        impact_scores = ImpactScoringEngine(project_state, dag).score()
        risk_result = RiskEngine(
            project_state=project_state,
            metrics=metrics,
            cp_result=cp_result,
            dag=dag,
            spillover=spillover,
            forecast=forecast,
            monte_carlo=monte_carlo,
            impact_scores=impact_scores,
        ).analyze()

        response = ScopeChangeResponse(
            session_id=session_id,
            project_name=project_state.project_info.project_name,
            descoped_item_ids=descoped_item_ids,
            changed_item_count=len(descoped_item_ids),
            updated_remaining_effort_hours=metrics.remaining_effort_hours,
            forecast=forecast,
            risk_analysis=risk_result,
        )

        return ApiResponse(success=True, data=response.model_dump(), message="Scope change applied")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ApiResponse(
                success=False,
                error_code=ErrorCodes.INTERNAL_ERROR,
                message=f"Error applying scope change: {str(e)}",
            ).model_dump(),
        )