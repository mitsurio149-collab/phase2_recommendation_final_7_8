# Sprint Whisperer — Recommendation Engine V2
## Full Architecture Specification & GitHub Copilot Implementation Guide

**Document Type:** Principal Architecture Review + Implementation Specification  
**Scope:** `backend/app/engines/recommendation_engine.py`, `simulation_engine.py`, `api/routes/recommendations.py`  
**Output Audience:** GitHub Copilot (implementation) + Engineering Lead (approval)

---

## Executive Summary

The existing recommendation subsystem suffers from seven confirmed architectural flaws that compound each other: counter-based recommendation IDs that change between requests, a seeded-but-undeclared Monte Carlo comparison that introduces noise masquerading as signal, generic action types used in simulation dispatch that produce unmeasurable state changes, resource lookups keyed on human-readable `.name` strings rather than stable IDs, signal detection embedded inside generation methods, no duplicate suppression, and a `CRITICAL_PATH_OPTIMIZATION` action whose simulation effect is an arbitrary 15% estimate with no engine backing.

The V2 design resolves all seven by separating the system into five independent, individually-testable layers: Signal Detection → Candidate Generation → Impact Estimation → Priority Scoring → Simulation. Each layer has a single responsibility, a typed contract, and is fully deterministic given the same `ProjectState` input.

The existing analytical engines (`metrics_engine`, `dependency_graph_engine`, `critical_path_engine`, `spillover_engine`, `forecast_engine`, `monte_carlo_engine`, `risk_engine`, `impact_scoring_engine`) are authoritative and are **not rewritten**. The V2 package wraps and orchestrates them.

---

## Part 1 — Repository Analysis

### 1.1 Engine Inventory

**MetricsEngine** (`metrics_engine.py`)
- Purpose: Derives aggregate project health indicators from raw `ProjectState`.
- Inputs: `ProjectState`
- Key Outputs: `ProjectMetrics` — `average_item_effort`, `velocity_trend`, `completion_rate`, `blocker_velocity_impact`, `items_at_risk`, `overloaded_resources`, `current_sprint_number`
- Consumed by: `ForecastEngine`, `MonteCarloEngine`, `RiskEngine`, `SpilloverAnalysisEngine`, `RecommendationEngine` (V1 + V2)

**DependencyGraphEngine** (`dependency_engine.py`)
- Purpose: Constructs a validated DAG with transitive closure and cycle detection.
- Inputs: `ProjectState`
- Key Outputs: `DependencyDAG` — `edges`, `transitive_closure`, `topological_order`, `has_cycles`
- Consumed by: `CriticalPathEngine`, `ImpactScoringEngine`, `RecommendationEngine` (for cascade computation)

**CriticalPathEngine** (`critical_path_engine.py`)
- Purpose: Forward/backward pass CPM over the DAG to identify the true critical path.
- Inputs: `ProjectState`, `DependencyDAG`
- Key Outputs: `CriticalPathResult` — `items_on_critical_path`, `slack_map`, `critical_path_hours`, `critical_path_count`
- Consumed by: `ForecastEngine`, `RiskEngine`, `ImpactScoringEngine`, `RecommendationEngine`

**SpilloverAnalysisEngine** (`spillover_engine.py`)
- Purpose: Probabilistic prediction of which items and sprints will overflow.
- Inputs: `ProjectState`, `avg_item_effort`
- Key Outputs: `SpilloverAnalysis` — `item_spillover_probability`, `sprint_spillover_probability`, `sprint_utilization`, `confidence_intervals`
- Consumed by: `ForecastEngine`, `MonteCarloEngine`, `RiskEngine`

**ForecastEngine** (`forecast_engine.py`)
- Purpose: Deterministic schedule forecast — remaining effort vs. capacity.
- Inputs: `ProjectState`, `ProjectMetrics`, `CriticalPathResult`, `SpilloverAnalysis`
- Key Outputs: `ForecastResult` — `expected_finish_date`, `expected_delay_days`, `remaining_effort_hours`, `remaining_capacity_hours`, `schedule_gap_hours`
- Consumed by: `MonteCarloEngine`, `RiskEngine`, `RecommendationEngine` (for schedule gap signals)

**MonteCarloEngine** (`monte_carlo_engine.py`)
- Purpose: Probabilistic completion date distribution via random simulation.
- Inputs: `ProjectState`, `ProjectMetrics`, `CriticalPathResult`, `SpilloverAnalysis`, `simulation_count`, `seed` (optional)
- Key Outputs: `MonteCarloResult` — `on_time_probability`, `p50_date`, `p80_date`, `expected_delay_days`, `risk_level`
- **Critical note:** `seed` parameter exists but is not provided by `RecommendationEngine._recalculate_summary()`, making the baseline vs. simulation comparison non-deterministic. This is the root cause of Monte Carlo noise flips.
- Consumed by: `RiskEngine`, `RecommendationEngine`

**RiskEngine** (`risk_engine.py`)
- Purpose: Composite risk scoring across schedule, dependency, resource, and scope dimensions.
- Inputs: `ProjectState`, `ProjectMetrics`, `CriticalPathResult`, `DependencyDAG`, `SpilloverAnalysis`, `ForecastResult`, `MonteCarloResult`, `RiskScores`
- Key Outputs: `RiskResult` — `overall_risk_score`, `schedule_risk`, `dependency_risk`, `resource_risk`, `scope_risk`, `sprint_risks`
- Consumed by: `RecommendationEngine` (priority scoring uses `overall_risk_score`)

**ImpactScoringEngine** (`impact_scoring_engine.py`)
- Purpose: Per-item risk score based on blocker cascade depth and dependency depth.
- Inputs: `ProjectState`, `DependencyDAG`
- Key Outputs: `RiskScores` — `item_scores`, `blocker_impact_scores`, `dependency_depth_scores`, `sprint_blocker_impact`
- Consumed by: `RiskEngine`, `RecommendationEngine`

### 1.2 Current Recommendation Files

**recommendation_engine.py** (V1)
- 1,100+ lines, monolithic class `RecommendationEngine`
- Mixes signal detection, candidate generation, impact estimation, simulation dispatch, and scoring in a single class
- Issues catalogued in §1.3

**simulation_engine.py** (V1)
- Separate `SimulationEngine` class that clones state and re-runs downstream engines
- Seed not propagated through Monte Carlo, making simulation results non-repeatable
- Action dispatch keyed on `RecommendationType` enum string values
- `_apply_critical_path_optimization` applies a hardcoded 15% reduction with no engine grounding

### 1.3 Dependency Graph (Current V1)

```
ProjectState
├── MetricsEngine
│   └── → ForecastEngine
│       └── → MonteCarloEngine (no seed ← BUG)
│           └── → RiskEngine
├── DependencyGraphEngine
│   ├── → CriticalPathEngine
│   │   └── → ForecastEngine (above)
│   └── → ImpactScoringEngine
│       └── → RiskEngine (above)
├── SpilloverAnalysisEngine
│   └── → ForecastEngine (above)
└── RecommendationEngine ← consumes all of the above
    ├── _generate_blocker_recommendations()  — detects + generates (mixed)
    ├── _generate_resource_recommendations() — detects + generates (mixed)
    ├── _generate_cp_optimization_recommendations() — generic bucket (BUG)
    ├── _simulate_candidate()                — re-runs ALL engines per candidate (expensive)
    └── SimulationEngine                     — separate but shares same seed bug
```

**Circular dependencies:** None detected.  
**Duplicated calculations:** `_recalculate_summary()` in `RecommendationEngine` and `_recalculate_clone()` in `SimulationEngine` are nearly identical — code duplication that creates divergence risk.  
**Hidden coupling:** `_apply_reassign_work` in both `RecommendationEngine` and `SimulationEngine` looks up resources by `.name` string (line 788 in `recommendation_engine.py`). If two resources share a name, the lookup is silently wrong.

### 1.4 Current Architecture Findings

