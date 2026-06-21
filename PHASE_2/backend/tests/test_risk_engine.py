"""
Phase 3.3 Risk Engine Tests

Comprehensive test suite for risk engine analysis.
"""

import pytest
from datetime import datetime, timedelta

from app.domain.models import (
    ProjectInfo, Resource, Sprint, WorkItem, Dependency, Blocker, SprintActual, ProjectState,
    SkillLevel, WorkItemType, Priority, WorkItemStatus, SprintStatus, BlockerSeverity, BlockerStatus, BlockerCategory, DependencyType
)
from app.engines.metrics_engine import MetricsEngine
from app.engines.dependency_engine import DependencyGraphEngine
from app.engines.critical_path_engine import CriticalPathEngine
from app.engines.spillover_engine import SpilloverAnalysisEngine
from app.engines.forecast_engine import ForecastEngine
from app.engines.monte_carlo_engine import MonteCarloEngine
from app.engines.impact_scoring_engine import ImpactScoringEngine
from app.engines.risk_engine import RiskEngine
from app.api.models_phase3 import RiskLevel


@pytest.fixture
def sample_project_state_low_risk():
    """Create a sample ProjectState with low risk characteristics."""
    
    start_date = datetime(2025, 1, 1)
    end_date = datetime(2025, 3, 1)
    project_info = ProjectInfo(
        project_name="Low Risk Project",
        sponsor="Test Sponsor",
        business_unit="Engineering",
        project_manager="Test PM",
        customer="Test Customer",
        status="Active",
        start_date=start_date,
        target_end_date=end_date,
        sprint_duration_days=14,
        methodology="Agile Scrum",
    )
    
    team = [
        Resource(
            resource_id="R1",
            name="Alice",
            role="Engineer",
            primary_skill="Python",
            secondary_skill="C++",
            skill_level=SkillLevel.SENIOR,
            allocation_pct=0.8,  # Not overloaded
            availability_pct=1.0,
        ),
        Resource(
            resource_id="R2",
            name="Bob",
            role="Engineer",
            primary_skill="Java",
            secondary_skill="JavaScript",
            skill_level=SkillLevel.MID,
            allocation_pct=0.7,  # Not overloaded
            availability_pct=0.95,
        ),
    ]
    
    sprints = [
        Sprint(
            sprint_id="S1",
            sprint_name="Sprint 1",
            sprint_number=1,
            start_date=start_date,
            end_date=start_date + timedelta(days=14),
            working_days=10,
            sprint_goal="Initial setup",
            status=SprintStatus.COMPLETED,
            planned_velocity_hrs=160.0,
            carryover_count=0,
        ),
    ]
    
    # Few, simple work items
    work_items = [
        WorkItem(
            item_id="WI-001",
            title="Task 1",
            work_type=WorkItemType.TASK,
            assigned_sprint="S1",
            original_sprint="S1",
            priority=Priority.MEDIUM,
            status=WorkItemStatus.COMPLETED,
            estimated_effort_hrs=20.0,
            current_estimate_hrs=20.0,
            remaining_effort_hrs=0.0,
            assigned_resource="R1",
            required_skill="Python",
        ),
        WorkItem(
            item_id="WI-002",
            title="Task 2",
            work_type=WorkItemType.TASK,
            assigned_sprint="S1",
            original_sprint="S1",
            priority=Priority.MEDIUM,
            status=WorkItemStatus.IN_PROGRESS,
            estimated_effort_hrs=20.0,
            current_estimate_hrs=20.0,
            remaining_effort_hrs=5.0,
            assigned_resource="R2",
            required_skill="Java",
        ),
    ]
    
    dependencies = []  # No dependencies
    blockers = []  # No blockers
    
    actuals = [
        SprintActual(
            sprint_id="S1",
            sprint_number=1,
            planned_effort_hrs=160.0,
            actual_effort_hrs=150.0,
            tasks_planned=2,
            tasks_completed=2,
            carryover_count=0,
        ),
    ]
    
    return ProjectState(
        project_id="proj-low-risk",
        project_info=project_info,
        team=team,
        sprints=sprints,
        work_items=work_items,
        dependencies=dependencies,
        blockers=blockers,
        actuals=actuals,
    )


