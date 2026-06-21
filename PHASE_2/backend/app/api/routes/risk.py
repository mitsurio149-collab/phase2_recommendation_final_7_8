"""
Phase 3.3 Risk Engine API Route

GET /api/risk - comprehensive project risk analysis
"""
from fastapi import APIRouter, HTTPException, Query
from app.storage import store
from app.api.models import ApiResponse, ErrorCodes
from app.api.models_phase3 import RiskResponse

from app.engines.metrics_engine import MetricsEngine
from app.engines.dependency_engine import DependencyGraphEngine
from app.engines.critical_path_engine import CriticalPathEngine
from app.engines.spillover_engine import SpilloverAnalysisEngine
from app.engines.forecast_engine import ForecastEngine
from app.engines.monte_carlo_engine import MonteCarloEngine
from app.engines.impact_scoring_engine import ImpactScoringEngine
from app.engines.risk_engine import RiskEngine

router = APIRouter(prefix="/api", tags=["Phase3.3"])


@router.get("/risk")
async def get_risk_analysis(
    session_id: str = Query(..., description="Session ID"),
):
    """
    Return comprehensive risk analysis for the project.

    This endpoint answers: Why is this project at risk?

    The Risk Engine:
    - Analyzes project data from all previous engines
    - Calculates 4 sub-risk scores (schedule, dependency, resource, scope)
    - Computes overall risk using weighted aggregation
    - Identifies top risk drivers with explanations
    - Provides sprint-level risk breakdown
    - Is deterministic (no randomness beyond Monte Carlo)

    Args:
        session_id: Session ID

    Returns:
        RiskResponse with:
        - overall_risk_score: 0-100 weighted risk score
        - risk_level: LOW, MODERATE, HIGH, VERY_HIGH, or CRITICAL
        - schedule_risk, dependency_risk, resource_risk, scope_risk: Sub-scores with explanations
        - top_risk_drivers: Top 10 drivers, ranked by impact
        - sprint_risks: Per-sprint risk analysis
    """
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

        # Calculate all required inputs for Risk Engine
        
        # 1. Metrics
        metrics_engine = MetricsEngine(project_state)
        metrics = metrics_engine.calculate()

        # 2. Dependency analysis
        dep_engine = DependencyGraphEngine(project_state)
        dag = dep_engine.build_dag()

        # 3. Critical path
        cp_engine = CriticalPathEngine(project_state, dag)
        cp_result = cp_engine.analyze()

        # 4. Spillover analysis
        spillover_engine = SpilloverAnalysisEngine(project_state, metrics.average_item_effort)
        spillover = spillover_engine.analyze()

        # 5. Deterministic forecast
        forecast_engine = ForecastEngine(project_state, metrics, cp_result, spillover)
        forecast = forecast_engine.calculate()

        # 6. Monte Carlo analysis
        mc_engine = MonteCarloEngine(
            project_state=project_state,
            metrics=metrics,
            cp_result=cp_result,
            spillover=spillover,
            simulation_count=10000,
        )
        monte_carlo = mc_engine.calculate()

        # 7. Dependency impact scoring
        impact_engine = ImpactScoringEngine(project_state, dag)
        impact_scores = impact_engine.score()

        # 8. Risk analysis (uses all of the above)
        risk_engine = RiskEngine(
            project_state=project_state,
            metrics=metrics,
            cp_result=cp_result,
            dag=dag,
            spillover=spillover,
            forecast=forecast,
            monte_carlo=monte_carlo,
            impact_scores=impact_scores,
        )
        risk_result = risk_engine.analyze()

        response = RiskResponse(
            session_id=session_id,
            project_name=project_state.project_info.project_name,
            risk_analysis=risk_result,
        )

        return ApiResponse(
            success=True,
            data=response.model_dump(),
            message="Risk analysis complete",
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=ApiResponse(
                success=False,
                error_code=ErrorCodes.INTERNAL_ERROR,
                message=f"Error calculating risk analysis: {str(e)}",
            ).model_dump()
        )
