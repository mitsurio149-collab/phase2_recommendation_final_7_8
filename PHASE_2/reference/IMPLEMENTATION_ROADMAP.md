# Sprint Whisperer - Implementation Roadmap & Action Plan
**Created:** 2026-06-11 | **Target:** Hackathon Demo (15 seconds)

---

## 🎯 PHASE 3 BUILD SEQUENCE

### BLOCK 1: Foundation (Forecast Engines)
**Time:** 8 hours | **Dependencies:** None | **Deliverable:** Monte Carlo forecasting

#### 1.1 Create Monte Carlo Engine
**File:** `backend/app/engines/monte_carlo_engine.py`
**Status:** ❌ NOT STARTED
**Effort:** 3 hours
**Lines of Code:** ~250

```python
# Key Components
class MonteCarloSimulation:
    def __init__(project_state: ProjectState, iterations: int = 10_000)
    def run() -> SimulationResult
        - _sample_effort_variance()  # Triangular: 80%-135%
        - _sample_velocity_variance()  # Normal: μ ± 15% std dev
        - _simulate_single_iteration()  # Run one sprint sequence
        - _compute_completion_date()  # When all work done
        - _build_histogram()  # Probability distribution

class SimulationResult:
    - iterations: int
    - completion_dates: List[datetime]  # One per iteration
    - completion_probabilities: Dict[date → probability]
    - percentile_50: datetime  # P50
    - percentile_80: datetime  # P80
    - percentile_95: datetime  # P95
    - on_time_probability: float  # Prob ≤ target_end_date
```

**Pseudocode:**
```python
def run(self):
    results = []
    for iteration in range(self.iterations):
        # Reset for new iteration
        current_effort = {}
        current_date = project_start_date
        
        # For each sprint
        for sprint in sprints:
            # Sample velocity variance
            velocity_multiplier = np.random.normal(1.0, self.velocity_std_dev)
            adjusted_velocity = sprint.planned_velocity * velocity_multiplier
            
            # Process work items
            for item in sprint.work_items:
                # Sample effort variance (triangular)
                effort_multiplier = np.random.triangular(0.8, 1.0, 1.35)
                adjusted_effort = item.estimated_effort * effort_multiplier
                
                current_effort[item.id] = adjusted_effort
            
            # Check for spillovers
            total_effort = sum(current_effort.values())
            if total_effort > adjusted_velocity:
                spillover_items = identify_spillovers(...)
                carryover = total_effort - adjusted_velocity
        
        # Record completion date
        completion_date = compute_final_date(...)
        results.append(completion_date)
    
    return build_histogram(results)
```

**Configuration Used:**
- `mc_iterations`: 10,000
- `effort_variance_min/mode/max`: 0.80 / 1.00 / 1.35
- `velocity_std_dev`: 0.15
- `velocity_min/max_clamp`: 0.30 / 1.50

**Testing:**
```python
# test_monte_carlo_engine.py
def test_mc_runs_10000_iterations():
    engine = MonteCarloSimulation(project_state, iterations=10_000)
    result = engine.run()
    assert len(result.completion_dates) == 10_000

def test_mc_produces_probability_distribution():
    result = engine.run()
    assert 0.0 <= result.on_time_probability <= 1.0
    assert result.percentile_50 < result.percentile_80
    assert result.percentile_80 < result.percentile_95
```

---

#### 1.2 Create Forecast Engine
**File:** `backend/app/engines/forecast_engine.py`
**Status:** ❌ NOT STARTED
**Effort:** 4 hours
**Lines of Code:** ~300

```python
class ForecastEngine:
    def __init__(project_state: ProjectState, monte_carlo_engine: MonteCarloSimulation)
    
    def forecast() -> ForecastResult
        - _run_simulation()  # Calls monte_carlo_engine.run()
        - _calculate_on_time_probability()  # Compare P50 to target
        - _identify_risk_factors()  # What's driving the forecast
        - _compute_risk_adjusted_schedule()  # Contingency calculations

class ForecastResult:
    - on_time_probability: float  # Main metric for demo
    - p50_date: datetime  # 50th percentile
    - p80_date: datetime  # 80th percentile
    - p95_date: datetime  # 95th percentile
    - target_date: datetime  # From project_info.target_end_date
    - days_vs_target: int  # p50_date relative to target
    - risk_factors: List[str]  # "Spillovers", "Blockers", "Resource constraints"
    - simulation_time_ms: int
```

