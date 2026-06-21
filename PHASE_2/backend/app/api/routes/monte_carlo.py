"""
Phase 3.2 Monte Carlo API Route

GET /monte-carlo - probabilistic forecast with confidence intervals
"""
from fastapi import APIRouter, HTTPException, Query
from app.storage import store
from app.api.models import ApiResponse, ErrorCodes
from app.api.models_phase3 import MonteCarloResponse

from app.engines.metrics_engine import MetricsEngine
from app.engines.dependency_engine import DependencyGraphEngine
from app.engines.critical_path_engine import CriticalPathEngine
from app.engines.spillover_engine import SpilloverAnalysisEngine
from app.engines.monte_carlo_engine import MonteCarloEngine

router = APIRouter(prefix="/api", tags=["Phase3.2"])


@router.get("/monte-carlo")
async def get_monte_carlo(
    session_id: str = Query(..., description="Session ID"),
    simulations: int = Query(10000, description="Number of simulations (default 10000)", ge=100, le=100000),
    seed: int = Query(None, description="Random seed for reproducibility (optional)"),
):
    """Return a probabilistic forecast using Monte Carlo simulation.

    This endpoint runs multiple simulations to generate a distribution of
    possible finish dates, accounting for variability in velocity, remaining work,
    blockers, and spillover.

    Key principle: Target end date is NEVER modified. It is a fixed business
    commitment used only for probability calculation.

    Args:
        session_id: Session ID
        simulations: Number of Monte Carlo simulations to run (100-100000, default 10000)
        seed: Random seed for reproducibility (optional)

    Returns:
        MonteCarloResponse with:
        - target_end_date: Fixed business commitment (constant)
        - statistics: Percentile distribution of finish dates
        - on_time_probability: Probability of finishing on or before target_end_date
        - on_time_risk_level: Risk rating (LOW, MEDIUM, HIGH, CRITICAL)
        - best_case/most_likely/worst_case: Summary scenarios
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

        # Monte Carlo simulation
        mc_engine = MonteCarloEngine(
            project_state=project_state,
            metrics=metrics,
            cp_result=cp_result,
            spillover=spillover,
            simulation_count=simulations,
            seed=seed,
        )
        monte_carlo_result = mc_engine.calculate()

        response = MonteCarloResponse(
            session_id=session_id,
            project_name=project_state.project_info.project_name,
            monte_carlo=monte_carlo_result,
        )

        return ApiResponse(
            success=True,
            data=response.model_dump(),
            message=f"Monte Carlo analysis completed ({simulations} simulations)"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ApiResponse(
                success=False,
                error_code=ErrorCodes.PROCESSING_ERROR,
                message=f"Error calculating Monte Carlo: {str(e)}",
            ).model_dump()
        )