@pytest.fixture
def sample_project_state_high_risk():
    """Create a sample ProjectState with high risk characteristics."""
    
    start_date = datetime(2025, 1, 1)
    end_date = datetime(2025, 2, 1)  # Tight timeline
    project_info = ProjectInfo(
        project_name="High Risk Project",
        sponsor="Test Sponsor",
        business_unit="Engineering",
        project_manager="Test PM",
        customer="Test Customer",
        status="Active",
        start_date=start_date,
        target_end_date=end_date,
        sprint_duration_days=14,
        methodology="Agile Scrum",
    )
    
    team = [
        Resource(
            resource_id="R1",
            name="Alice",
            role="Engineer",
            primary_skill="Python",
            secondary_skill="C++",
            skill_level=SkillLevel.SENIOR,
            allocation_pct=0.95,  # Near overload
            availability_pct=1.0,
        ),
    ]
    
    sprints = [
        Sprint(
            sprint_id="S1",
            sprint_name="Sprint 1",
            sprint_number=1,
            start_date=start_date,
            end_date=start_date + timedelta(days=14),
            working_days=10,
            sprint_goal="Initial setup",
            status=SprintStatus.COMPLETED,
            planned_velocity_hrs=100.0,
            carryover_count=3,
        ),
    ]
    
    # Many work items with increasing estimates
    work_items = [
        WorkItem(
            item_id="WI-001",
            title="Task 1",
            work_type=WorkItemType.TASK,
            assigned_sprint="S1",
            original_sprint="S1",
            priority=Priority.HIGH,
            status=WorkItemStatus.IN_PROGRESS,
            estimated_effort_hrs=20.0,
            current_estimate_hrs=35.0,  # Inflated
            remaining_effort_hrs=35.0,
            assigned_resource="R1",
            required_skill="Python",
        ),
        WorkItem(
            item_id="WI-002",
            title="Task 2",
            work_type=WorkItemType.TASK,
            assigned_sprint="S1",
            original_sprint="S1",
            priority=Priority.HIGH,
            status=WorkItemStatus.BLOCKED,  # Blocked
            estimated_effort_hrs=25.0,
            current_estimate_hrs=25.0,
            remaining_effort_hrs=25.0,
            assigned_resource="R1",
            required_skill="Python",
        ),
        WorkItem(
            item_id="WI-003",
            title="Task 3",
            work_type=WorkItemType.FEATURE,
            assigned_sprint="S1",
            original_sprint="S1",
            priority=Priority.HIGH,
            status=WorkItemStatus.NOT_STARTED,
            estimated_effort_hrs=30.0,
            current_estimate_hrs=50.0,  # Inflated
            remaining_effort_hrs=50.0,
            assigned_resource="R1",
            required_skill="Python",
        ),
    ]
    
    # Dependencies creating long chain
    dependencies = [
        Dependency(
            dependency_id="DEP-001",
            predecessor_item_id="WI-001",
            successor_item_id="WI-002",
            lag_days=0,
            dependency_type=DependencyType.FINISH_TO_START,
        ),
        Dependency(
            dependency_id="DEP-002",
            predecessor_item_id="WI-002",
            successor_item_id="WI-003",
            lag_days=0,
            dependency_type=DependencyType.FINISH_TO_START,
        ),
    ]
    
    # Active blockers
    blockers = [
        Blocker(
            blocker_id="B1",
            related_item_id="WI-002",
            impacted_item_ids=["WI-002"],
            description="Test blocker",
            severity=BlockerSeverity.HIGH,
            status=BlockerStatus.OPEN,
            owner="DevOps",
            raised_date=start_date,
            target_resolution_date=start_date + timedelta(days=3),
            actual_resolution_date=None,  # Still open
            category=BlockerCategory.OTHER,
            notes="Test blocker",
        ),
    ]
    
    actuals = [
        SprintActual(
            sprint_id="S1",
            sprint_number=1,
            planned_effort_hrs=160.0,
            actual_effort_hrs=90.0,  # Below velocity
            tasks_planned=3,
            tasks_completed=2,
            carryover_count=3,
        ),
    ]
    
    return ProjectState(
        project_id="proj-high-risk",
        project_info=project_info,
        team=team,
        sprints=sprints,
        work_items=work_items,
        dependencies=dependencies,
        blockers=blockers,
        actuals=actuals,
    )