**Usage:**
```python
# In endpoint handler
@router.post("/api/simulate")
async def post_simulate(session_id: str, iterations: int = 10_000):
    project_state = store.get_project_state(session_id)
    
    # Create and run engines
    mc_engine = MonteCarloSimulation(project_state, iterations)
    forecast_engine = ForecastEngine(project_state, mc_engine)
    result = forecast_engine.forecast()
    
    # Store baseline (first time only)
    if not store.baseline_result:
        store.baseline_result = result
    
    # Store current result
    store.current_result = result
    
    return ApiResponse(success=True, data=result.model_dump())
```

---

### BLOCK 2: Risk Assessment (Risk Engine)
**Time:** 2.5 hours | **Dependencies:** Block 1 | **Deliverable:** Risk scoring

#### 2.1 Create Risk Engine
**File:** `backend/app/engines/risk_engine.py`
**Status:** ❌ NOT STARTED
**Effort:** 2.5 hours
**Lines of Code:** ~200

```python
class RiskEngine:
    def __init__(project_state: ProjectState, forecast_result: ForecastResult)
    
    def analyze() -> RiskAssessment
        - _calculate_schedule_risk()  # Impact of late forecast
        - _calculate_resource_risk()  # Utilization issues
        - _calculate_dependency_risk()  # Critical path exposure
        - _calculate_scope_risk()  # Scope changes
        - _compute_sprint_risks()  # Per-sprint breakdown (NEW in V2)

class RiskAssessment:
    # Project-level
    - overall_score: int  # 0-100, weighted combination
    - level: str  # "Critical", "High", "Medium", "Low"
    - schedule_score: int
    - resource_score: int
    - dependency_score: int
    - scope_score: int
    
    # Sprint-level (NEW)
    - sprint_risks: List[SprintRisk]

class SprintRisk:
    - sprint_id: str
    - sprint_name: str
    - risk_score: int
    - level: str
    - drivers: List[str]  # ["3 blocked items", "95% capacity"]
```

**Risk Scoring Formula:**
```python
# Weighted composite score
schedule_weight = 0.35
resource_weight = 0.25
dependency_weight = 0.25
scope_weight = 0.15

overall_score = (
    schedule_score * schedule_weight +
    resource_score * resource_weight +
    dependency_score * dependency_weight +
    scope_score * scope_weight
)

# Classification
if overall_score >= 75: level = "Critical"
elif overall_score >= 50: level = "High"
elif overall_score >= 25: level = "Medium"
else: level = "Low"
```

**Component Scores:**
```python
# Schedule Risk: based on forecast probability
if on_time_probability >= 0.70:
    schedule_score = 10  # Low risk
elif on_time_probability >= 0.40:
    schedule_score = 50  # Medium risk
else:
    schedule_score = 85  # High risk

# Resource Risk: based on utilization
overloaded = sum(1 for r in resources if utilization > 1.0)
if overloaded >= len(resources) * 0.3:
    resource_score = 70  # High risk
...

# Dependency Risk: based on critical path
if critical_path_length > 30:
    dependency_score = 60  # Many dependencies
...

# Scope Risk: based on changes
if scope_changes_hours > total_effort * 0.1:
    scope_score = 50  # 10%+ of scope changed
...
```

---

### BLOCK 3: Recommendations (Recommendation Engine)
**Time:** 3 hours | **Dependencies:** Block 1, 2 | **Deliverable:** Action recommendations

#### 3.1 Create Recommendation Engine
**File:** `backend/app/engines/recommendation_engine.py`
**Status:** ❌ NOT STARTED
**Effort:** 3 hours
**Lines of Code:** ~250

```python
class RecommendationEngine:
    def __init__(project_state: ProjectState, forecast_result: ForecastResult, 
                 risk_assessment: RiskAssessment)
    
    def generate_recommendations() -> RecommendationResult
        - _generate_descope_recommendations()
        - _generate_blocker_recommendations()
        - _generate_reallocation_recommendations()
        - _rank_by_impact()

class Recommendation:
    - id: str  # "rec-001"
    - rank: int  # 1, 2, 3...
    - action: str  # "Descope 2 low-priority items: WI-045, WI-050"
    - action_type: str  # "descope", "resolve_blocker", "reallocate"
    - confidence: str  # "High", "Medium", "Low"
    - estimated_impact_prob: float  # +0.18 (e.g., 0.34 → 0.52)
    - effort_saved_hours: float  # e.g., 40 hours
    - reason: str  # "These items are low-priority and in critical path"

class RecommendationResult:
    - baseline_on_time_prob: float
    - recommendations: List[Recommendation]
```

