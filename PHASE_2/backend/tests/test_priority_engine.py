from app.engines.recommendations.models import (
    ConfidenceLevel,
    ImpactEstimate,
    RecommendationAction,
    RecommendationCandidate,
    ScoringWeights,
    UpstreamEngineOutputs,
)
from app.engines.recommendations.priority_engine import PriorityEngine
from tests.test_candidate_generator import build_upstream
from tests.test_recommendation_engine import make_recommendation_project_state


def test_priority_engine_scores_and_ranks_deterministically():
    project_state = make_recommendation_project_state()
    upstream = build_upstream(project_state)
    engine = PriorityEngine(upstream)

    candidates = [
        RecommendationCandidate(
            recommendation_id="a",
            action_type=RecommendationAction.RESOLVE_BLOCKER,
            title="Resolve blocker (BLK-01)",
            description="Resolve blocker",
            affected_item_ids=["WI-02"],
            affected_resource_ids=[],
            affected_sprint_ids=["S1"],
            affected_blocker_ids=["BLK-01"],
            root_cause_signal_id="sig-1",
            supporting_signal_ids=["sig-1"],
            simulation_params={},
            feasibility_checks={},
        ),
        RecommendationCandidate(
            recommendation_id="b",
            action_type=RecommendationAction.REASSIGN_ITEM,
            title="Reassign item (WI-02)",
            description="Reassign item",
            affected_item_ids=["WI-02"],
            affected_resource_ids=["R1"],
            affected_sprint_ids=["S2"],
            affected_blocker_ids=[],
            root_cause_signal_id="sig-2",
            supporting_signal_ids=["sig-2"],
            simulation_params={"target_resource_id": "R1"},
            feasibility_checks={},
        ),
    ]

    impact_estimates = {
        "a": ImpactEstimate(
            estimated_hours_recovered=24.0,
            estimated_delay_reduction_days=2.0,
            estimated_risk_reduction=0.2,
            confidence=ConfidenceLevel.HIGH,
            evidence=[],
            calculation_notes="",
        ),
        "b": ImpactEstimate(
            estimated_hours_recovered=10.0,
            estimated_delay_reduction_days=0.0,
            estimated_risk_reduction=0.1,
            confidence=ConfidenceLevel.MEDIUM,
            evidence=[],
            calculation_notes="",
        ),
    }

    first_pass = engine.score_and_rank(candidates, impact_estimates)
    second_pass = engine.score_and_rank(candidates, impact_estimates)

    assert [item.recommendation_id for item in first_pass] == [item.recommendation_id for item in second_pass]
    assert first_pass[0].priority_score >= first_pass[1].priority_score
    assert 0.0 <= first_pass[0].priority_score <= 1.0
    assert 0.0 <= first_pass[1].priority_score <= 1.0


def test_scoring_weights_must_sum_to_one():
    try:
        ScoringWeights(w_risk=0.2, w_schedule=0.2, w_blocker=0.2, w_cp=0.2, w_capacity=0.1)
    except ValueError:
        return
    raise AssertionError("Expected ValueError for invalid weights")