| # | Finding | Severity | File | Detail |
|---|---------|----------|------|--------|
| F1 | Counter-based recommendation IDs | **Critical** | `recommendation_engine.py:977` | `REC-001`, `REC-002`, etc. change if any generator is added, removed, or reordered. IDs are not stable across restarts. |
| F2 | Monte Carlo seed not propagated in simulation | **Critical** | `recommendation_engine.py:_recalculate_summary` | `MonteCarloEngine` called without `seed=` parameter. Baseline and simulated probabilities come from different random draws, producing noise-driven probability deltas that may flip sign. |
| F3 | Signal detection embedded in generation | **High** | `recommendation_engine.py:281–640` | Each `_generate_*` method performs its own condition checks. Signals cannot be unit-tested, reused, or inspected independently. |
| F4 | Generic `CRITICAL_PATH_OPTIMIZATION` action type | **High** | `recommendation_engine.py:629`, `simulation_engine.py:321` | The action emits a non-specific "optimize critical path" recommendation, and simulation applies a hardcoded 15% reduction with no engine backing. The impact is fabricated. |
| F5 | Resource lookup by `.name` string | **High** | `recommendation_engine.py:788`, `simulation_engine.py:302` | `next((r for r in clone.team if r.name == to_name), None)` — silently fails if name not found; silently wrong if names are not unique. Should use `resource_id`. |
| F6 | No duplicate suppression | **Medium** | `recommendation_engine.py:209` | Multiple generators can produce overlapping recommendations for the same root cause. No deduplication exists. |
| F7 | `simulate_recommendation` requires full generation first | **Medium** | `recommendation_engine.py:232` | `simulate_recommendation(id)` calls `_find_candidate_by_id` which searches `_cached_candidates`. If `generate_recommendations()` was not called first in this instance, the cache is empty. Stateful coupling. |
| F8 | Simulation re-runs ALL engines per candidate | **Medium** | `recommendation_engine.py:_simulate_candidate` | Full engine pipeline re-runs for each candidate during `generate_recommendations()`. With 10 candidates this is 10× full engine invocations inside a single API call. |
| F9 | Monte Carlo seed in `simulate_scenario` not set | **Medium** | `recommendation_engine.py:244` | `SimulationEngine` created without `seed=` parameter in scenario path, so scenario comparison is non-deterministic. |
| F10 | Priority scoring uses raw probability delta | **Low** | `recommendation_engine.py:_score_candidate` | Noise thresholds suppress small deltas, but the underlying scoring formula is not documented and has no configurable weights. |

---

## Part 2 — Recommendation Engine V2 Design

### 2.1 Architectural Principles

**Principle 1 — Separate Signal Detection from Candidate Generation**  
Why: Signals represent facts about the project state (a blocker affects 3 critical path items). Recommendations represent proposed actions (reassign item X to resource Y). These are different concerns with different testing requirements. Mixing them makes both untestable.

**Principle 2 — Determinism by construction**  
Why: Any non-deterministic output means recommendation IDs change between API calls, simulation deltas flip, and users distrust the system. All randomness is seeded with `seed=42`, always.

**Principle 3 — Never fabricate impact values**  
Why: If the system invents a "saves 3 days" value, users will eventually discover it is wrong and trust collapses entirely. Every impact value must trace to an upstream engine output or a deterministic formula over engine outputs.

**Principle 4 — Stable identifiers derived from content, not position**  
Why: Counter-based IDs couple identifier stability to execution order. A content-derived hash (SHA-1 of action type + sorted target IDs) is stable regardless of which generators run, in what order, or how many times.

**Principle 5 — Simulation must not mutate shared state**  
Why: Deep-cloning `ProjectState` before any simulation application prevents cross-simulation contamination and makes the system safe for concurrent simulation requests.

**Principle 6 — Impact estimation is a separate, engine-backed layer**  
Why: Centralizing impact estimation means every recommendation type uses the same evidence-based methodology. It also enables future LLM narrative generation to consume `ImpactEstimate` without needing access to internal engine logic.

**Principle 7 — Priority scoring is weight-driven, not rule-driven**  
Why: A fixed priority ladder (blockers always beat capacity, capacity always beats schedule) encodes assumptions that change per project context. A configurable weight vector produces a total ordering that can be tuned without code changes.

### 2.2 Proposed Package Structure

```
backend/app/engines/recommendations/
├── __init__.py
├── models.py                    # All data contracts (signals, recommendations, results)
├── signals.py                   # OpportunitySignal type definitions + SignalCategory/Severity enums
├── signal_detectors.py          # Five detector classes, one per signal family
├── candidate_generator.py       # Converts List[OpportunitySignal] → List[RecommendationCandidate]
├── impact_estimator.py          # ImpactEstimator: evidence-backed hours/days/confidence
├── priority_engine.py           # PriorityEngine: configurable weight-based scoring
├── simulation_engine_v2.py      # SimulationEngineV2: deterministic what-if engine
└── recommendation_engine_v2.py  # Orchestrator: pipeline entry point
```

**File responsibilities:**

`models.py` — All frozen dataclasses and Pydantic models used across the package. Imports nothing from within the `recommendations/` subpackage to prevent circular imports.

`signals.py` — Enumerations: `SignalCategory`, `SignalSeverity`, `SignalEvidence`. The `OpportunitySignal` base dataclass and all signal-family subclasses.

`signal_detectors.py` — Five stateless detector classes: `BlockerDetector`, `CapacityDetector`, `SprintDetector`, `CriticalPathDetector`, `ScheduleDetector`. Each receives pre-computed engine outputs and returns `List[OpportunitySignal]`.

`candidate_generator.py` — `CandidateGenerator` maps each `OpportunitySignal` to zero or more specific, actionable `RecommendationCandidate` instances. No hardcoded buckets. Includes root-cause grouping and duplicate suppression.

`impact_estimator.py` — `ImpactEstimator` receives a `RecommendationCandidate` and upstream engine outputs and returns an `ImpactEstimate` with sourced values for hours recovered, delay reduction, and confidence.

`priority_engine.py` — `PriorityEngine` scores each candidate using five weighted sub-factors and returns a ranked list.

`simulation_engine_v2.py` — `SimulationEngineV2` deep-clones `ProjectState`, applies action mutations, and re-runs the engine pipeline with `seed=42` for reproducibility.

`recommendation_engine_v2.py` — `RecommendationEngineV2` orchestrates the full pipeline and exposes three public methods: `generate()`, `simulate(recommendation_id)`, `simulate_scenario(recommendation_ids)`.

---

## Part 3 — Signal Architecture

### 3.1 Core Signal Types

```python
# signals.py

class SignalCategory(str, Enum):
    BLOCKER = "blocker"
    CAPACITY = "capacity"
    SPRINT = "sprint"
    CRITICAL_PATH = "critical_path"
    SCHEDULE = "schedule"
    RISK = "risk"
    SPILLOVER = "spillover"
    DEPENDENCY = "dependency"

class SignalSeverity(str, Enum):
    CRITICAL = "critical"   # Immediate action required; CP impact confirmed
    HIGH = "high"           # Strong evidence, measurable impact
    MEDIUM = "medium"       # Moderate evidence, probabilistic impact
    LOW = "low"             # Weak signal, advisory only

@dataclass(frozen=True)
class SignalEvidence:
    source_engine: str          # "critical_path_engine", "risk_engine", etc.
    metric_name: str            # "on_time_probability", "slack_hours", etc.
    metric_value: float
    threshold: float
    explanation: str

@dataclass(frozen=True)
class OpportunitySignal:
    signal_id: str              # stable hash of category + target_ids
    category: SignalCategory
    severity: SignalSeverity
    affected_item_ids: List[str]
    affected_resource_ids: List[str]
    affected_sprint_ids: List[str]
    affected_blocker_ids: List[str]
    evidence: List[SignalEvidence]
    context: Dict[str, Any]     # signal-family-specific payload
    detected_at: str            # ISO timestamp, set once at detection time
```

### 3.2 Signal Families

