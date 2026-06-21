"""
Phase 3 Forecast API Route

GET /forecast - deterministic single-point forecast
"""
from fastapi import APIRouter, HTTPException, Query
from app.storage import store
from app.api.models import ApiResponse, ErrorCodes
from app.api.models_phase3 import ForecastResponse, ForecastResult

from app.engines.metrics_engine import MetricsEngine
from app.engines.dependency_engine import DependencyGraphEngine
from app.engines.critical_path_engine import CriticalPathEngine
from app.engines.spillover_engine import SpilloverAnalysisEngine
from app.engines.forecast_engine import ForecastEngine

router = APIRouter(prefix="/api", tags=["Phase3"])


@router.get("/forecast")
async def get_forecast(session_id: str = Query(..., description="Session ID")):
    """Return a deterministic forecast for the session."""
    try:
        project_state = store.get_project_state(session_id)
        if not project_state:
            raise HTTPException(
                status_code=404,
                detail=ApiResponse(
                    success=False,
                    error_code=ErrorCodes.SESSION_NOT_FOUND,
                    message=f"Session {session_id} not found",
                ).model_dump()
            )

        # Calculate metrics
        metrics_engine = MetricsEngine(project_state)
        metrics = metrics_engine.calculate()

        # Build dependency DAG and critical path
        dep_engine = DependencyGraphEngine(project_state)
        dag = dep_engine.build_dag()
        cp_engine = CriticalPathEngine(project_state, dag)
        cp_result = cp_engine.analyze()

        # Analyze spillover
        spillover_engine = SpilloverAnalysisEngine(project_state, metrics.average_item_effort)
        spillover = spillover_engine.analyze()

        # Forecast
        forecast_engine = ForecastEngine(project_state, metrics, cp_result, spillover)
        forecast = forecast_engine.calculate()

        response = ForecastResponse(
            session_id=session_id,
            project_name=project_state.project_info.project_name,
            forecast=forecast,
        )

        return ApiResponse(success=True, data=response.model_dump(), message="Forecast generated")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ApiResponse(
                success=False,
                error_code=ErrorCodes.PROCESSING_ERROR,
                message=f"Error calculating forecast: {str(e)}",
            ).model_dump()
        )