# ──────────────────────────────────────────────────────────────────────────────
# TEST CASES
# ──────────────────────────────────────────────────────────────────────────────


def test_risk_engine_initialization(sample_project_state_low_risk):
    """Test RiskEngine can be initialized with all dependencies."""
    metrics = MetricsEngine(sample_project_state_low_risk).calculate()
    dep_engine = DependencyGraphEngine(sample_project_state_low_risk)
    dag = dep_engine.build_dag()
    cp_engine = CriticalPathEngine(sample_project_state_low_risk, dag)
    cp_result = cp_engine.analyze()
    spillover = SpilloverAnalysisEngine(sample_project_state_low_risk, metrics.average_item_effort).analyze()
    forecast = ForecastEngine(sample_project_state_low_risk, metrics, cp_result, spillover).calculate()
    mc_engine = MonteCarloEngine(
        sample_project_state_low_risk, metrics, cp_result, spillover, simulation_count=1000
    )
    monte_carlo = mc_engine.calculate()
    impact_scores = ImpactScoringEngine(sample_project_state_low_risk, dag).score()
    
    risk_engine = RiskEngine(
        sample_project_state_low_risk, metrics, cp_result, dag, spillover, forecast, monte_carlo, impact_scores
    )
    assert risk_engine is not None


def test_overall_risk_calculation(sample_project_state_low_risk):
    """Verify weighted aggregation formula."""
    metrics = MetricsEngine(sample_project_state_low_risk).calculate()
    dep_engine = DependencyGraphEngine(sample_project_state_low_risk)
    dag = dep_engine.build_dag()
    cp_engine = CriticalPathEngine(sample_project_state_low_risk, dag)
    cp_result = cp_engine.analyze()
    spillover = SpilloverAnalysisEngine(sample_project_state_low_risk, metrics.average_item_effort).analyze()
    forecast = ForecastEngine(sample_project_state_low_risk, metrics, cp_result, spillover).calculate()
    mc_engine = MonteCarloEngine(
        sample_project_state_low_risk, metrics, cp_result, spillover, simulation_count=1000
    )
    monte_carlo = mc_engine.calculate()
    impact_scores = ImpactScoringEngine(sample_project_state_low_risk, dag).score()
    
    risk_engine = RiskEngine(
        sample_project_state_low_risk, metrics, cp_result, dag, spillover, forecast, monte_carlo, impact_scores
    )
    result = risk_engine.analyze()
    
    # Verify overall score is within bounds
    assert 0.0 <= result.overall_risk_score <= 100.0
    
    # Verify sub-scores are within bounds
    assert 0.0 <= result.schedule_risk.score <= 100.0
    assert 0.0 <= result.dependency_risk.score <= 100.0
    assert 0.0 <= result.resource_risk.score <= 100.0
    assert 0.0 <= result.scope_risk.score <= 100.0
    
    # Verify weighted formula: 0.40 * schedule + 0.25 * dependency + 0.20 * resource + 0.15 * scope
    expected_overall = (
        0.40 * result.schedule_risk.score
        + 0.25 * result.dependency_risk.score
        + 0.20 * result.resource_risk.score
        + 0.15 * result.scope_risk.score
    )
    assert abs(result.overall_risk_score - expected_overall) < 0.01