#### Blocker Signals (`BlockerDetector`)
**Trigger conditions:**
- Active blocker exists (no `actual_resolution_date`)
- Impacted items include at least one critical path item: severity → CRITICAL
- Impacted items NOT on CP but cascade size ≥ 3: severity → HIGH
- Impacted items NOT on CP, cascade size < 3: severity → MEDIUM

**Required inputs:** `ProjectState.blockers`, `CriticalPathResult.items_on_critical_path`, `DependencyDAG.transitive_closure`, `ImpactScoringEngine.blocker_impact_scores`

**Signal context payload:**
```python
{
    "blocker_id": str,
    "category": BlockerCategory,
    "severity": BlockerSeverity,
    "impacted_item_ids": List[str],
    "cascade_item_ids": List[str],       # transitive successors via DAG
    "blocked_hours": float,              # sum of remaining_effort_hrs for impacted items
    "on_critical_path": bool,
    "days_until_target_resolution": int,
    "sprint_gate_pct": float,            # blocked_hours / sprint planned_velocity_hrs
    "affected_sprint_numbers": List[int],
}
```

**Confidence:** HIGH if blocker.severity == CRITICAL and on_critical_path; MEDIUM otherwise.

#### Capacity Signals (`CapacityDetector`)
**Trigger conditions:**
- Resource load ratio > 1.2 (remaining_hrs / effective_remaining_capacity): OVERLOADED
- Resource load ratio < 0.4 AND remaining sprints ≥ 2: UNDERUTILIZED
- Single resource owns > 60% of critical path remaining hours: CONCENTRATION

**Required inputs:** `ProjectMetrics` (overloaded_resources), `ImpactScoringEngine.item_scores`, `CriticalPathResult.items_on_critical_path`

**Signal context payload:**
```python
{
    "resource_id": str,              # Always ID, never name
    "load_ratio": float,
    "assigned_remaining_hrs": float,
    "effective_remaining_capacity_hrs": float,
    "flag": str,                     # OVERLOADED | UNDERUTILIZED | CONCENTRATION
    "cp_items_owned": List[str],
    "is_single_owner_of_cp": bool,
    "owns_blocked_cp_items": bool,
}
```

**Confidence:** HIGH if resource owns blocked CP items; MEDIUM if overloaded only; LOW if underutilized.

#### Sprint Signals (`SprintDetector`)
**Trigger conditions:**
- Sprint utilization > 1.1 (planned hours > capacity): OVERLOADED
- Sprint utilization < 0.5 AND sprint is not the current sprint: UNDERLOADED
- > 60% of sprint's planned hours are from blocked items: BLOCKER_GATED
- `SpilloverAnalysis.sprint_spillover_probability[sprint_num]` > 0.6: SPILLOVER_RISK

**Required inputs:** `ProjectMetrics`, `SpilloverAnalysis`, `ForecastEngine` output, `ProjectState.sprints`

**Signal context payload:**
```python
{
    "sprint_id": str,
    "sprint_number": int,
    "flag": str,                     # OVERLOADED | UNDERLOADED | BLOCKER_GATED | SPILLOVER_RISK
    "utilization_ratio": float,
    "planned_hours": float,
    "capacity_hours": float,
    "blocked_hours": float,
    "blocked_pct": float,
    "spillover_probability": float,
    "is_cp_sprint": bool,
}
```

#### Critical Path Signals (`CriticalPathDetector`)
**Trigger conditions:**
- Any CP item is blocked: CP_AT_RISK → severity CRITICAL
- A single resource owns > 2 CP items AND has availability < 1.0: OWNER_RISK → HIGH
- Items with slack < 0.25 × sprint_duration_hours > 3: NEAR_CRITICAL_RISK → MEDIUM
- CP has a single dependency bottleneck (one item feeds > 3 CP items): DEPENDENCY_BOTTLENECK → HIGH

**Required inputs:** `CriticalPathResult`, `DependencyDAG`, `ImpactScoringEngine`

**Signal context payload:**
```python
{
    "cp_nodes": List[str],
    "cp_remaining_hours": float,
    "cp_single_owners": List[str],   # resource_ids, not names
    "cp_blocked_items": List[str],
    "near_critical_items": List[str],
    "dependency_bottleneck_item_ids": List[str],
    "flag": str,
}
```

#### Schedule Signals (`ScheduleDetector`)
**Trigger conditions:**
- `ForecastResult.schedule_gap_hours` > 0: SCHEDULE_GAP
- `ProjectMetrics.velocity_trend` < -0.1 (degrading): VELOCITY_CONCERN
- Scope added in last sprint > 10% of remaining: SCOPE_INFLATION
- `MonteCarloResult.on_time_probability` < 0.5: PROBABILITY_CONCERN

**Required inputs:** `ForecastResult`, `MonteCarloResult`, `RiskResult`

**Signal context payload:**
```python
{
    "schedule_gap_hours": float,
    "on_time_probability": float,
    "expected_delay_days": float,
    "velocity_trend": Optional[float],
    "velocity_degrading": bool,
    "scope_inflation_pct": float,
    "flag": str,
}
```

### 3.3 Signal ID Generation

```python
import hashlib

def signal_id(category: SignalCategory, target_ids: List[str]) -> str:
    key = f"sig:{category.value}:{':'.join(sorted(target_ids))}"
    return hashlib.sha1(key.encode()).hexdigest()[:10]
```

---

## Part 4 — Candidate Generation Architecture

### 4.1 Design Contract

`CandidateGenerator` receives:
- `List[OpportunitySignal]` — from all detectors
- All upstream engine outputs — for candidate feasibility checks
- `ProjectState` — for entity resolution

It returns `List[RecommendationCandidate]` where each candidate:
- Has a stable `recommendation_id` derived from action type + sorted target IDs
- References specific entity IDs (item_ids, resource_ids, sprint_ids) — never names
- Was generated from a specific `OpportunitySignal` (traceable root cause)
- Has passed basic feasibility checks before being emitted

### 4.2 Data Contracts

```python
@dataclass
class RecommendationAction(str, Enum):
    RESOLVE_BLOCKER = "resolve_blocker"
    REASSIGN_ITEM = "reassign_item"
    SPLIT_ITEM = "split_item"
    ADVANCE_ITEM_TO_EARLIER_SPRINT = "advance_item_to_earlier_sprint"
    PARALLELIZE_ITEMS = "parallelize_items"
    REBALANCE_SPRINT_LOAD = "rebalance_sprint_load"
    REMOVE_DEPENDENCY_BOTTLENECK = "remove_dependency_bottleneck"
    ADD_RESOURCE_SKILL = "add_resource_skill"

@dataclass
class RecommendationCandidate:
    recommendation_id: str          # stable_id(action_type, target_ids)
    action_type: RecommendationAction
    title: str                      # "Reassign WI-042 to Alice (R-003)"
    description: str                # Full action description
    affected_item_ids: List[str]
    affected_resource_ids: List[str]   # resource_id, not name
    affected_sprint_ids: List[str]
    affected_blocker_ids: List[str]
    root_cause_signal_id: str       # which OpportunitySignal triggered this
    supporting_signal_ids: List[str]
    simulation_params: Dict[str, Any]  # structured inputs for SimulationEngineV2
    feasibility_checks: Dict[str, bool]

@dataclass
class ImpactEstimate:
    estimated_hours_recovered: float
    estimated_delay_reduction_days: float
    estimated_risk_reduction: float
    confidence: str                 # HIGH | MEDIUM | LOW
    evidence: List[SignalEvidence]
    calculation_notes: str

@dataclass
class Recommendation:
    recommendation_id: str
    title: str
    description: str
    action_type: RecommendationAction
    priority_score: float
    confidence: str
    estimated_hours_recovered: float
    estimated_delay_reduction_days: float
    affected_item_ids: List[str]
    affected_resource_ids: List[str]
    affected_sprint_ids: List[str]
    root_cause_signal_id: str
    supporting_signal_ids: List[str]
    impact_evidence: List[SignalEvidence]
    metadata: Dict[str, Any]
```

### 4.3 Candidate Generation Rules

