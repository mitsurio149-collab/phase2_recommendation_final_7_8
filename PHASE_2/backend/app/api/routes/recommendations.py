"""Recommendation API Routes (Phase 3.4)

Endpoints:
- GET /api/recommendations
- POST /api/recommendations/simulate
- POST /api/recommendations/scenario
"""
from fastapi import APIRouter, HTTPException, Query
from app.storage import store
from app.api.models import ApiResponse, ErrorCodes
from app.api.models_phase3 import (
    RecommendationResponse,
    RecommendationSimulationRequest,
    RecommendationScenarioRequest,
    RecommendationSimulationResponse,
    RecommendationSimulationResult,
)
from app.engines.metrics_engine import MetricsEngine
from app.engines.dependency_engine import DependencyGraphEngine
from app.engines.critical_path_engine import CriticalPathEngine
from app.engines.spillover_engine import SpilloverAnalysisEngine
from app.engines.forecast_engine import ForecastEngine
from app.engines.monte_carlo_engine import MonteCarloEngine
from app.engines.impact_scoring_engine import ImpactScoringEngine
from app.engines.risk_engine import RiskEngine
from app.engines.recommendation_engine import RecommendationEngine

router = APIRouter(prefix="/api", tags=["Phase3.4"])


def _build_engines(session_id: str):
    project_state = store.get_project_state(session_id)
    if not project_state:
        raise HTTPException(
            status_code=404,
            detail=ApiResponse(
                success=False,
                error_code=ErrorCodes.SESSION_NOT_FOUND,
                message=f"Session {session_id} not found",
            ).model_dump(),
        )

    metrics = MetricsEngine(project_state).calculate()
    dep_engine = DependencyGraphEngine(project_state)
    dag = dep_engine.build_dag()
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

    return project_state, metrics, dag, cp_result, spillover, forecast, monte_carlo, risk_result


@router.get("/recommendations")
async def get_recommendations(
    session_id: str = Query(..., description="Session ID"),
    top_n: int = Query(5, description="Number of recommendations to return"),
):
    try:
        session_id = session_id.strip()
        project_state, metrics, dag, cp_result, spillover, forecast, monte_carlo, risk_result = _build_engines(session_id)

        recommendation_engine = RecommendationEngine(
            project_state=project_state,
            metrics=metrics,
            cp_result=cp_result,
            dag=dag,
            spillover=spillover,
            forecast=forecast,
            monte_carlo=monte_carlo,
            risk_result=risk_result,
        )
        candidates = recommendation_engine.generate_recommendations()[:top_n]
        response = RecommendationResponse(
            session_id=session_id,
            project_name=project_state.project_info.project_name,
            recommendations=[candidate.to_dict() for candidate in candidates],
        )
        return ApiResponse(success=True, data=response.model_dump(), message="Recommendations generated")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ApiResponse(
                success=False,
                error_code=ErrorCodes.INTERNAL_ERROR,
                message=f"Error generating recommendations: {str(e)}",
            ).model_dump(),
        )


@router.post("/recommendations/simulate")
async def simulate_recommendation(
    session_id: str = Query(..., description="Session ID"),
    request: RecommendationSimulationRequest = ..., 
):
    try:
        project_state, metrics, dag, cp_result, spillover, forecast, monte_carlo, risk_result = _build_engines(session_id)

        recommendation_engine = RecommendationEngine(
            project_state=project_state,
            metrics=metrics,
            cp_result=cp_result,
            dag=dag,
            spillover=spillover,
            forecast=forecast,
            monte_carlo=monte_carlo,
            risk_result=risk_result,
        )
        candidate = recommendation_engine.simulate_recommendation(request.recommendation_id)
        response = RecommendationSimulationResponse(
            session_id=session_id,
            project_name=project_state.project_info.project_name,
            simulation_result=RecommendationSimulationResult(
                session_id=session_id,
                project_name=project_state.project_info.project_name,
                recommendation_id=candidate.recommendation_id,
                baseline_probability=candidate.baseline_probability,
                after_probability=candidate.after_probability,
                probability_gain=candidate.expected_probability_gain,
                baseline_delay_days=candidate.baseline_delay_days,
                after_delay_days=candidate.after_delay_days,
                delay_reduction_days=candidate.expected_delay_gain_days,
                baseline_risk_score=candidate.baseline_risk_score,
                after_risk_score=candidate.after_risk_score,
                risk_reduction=candidate.expected_risk_reduction,
                scenario_recommendation_ids=[candidate.recommendation_id],
            ),
        )
        return ApiResponse(success=True, data=response.model_dump(), message="Simulation completed")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ApiResponse(
                success=False,
                error_code=ErrorCodes.INTERNAL_ERROR,
                message=f"Error simulating recommendation: {str(e)}",
            ).model_dump(),
        )


@router.post("/recommendations/scenario")
async def simulate_scenario(
    session_id: str = Query(..., description="Session ID"),
    request: RecommendationScenarioRequest = ..., 
):
    try:
        project_state, metrics, dag, cp_result, spillover, forecast, monte_carlo, risk_result = _build_engines(session_id)

        recommendation_engine = RecommendationEngine(
            project_state=project_state,
            metrics=metrics,
            cp_result=cp_result,
            dag=dag,
            spillover=spillover,
            forecast=forecast,
            monte_carlo=monte_carlo,
            risk_result=risk_result,
        )
        scenario = recommendation_engine.simulate_scenario(request.recommendation_ids)
        response = RecommendationSimulationResponse(
            session_id=session_id,
            project_name=project_state.project_info.project_name,
            simulation_result=RecommendationSimulationResult(
                session_id=session_id,
                project_name=project_state.project_info.project_name,
                recommendation_id=None,
                baseline_probability=scenario["baseline"]["probability"],
                after_probability=scenario["scenario"]["probability"],
                probability_gain=scenario["probability_gain"],
                baseline_delay_days=scenario["baseline"]["delay_days"],
                after_delay_days=scenario["scenario"]["delay_days"],
                delay_reduction_days=scenario["delay_reduction"],
                baseline_risk_score=scenario["baseline"]["risk_score"],
                after_risk_score=scenario["scenario"]["risk_score"],
                risk_reduction=scenario["risk_reduction"],
                scenario_recommendation_ids=request.recommendation_ids,
            ),
        )
        return ApiResponse(success=True, data=response.model_dump(), message="Scenario simulation completed")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ApiResponse(
                success=False,
                error_code=ErrorCodes.INTERNAL_ERROR,
                message=f"Error simulating recommendation scenario: {str(e)}",
            ).model_dump(),
        )