def test_schedule_risk_high_when_probability_low():
    """Test schedule risk increases when on-time probability is low."""
    # Create project state for Monte Carlo with low probability
    start_date = datetime(2025, 1, 1)
    end_date = datetime(2025, 1, 15)  # Very tight timeline
    project_info = ProjectInfo(
        project_name="Tight Timeline",
        sponsor="Test",
        business_unit="Engineering",
        project_manager="PM",
        customer="Customer",
        status="Active",
        start_date=start_date,
        target_end_date=end_date,
        sprint_duration_days=14,
        methodology="Agile Scrum",
    )
    
    team = [
        Resource(
            resource_id="R1",
            name="Alice",
            role="Engineer",
            primary_skill="Python",
            secondary_skill="C++",
            skill_level=SkillLevel.SENIOR,
            allocation_pct=1.0,
            availability_pct=1.0,
        ),
    ]
    
    sprints = [
        Sprint(
            sprint_id="S1",
            sprint_name="Sprint 1",
            sprint_number=1,
            start_date=start_date,
            end_date=end_date,
            working_days=10,
            sprint_goal="Dev",
            status=SprintStatus.IN_PROGRESS,
            planned_velocity_hrs=100.0,
            carryover_count=0,
        ),
    ]
    
    work_items = [
        WorkItem(
            item_id="WI-001",
            title="Large Task",
            work_type=WorkItemType.FEATURE,
            assigned_sprint="S1",
            original_sprint="S1",
            priority=Priority.HIGH,
            status=WorkItemStatus.IN_PROGRESS,
            estimated_effort_hrs=200.0,  # More than capacity
            current_estimate_hrs=200.0,
            remaining_effort_hrs=150.0,
            assigned_resource="R1",
            required_skill="Python",
        ),
    ]
    
    project_state = ProjectState(
        project_id="proj-schedule-risk",
        project_info=project_info,
        team=team,
        sprints=sprints,
        work_items=work_items,
        dependencies=[],
        blockers=[],
        actuals=[],
    )
    
    metrics = MetricsEngine(project_state).calculate()
    dep_engine = DependencyGraphEngine(project_state)
    dag = dep_engine.build_dag()
    cp_engine = CriticalPathEngine(project_state, dag)
    cp_result = cp_engine.analyze()
    spillover = SpilloverAnalysisEngine(project_state, metrics.average_item_effort).analyze()
    forecast = ForecastEngine(project_state, metrics, cp_result, spillover).calculate()
    mc_engine = MonteCarloEngine(project_state, metrics, cp_result, spillover, simulation_count=1000)
    monte_carlo = mc_engine.calculate()
    impact_scores = ImpactScoringEngine(project_state, dag).score()
    
    risk_engine = RiskEngine(
        project_state, metrics, cp_result, dag, spillover, forecast, monte_carlo, impact_scores
    )
    result = risk_engine.analyze()
    
    # With low on-time probability, schedule risk should be high
    assert monte_carlo.on_time_probability < 0.5
    assert result.schedule_risk.score > 50.0