**Rule 1 — One signal, one or more specific candidates**
A `BlockerSignal` for blocker B1 affecting items [WI-001, WI-002] should generate:
- One `RESOLVE_BLOCKER` candidate targeting blocker B1
- One `ADVANCE_ITEM_TO_EARLIER_SPRINT` candidate per item that can be moved if it has no other active blockers

**Rule 2 — No generic buckets**
`CRITICAL_PATH_OPTIMIZATION` as a type is **forbidden**. Instead, if the CriticalPathDetector emits a `CP_AT_RISK` signal because WI-010 is blocked, the generator emits a `RESOLVE_BLOCKER` candidate for the specific blocker, and an `ADVANCE_ITEM_TO_EARLIER_SPRINT` candidate for any CP items that can proceed around the blocker.

**Rule 3 — Duplicate suppression via ID set**
Before appending a candidate, check if its `recommendation_id` (hash of action_type + sorted target_ids) is already in the emitted set. If so, merge `supporting_signal_ids` into the existing candidate rather than creating a duplicate.

**Rule 4 — Root cause grouping**
If two signals produce a candidate with the same target (e.g., a blocker signal and a CP signal both trigger `RESOLVE_BLOCKER` for blocker B1), the deduplicated candidate carries both signal IDs in `supporting_signal_ids`, raising its evidence strength.

**Rule 5 — Feasibility gates before emission**
Every candidate must pass feasibility checks relevant to its action type before being emitted:

| Action Type | Feasibility Checks |
|-------------|-------------------|
| `REASSIGN_ITEM` | Target resource exists, has available capacity, has required skill |
| `ADVANCE_ITEM_TO_EARLIER_SPRINT` | Prior sprint has unblocked capacity, item has no unresolved predecessors in current sprint |
| `PARALLELIZE_ITEMS` | Items do not have a dependency relationship in the DAG |
| `SPLIT_ITEM` | Item has remaining_effort_hrs > minimum threshold (configurable, default: 4h) |
| `RESOLVE_BLOCKER` | Blocker is still active (no actual_resolution_date) |

### 4.4 Stable Recommendation ID

```python
import hashlib

def stable_id(action_type: str, target_ids: List[str]) -> str:
    key = f"{action_type}:{':'.join(sorted(target_ids))}"
    return hashlib.sha1(key.encode()).hexdigest()[:10]
```

This is identical to the spec. IDs are:
- Stable across engine restarts (pure function of content)
- Stable across route invocations (same project state → same IDs)
- Stable across simulation requests
- Independent of generation order (target_ids are sorted before hashing)

**Collision handling:** SHA-1 with 10-hex-char output gives 2^40 ≈ 1 trillion possible IDs. For project sizes of hundreds of recommendations, collision probability is negligible. If a collision is detected (same ID, different content), append a 1-character disambiguation suffix: `{id}a`, `{id}b`. Log as a warning.

---

## Part 5 — Impact Estimation Architecture

### 5.1 Design Principles

