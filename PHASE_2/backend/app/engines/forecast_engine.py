"""
Forecast Engine (deterministic)

Produces a single-point forecast based on remaining effort, current velocity,
critical-path sequencing, spillover, and blocker impacts. No Monte Carlo,
no probabilities.
"""
from datetime import datetime, timedelta
from typing import Optional

from app.domain.models import ProjectState, SprintStatus
from app.engines.metrics_engine import ProjectMetrics
from app.engines.critical_path_engine import CriticalPathResult
from app.engines.spillover_engine import SpilloverAnalysis
from app.api.models_phase3 import (
    ForecastResult,
    ForecastDelayBreakdown,
    ForecastScheduleDiagnostics,
    ForecastEffortBreakdown,
)


class ForecastEngine:
    """Deterministic forecast engine.

    High-level approach:
    - Use remaining effort (sum of remaining_effort_hrs) as the work to schedule.
    - Adjust for dependency sequencing by ensuring remaining work is at least
      the critical path duration (hours) — this captures serialisation delays.
    - Add spillover-induced extra work (predicted_spillover_count * avg_item_effort).
    - Project velocity = historical avg velocity per sprint adjusted for active
      blocker impact (velocity reduction factor). No randomness.
    - Compute remaining_sprints = adjusted_remaining_effort / projected_velocity
      and convert to days using project sprint length.
    - Return a single expected finish date (now + days) and derived fields.
    """

    def __init__(
        self,
        project_state: ProjectState,
        metrics: ProjectMetrics,
        cp_result: CriticalPathResult,
        spillover: Optional[SpilloverAnalysis] = None,
    ):
        self.project_state = project_state
        self.metrics = metrics
        self.cp_result = cp_result
        self.spillover = spillover

    def calculate(self) -> ForecastResult:
        """Calculate deterministic forecast and return ForecastResult."""

        # 1) Remaining effort (use metrics which sum remaining_effort_hrs)
        remaining_effort = float(self.metrics.remaining_effort_hours)

        # 2) R2: Account for dependency sequencing using REMAINING critical path effort
        # Use critical_path_remaining_hours (effort still to do on critical path), not full duration
        cp_remaining_hours = float(getattr(self.cp_result, "critical_path_remaining_hours", 0.0) or 0.0)
        adjusted_remaining = max(remaining_effort, cp_remaining_hours)

        # 3) Add spillover impact (convert predicted spillover items to hours)
        avg_item_effort = float(getattr(self.metrics, "average_item_effort", 20.0) or 20.0)
        spillover_hours = 0.0
        if self.spillover:
            try:
                total_spill = sum(self.spillover.predicted_spillover_by_sprint.values())
                spillover_hours = float(total_spill) * avg_item_effort
            except Exception:
                spillover_hours = 0.0

        adjusted_remaining += spillover_hours

        # 4) Projected velocity (hours per sprint), adjust for blocker impact
        base_velocity = float(self.metrics.actual_avg_velocity or self.metrics.planned_total_velocity or 1.0)
        blocker_impact = float(getattr(self.metrics, "estimated_blocker_velocity_impact", 0.0) or 0.0)

        projected_velocity = max(
            base_velocity * (1.0 - blocker_impact),
            base_velocity * 0.25,
        )

        # 5) Remaining sprints and days
        remaining_sprints = adjusted_remaining / projected_velocity if projected_velocity > 0 else float('inf')
        sprint_days = float(self.project_state.project_info.sprint_duration_days or 14)
        remaining_days = remaining_sprints * sprint_days

        # 6) Additive delay breakdown (same basis as expected_delay_days)
        # Partition remaining_days (which uses projected_velocity) into additive components
        pre_spillover_adjusted = max(remaining_effort, cp_remaining_hours)

        remaining_days_total = remaining_days
        if projected_velocity > 0:
            remaining_days_base_work = (pre_spillover_adjusted / projected_velocity) * sprint_days
            remaining_days_spillover = (spillover_hours / projected_velocity) * sprint_days
        else:
            remaining_days_base_work = 0.0
            remaining_days_spillover = 0.0

        # Blocker loss = residual slice after accounting for base work and spillover
        if projected_velocity > 0:
            remaining_days_blocker_loss = max(
                0.0,
                remaining_days - remaining_days_base_work - remaining_days_spillover,
            )
        else:
            remaining_days_blocker_loss = 0.0

        # Diagnostic breakdown (keeps original base_velocity-based values for explanation)
        base_schedule_days = (remaining_effort / base_velocity) * sprint_days if base_velocity > 0 else 0.0
        critical_path_days = 0.0
        if cp_remaining_hours > remaining_effort and base_velocity > 0:
            critical_path_days = ((cp_remaining_hours - remaining_effort) / base_velocity) * sprint_days
        spillover_days_diag = (spillover_hours / base_velocity) * sprint_days if base_velocity > 0 else 0.0
        blocker_days_diag = 0.0
        if base_velocity > 0:
            baseline_sprints = adjusted_remaining / base_velocity
            blocker_days_diag = max(0.0, (remaining_sprints - baseline_sprints) * sprint_days)
        diagnostic_total = base_schedule_days + critical_path_days + spillover_days_diag + blocker_days_diag

        # R1: Timeline Anchoring - calculate progress using workbook schedule dates,
        # not the current wall clock. This keeps forecasts deterministic and tied to
        # the planned project timeline.
        project_start = self.project_state.project_info.forecast_anchor_date()
        days_elapsed = self._calculate_schedule_elapsed_days(sprint_days)
        
        # Expected finish = project_start + elapsed + remaining
        expected_finish = project_start + timedelta(days=days_elapsed + remaining_days)

        # R5: Target Date Comparison
        target_end_date = self.project_state.project_info.target_end_date
        # planned window in days between anchor and target
        planned_window_days = float((target_end_date - project_start).days)

        # Use the additive decomposition for expected_delay_days so top-level
        # value matches the delay_breakdown exactly (preserve decimals).
        expected_delay_raw = days_elapsed + remaining_days - planned_window_days
        expected_delay_days = float(round(expected_delay_raw, 2))
        on_track = expected_delay_days <= 0

        # 7) Completion percentage (based on total effort and remaining effort)
        total_effort = float(getattr(self.metrics, "total_effort_hours", 0.0) or 0.0)
        if total_effort > 0:
            completion_pct = max(0.0, min(1.0, (total_effort - remaining_effort) / total_effort))
        else:
            completion_pct = 0.0

        return ForecastResult(
            target_end_date=target_end_date,
            expected_finish_date=expected_finish,
            expected_delay_days=float(round(expected_delay_days, 2)),
            remaining_effort_hours=adjusted_remaining,
            completion_percentage=completion_pct,
            projected_velocity=projected_velocity,
            on_track=on_track,
            raw_remaining_effort_hours=remaining_effort,
            critical_path_remaining_hours=cp_remaining_hours,
            spillover_penalty_hours=spillover_hours,
            blocker_penalty_hours=max(0.0, base_velocity - projected_velocity) * remaining_sprints if projected_velocity > 0 else 0.0,
            forecast_adjusted_effort_hours=adjusted_remaining,
            delay_breakdown={
                "planned_window_days": float(round(planned_window_days, 2)),
                "days_elapsed": float(round(days_elapsed, 2)),
                "remaining_days_total": float(round(remaining_days_total, 2)),
                "remaining_days_base_work": float(round(remaining_days_base_work, 2)),
                "remaining_days_spillover": float(round(remaining_days_spillover, 2)),
                "remaining_days_blocker_loss": float(round(remaining_days_blocker_loss, 2)),
                "expected_delay_days": float(round(days_elapsed + remaining_days_total - planned_window_days, 2)),
            },
            schedule_diagnostics={
                "is_additive": False,
                "base_schedule_days": float(round(base_schedule_days, 2)),
                "spillover_days": float(round(spillover_days_diag, 2)),
                "blocker_days": float(round(blocker_days_diag, 2)),
                "critical_path_days": float(round(critical_path_days, 2)),
                "diagnostic_total_days": float(round(diagnostic_total, 2)),
            },
            effort_breakdown={
                "raw_remaining_effort_hours": float(round(remaining_effort, 2)),
                "critical_path_remaining_hours": float(round(cp_remaining_hours, 2)),
                "spillover_penalty_hours": float(round(spillover_hours, 2)),
                "blocker_penalty_hours": float(round(max(0.0, base_velocity - projected_velocity) * remaining_sprints if projected_velocity > 0 else 0.0, 2)),
                "forecast_adjusted_effort_hours": float(round(adjusted_remaining, 2)),
            },
            forecast_vs_montecarlo_note=(
                "The deterministic forecast applies worst-credible-case assumptions: "
                "100% of predicted spillover and full blocker velocity reduction. "
                "Monte Carlo samples the full uncertainty range: spillover between 0-100% "
                "of predicted and blocker impact between 0% and the maximum estimated value. "
                "The on-time probability reflects how often optimistic scenarios occur. "
                "The delay figure reflects the pessimistic single-point estimate. "
                "Both are correct — they answer different questions."
            ),
        )

    def _calculate_schedule_elapsed_days(self, sprint_days: float) -> float:
        """Estimate elapsed project time using sprint schedule dates only."""
        completed_sprints = sum(
            1
            for sprint in self.project_state.sprints
            if (
                sprint.status == SprintStatus.COMPLETED
                or (isinstance(sprint.status, str) and sprint.status == SprintStatus.COMPLETED.value)
            )
        )

        days_from_completed = completed_sprints * sprint_days

        current_sprint = next(
            (
                sprint
                for sprint in self.project_state.sprints
                if (
                    sprint.status == SprintStatus.IN_PROGRESS
                    or (isinstance(sprint.status, str) and sprint.status == SprintStatus.IN_PROGRESS.value)
                )
            ),
            None,
        )
        if not current_sprint:
            return days_from_completed

        sprint_window_days = max(
            0.0,
            (current_sprint.end_date - current_sprint.start_date).total_seconds() / (24 * 3600),
        )
        return days_from_completed + min(sprint_window_days, sprint_days)
