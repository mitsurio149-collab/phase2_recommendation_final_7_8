from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.domain.models import Blocker, ProjectState, SprintStatus
from app.engines.critical_path_engine import CriticalPathResult
from app.engines.dependency_engine import DependencyDAG
from app.engines.forecast_engine import ForecastResult
from app.engines.impact_scoring_engine import RiskScores
from app.engines.metrics_engine import ProjectMetrics
from app.engines.monte_carlo_engine import MonteCarloResult
from app.engines.risk_engine import RiskResult
from app.engines.spillover_engine import SpilloverAnalysis
from app.engines.recommendations.models import (
    OpportunitySignal,
    SignalCategory,
    SignalEvidence,
    SignalSeverity,
    signal_id,
)


class BlockerDetector:
    def __init__(
        self,
        project_state: ProjectState,
        cp_result: CriticalPathResult,
        dag: DependencyDAG,
        impact_scores: RiskScores,
    ) -> None:
        self.project_state = project_state
        self.cp_result = cp_result
        self.dag = dag
        self.impact_scores = impact_scores

    def detect(self) -> List[OpportunitySignal]:
        signals: List[OpportunitySignal] = []
        active_blockers = [b for b in self.project_state.blockers if not getattr(b, "actual_resolution_date", None)]
        if not active_blockers:
            return signals

        for blocker in active_blockers:
            impacted_ids = list(getattr(blocker, "impacted_item_ids", []) or [])
            cascade_ids = self._cascade_item_ids(impacted_ids)
            blocked_hours = sum(
                float(next((wi.remaining_effort_hrs for wi in self.project_state.work_items if wi.item_id == item_id), 0.0))
                for item_id in impacted_ids
            )
            on_cp = any(item_id in self.cp_result.items_on_critical_path for item_id in impacted_ids)
            severity = SignalSeverity.CRITICAL if on_cp else SignalSeverity.HIGH
            if not on_cp and len(cascade_ids) < 3:
                severity = SignalSeverity.MEDIUM

            context: Dict[str, Any] = {
                "blocker_id": blocker.blocker_id,
                "category": getattr(blocker, "category", None),
                "severity": getattr(blocker, "severity", None),
                "impacted_item_ids": impacted_ids,
                "cascade_item_ids": cascade_ids,
                "blocked_hours": round(blocked_hours, 2),
                "on_critical_path": on_cp,
                "days_until_target_resolution": self._days_until_resolution(blocker),
                "sprint_gate_pct": round(blocked_hours / max(1.0, self._sprint_capacity_hours()), 4),
                "affected_sprint_numbers": self._affected_sprint_numbers(impacted_ids),
            }
            evidence = [
                SignalEvidence(
                    source_engine="critical_path_engine",
                    metric_name="impacted_items_on_cp",
                    metric_value=float(on_cp),
                    threshold=1.0,
                    explanation="Active blocker affects critical path items",
                )
            ]
            signal = OpportunitySignal(
                signal_id=signal_id(SignalCategory.BLOCKER, [blocker.blocker_id]),
                category=SignalCategory.BLOCKER,
                severity=severity,
                affected_item_ids=impacted_ids,
                affected_resource_ids=[],
                affected_sprint_ids=self._affected_sprint_ids(impacted_ids),
                affected_blocker_ids=[blocker.blocker_id],
                evidence=evidence,
                context=context,
                detected_at=datetime.now(timezone.utc).isoformat(),
            )
            signals.append(signal)
        return signals

    def _cascade_item_ids(self, impacted_item_ids: List[str]) -> List[str]:
        cascade: set[str] = set()
        for item_id in impacted_item_ids:
            for descendant in self.dag.transitive_closure.get(item_id, []):
                cascade.add(descendant)
        return sorted(cascade)

    def _days_until_resolution(self, blocker: Blocker) -> int:
        target = getattr(blocker, "target_resolution_date", None)
        raised = getattr(blocker, "raised_date", None)
        if not target or not raised:
            return 0
        return max(0, (target - raised).days)

    def _sprint_capacity_hours(self) -> float:
        sprint = next((s for s in self.project_state.sprints if getattr(s, "status", None) == SprintStatus.IN_PROGRESS), None)
        if sprint:
            return float(getattr(sprint, "planned_velocity_hrs", 0.0) or 0.0)
        return max(1.0, float(sum(getattr(s, "planned_velocity_hrs", 0.0) or 0.0 for s in self.project_state.sprints)))

    def _affected_sprint_numbers(self, affected_item_ids: List[str]) -> List[int]:
        sprint_numbers = []
        for item_id in affected_item_ids:
            work_item = next((wi for wi in self.project_state.work_items if wi.item_id == item_id), None)
            if work_item and getattr(work_item, "assigned_sprint", None):
                sprint = next((s for s in self.project_state.sprints if s.sprint_id == work_item.assigned_sprint), None)
                if sprint is not None:
                    sprint_numbers.append(sprint.sprint_number)
        return sorted(set(sprint_numbers))

    def _affected_sprint_ids(self, affected_item_ids: List[str]) -> List[str]:
        sprint_ids = []
        for item_id in affected_item_ids:
            work_item = next((wi for wi in self.project_state.work_items if wi.item_id == item_id), None)
            if work_item and getattr(work_item, "assigned_sprint", None):
                sprint_ids.append(work_item.assigned_sprint)
        return sorted(set(sprint_ids))