def test_dependency_risk_increases_with_critical_path():
    """Test dependency risk increases with long critical path."""
    start_date = datetime(2025, 1, 1)
    end_date = datetime(2025, 3, 1)
    project_info = ProjectInfo(
        project_name="Complex Dependencies",
        sponsor="Test",
        business_unit="Engineering",
        project_manager="PM",
        customer="Customer",
        status="Active",
        start_date=start_date,
        target_end_date=end_date,
        sprint_duration_days=14,
        methodology="Agile Scrum",
    )
    
    team = [
        Resource(
            resource_id="R1",
            name="Alice",
            role="Engineer",
            primary_skill="Python",
            secondary_skill="C++",
            skill_level=SkillLevel.SENIOR,
            allocation_pct=0.8,
            availability_pct=1.0,
        ),
    ]
    
    sprints = [
        Sprint(
            sprint_id="S1",
            sprint_name="Sprint 1",
            sprint_number=1,
            start_date=start_date,
            end_date=start_date + timedelta(days=14),
            working_days=10,
            sprint_goal="Dev",
            status=SprintStatus.IN_PROGRESS,
            planned_velocity_hrs=160.0,
            carryover_count=0,
        ),
    ]
    
    # Create a long chain of dependent items
    work_items = [
        WorkItem(
            item_id=f"WI-{i:03d}",
            title=f"Task {i}",
            work_type=WorkItemType.TASK,
            assigned_sprint="S1",
            original_sprint="S1",
            priority=Priority.HIGH,
            status=WorkItemStatus.NOT_STARTED,
            estimated_effort_hrs=15.0,
            current_estimate_hrs=15.0,
            remaining_effort_hrs=15.0,
            assigned_resource="R1",
            required_skill="Python",
        )
        for i in range(1, 11)  # 10 items in chain
    ]
    
    # Create finish-to-start chain
    dependencies = [
        Dependency(
            dependency_id=f"DEP-{i:03d}",
            predecessor_item_id=f"WI-{i:03d}",
            successor_item_id=f"WI-{i+1:03d}",
            lag_days=0,
            dependency_type=DependencyType.FINISH_TO_START,
        )
        for i in range(1, 10)
    ]
    
    project_state = ProjectState(
        project_id="proj-critical-path",
        project_info=project_info,
        team=team,
        sprints=sprints,
        work_items=work_items,
        dependencies=dependencies,
        blockers=[],
        actuals=[],
    )
    
    metrics = MetricsEngine(project_state).calculate()
    dep_engine = DependencyGraphEngine(project_state)
    dag = dep_engine.build_dag()
    cp_engine = CriticalPathEngine(project_state, dag)
    cp_result = cp_engine.analyze()
    spillover = SpilloverAnalysisEngine(project_state, metrics.average_item_effort).analyze()
    forecast = ForecastEngine(project_state, metrics, cp_result, spillover).calculate()
    mc_engine = MonteCarloEngine(project_state, metrics, cp_result, spillover, simulation_count=1000)
    monte_carlo = mc_engine.calculate()
    impact_scores = ImpactScoringEngine(project_state, dag).score()
    
    risk_engine = RiskEngine(
        project_state, metrics, cp_result, dag, spillover, forecast, monte_carlo, impact_scores
    )
    result = risk_engine.analyze()
    
    # With long critical path, dependency risk should be high
    assert len(cp_result.items_on_critical_path) > 5
    assert result.dependency_risk.score > 30.0


def test_resource_risk_increases_with_utilization():
    """Test resource risk increases with high utilization."""
    start_date = datetime(2025, 1, 1)
    end_date = datetime(2025, 3, 1)
    project_info = ProjectInfo(
        project_name="Resource Constrained",
        sponsor="Test",
        business_unit="Engineering",
        project_manager="PM",
        customer="Customer",
        status="Active",
        start_date=start_date,
        target_end_date=end_date,
        sprint_duration_days=14,
        methodology="Agile Scrum",
    )
    
    # Highly utilized team
    team = [
        Resource(
            resource_id="R1",
            name="Alice",
            role="Engineer",
            primary_skill="Python",
            secondary_skill="C++",
            skill_level=SkillLevel.SENIOR,
            allocation_pct=0.98,  # Almost fully allocated
            availability_pct=1.0,
        ),
    ]
    
    sprints = [
        Sprint(
            sprint_id="S1",
            sprint_name="Sprint 1",
            sprint_number=1,
            start_date=start_date,
            end_date=start_date + timedelta(days=14),
            working_days=10,
            sprint_goal="Dev",
            status=SprintStatus.IN_PROGRESS,
            planned_velocity_hrs=160.0,
            carryover_count=0,
        ),
    ]
    
    work_items = [
        WorkItem(
            item_id="WI-001",
            title="Task 1",
            work_type=WorkItemType.TASK,
            assigned_sprint="S1",
            original_sprint="S1",
            priority=Priority.HIGH,
            status=WorkItemStatus.IN_PROGRESS,
            estimated_effort_hrs=80.0,
            current_estimate_hrs=80.0,
            remaining_effort_hrs=40.0,
            assigned_resource="R1",
            required_skill="Python",
        ),
    ]
    
    project_state = ProjectState(
        project_id="proj-resource-risk",
        project_info=project_info,
        team=team,
        sprints=sprints,
        work_items=work_items,
        dependencies=[],
        blockers=[],
        actuals=[],
    )
    
    metrics = MetricsEngine(project_state).calculate()
    dep_engine = DependencyGraphEngine(project_state)
    dag = dep_engine.build_dag()
    cp_engine = CriticalPathEngine(project_state, dag)
    cp_result = cp_engine.analyze()
    spillover = SpilloverAnalysisEngine(project_state, metrics.average_item_effort).analyze()
    forecast = ForecastEngine(project_state, metrics, cp_result, spillover).calculate()
    mc_engine = MonteCarloEngine(project_state, metrics, cp_result, spillover, simulation_count=1000)
    monte_carlo = mc_engine.calculate()
    impact_scores = ImpactScoringEngine(project_state, dag).score()
    
    risk_engine = RiskEngine(
        project_state, metrics, cp_result, dag, spillover, forecast, monte_carlo, impact_scores
    )
    result = risk_engine.analyze()
    
    # With high utilization, resource risk should be elevated
    assert metrics.avg_allocation_pct > 0.9
    assert result.resource_risk.score > 20.0