- Every value returned by `ImpactEstimator` must trace to an upstream engine field or a deterministic formula over those fields.
- No hardcoded percentage reductions (the 15% in V1's `_apply_critical_path_optimization` is the primary violation).
- Confidence is determined by the strength of the evidence chain, not by the action type.

### 5.2 Estimation Methods by Action Type

**`RESOLVE_BLOCKER`**
- `hours_recovered` = `BlockerSignal.blocked_hours` (directly from `ImpactScoringEngine.blocker_impact_scores` or sum of `remaining_effort_hrs` for impacted items)
- `delay_reduction_days` = IF `on_critical_path`: `ForecastResult.expected_delay_days × (blocked_hours / cp_remaining_hours)`, capped at `blocked_hours / team_velocity_hrs_per_day`; ELSE: 0.0
- Confidence: HIGH if `on_critical_path`; MEDIUM if cascade_size ≥ 3; LOW otherwise
- Evidence source: `critical_path_engine`, `impact_scoring_engine`

**`REASSIGN_ITEM`**
- `hours_recovered` = 0.0 (reassignment doesn't reduce work; it reduces schedule risk)
- `delay_reduction_days` = `item.remaining_effort_hrs / (target_resource_velocity - current_resource_velocity)` where velocities are derived from `ProjectMetrics`; clamp to [0, `ForecastResult.expected_delay_days`]
- Confidence: MEDIUM (depends on velocity estimates)
- Evidence source: `metrics_engine`

**`ADVANCE_ITEM_TO_EARLIER_SPRINT`**
- `hours_recovered` = 0.0 (no work removed, schedule headroom created)
- `delay_reduction_days` = difference in sprint end date if item ships in sprint N-1 vs. sprint N, based on `ForecastResult.sprint_end_dates`
- Confidence: MEDIUM if item has no dependencies on current sprint; LOW if uncertain
- Evidence source: `forecast_engine`, `spillover_engine`

**`PARALLELIZE_ITEMS`**
- `hours_recovered` = `successor.remaining_effort_hrs × overlap_fraction` where `overlap_fraction = min(predecessor.remaining_effort_hrs, successor.remaining_effort_hrs) / max(...)` — engine-derived
- `delay_reduction_days` = `hours_recovered / team_velocity_hrs_per_day`
- Confidence: MEDIUM
- Evidence source: `dependency_graph_engine`, `forecast_engine`

**`SPLIT_ITEM`**
- `hours_recovered` = 0.0 (scope neutral)
- `delay_reduction_days` = estimated sprint brought forward if partial deliverable reduces CP hours; use `CriticalPathResult.slack_map` to determine if split changes CP
- Confidence: LOW (highly dependent on how the split is executed)
- Evidence source: `critical_path_engine`

**`ADD_RESOURCE_SKILL`**
- `hours_recovered` = `ForecastResult.schedule_gap_hours × resource_allocation_fraction` (e.g., 1.0 FTE for remainder)
- `delay_reduction_days` = `hours_recovered / (new_team_velocity_hrs_per_day - current_velocity)`
- Confidence: LOW (velocity of new resource is uncertain)
- Evidence source: `forecast_engine`, `metrics_engine`

**`REMOVE_DEPENDENCY_BOTTLENECK`**
- `hours_recovered` = sum of `remaining_effort_hrs` for items blocked by the bottleneck node
- `delay_reduction_days` = CP slack freed, sourced from `CriticalPathResult`
- Confidence: HIGH if bottleneck is on critical path; MEDIUM otherwise
- Evidence source: `dependency_graph_engine`, `critical_path_engine`

### 5.3 Confidence Model

```
HIGH:  Evidence comes from confirmed critical path analysis + blocker cascade data
MEDIUM: Evidence comes from workload/capacity analysis or velocity trends
LOW:   Evidence comes from probabilistic schedule forecasts or Monte Carlo scenarios
```

Confidence degrades one level if:
- The target resource's velocity has < 2 sprints of historical data
- The affected sprint is more than 3 sprints away (high uncertainty)
- The item's estimate has changed > 50% from original in this sprint

---

## Part 6 — Priority Scoring Architecture

### 6.1 Scoring Formula

```
priority_score = (
    w_risk      × risk_reduction_score        +
    w_schedule  × schedule_improvement_score  +
    w_blocker   × blocker_reduction_score     +
    w_cp        × cp_protection_score         +
    w_capacity  × capacity_improvement_score
)
```

Default weights: `w_risk=0.30, w_schedule=0.25, w_blocker=0.25, w_cp=0.15, w_capacity=0.05`  
All weights must sum to 1.0. Weights are configurable via `ScoringWeights` dataclass passed to `PriorityEngine.__init__`.

### 6.2 Sub-Factor Calculation

**`risk_reduction_score`** [0.0 – 1.0]  
= `impact.estimated_risk_reduction / RiskResult.overall_risk_score` (clamped to 1.0)  
Source: `risk_engine` output, not fabricated.

**`schedule_improvement_score`** [0.0 – 1.0]  
= `impact.estimated_delay_reduction_days / ForecastResult.expected_delay_days` (clamped to 1.0, 0.0 if no delay)

**`blocker_reduction_score`** [0.0 – 1.0]  
= 1.0 if action type is `RESOLVE_BLOCKER` and signal severity is CRITICAL  
= 0.7 if action type is `RESOLVE_BLOCKER` and signal severity is HIGH  
= 0.0 for non-blocker actions  
(This makes blocker-resolving actions compete on weighted terms, not a fixed ladder)

**`cp_protection_score`** [0.0 – 1.0]  
= `len(affected_cp_items) / len(CriticalPathResult.items_on_critical_path)` (clamped to 1.0)  
If no CP items affected: 0.0

**`capacity_improvement_score`** [0.0 – 1.0]  
= For REASSIGN/REBALANCE actions: `abs(load_delta) / max_load_ratio` where `max_load_ratio` = overloaded resource's load ratio  
= 0.0 for non-capacity actions

### 6.3 Tie-breaking

When two candidates have equal `priority_score` (within 0.001), rank by:
1. `confidence` (HIGH > MEDIUM > LOW)
2. `estimated_hours_recovered` descending
3. `recommendation_id` lexicographic ascending (deterministic final tiebreak)

---

## Part 7 — Simulation Architecture

### 7.1 SimulationEngineV2 Interface

```python
class SimulationEngineV2:
    SEED = 42   # Module-level constant — never overridden

    def __init__(
        self,
        project_state: ProjectState,
        upstream: UpstreamEngineOutputs,    # pre-computed engine outputs
    ): ...

    def simulate(
        self, recommendation: Recommendation
    ) -> SimulationResult: ...

    def simulate_scenario(
        self, recommendations: List[Recommendation]
    ) -> SimulationResult: ...
```

`UpstreamEngineOutputs` is a frozen dataclass holding pre-computed outputs from all upstream engines. The orchestrator computes these once and passes them to both `RecommendationEngineV2` and `SimulationEngineV2`. This eliminates the current problem where `_recalculate_summary()` and `_recalculate_clone()` contain nearly-identical but separately-maintained engine pipelines.

### 7.2 Simulation Process

```
1. Deep clone ProjectState → simulated_state
2. Apply recommendation.simulation_params to simulated_state via ActionApplicator
3. Re-run engine pipeline on simulated_state with seed=42:
   a. MetricsEngine(simulated_state).calculate()
   b. DependencyGraphEngine(simulated_state).build_dag()
   c. CriticalPathEngine(simulated_state, dag).analyze()
   d. SpilloverAnalysisEngine(simulated_state, avg_effort).analyze()
   e. ForecastEngine(simulated_state, metrics, cp, spillover).calculate()
   f. MonteCarloEngine(simulated_state, ..., seed=42).calculate()    ← SEED ALWAYS SET
   g. ImpactScoringEngine(simulated_state, dag).score()
   h. RiskEngine(simulated_state, ...).analyze()
4. Compute SimulationResult as delta: simulated - baseline
5. Baseline values come from upstream.monte_carlo / upstream.forecast / upstream.risk_result
   (also computed with seed=42)
```

### 7.3 ActionApplicator

`ActionApplicator` replaces the current split dispatch between `RecommendationEngine._apply_*` and `SimulationEngine._apply_*`. There is now ONE applicator used for both single-recommendation simulation and scenario simulation. Each method is keyed on `RecommendationAction` enum, not `RecommendationType`.

```python
class ActionApplicator:
    def apply(self, state: ProjectState, rec: Recommendation) -> None:
        handler = self._handlers.get(rec.action_type)
        if not handler:
            raise SimulationError(f"No handler for action type: {rec.action_type}")
        handler(state, rec)

    def _apply_resolve_blocker(self, state, rec): ...
    def _apply_reassign_item(self, state, rec): ...       # uses resource_id, not name
    def _apply_split_item(self, state, rec): ...
    def _apply_advance_item(self, state, rec): ...
    def _apply_parallelize_items(self, state, rec): ...
    def _apply_rebalance_sprint_load(self, state, rec): ...
    def _apply_remove_dependency_bottleneck(self, state, rec): ...
    def _apply_add_resource_skill(self, state, rec): ...
```

**Critical fix for F5:** All resource lookups inside `ActionApplicator` use `resource_id` (from `rec.affected_resource_ids`). The `simulation_params` dict stored on the candidate must contain `target_resource_id`, not `target_resource_name`.

### 7.4 SimulationResult Contract

```python
@dataclass
class SimulationResult:
    recommendation_ids: List[str]
    baseline_metrics: BaselineMetrics
    simulated_metrics: SimulatedMetrics
    delta_on_time_probability: float
    delta_expected_delay_days: float
    delta_spillover_risk: float
    delta_risk_score: float
    seed_used: int                      # always 42 — included for audit
    is_positive_impact: bool
    summary: str

@dataclass
class BaselineMetrics:
    on_time_probability: float
    expected_delay_days: float
    overall_risk_score: float
    critical_path_hours: float

@dataclass
class SimulatedMetrics:
    on_time_probability: float
    expected_delay_days: float
    overall_risk_score: float
    critical_path_hours: float
```

### 7.5 Determinism Requirements

- `MonteCarloEngine` must ALWAYS be called with `seed=42` in both baseline and simulation paths.
- The baseline `UpstreamEngineOutputs` computed at the start of a request must also use `seed=42`.
- The `SEED = 42` constant must live at module level in `simulation_engine_v2.py` — not as a default parameter that could be silently overridden.
- Simulation results are fully reproducible: same `ProjectState` + same `recommendation_id` → identical `SimulationResult`.
- Scenario simulation applies actions in deterministic order: sorted by `recommendation_id` lexicographically before applying.

---

## Part 8 — Testing Strategy

### 8.1 Unit Tests

**`test_signal_detectors.py`**
- For each detector: provide minimal `ProjectState` fixture, assert correct `OpportunitySignal` fields
- Test severity thresholds (boundary conditions: load_ratio = 1.19 → no signal, 1.20 → MEDIUM, 1.21 → HIGH)
- Test signal_id stability: same inputs → same ID across 100 repeated calls
- Test empty state: no blockers, no items → empty signal list, no exceptions

**`test_candidate_generator.py`**
- Test deduplication: two signals for same target → one candidate with both signal_ids in `supporting_signal_ids`
- Test feasibility gates: candidate not emitted if feasibility check fails
- Test stable ID: `stable_id(action, targets)` returns same result regardless of target order
- Test all action types produce candidates with populated `simulation_params`

**`test_impact_estimator.py`**
- For each action type: assert `estimated_hours_recovered` is non-negative and not greater than total remaining hours
- Assert values trace to engine output fields (mock engine outputs, verify formula)
- Test confidence degradation rules

**`test_priority_engine.py`**
- Weights sum to 1.0 assertion
- Test ordering: CRITICAL CP blocker > MEDIUM capacity concern
- Test configurable weights: if `w_schedule=1.0, others=0.0`, highest schedule improvement wins
- Test tiebreaking determinism

**`test_simulation_engine_v2.py`**
- Test seed: two identical calls produce identical `SimulationResult`
- Test non-mutation: original `ProjectState` unchanged after simulation
- Test baseline comparison: if no action applied, `delta_*` fields are ~0.0 (floating point tolerance)
- Test each `ActionApplicator` method: correct state mutation, resource lookup by ID
- Test scenario order determinism: applying [R1, R2] in either order produces same result

**`test_stable_id.py`**
- `stable_id("reassign_item", ["WI-001", "R-003"])` == `stable_id("reassign_item", ["R-003", "WI-001"])`
- Different action types with same targets → different IDs
- Same action type and targets → identical IDs across 1000 calls

### 8.2 Integration Tests

**`test_recommendation_pipeline.py`**
- Load the included demo `ProjectState` fixture
- Run `RecommendationEngineV2.generate()` twice; assert identical recommendation lists (same IDs, same order)
- Assert no recommendation has `estimated_hours_recovered > total_remaining_hours`
- Assert no two recommendations share the same `recommendation_id`
- Assert all `affected_resource_ids` resolve to resources in `ProjectState.team`
- Assert all `affected_item_ids` resolve to items in `ProjectState.work_items`

**`test_simulation_integration.py`**
- Generate recommendations, then simulate each one
- Assert `delta_on_time_probability` is within [-1.0, 1.0]
- Assert `delta_expected_delay_days` does not exceed baseline `expected_delay_days`
- Assert `seed_used == 42` in all results

### 8.3 Regression Tests

Create a golden file `tests/fixtures/golden_recommendations.json` from the first correct V2 run. On each subsequent test run, assert:
- Same recommendation IDs present
- Priority order stable
- Impact estimates within ±0.5% tolerance

### 8.4 Contract Tests

Verify that `Recommendation.to_dict()` output is backward-compatible with the existing `RecommendationResponse` Pydantic schema in `models_phase3.py`. If fields are renamed, provide a mapping shim in `recommendation_engine_v2.py`.

---

## Part 9 — Migration Strategy

### Phase 1 — Package Scaffold (No behavior change)
Tasks: Create `backend/app/engines/recommendations/` directory. Add empty `__init__.py` and `models.py` with copied/adapted data contracts. No routes changed. No engine behavior changed.  
Risk: Low. Purely additive.  
Validation: `import recommendations.models` succeeds in tests.  
Rollback: Delete the new directory.

### Phase 2 — Signal Detectors (Parallel to V1)
Tasks: Implement all five detectors in `signal_detectors.py`. Write unit tests. Add `GET /api/recommendations/signals` endpoint that exposes detected signals for inspection.  
Risk: Low. Detectors are read-only.  
Validation: All unit tests pass. Signal endpoint returns expected structure on demo data.  
Rollback: Remove the new endpoint.

### Phase 3 — Candidate Generator + Impact Estimator + Priority Engine
Tasks: Implement `candidate_generator.py`, `impact_estimator.py`, `priority_engine.py`. Wire them together in `recommendation_engine_v2.py` (generation-only, no simulation). Add `GET /api/v2/recommendations` endpoint alongside the existing V1 endpoint.  
Risk: Medium. New output format. Do not remove V1 endpoint.  
Validation: V2 endpoint returns recommendations with stable IDs and no duplicates on demo data. Run both endpoints and compare recommendation quality.  
Rollback: Disable V2 endpoint, return to V1.

### Phase 4 — Simulation Engine V2
Tasks: Implement `simulation_engine_v2.py` with seed=42 fixed. Add `POST /api/v2/recommendations/simulate`. Update `ActionApplicator` to use `resource_id` lookups.  
Risk: Medium. Simulation behavior changes. Verify delta values are non-trivially different from V1 due to seed fix.  
Validation: Repeated simulation calls with same ID produce identical results. Compare V1 vs. V2 simulation outputs and document expected differences.  
Rollback: Keep V1 simulation endpoint active.

### Phase 5 — Route Cutover
Tasks: Point `GET /api/recommendations` to V2 engine. Deprecate V1 recommendation_engine.py (but keep file for 1 sprint). Remove `recommendation_engine.py` and `simulation_engine.py` after validation period.  
Risk: Low if Phase 3 and 4 validated.  
Validation: Golden file regression test passes. All existing API consumers receive backward-compatible response shapes.  
Rollback: Revert route to V1 engine import.

---

## Part 10 — Risks and Tradeoffs

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Impact estimate values differ significantly from V1 (breaking user expectations) | High | Medium | Document the change in a CHANGELOG; provide a comparison mode that shows V1 vs. V2 deltas |
| Stable ID collisions on projects with many similar actions | Very Low | Low | Append disambiguation suffix; log warnings |
| Simulation performance degrades (full engine pipeline per simulation) | Medium | Medium | Cache `UpstreamEngineOutputs` per session; simulate on-demand rather than during generation |
| ActionApplicator resource_id change breaks existing scenario requests that pass resource names | Medium | High | Validate that the route layer converts legacy name-based inputs to ID-based inputs in the request model |
| Tests fail due to non-deterministic upstream engine behavior other than Monte Carlo | Low | High | Audit all upstream engines for any `random` or `datetime.now()` calls that are not seeded |

---

# GITHUB COPILOT IMPLEMENTATION SPECIFICATION

## Overview

You are implementing Recommendation Engine V2 for the Sprint Whisperer backend. The architecture review is complete. All design decisions are approved. Follow this specification exactly. Do not modify any existing files except `recommendations.py` (route layer).

## Constraints

- Python 3.11+. All dataclasses use `from __future__ import annotations`.
- All functions and methods are fully type-annotated.
- All classes use `@dataclass` or Pydantic `BaseModel` as specified below.
- Use `hashlib.sha1` for ID generation. Do not use `uuid`, `random`, or any other ID strategy.
- `MonteCarloEngine` MUST be called with `seed=42` everywhere in V2 code.
- Resource lookups MUST use `resource_id`, never `.name`.
- No hardcoded percentage reductions in `ActionApplicator` unless the value is derived from an engine output.

---

## File 1: `backend/app/engines/recommendations/models.py`

### Classes to implement (all as frozen dataclasses unless noted)

```python
class SignalCategory(str, Enum):  # values as specified in Part 3
class SignalSeverity(str, Enum):  # CRITICAL, HIGH, MEDIUM, LOW
class RecommendationAction(str, Enum):  # values as specified in Part 4.2
class ConfidenceLevel(str, Enum):  # HIGH, MEDIUM, LOW

@dataclass(frozen=True)
class SignalEvidence:
    source_engine: str
    metric_name: str
    metric_value: float
    threshold: float
    explanation: str

@dataclass(frozen=True)
class OpportunitySignal:
    signal_id: str
    category: SignalCategory
    severity: SignalSeverity
    affected_item_ids: List[str]
    affected_resource_ids: List[str]
    affected_sprint_ids: List[str]
    affected_blocker_ids: List[str]
    evidence: List[SignalEvidence]
    context: Dict[str, Any]
    detected_at: str

@dataclass
class RecommendationCandidate:
    recommendation_id: str
    action_type: RecommendationAction
    title: str
    description: str
    affected_item_ids: List[str]
    affected_resource_ids: List[str]
    affected_sprint_ids: List[str]
    affected_blocker_ids: List[str]
    root_cause_signal_id: str
    supporting_signal_ids: List[str]
    simulation_params: Dict[str, Any]
    feasibility_checks: Dict[str, bool]

@dataclass(frozen=True)
class ImpactEstimate:
    estimated_hours_recovered: float
    estimated_delay_reduction_days: float
    estimated_risk_reduction: float
    confidence: ConfidenceLevel
    evidence: List[SignalEvidence]
    calculation_notes: str

@dataclass
class Recommendation:
    recommendation_id: str
    title: str
    description: str
    action_type: RecommendationAction
    priority_score: float
    confidence: ConfidenceLevel
    estimated_hours_recovered: float
    estimated_delay_reduction_days: float
    estimated_risk_reduction: float
    affected_item_ids: List[str]
    affected_resource_ids: List[str]
    affected_sprint_ids: List[str]
    affected_blocker_ids: List[str]
    root_cause_signal_id: str
    supporting_signal_ids: List[str]
    impact_evidence: List[SignalEvidence]
    metadata: Dict[str, Any]

    def to_api_dict(self) -> Dict[str, Any]:
        """Produce dict compatible with RecommendationResponse schema."""
        ...

@dataclass(frozen=True)
class BaselineMetrics:
    on_time_probability: float
    expected_delay_days: float
    overall_risk_score: float
    critical_path_hours: float

@dataclass(frozen=True)
class SimulatedMetrics:
    on_time_probability: float
    expected_delay_days: float
    overall_risk_score: float
    critical_path_hours: float

@dataclass(frozen=True)
class SimulationResult:
    recommendation_ids: List[str]
    baseline_metrics: BaselineMetrics
    simulated_metrics: SimulatedMetrics
    delta_on_time_probability: float
    delta_expected_delay_days: float
    delta_spillover_risk: float
    delta_risk_score: float
    seed_used: int
    is_positive_impact: bool
    summary: str

@dataclass
class ScoringWeights:
    w_risk: float = 0.30
    w_schedule: float = 0.25
    w_blocker: float = 0.25
    w_cp: float = 0.15
    w_capacity: float = 0.05

    def __post_init__(self):
        total = self.w_risk + self.w_schedule + self.w_blocker + self.w_cp + self.w_capacity
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"ScoringWeights must sum to 1.0, got {total}")

@dataclass
class UpstreamEngineOutputs:
    """Pre-computed engine outputs. Always produced with seed=42."""
    metrics: ProjectMetrics
    dag: DependencyDAG
    cp_result: CriticalPathResult
    spillover: SpilloverAnalysis
    forecast: ForecastResult
    monte_carlo: MonteCarloResult
    impact_scores: RiskScores
    risk_result: RiskResult
```

### Module-level functions

```python
def stable_id(action_type: str, target_ids: List[str]) -> str:
    """Deterministic SHA-1 recommendation ID."""
    key = f"{action_type}:{':'.join(sorted(target_ids))}"
    return hashlib.sha1(key.encode()).hexdigest()[:10]

def signal_id(category: SignalCategory, target_ids: List[str]) -> str:
    """Deterministic SHA-1 signal ID."""
    key = f"sig:{category.value}:{':'.join(sorted(target_ids))}"
    return hashlib.sha1(key.encode()).hexdigest()[:10]
```

---

## File 2: `backend/app/engines/recommendations/signal_detectors.py`

### Class: `BlockerDetector`

```python
class BlockerDetector:
    def __init__(
        self,
        project_state: ProjectState,
        cp_result: CriticalPathResult,
        dag: DependencyDAG,
        impact_scores: RiskScores,
    ): ...

    def detect(self) -> List[OpportunitySignal]:
        """One signal per active blocker. See Part 3.2 for trigger conditions."""
        ...
```

Acceptance criteria:
- Returns empty list if no active blockers
- Each signal has `affected_blocker_ids = [blocker.blocker_id]`
- `context["cascade_item_ids"]` populated via `dag.transitive_closure`
- `context["blocked_hours"]` = sum of `remaining_effort_hrs` for `blocker.impacted_item_ids`
- Severity is CRITICAL if any impacted item is in `cp_result.items_on_critical_path`

### Class: `CapacityDetector`

```python
class CapacityDetector:
    def __init__(
        self,
        project_state: ProjectState,
        metrics: ProjectMetrics,
        cp_result: CriticalPathResult,
        impact_scores: RiskScores,
    ): ...

    def detect(self) -> List[OpportunitySignal]:
        """One signal per flagged resource. See Part 3.2 for trigger conditions."""
        ...
```

Acceptance criteria:
- `context["resource_id"]` is always `resource.resource_id`, not `resource.name`
- No signal emitted for resources at equilibrium (0.4 ≤ load_ratio ≤ 1.2)
- `affected_resource_ids` contains resource_id

### Class: `SprintDetector`

```python
class SprintDetector:
    def __init__(
        self,
        project_state: ProjectState,
        metrics: ProjectMetrics,
        spillover: SpilloverAnalysis,
        forecast: ForecastResult,
    ): ...

    def detect(self) -> List[OpportunitySignal]:
        """One signal per flagged sprint."""
        ...
```

Acceptance criteria:
- `context["sprint_id"]` populated
- `context["spillover_probability"]` sourced from `spillover.sprint_spillover_probability`
- DONE sprints are excluded

### Class: `CriticalPathDetector`

```python
class CriticalPathDetector:
    def __init__(
        self,
        project_state: ProjectState,
        cp_result: CriticalPathResult,
        dag: DependencyDAG,
        impact_scores: RiskScores,
    ): ...

    def detect(self) -> List[OpportunitySignal]:
        """Zero or more CP-level signals."""
        ...
```

Acceptance criteria:
- Emits CP_AT_RISK signal if any CP item appears in any active blocker's `impacted_item_ids`
- `near_critical_items` computed using `cp_result.slack_map`, threshold = 0.25 × sprint_duration_hours
- Dependency bottleneck: item feeds ≥ 3 CP items

### Class: `ScheduleDetector`

```python
class ScheduleDetector:
    def __init__(
        self,
        project_state: ProjectState,
        forecast: ForecastResult,
        monte_carlo: MonteCarloResult,
        risk_result: RiskResult,
        metrics: ProjectMetrics,
    ): ...

    def detect(self) -> List[OpportunitySignal]:
        """Zero or more schedule-level signals."""
        ...
```

Acceptance criteria:
- SCHEDULE_GAP signal only if `forecast.schedule_gap_hours > 0`
- PROBABILITY_CONCERN signal only if `monte_carlo.on_time_probability < 0.5`
- VELOCITY_CONCERN signal only if `metrics.velocity_trend < -0.1` AND velocity_trend is not None

---

## File 3: `backend/app/engines/recommendations/candidate_generator.py`

### Class: `CandidateGenerator`

```python
class CandidateGenerator:
    def __init__(
        self,
        project_state: ProjectState,
        upstream: UpstreamEngineOutputs,
    ): ...

    def generate(self, signals: List[OpportunitySignal]) -> List[RecommendationCandidate]:
        """
        Convert signals to candidates.
        Applies deduplication via stable_id.
        Applies feasibility checks before emitting.
        """
        ...
```

**Required internal methods:**

```python
def _from_blocker_signal(self, signal: OpportunitySignal) -> List[RecommendationCandidate]:
    """Generate RESOLVE_BLOCKER + ADVANCE_ITEM_TO_EARLIER_SPRINT candidates."""

def _from_capacity_signal(self, signal: OpportunitySignal) -> List[RecommendationCandidate]:
    """Generate REASSIGN_ITEM or REBALANCE_SPRINT_LOAD candidates."""

def _from_sprint_signal(self, signal: OpportunitySignal) -> List[RecommendationCandidate]:
    """Generate ADVANCE_ITEM_TO_EARLIER_SPRINT or REBALANCE_SPRINT_LOAD candidates."""

def _from_critical_path_signal(self, signal: OpportunitySignal) -> List[RecommendationCandidate]:
    """Generate specific item-level candidates. No CRITICAL_PATH_OPTIMIZATION allowed."""

def _from_schedule_signal(self, signal: OpportunitySignal) -> List[RecommendationCandidate]:
    """Generate ADD_RESOURCE_SKILL or SPLIT_ITEM candidates."""

def _deduplicate(
    self,
    existing: Dict[str, RecommendationCandidate],
    new: RecommendationCandidate,
) -> None:
    """If ID collision: merge supporting_signal_ids. Else insert."""

def _check_feasibility(self, candidate: RecommendationCandidate) -> bool:
    """Return True only if all feasibility_checks values are True."""
```

Acceptance criteria:
- No candidate with `action_type == CRITICAL_PATH_OPTIMIZATION` (forbidden)
- All `simulation_params` dicts contain `target_resource_id` (not `target_resource_name`) when a resource is involved
- Titles follow format: `"{ActionVerb} {specific_entity_name} ({entity_id})"`
- No more than one candidate per stable_id in output

---

## File 4: `backend/app/engines/recommendations/impact_estimator.py`

### Class: `ImpactEstimator`

```python
class ImpactEstimator:
    def __init__(
        self,
        project_state: ProjectState,
        upstream: UpstreamEngineOutputs,
    ): ...

    def estimate(self, candidate: RecommendationCandidate) -> ImpactEstimate:
        """Dispatch to action-type-specific method."""
        ...
```

**Required internal methods (one per `RecommendationAction` value):**

```python
def _estimate_resolve_blocker(self, candidate) -> ImpactEstimate: ...
def _estimate_reassign_item(self, candidate) -> ImpactEstimate: ...
def _estimate_split_item(self, candidate) -> ImpactEstimate: ...
def _estimate_advance_item(self, candidate) -> ImpactEstimate: ...
def _estimate_parallelize_items(self, candidate) -> ImpactEstimate: ...
def _estimate_rebalance_sprint_load(self, candidate) -> ImpactEstimate: ...
def _estimate_remove_dependency_bottleneck(self, candidate) -> ImpactEstimate: ...
def _estimate_add_resource_skill(self, candidate) -> ImpactEstimate: ...
```

Acceptance criteria:
- No method returns a value > `upstream.forecast.remaining_effort_hours` for `estimated_hours_recovered`
- All `ImpactEstimate.evidence` entries have a `source_engine` field matching an actual engine class name
- `estimated_delay_reduction_days` is 0.0 for action types that cannot affect the schedule (e.g., simple capacity rebalancing within a sprint that has no schedule slack)

---

## File 5: `backend/app/engines/recommendations/priority_engine.py`

### Class: `PriorityEngine`

```python
class PriorityEngine:
    def __init__(
        self,
        upstream: UpstreamEngineOutputs,
        weights: Optional[ScoringWeights] = None,
    ):
        self.weights = weights or ScoringWeights()
        ...

    def score_and_rank(
        self,
        candidates: List[RecommendationCandidate],
        impact_estimates: Dict[str, ImpactEstimate],
    ) -> List[Recommendation]:
        """
        Score each candidate, attach impact estimate, sort descending by priority_score.
        Apply tiebreaking as specified in Part 6.3.
        """
        ...

    def _score(
        self,
        candidate: RecommendationCandidate,
        impact: ImpactEstimate,
    ) -> float:
        """Compute weighted priority score using formula from Part 6.1."""
        ...
```

Acceptance criteria:
- Output is sorted descending by `priority_score`
- Two identical project states produce identical ranking
- `ScoringWeights` with sum ≠ 1.0 raises `ValueError` in `__post_init__`
- `Recommendation.priority_score` is in [0.0, 1.0] (not raw count or unbounded float)

---

## File 6: `backend/app/engines/recommendations/simulation_engine_v2.py`

### Module constant

```python
MONTE_CARLO_SEED: int = 42  # Never override
```

### Class: `ActionApplicator`

```python
class ActionApplicator:
    def apply(self, state: ProjectState, rec: Recommendation) -> None: ...
    def apply_many(self, state: ProjectState, recs: List[Recommendation]) -> None:
        """Apply in lexicographic recommendation_id order for determinism."""
        for rec in sorted(recs, key=lambda r: r.recommendation_id):
            self.apply(state, rec)
    
    # Internal methods — all use resource_id from rec.affected_resource_ids
    def _apply_resolve_blocker(self, state, rec): ...
    def _apply_reassign_item(self, state, rec): ...       # resource_id lookup only
    def _apply_split_item(self, state, rec): ...
    def _apply_advance_item(self, state, rec): ...
    def _apply_parallelize_items(self, state, rec): ...
    def _apply_rebalance_sprint_load(self, state, rec): ...
    def _apply_remove_dependency_bottleneck(self, state, rec): ...
    def _apply_add_resource_skill(self, state, rec): ...
```

### Class: `EngineRunner`

```python
class EngineRunner:
    """Runs the full engine pipeline on a ProjectState with seed=42."""

    SEED: int = MONTE_CARLO_SEED

    def run(self, state: ProjectState, simulation_count: int = 1000) -> UpstreamEngineOutputs:
        """
        Run: MetricsEngine → DependencyGraphEngine → CriticalPathEngine →
             SpilloverAnalysisEngine → ForecastEngine → MonteCarloEngine(seed=42) →
             ImpactScoringEngine → RiskEngine
        Return UpstreamEngineOutputs.
        """
        ...
```

### Class: `SimulationEngineV2`

```python
class SimulationEngineV2:
    SEED: int = MONTE_CARLO_SEED

    def __init__(
        self,
        project_state: ProjectState,
        baseline: UpstreamEngineOutputs,
        simulation_count: int = 1000,
    ): ...

    def simulate(self, recommendation: Recommendation) -> SimulationResult:
        """Deep clone → apply → re-run pipeline → compute deltas."""
        ...

    def simulate_scenario(self, recommendations: List[Recommendation]) -> SimulationResult:
        """Deep clone → apply all (sorted by ID) → re-run pipeline → compute deltas."""
        ...

    def _compute_result(
        self,
        rec_ids: List[str],
        simulated: UpstreamEngineOutputs,
    ) -> SimulationResult:
        """Compute delta fields. baseline comes from self.baseline."""
        ...
```

Acceptance criteria:
- `project_state.model_copy(deep=True)` used before any mutation — original never modified
- `EngineRunner.run()` is called on the cloned state — NOT on the original
- `seed=42` passed to `MonteCarloEngine` in `EngineRunner.run()`
- Two calls to `simulate(same_recommendation)` return identical `SimulationResult`
- `SimulationResult.seed_used` is always 42

---

## File 7: `backend/app/engines/recommendations/recommendation_engine_v2.py`

### Class: `RecommendationEngineV2`

```python
class RecommendationEngineV2:
    """
    Orchestrates the full V2 pipeline.
    Computes upstream once per instance (cached).
    """

    def __init__(
        self,
        project_state: ProjectState,
        simulation_count: int = 1000,
        scoring_weights: Optional[ScoringWeights] = None,
    ): ...

    def generate(self, top_n: int = 10) -> List[Recommendation]:
        """
        Full pipeline:
        1. Compute upstream (with seed=42)
        2. Detect signals (all five detectors)
        3. Generate candidates
        4. Estimate impacts
        5. Score and rank
        6. Return top_n
        """
        ...

    def simulate(self, recommendation_id: str) -> SimulationResult:
        """
        Find recommendation by ID in cached generate() results.
        If generate() not called yet, call it first.
        Run SimulationEngineV2.simulate().
        """
        ...

    def simulate_scenario(self, recommendation_ids: List[str]) -> SimulationResult:
        """
        Resolve all recommendation_ids from cache.
        Run SimulationEngineV2.simulate_scenario().
        """
        ...

    def _compute_upstream(self) -> UpstreamEngineOutputs:
        """
        Run EngineRunner.run(self.project_state).
        Cache result in self._upstream.
        """
        ...
```

Acceptance criteria:
- `_compute_upstream()` called exactly once per instance (cached)
- `simulate()` does not require `generate()` to have been called first (call it internally if needed)
- `generate()` returns a list with no duplicate `recommendation_id` values
- All returned `Recommendation` objects have non-empty `affected_item_ids` OR `affected_resource_ids` OR `affected_blocker_ids` — never a fully generic recommendation

---

## File 8: Route Update `backend/app/api/routes/recommendations.py`

Replace the import of `RecommendationEngine` with `RecommendationEngineV2`. Replace `_build_engines()` helper with `RecommendationEngineV2.__init__` (which handles upstream computation internally).

```python
# REPLACE:
from app.engines.recommendation_engine import RecommendationEngine

# WITH:
from app.engines.recommendations.recommendation_engine_v2 import RecommendationEngineV2
from app.engines.recommendations.models import ScoringWeights
```

The three routes (`GET /api/recommendations`, `POST /api/recommendations/simulate`, `POST /api/recommendations/scenario`) retain their URLs and response schemas. Map V2 `Recommendation.to_api_dict()` to the existing `RecommendationResponse` shape.

---

## Acceptance Criteria (Full System)

1. `GET /api/recommendations?session_id=X` called twice in sequence returns identical `recommendation_id` values in identical order.
2. `POST /api/recommendations/simulate` called twice with the same `recommendation_id` returns identical `delta_on_time_probability` and `delta_expected_delay_days`.
3. No recommendation in the response has `estimated_hours_recovered > total_remaining_work_hours`.
4. No two recommendations in the response share the same `recommendation_id`.
5. All `affected_resource_ids` in responses resolve to valid `resource_id` values in the project state.
6. `SimulationResult.seed_used` is always `42` in all simulation responses.
7. The response body is backward-compatible with the existing `RecommendationResponse` Pydantic model.
8. All unit and integration tests pass with `pytest -x`.
9. `recommendation_engine.py` and `simulation_engine.py` (V1) remain unmodified during Phase 3 and 4. They are deleted only in Phase 5 after cutover validation.

---

*Document version: 1.0 | Generated against Phase2_recommendation-main codebase | June 2026*