**Recommendation Rules:**

Rule 1: **Descope Low-Priority Items**
```
IF on_time_probability < 0.5 AND exists(low_priority_items_on_critical_path):
    action = "Descope N low-priority items from critical path"
    confidence = "High" if N >= 2 else "Medium"
    impact = estimated_freed_effort / total_remaining_effort
```

Rule 2: **Resolve Blockers First**
```
IF active_blocker_count > 0:
    critical_blockers = filter(blockers, severity=="Critical")
    action = f"Resolve {len(critical_blockers)} critical blockers"
    confidence = "High"
    impact = blocker_velocity_impact_factor
```

Rule 3: **Reallocate Underutilized Resources**
```
IF exists(underutilized_resources) AND exists(overloaded_resources):
    action = "Shift work from overloaded to underutilized resources"
    confidence = "Medium"
    impact = skill_match_factor * capacity_delta
```

Rule 4: **Add Contingency Time**
```
IF velocity_variance > 0.20:  # High variance
    action = "Add contingency buffer (10% of critical path)"
    confidence = "Low"
    impact = contingency_buffer_factor
```

---

### BLOCK 4: API Endpoints (Routes)
**Time:** 5 hours | **Dependencies:** Blocks 1-3 | **Deliverable:** 5 endpoints

#### 4.1 POST /api/simulate Endpoint
**File:** `backend/app/api/routes/simulate.py`
**Effort:** 2 hours

```python
@router.post("/api/simulate")
async def post_simulate(session_id: str = Query(...), iterations: int = Query(10_000)):
    """
    Run Monte Carlo simulation for baseline forecast.
    """
    try:
        project_state = store.get_project_state(session_id)
        if not project_state:
            raise HTTPException(404, "Session not found")
        
        # Initialize engines
        mc_engine = MonteCarloSimulation(project_state, iterations)
        forecast_engine = ForecastEngine(project_state, mc_engine)
        
        # Run simulation
        result = forecast_engine.forecast()
        
        # Store baseline on first simulation
        if not store.baseline_result:
            store.baseline_result = result
        
        # Store current result
        store.current_result = result
        store.last_updated = datetime.utcnow()
        
        # Return response
        return ApiResponse(
            success=True,
            data=result.model_dump(),
            message="Simulation complete"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))
```

#### 4.2 GET /api/risks Endpoint
**File:** `backend/app/api/routes/risks.py`
**Effort:** 1.5 hours

```python
@router.get("/api/risks")
async def get_risks(session_id: str = Query(...), sprint_id: str = Query(None)):
    """
    Get project and sprint-level risk assessments.
    """
    try:
        project_state = store.get_project_state(session_id)
        current_result = store.current_result
        
        if not project_state or not current_result:
            raise HTTPException(404, "Session or simulation not found")
        
        # Run risk analysis
        risk_engine = RiskEngine(project_state, current_result)
        risk_assessment = risk_engine.analyze()
        
        return ApiResponse(
            success=True,
            data=risk_assessment.model_dump()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))
```

#### 4.3 GET /api/recommendations Endpoint
**File:** `backend/app/api/routes/recommendations.py`
**Effort:** 1.5 hours

```python
@router.get("/api/recommendations")
async def get_recommendations(session_id: str = Query(...), top_n: int = Query(5)):
    """
    Get ranked recommendations to improve forecast.
    """
    try:
        project_state = store.get_project_state(session_id)
        current_result = store.current_result
        risk_assessment = store.risk_result
        
        if not all([project_state, current_result, risk_assessment]):
            raise HTTPException(404, "Missing required data")
        
        # Generate recommendations
        rec_engine = RecommendationEngine(project_state, current_result, risk_assessment)
        recommendations = rec_engine.generate_recommendations()
        
        # Limit to top_n
        recommendations.recommendations = recommendations.recommendations[:top_n]
        
        store.recommendation_result = recommendations
        
        return ApiResponse(
            success=True,
            data=recommendations.model_dump()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))
```

---

### BLOCK 5: Comparison & Demo Endpoints
**Time:** 3 hours | **Dependencies:** Blocks 1-4 | **Deliverable:** Demo magic

#### 5.1 GET /api/reforecast-comparison Endpoint
**File:** `backend/app/api/routes/reforecast_comparison.py`
**Effort:** 1.5 hours