class CapacityDetector:
    def __init__(
        self,
        project_state: ProjectState,
        metrics: ProjectMetrics,
        cp_result: CriticalPathResult,
        impact_scores: RiskScores,
    ) -> None:
        self.project_state = project_state
        self.metrics = metrics
        self.cp_result = cp_result
        self.impact_scores = impact_scores

    def detect(self) -> List[OpportunitySignal]:
        signals: List[OpportunitySignal] = []
        for resource in self.project_state.team:
            load_ratio = self._load_ratio(resource)
            if 0.4 <= load_ratio <= 1.2:
                continue
            if resource.resource_id is None:
                continue
            flag = "OVERLOADED" if load_ratio > 1.2 else "UNDERUTILIZED"
            cp_items_owned = [
                wi.item_id for wi in self.project_state.work_items if wi.assigned_resource == resource.resource_id and wi.item_id in self.cp_result.items_on_critical_path
            ]
            context: Dict[str, Any] = {
                "resource_id": resource.resource_id,
                "load_ratio": round(load_ratio, 4),
                "assigned_remaining_hrs": round(self._assigned_remaining_hours(resource.resource_id), 2),
                "effective_remaining_capacity_hrs": round(self._effective_remaining_capacity(resource), 2),
                "flag": flag,
                "cp_items_owned": cp_items_owned,
                "is_single_owner_of_cp": len(cp_items_owned) > 0 and len(cp_items_owned) == 1,
                "owns_blocked_cp_items": any(item_id in self._blocked_cp_items() for item_id in cp_items_owned),
            }
            evidence = [
                SignalEvidence(
                    source_engine="metrics_engine",
                    metric_name="load_ratio",
                    metric_value=load_ratio,
                    threshold=1.2,
                    explanation="Resource load ratio exceeds the planned threshold",
                )
            ]
            severity = SignalSeverity.HIGH if context["owns_blocked_cp_items"] else SignalSeverity.MEDIUM
            if flag == "UNDERUTILIZED":
                severity = SignalSeverity.LOW
            signal = OpportunitySignal(
                signal_id=signal_id(SignalCategory.CAPACITY, [resource.resource_id]),
                category=SignalCategory.CAPACITY,
                severity=severity,
                affected_item_ids=[wi.item_id for wi in self.project_state.work_items if wi.assigned_resource == resource.resource_id],
                affected_resource_ids=[resource.resource_id],
                affected_sprint_ids=self._resource_sprint_ids(resource.resource_id),
                affected_blocker_ids=[],
                evidence=evidence,
                context=context,
                detected_at=datetime.now(timezone.utc).isoformat(),
            )
            signals.append(signal)
        return signals

    def _load_ratio(self, resource: Any) -> float:
        assigned_hours = self._assigned_remaining_hours(resource.resource_id)
        capacity_hours = self._effective_remaining_capacity(resource)
        return assigned_hours / max(capacity_hours, 1.0)

    def _assigned_remaining_hours(self, resource_id: str) -> float:
        return sum(float(wi.remaining_effort_hrs) for wi in self.project_state.work_items if wi.assigned_resource == resource_id)

    def _effective_remaining_capacity(self, resource: Any) -> float:
        availability = float(getattr(resource, "availability_pct", 1.0) or 1.0)
        allocation = float(getattr(resource, "allocation_pct", 1.0) or 1.0)
        return max(1.0, availability * allocation * 8.0 * 5.0)

    def _blocked_cp_items(self) -> List[str]:
        active_blockers = [b for b in self.project_state.blockers if not getattr(b, "actual_resolution_date", None)]
        blocked_items = set()
        for blocker in active_blockers:
            blocked_items.update(getattr(blocker, "impacted_item_ids", []) or [])
        return [item_id for item_id in blocked_items if item_id in self.cp_result.items_on_critical_path]

    def _resource_sprint_ids(self, resource_id: str) -> List[str]:
        sprint_ids = []
        for wi in self.project_state.work_items:
            if wi.assigned_resource == resource_id:
                sprint_ids.append(wi.assigned_sprint)
        return sorted(set(sprint_ids))