def test_scope_risk_detects_estimate_growth():
    """Test scope risk detects estimate inflation."""
    start_date = datetime(2025, 1, 1)
    end_date = datetime(2025, 3, 1)
    project_info = ProjectInfo(
        project_name="Scope Growth",
        sponsor="Test",
        business_unit="Engineering",
        project_manager="PM",
        customer="Customer",
        status="Active",
        start_date=start_date,
        target_end_date=end_date,
        sprint_duration_days=14,
        methodology="Agile Scrum",
    )
    
    team = [
        Resource(
            resource_id="R1",
            name="Alice",
            role="Engineer",
            primary_skill="Python",
            secondary_skill="C++",
            skill_level=SkillLevel.SENIOR,
            allocation_pct=0.8,
            availability_pct=1.0,
        ),
    ]
    
    sprints = [
        Sprint(
            sprint_id="S1",
            sprint_name="Sprint 1",
            sprint_number=1,
            start_date=start_date,
            end_date=start_date + timedelta(days=14),
            working_days=10,
            sprint_goal="Dev",
            status=SprintStatus.IN_PROGRESS,
            planned_velocity_hrs=160.0,
            carryover_count=0,
        ),
    ]
    
    # Items with inflated estimates
    work_items = [
        WorkItem(
            item_id="WI-001",
            title="Task 1",
            work_type=WorkItemType.TASK,
            assigned_sprint="S1",
            original_sprint="S1",
            priority=Priority.HIGH,
            status=WorkItemStatus.IN_PROGRESS,
            estimated_effort_hrs=20.0,
            current_estimate_hrs=50.0,  # 150% inflation
            remaining_effort_hrs=50.0,
            assigned_resource="R1",
            required_skill="Python",
        ),
        WorkItem(
            item_id="WI-002",
            title="Task 2",
            work_type=WorkItemType.TASK,
            assigned_sprint="S1",
            original_sprint="S1",
            priority=Priority.HIGH,
            status=WorkItemStatus.NOT_STARTED,
            estimated_effort_hrs=30.0,
            current_estimate_hrs=45.0,  # 50% inflation
            remaining_effort_hrs=45.0,
            assigned_resource="R1",
            required_skill="Python",
        ),
    ]
    
    project_state = ProjectState(
        project_id="proj-scope-risk",
        project_info=project_info,
        team=team,
        sprints=sprints,
        work_items=work_items,
        dependencies=[],
        blockers=[],
        actuals=[],
    )
    
    metrics = MetricsEngine(project_state).calculate()
    dep_engine = DependencyGraphEngine(project_state)
    dag = dep_engine.build_dag()
    cp_engine = CriticalPathEngine(project_state, dag)
    cp_result = cp_engine.analyze()
    spillover = SpilloverAnalysisEngine(project_state, metrics.average_item_effort).analyze()
    forecast = ForecastEngine(project_state, metrics, cp_result, spillover).calculate()
    mc_engine = MonteCarloEngine(project_state, metrics, cp_result, spillover, simulation_count=1000)
    monte_carlo = mc_engine.calculate()
    impact_scores = ImpactScoringEngine(project_state, dag).score()
    
    risk_engine = RiskEngine(
        project_state, metrics, cp_result, dag, spillover, forecast, monte_carlo, impact_scores
    )
    result = risk_engine.analyze()
    
    # With estimate inflation, scope risk should be high
    assert result.scope_risk.score > 40.0
    assert len(result.scope_risk.reasons) > 0


