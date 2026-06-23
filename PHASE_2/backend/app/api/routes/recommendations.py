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
    RecommendationSummary,
)
from app.engines.recommendations.recommendation_engine_v2 import RecommendationEngineV2
from app.engines.recommendations.models import ScoringWeights

router = APIRouter(prefix="/api", tags=["Phase3.4"])


def _recommendation_to_summary(rec) -> RecommendationSummary:
    return RecommendationSummary(
        recommendation_id=rec.recommendation_id,
        type=rec.action_type.value,
        action=rec.title,
        target_ids=rec.affected_item_ids + rec.affected_resource_ids + rec.affected_sprint_ids + rec.affected_blocker_ids,
        details={
            "affected_item_ids": rec.affected_item_ids,
            "affected_resource_ids": rec.affected_resource_ids,
            "affected_sprint_ids": rec.affected_sprint_ids,
            "affected_blocker_ids": rec.affected_blocker_ids,
            "metadata": rec.metadata,
        },
        reason=rec.description,
        implementation_effort="Medium",
        confidence=rec.confidence.value,
        priority_score=round(rec.priority_score * 100.0, 2),
        baseline_probability=0.0,
        after_probability=0.0,
        expected_probability_gain=0.0,
        baseline_delay_days=0.0,
        after_delay_days=0.0,
        expected_delay_gain_days=rec.estimated_delay_reduction_days,
        baseline_risk_score=0.0,
        after_risk_score=0.0,
        expected_risk_reduction=rec.estimated_risk_reduction,
        impact_level="Medium",
        impact_confidence=rec.confidence.value,
        impact_classification="Positive Impact" if rec.estimated_delay_reduction_days > 0.0 else "Negligible Impact",
        business_impact=rec.description,
        impact_summary=rec.description,
        category=None,
        recommended_actions=[rec.title],
    )


def _build_engine(session_id: str) -> RecommendationEngineV2:
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
    return RecommendationEngineV2(project_state=project_state, simulation_count=1000, scoring_weights=ScoringWeights())


@router.get("/recommendations")
async def get_recommendations(
    session_id: str = Query(..., description="Session ID"),
    top_n: int = Query(5, description="Number of recommendations to return"),
):
    try:
        session_id = session_id.strip()
        recommendation_engine = _build_engine(session_id)
        candidates = recommendation_engine.generate(top_n=top_n)
        response = RecommendationResponse(
            session_id=session_id,
            project_name=recommendation_engine.project_state.project_info.project_name,
            recommendations=[_recommendation_to_summary(rec) for rec in candidates],
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
        recommendation_engine = _build_engine(session_id)
        simulation_result = recommendation_engine.simulate(request.recommendation_id)
        response = RecommendationSimulationResponse(
            session_id=session_id,
            project_name=recommendation_engine.project_state.project_info.project_name,
            simulation_result=RecommendationSimulationResult(
                session_id=session_id,
                project_name=recommendation_engine.project_state.project_info.project_name,
                recommendation_id=simulation_result.recommendation_ids[0] if simulation_result.recommendation_ids else None,
                baseline_probability=simulation_result.baseline_metrics.on_time_probability,
                after_probability=simulation_result.simulated_metrics.on_time_probability,
                probability_gain=simulation_result.delta_on_time_probability,
                baseline_delay_days=simulation_result.baseline_metrics.expected_delay_days,
                after_delay_days=simulation_result.simulated_metrics.expected_delay_days,
                delay_reduction_days=simulation_result.delta_expected_delay_days,
                baseline_risk_score=simulation_result.baseline_metrics.overall_risk_score,
                after_risk_score=simulation_result.simulated_metrics.overall_risk_score,
                risk_reduction=simulation_result.delta_risk_score,
                scenario_recommendation_ids=simulation_result.recommendation_ids,
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
        recommendation_engine = _build_engine(session_id)
        scenario = recommendation_engine.simulate_scenario(request.recommendation_ids)
        response = RecommendationSimulationResponse(
            session_id=session_id,
            project_name=recommendation_engine.project_state.project_info.project_name,
            simulation_result=RecommendationSimulationResult(
                session_id=session_id,
                project_name=recommendation_engine.project_state.project_info.project_name,
                recommendation_id=None,
                baseline_probability=scenario.baseline_metrics.on_time_probability,
                after_probability=scenario.simulated_metrics.on_time_probability,
                probability_gain=scenario.delta_on_time_probability,
                baseline_delay_days=scenario.baseline_metrics.expected_delay_days,
                after_delay_days=scenario.simulated_metrics.expected_delay_days,
                delay_reduction_days=scenario.delta_expected_delay_days,
                baseline_risk_score=scenario.baseline_metrics.overall_risk_score,
                after_risk_score=scenario.simulated_metrics.overall_risk_score,
                risk_reduction=scenario.delta_risk_score,
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