class SprintDetector:
    def __init__(
        self,
        project_state: ProjectState,
        metrics: ProjectMetrics,
        spillover: SpilloverAnalysis,
        forecast: ForecastResult,
    ) -> None:
        self.project_state = project_state
        self.metrics = metrics
        self.spillover = spillover
        self.forecast = forecast

    def detect(self) -> List[OpportunitySignal]:
        signals: List[OpportunitySignal] = []
        for sprint in self.project_state.sprints:
            if getattr(sprint, "status", None) == SprintStatus.COMPLETED:
                continue
            planned_hours = float(getattr(sprint, "planned_velocity_hrs", 0.0) or 0.0)
            capacity_hours = float(getattr(sprint, "planned_velocity_hrs", 0.0) or 0.0)
            utilization_ratio = planned_hours / max(capacity_hours, 1.0)
            if utilization_ratio < 0.5 and getattr(sprint, "sprint_number", 0) != self.metrics.current_sprint_number:
                flag = "UNDERLOADED"
            elif planned_hours > capacity_hours * 1.1:
                flag = "OVERLOADED"
            else:
                continue
            context: Dict[str, Any] = {
                "sprint_id": sprint.sprint_id,
                "sprint_number": sprint.sprint_number,
                "flag": flag,
                "utilization_ratio": round(utilization_ratio, 4),
                "planned_hours": round(planned_hours, 2),
                "capacity_hours": round(capacity_hours, 2),
                "blocked_hours": self._blocked_hours(sprint.sprint_id),
                "blocked_pct": round(self._blocked_hours(sprint.sprint_id) / max(planned_hours, 1.0), 4),
                "spillover_probability": self._spillover_probability(sprint.sprint_number),
                "is_cp_sprint": self._is_cp_sprint(sprint.sprint_id),
            }
            evidence = [
                SignalEvidence(
                    source_engine="spillover_engine",
                    metric_name="sprint_spillover_probability",
                    metric_value=float(context["spillover_probability"]),
                    threshold=0.6,
                    explanation="Sprint spillover risk is elevated",
                )
            ]
            signals.append(
                OpportunitySignal(
                    signal_id=signal_id(SignalCategory.SPRINT, [sprint.sprint_id]),
                    category=SignalCategory.SPRINT,
                    severity=SignalSeverity.MEDIUM,
                    affected_item_ids=self._items_in_sprint(sprint.sprint_id),
                    affected_resource_ids=[],
                    affected_sprint_ids=[sprint.sprint_id],
                    affected_blocker_ids=[],
                    evidence=evidence,
                    context=context,
                    detected_at=datetime.now(timezone.utc).isoformat(),
                )
            )
        return signals

    def _blocked_hours(self, sprint_id: str) -> float:
        blocked_hours = 0.0
        for wi in self.project_state.work_items:
            if getattr(wi, "assigned_sprint", None) == sprint_id:
                if getattr(wi, "status", None) == getattr(wi.status, "BLOCKED", None):
                    blocked_hours += float(getattr(wi, "remaining_effort_hrs", 0.0) or 0.0)
        return round(blocked_hours, 2)

    def _spillover_probability(self, sprint_number: int) -> float:
        probs = getattr(self.spillover, "sprint_spillover_probability", None) or {}
        if isinstance(probs, dict):
            return float(probs.get(sprint_number, 0.0))
        return 0.0

    def _items_in_sprint(self, sprint_id: str) -> List[str]:
        return [wi.item_id for wi in self.project_state.work_items if getattr(wi, "assigned_sprint", None) == sprint_id]

    def _is_cp_sprint(self, sprint_id: str) -> bool:
        return any(
            wi.item_id in self.forecast.cp_result.items_on_critical_path if hasattr(self.forecast, 'cp_result') else False
            for wi in self.project_state.work_items
            if getattr(wi, "assigned_sprint", None) == sprint_id
        )