```python
@router.get("/api/reforecast-comparison")
async def get_reforecast_comparison(session_id: str = Query(...)):
    """
    Compare baseline vs. current forecast.
    THE MONEY SHOT — Before and after side-by-side.
    """
    try:
        baseline = store.baseline_result
        current = store.current_result
        
        if not baseline or not current:
            raise HTTPException(404, "No forecasts available")
        
        # Build scenarios
        scenarios = {
            "baseline": {
                "label": "Initial Upload",
                "on_time_probability": baseline.on_time_probability,
                "p50_date": baseline.p50_date.isoformat(),
                "days_vs_target": (baseline.p50_date - target_date).days,
                "factors": baseline.risk_factors
            },
            "current": {
                "label": "After Recommendations",
                "on_time_probability": current.on_time_probability,
                "p50_date": current.p50_date.isoformat(),
                "days_vs_target": (current.p50_date - target_date).days,
                "factors": current.risk_factors
            }
        }
        
        # Compute delta
        prob_improvement = current.on_time_probability - baseline.on_time_probability
        schedule_improvement = (baseline.p50_date - current.p50_date).days
        
        return ApiResponse(
            success=True,
            data={
                "scenarios": scenarios,
                "delta_summary": {
                    "probability_improvement": f"+{prob_improvement:.2f}" if prob_improvement > 0 else f"{prob_improvement:.2f}",
                    "schedule_improvement": f"{schedule_improvement} days" + (" earlier" if schedule_improvement > 0 else " later"),
                    "recommendations_applied": store.scope_change_log
                }
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))
```

#### 5.2 POST /api/simulate-recommendation Endpoint
**File:** `backend/app/api/routes/simulate_recommendation.py`
**Effort:** 1 hour

```python
@router.post("/api/simulate-recommendation")
async def post_simulate_recommendation(
    session_id: str,
    recommendation_id: str,
    action_type: str,  # "descope", "resolve_blocker", "reallocate"
    item_ids: List[str] = []
):
    """
    Apply a recommendation and re-simulate forecast.
    """
    try:
        project_state = store.get_project_state(session_id)
        
        # Apply action to project state
        if action_type == "descope":
            for item_id in item_ids:
                item = find_item(project_state, item_id)
                item.is_scope_changed = True
                item.status = WorkItemStatus.SPILLOVER  # or similar
        
        elif action_type == "resolve_blocker":
            for blocker_id in item_ids:
                blocker = find_blocker(project_state, blocker_id)
                blocker.actual_resolution_date = datetime.utcnow()
        
        # Re-run simulation with modified state
        mc_engine = MonteCarloSimulation(project_state)
        forecast_engine = ForecastEngine(project_state, mc_engine)
        new_result = forecast_engine.forecast()
        
        # Store updated result
        store.current_result = new_result
        store.record_scope_change(...)
        
        return ApiResponse(
            success=True,
            data={
                "previous_forecast": store.baseline_result.model_dump(),
                "updated_forecast": new_result.model_dump(),
                "delta": {
                    "probability": f"+{new_result.on_time_probability - store.baseline_result.on_time_probability:.2f}",
                    "days": f"{(store.baseline_result.p50_date - new_result.p50_date).days} days"
                }
            }
        )
    
    except Exception as e:
        raise HTTPException(500, str(e))
```

#### 5.3 POST /api/demo/reset & POST /api/demo/load
**File:** `backend/app/api/routes/demo.py`
**Effort:** 1 hour

```python
@router.post("/api/demo/reset")
async def post_demo_reset(session_id: str):
    """Reset system for demo restart."""
    store.reset()
    return ApiResponse(success=True, message="Demo reset")

@router.post("/api/demo/load")
async def post_demo_load():
    """Pre-load demo workbook."""
    parser = WorkbookParser("TIO2_Sprint_Intelligence_VALIDATED.xlsx")
    project_state = parser.parse()
    
    session_id = generate_session_id()
    store.project_state = project_state
    
    return ApiResponse(
        success=True,
        data={
            "session_id": session_id,
            "project_summary": ProjectSummary(...).model_dump()
        }
    )
```

---

## 📝 API MODELS FILE

**File:** `backend/app/api/models_phase3.py`
**Status:** ❌ NOT STARTED
**Effort:** 2.5 hours
**Lines:** ~350