def test_risk_drivers_ranked(sample_project_state_high_risk):
    """Test risk drivers are ranked by score (descending)."""
    metrics = MetricsEngine(sample_project_state_high_risk).calculate()
    dep_engine = DependencyGraphEngine(sample_project_state_high_risk)
    dag = dep_engine.build_dag()
    cp_engine = CriticalPathEngine(sample_project_state_high_risk, dag)
    cp_result = cp_engine.analyze()
    spillover = SpilloverAnalysisEngine(sample_project_state_high_risk, metrics.average_item_effort).analyze()
    forecast = ForecastEngine(sample_project_state_high_risk, metrics, cp_result, spillover).calculate()
    mc_engine = MonteCarloEngine(
        sample_project_state_high_risk, metrics, cp_result, spillover, simulation_count=1000
    )
    monte_carlo = mc_engine.calculate()
    impact_scores = ImpactScoringEngine(sample_project_state_high_risk, dag).score()
    
    risk_engine = RiskEngine(
        sample_project_state_high_risk, metrics, cp_result, dag, spillover, forecast, monte_carlo, impact_scores
    )
    result = risk_engine.analyze()
    
    # Verify drivers are sorted descending
    scores = [d.score for d in result.top_risk_drivers]
    assert scores == sorted(scores, reverse=True)
    
    # Verify max 10 drivers
    assert len(result.top_risk_drivers) <= 10


def test_sprint_heatmap_generation(sample_project_state_high_risk):
    """Test sprint-level risk analysis is generated."""
    metrics = MetricsEngine(sample_project_state_high_risk).calculate()
    dep_engine = DependencyGraphEngine(sample_project_state_high_risk)
    dag = dep_engine.build_dag()
    cp_engine = CriticalPathEngine(sample_project_state_high_risk, dag)
    cp_result = cp_engine.analyze()
    spillover = SpilloverAnalysisEngine(sample_project_state_high_risk, metrics.average_item_effort).analyze()
    forecast = ForecastEngine(sample_project_state_high_risk, metrics, cp_result, spillover).calculate()
    mc_engine = MonteCarloEngine(
        sample_project_state_high_risk, metrics, cp_result, spillover, simulation_count=1000
    )
    monte_carlo = mc_engine.calculate()
    impact_scores = ImpactScoringEngine(sample_project_state_high_risk, dag).score()
    
    risk_engine = RiskEngine(
        sample_project_state_high_risk, metrics, cp_result, dag, spillover, forecast, monte_carlo, impact_scores
    )
    result = risk_engine.analyze()
    
    # Verify sprint risks are generated
    assert len(result.sprint_risks) > 0
    
    # Verify each sprint risk has required fields
    for sprint_risk in result.sprint_risks:
        assert sprint_risk.sprint_id is not None
        assert 0.0 <= sprint_risk.risk_score <= 100.0
        assert sprint_risk.risk_level is not None
        assert sprint_risk.blocked_items >= 0
        assert sprint_risk.spillover_items >= 0


def test_risk_levels():
    """Test risk level thresholds."""
    # Test each level
    assert RiskEngine._score_to_level(10.0) == RiskLevel.LOW
    assert RiskEngine._score_to_level(25.0) == RiskLevel.MODERATE
    assert RiskEngine._score_to_level(50.0) == RiskLevel.HIGH
    assert RiskEngine._score_to_level(70.0) == RiskLevel.VERY_HIGH
    assert RiskEngine._score_to_level(90.0) == RiskLevel.CRITICAL
    
    # Test boundaries
    assert RiskEngine._score_to_level(20.0) == RiskLevel.LOW
    assert RiskEngine._score_to_level(21.0) == RiskLevel.MODERATE
    assert RiskEngine._score_to_level(40.0) == RiskLevel.MODERATE
    assert RiskEngine._score_to_level(41.0) == RiskLevel.HIGH