class CriticalPathDetector:
    def __init__(
        self,
        project_state: ProjectState,
        cp_result: CriticalPathResult,
        dag: DependencyDAG,
        impact_scores: RiskScores,
    ) -> None:
        self.project_state = project_state
        self.cp_result = cp_result
        self.dag = dag
        self.impact_scores = impact_scores

    def detect(self) -> List[OpportunitySignal]:
        signals: List[OpportunitySignal] = []
        active_blockers = [b for b in self.project_state.blockers if not getattr(b, "actual_resolution_date", None)]
        blocked_cp_items = []
        for blocker in active_blockers:
            for item_id in getattr(blocker, "impacted_item_ids", []) or []:
                if item_id in self.cp_result.items_on_critical_path:
                    blocked_cp_items.append(item_id)
        if blocked_cp_items:
            signal = OpportunitySignal(
                signal_id=signal_id(SignalCategory.CRITICAL_PATH, sorted(set(blocked_cp_items))),
                category=SignalCategory.CRITICAL_PATH,
                severity=SignalSeverity.CRITICAL,
                affected_item_ids=sorted(set(blocked_cp_items)),
                affected_resource_ids=[],
                affected_sprint_ids=self._affected_sprint_ids(sorted(set(blocked_cp_items))),
                affected_blocker_ids=[b.blocker_id for b in active_blockers if any(item_id in getattr(b, 'impacted_item_ids', []) or [] for item_id in blocked_cp_items)],
                evidence=[
                    SignalEvidence(
                        source_engine="critical_path_engine",
                        metric_name="cp_at_risk",
                        metric_value=float(len(blocked_cp_items)),
                        threshold=1.0,
                        explanation="Critical path items are affected by active blockers",
                    )
                ],
                context={
                    "cp_nodes": sorted(set(blocked_cp_items)),
                    "cp_remaining_hours": round(self._cp_remaining_hours(sorted(set(blocked_cp_items))), 2),
                    "cp_single_owners": self._cp_single_owners(sorted(set(blocked_cp_items))),
                    "cp_blocked_items": sorted(set(blocked_cp_items)),
                    "near_critical_items": self._near_critical_items(),
                    "dependency_bottleneck_item_ids": self._dependency_bottlenecks(),
                    "flag": "CP_AT_RISK",
                },
                detected_at=datetime.now(timezone.utc).isoformat(),
            )
            signals.append(signal)

        return signals

    def _affected_sprint_ids(self, item_ids: List[str]) -> List[str]:
        sprint_ids = []
        for item_id in item_ids:
            work_item = next((wi for wi in self.project_state.work_items if wi.item_id == item_id), None)
            if work_item and getattr(work_item, "assigned_sprint", None):
                sprint_ids.append(work_item.assigned_sprint)
        return sorted(set(sprint_ids))

    def _cp_remaining_hours(self, item_ids: List[str]) -> float:
        return sum(float(next((wi.remaining_effort_hrs for wi in self.project_state.work_items if wi.item_id == item_id), 0.0)) for item_id in item_ids)

    def _cp_single_owners(self, item_ids: List[str]) -> List[str]:
        owners = []
        for item_id in item_ids:
            work_item = next((wi for wi in self.project_state.work_items if wi.item_id == item_id), None)
            if work_item and getattr(work_item, "assigned_resource", None):
                owners.append(work_item.assigned_resource)
        return sorted(set(owners))

    def _near_critical_items(self) -> List[str]:
        sprint_duration_hours = self.project_state.project_info.sprint_duration_days * 24.0
        threshold = 0.25 * sprint_duration_hours
        near = []
        slack_map = getattr(self.cp_result, "item_slack_map", {}) or {}
        for each in slack_map:
            if slack_map[each] <= threshold:
                near.append(each)
        return sorted(near)

    def _dependency_bottlenecks(self) -> List[str]:
        reverse_counts: Dict[str, int] = {}
        for node, successors in self.dag.graph.items():
            for successor in successors:
                if successor in self.cp_result.items_on_critical_path:
                    reverse_counts[successor] = reverse_counts.get(successor, 0) + 1
        return [item_id for item_id, count in sorted(reverse_counts.items()) if count >= 3]