```python
from pydantic import BaseModel
from typing import List, Dict, Tuple
from datetime import datetime

class ForecastResult(BaseModel):
    on_time_probability: float  # 0.0-1.0
    p50_date: datetime
    p80_date: datetime
    p95_date: datetime
    target_date: datetime
    days_vs_target: int
    risk_factors: List[str]
    simulation_time_ms: int

class RiskAssessment(BaseModel):
    overall_score: int  # 0-100
    level: str  # "Critical", "High", "Medium", "Low"
    schedule_score: int
    resource_score: int
    dependency_score: int
    scope_score: int
    sprint_risks: List['SprintRisk']

class SprintRisk(BaseModel):
    sprint_id: str
    sprint_name: str
    risk_score: int
    level: str
    drivers: List[str]

class Recommendation(BaseModel):
    id: str
    rank: int
    action: str
    action_type: str  # "descope", "resolve_blocker", "reallocate"
    confidence: str  # "High", "Medium", "Low"
    estimated_impact_prob: float
    effort_saved_hours: float
    reason: str

class RecommendationResult(BaseModel):
    baseline_on_time_prob: float
    recommendations: List[Recommendation]

class ReforecastComparison(BaseModel):
    scenarios: Dict  # "baseline" and "current"
    delta_summary: Dict
```

---

## 🧪 TESTING STRATEGY

### Phase 3 Unit Tests
**File:** `backend/tests/test_phase3.py`
**Status:** ❌ NOT STARTED
**Effort:** 3 hours

```python
import pytest
from app.engines.monte_carlo_engine import MonteCarloSimulation
from app.engines.forecast_engine import ForecastEngine
from app.engines.risk_engine import RiskEngine
from app.engines.recommendation_engine import RecommendationEngine

class TestMonteCarloEngine:
    def test_mc_runs_n_iterations(self):
        engine = MonteCarloSimulation(project_state, iterations=1000)
        result = engine.run()
        assert len(result.completion_dates) == 1000
    
    def test_mc_produces_valid_probabilities(self):
        result = engine.run()
        assert 0.0 <= result.on_time_probability <= 1.0
        assert result.p50_date < result.p95_date

class TestForecastEngine:
    def test_forecast_runs_successfully(self):
        engine = ForecastEngine(project_state, mc_engine)
        result = engine.forecast()
        assert result.on_time_probability is not None

class TestRiskEngine:
    def test_risk_score_calculation(self):
        engine = RiskEngine(project_state, forecast_result)
        assessment = engine.analyze()
        assert 0 <= assessment.overall_score <= 100

class TestRecommendationEngine:
    def test_generates_recommendations(self):
        engine = RecommendationEngine(project_state, forecast_result, risk_assessment)
        result = engine.generate_recommendations()
        assert len(result.recommendations) > 0

# Integration tests
class TestPhase3Integration:
    @pytest.mark.asyncio
    async def test_full_simulation_flow(self):
        """Test complete flow: upload → simulate → risks → recommendations."""
        # Upload
        session_id = await upload_workbook(...)
        
        # Simulate
        forecast = await post_simulate(session_id)
        assert forecast.on_time_probability < 1.0
        
        # Get risks
        risks = await get_risks(session_id)
        assert risks.overall_score >= 0
        
        # Get recommendations
        recs = await get_recommendations(session_id)
        assert len(recs.recommendations) > 0
        
        # Compare
        comparison = await get_reforecast_comparison(session_id)
        assert "baseline" in comparison.scenarios
```

---

## 🚀 BUILD SEQUENCE (In Order)

### Sprint 1: Foundation (8 hours)
1. **1.1** Create `monte_carlo_engine.py` (3 hrs)
2. **1.2** Create `forecast_engine.py` (4 hrs)
3. **Test:** Monte Carlo produces valid distributions

### Sprint 2: Risk & Recommendations (5.5 hours)
4. **2.1** Create `risk_engine.py` (2.5 hrs)
5. **3.1** Create `recommendation_engine.py` (3 hrs)
6. **Test:** Risk scores and recommendations generated

### Sprint 3: API Integration (5 hours)
7. **4.1** Create `simulate.py` endpoint (2 hrs)
8. **4.2** Create `risks.py` endpoint (1.5 hrs)
9. **4.3** Create `recommendations.py` endpoint (1.5 hrs)
10. **Test:** All endpoints return valid JSON

### Sprint 4: Demo Magic (3 hours)
11. **5.1** Create `reforecast_comparison.py` endpoint (1.5 hrs)
12. **5.2** Create `simulate_recommendation.py` endpoint (1 hr)
13. **5.3** Create `demo.py` endpoints (0.5 hrs)
14. **Test:** Full demo flow works end-to-end