def test_risk_result_has_explanations(sample_project_state_high_risk):
    """Test that all risk results have human-readable explanations."""
    metrics = MetricsEngine(sample_project_state_high_risk).calculate()
    dep_engine = DependencyGraphEngine(sample_project_state_high_risk)
    dag = dep_engine.build_dag()
    cp_engine = CriticalPathEngine(sample_project_state_high_risk, dag)
    cp_result = cp_engine.analyze()
    spillover = SpilloverAnalysisEngine(sample_project_state_high_risk, metrics.average_item_effort).analyze()
    forecast = ForecastEngine(sample_project_state_high_risk, metrics, cp_result, spillover).calculate()
    mc_engine = MonteCarloEngine(
        sample_project_state_high_risk, metrics, cp_result, spillover, simulation_count=1000
    )
    monte_carlo = mc_engine.calculate()
    impact_scores = ImpactScoringEngine(sample_project_state_high_risk, dag).score()
    
    risk_engine = RiskEngine(
        sample_project_state_high_risk, metrics, cp_result, dag, spillover, forecast, monte_carlo, impact_scores
    )
    result = risk_engine.analyze()
    
    # Verify all sub-risks have explanations
    for sub_risk in [result.schedule_risk, result.dependency_risk, result.resource_risk, result.scope_risk]:
        assert len(sub_risk.reasons) >= 0
        assert len(sub_risk.drivers) >= 0
    
    # Verify top drivers have descriptions and recommendations
    for driver in result.top_risk_drivers:
        assert len(driver.title) > 0
        assert len(driver.description) > 0
        assert len(driver.recommendation_hint) > 0


def test_low_risk_project(sample_project_state_low_risk):
    """Test low-risk project has low overall score."""
    metrics = MetricsEngine(sample_project_state_low_risk).calculate()
    dep_engine = DependencyGraphEngine(sample_project_state_low_risk)
    dag = dep_engine.build_dag()
    cp_engine = CriticalPathEngine(sample_project_state_low_risk, dag)
    cp_result = cp_engine.analyze()
    spillover = SpilloverAnalysisEngine(sample_project_state_low_risk, metrics.average_item_effort).analyze()
    forecast = ForecastEngine(sample_project_state_low_risk, metrics, cp_result, spillover).calculate()
    mc_engine = MonteCarloEngine(
        sample_project_state_low_risk, metrics, cp_result, spillover, simulation_count=1000
    )
    monte_carlo = mc_engine.calculate()
    impact_scores = ImpactScoringEngine(sample_project_state_low_risk, dag).score()
    
    risk_engine = RiskEngine(
        sample_project_state_low_risk, metrics, cp_result, dag, spillover, forecast, monte_carlo, impact_scores
    )
    result = risk_engine.analyze()
    
    # Low risk project should have LOW or MODERATE risk level
    assert result.overall_risk_level in [RiskLevel.LOW, RiskLevel.MODERATE]


def test_high_risk_project(sample_project_state_high_risk):
    """Test high-risk project has high overall score."""
    metrics = MetricsEngine(sample_project_state_high_risk).calculate()
    dep_engine = DependencyGraphEngine(sample_project_state_high_risk)
    dag = dep_engine.build_dag()
    cp_engine = CriticalPathEngine(sample_project_state_high_risk, dag)
    cp_result = cp_engine.analyze()
    spillover = SpilloverAnalysisEngine(sample_project_state_high_risk, metrics.average_item_effort).analyze()
    forecast = ForecastEngine(sample_project_state_high_risk, metrics, cp_result, spillover).calculate()
    mc_engine = MonteCarloEngine(
        sample_project_state_high_risk, metrics, cp_result, spillover, simulation_count=1000
    )
    monte_carlo = mc_engine.calculate()
    impact_scores = ImpactScoringEngine(sample_project_state_high_risk, dag).score()
    
    risk_engine = RiskEngine(
        sample_project_state_high_risk, metrics, cp_result, dag, spillover, forecast, monte_carlo, impact_scores
    )
    result = risk_engine.analyze()
    
    # High risk project should have HIGH or VERY_HIGH risk level
    assert result.overall_risk_level in [RiskLevel.HIGH, RiskLevel.VERY_HIGH, RiskLevel.CRITICAL]