class ScheduleDetector:
    def __init__(
        self,
        project_state: ProjectState,
        forecast: ForecastResult,
        monte_carlo: MonteCarloResult,
        risk_result: RiskResult,
        metrics: ProjectMetrics,
    ) -> None:
        self.project_state = project_state
        self.forecast = forecast
        self.monte_carlo = monte_carlo
        self.risk_result = risk_result
        self.metrics = metrics

    def _schedule_gap_hours(self) -> float:
        direct_value = getattr(self.forecast, "schedule_gap_hours", None)
        if direct_value is not None:
            return float(direct_value)
        expected_delay = float(getattr(self.forecast, "expected_delay_days", 0.0) or 0.0)
        return max(0.0, expected_delay * 8.0)

    def _velocity_trend(self) -> Optional[float]:
        direct_value = getattr(self.metrics, "velocity_trend", None)
        if direct_value is not None:
            return float(direct_value)
        actuals = [
            float(getattr(actual, "actual_effort_hrs", 0.0) or 0.0)
            for actual in getattr(self.project_state, "actuals", [])
            if float(getattr(actual, "actual_effort_hrs", 0.0) or 0.0) > 0.0
        ]
        if len(actuals) >= 2:
            start = actuals[0]
            end = actuals[-1]
            if start > 0:
                return (end - start) / start
        return None

    def detect(self) -> List[OpportunitySignal]:
        signals: List[OpportunitySignal] = []
        schedule_gap_hours = self._schedule_gap_hours()
        velocity_trend = self._velocity_trend()
        if schedule_gap_hours > 0:
            signals.append(
                OpportunitySignal(
                    signal_id=signal_id(SignalCategory.SCHEDULE, ["schedule_gap"]),
                    category=SignalCategory.SCHEDULE,
                    severity=SignalSeverity.HIGH,
                    affected_item_ids=[],
                    affected_resource_ids=[],
                    affected_sprint_ids=[],
                    affected_blocker_ids=[],
                    evidence=[
                        SignalEvidence(
                            source_engine="forecast_engine",
                            metric_name="schedule_gap_hours",
                            metric_value=schedule_gap_hours,
                            threshold=0.0,
                            explanation="Forecast indicates a schedule gap",
                        )
                    ],
                    context={
                        "schedule_gap_hours": round(schedule_gap_hours, 2),
                        "on_time_probability": round(self.monte_carlo.on_time_probability, 4),
                        "expected_delay_days": round(self.forecast.expected_delay_days, 2),
                        "velocity_trend": velocity_trend,
                        "velocity_degrading": bool(velocity_trend is not None and velocity_trend < -0.1),
                        "scope_inflation_pct": 0.0,
                        "flag": "SCHEDULE_GAP",
                    },
                    detected_at=datetime.now(timezone.utc).isoformat(),
                )
            )
        if self.monte_carlo.on_time_probability < 0.5:
            signals.append(
                OpportunitySignal(
                    signal_id=signal_id(SignalCategory.SCHEDULE, ["probability_concern"]),
                    category=SignalCategory.SCHEDULE,
                    severity=SignalSeverity.MEDIUM,
                    affected_item_ids=[],
                    affected_resource_ids=[],
                    affected_sprint_ids=[],
                    affected_blocker_ids=[],
                    evidence=[
                        SignalEvidence(
                            source_engine="monte_carlo_engine",
                            metric_name="on_time_probability",
                            metric_value=self.monte_carlo.on_time_probability,
                            threshold=0.5,
                            explanation="Monte Carlo probability of on-time delivery is below the threshold",
                        )
                    ],
                    context={
                        "schedule_gap_hours": round(schedule_gap_hours, 2),
                        "on_time_probability": round(self.monte_carlo.on_time_probability, 4),
                        "expected_delay_days": round(self.forecast.expected_delay_days, 2),
                        "velocity_trend": velocity_trend,
                        "velocity_degrading": bool(velocity_trend is not None and velocity_trend < -0.1),
                        "scope_inflation_pct": 0.0,
                        "flag": "PROBABILITY_CONCERN",
                    },
                    detected_at=datetime.now(timezone.utc).isoformat(),
                )
            )
        if velocity_trend is not None and velocity_trend < -0.1:
            signals.append(
                OpportunitySignal(
                    signal_id=signal_id(SignalCategory.SCHEDULE, ["velocity_concern"]),
                    category=SignalCategory.SCHEDULE,
                    severity=SignalSeverity.LOW,
                    affected_item_ids=[],
                    affected_resource_ids=[],
                    affected_sprint_ids=[],
                    affected_blocker_ids=[],
                    evidence=[
                        SignalEvidence(
                            source_engine="metrics_engine",
                            metric_name="velocity_trend",
                            metric_value=velocity_trend,
                            threshold=-0.1,
                            explanation="Velocity trend is degrading",
                        )
                    ],
                    context={
                        "schedule_gap_hours": round(schedule_gap_hours, 2),
                        "on_time_probability": round(self.monte_carlo.on_time_probability, 4),
                        "expected_delay_days": round(self.forecast.expected_delay_days, 2),
                        "velocity_trend": velocity_trend,
                        "velocity_degrading": True,
                        "scope_inflation_pct": 0.0,
                        "flag": "VELOCITY_CONCERN",
                    },
                    detected_at=datetime.now(timezone.utc).isoformat(),
                )
            )
        return signals