### Sprint 5: Data Models & Tests (5.5 hours)
15. **Create** `models_phase3.py` (2.5 hrs)
16. **Create** `test_phase3.py` (3 hrs)
17. **Test:** All 20+ new tests pass

### **TOTAL: 26.5 Hours to Demo-Ready Backend**

---

## 🎬 DEMO SCRIPT (15 seconds)

```
[Step 1 - 2 sec] Upload workbook
  Browser shows: "Parsing... 67 work items, 23 dependencies"

[Step 2 - 2 sec] Click "Simulate"
  API returns: on_time_probability: 34%
  Screen shows: Large red gauge, P50 = Feb 14 (18 days late)

[Step 3 - 3 sec] Show risk assessment
  Screen highlights: "Sprint 4 is critical — 3 blocked tasks, 2 spillovers"
  Badge shows: Overall risk = HIGH (67/100)

[Step 4 - 2 sec] Show top recommendation
  Card displays: "Descope 2 low-priority items: WI-045, WI-050"
  Button: "Simulate This Recommendation"

[Step 5 - 3 sec] Click simulate
  New forecast appears: on_time_probability: 71%
  P50 = Jan 27 (2 days early)

[Step 6 - 3 sec] Show before/after comparison
  Left side: "Initial: P50 = Feb 14 (18 days late)"
  Right side: "After Recommendation: P50 = Jan 27 (2 days early)"
  Bottom: "+37% probability improvement | 20 days earlier"

[Total: 15 seconds]
Judge sees:
  ✓ Problem identified (34% on-time)
  ✓ Root cause shown (blocked tasks, spillovers)
  ✓ Solution recommended (descope 2 items)
  ✓ Impact validated (71% on-time, 20 days early)
```

---

## 📋 CHECKLIST FOR IMPLEMENTATION

### Backend Engines
- [ ] Monte Carlo Engine (monte_carlo_engine.py)
- [ ] Forecast Engine (forecast_engine.py)
- [ ] Risk Engine (risk_engine.py)
- [ ] Recommendation Engine (recommendation_engine.py)
- [ ] Capacity Engine (capacity_engine.py) — Optional for MVP

### API Models
- [ ] models_phase3.py with 8 response models

### API Routes
- [ ] simulate.py (POST /api/simulate)
- [ ] risks.py (GET /api/risks)
- [ ] recommendations.py (GET /api/recommendations)
- [ ] simulate_recommendation.py (POST /api/simulate-recommendation)
- [ ] reforecast_comparison.py (GET /api/reforecast-comparison)
- [ ] scope_change.py (POST /api/scope-change) — Optional for MVP
- [ ] demo.py (POST /api/demo/reset, POST /api/demo/load)

### Tests
- [ ] test_phase3.py with 20+ unit and integration tests

### Configuration
- [ ] Update config.py with any missing settings
- [ ] Update main.py to register new routes

### Documentation
- [ ] Phase 3 API spec
- [ ] Update README

---

## 📊 PROGRESS TRACKING

| Component | Status | Hours | Start | End | Notes |
|-----------|--------|-------|-------|-----|-------|
| Monte Carlo Engine | ⬜ | 3 | — | — | |
| Forecast Engine | ⬜ | 4 | — | — | |
| Risk Engine | ⬜ | 2.5 | — | — | |
| Recommendation Engine | ⬜ | 3 | — | — | |
| API Models | ⬜ | 2.5 | — | — | |
| Simulate Endpoint | ⬜ | 2 | — | — | |
| Risks Endpoint | ⬜ | 1.5 | — | — | |
| Recommendations Endpoint | ⬜ | 1.5 | — | — | |
| Reforecast Endpoint | ⬜ | 1.5 | — | — | |
| Demo Endpoints | ⬜ | 1.5 | — | — | |
| Tests | ⬜ | 3 | — | — | |
| **TOTAL** | | **26.5 hrs** | | | |

---

## ✅ SUCCESS CRITERIA

- [ ] All 5 engines implemented and unit tested
- [ ] All 7 endpoints return valid JSON responses
- [ ] Integration tests pass (upload → simulate → compare)
- [ ] Demo script executes without errors
- [ ] Comparison endpoint shows +20% probability improvement minimum
- [ ] Server handles 10,000 MC iterations in < 10 seconds
- [ ] No TODO/FIXME comments in production code
- [ ] All errors return user-friendly messages
- [ ] Swagger UI (/docs) shows all Phase 3 endpoints
- [ ] Ready for live 15-second demo

---

**Ready to start building? Begin with Block 1 (Monte Carlo + Forecast Engines).**
