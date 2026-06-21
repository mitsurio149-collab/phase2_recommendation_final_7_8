# Sprint Whisperer - Missing Implementations Analysis
**Date:** 2026-06-11 | **Status:** In-Progress | **Scope:** Phase 3 Features & Frontend

---

## EXECUTIVE SUMMARY

The Sprint Whisperer backend is **60% complete**:
- ✅ Phase 1 (Upload & Parsing): **100% Complete**
- ✅ Phase 2 (Metrics & Analysis): **100% Complete**  
- ❌ Phase 3 (Simulation & Recommendations): **0% Complete**
- ❌ Frontend: **0% Complete**
- ❌ Docker/Deployment: **0% Complete**

**Missing Feature Count:** 12 major components
**Missing Lines of Code:** ~2,500+ lines

---

## 1. MISSING ENGINES (5/5 Not Implemented)

### 1.1 Forecast Engine ❌
**Status:** NOT IMPLEMENTED  
**Purpose:** Predict project completion probability and dates using Monte Carlo  
**Planned Location:** `backend/app/engines/forecast_engine.py`  
**Key Methods:**
```python
class ForecastEngine:
    def __init__(project_state: ProjectState) -> None
    def forecast() -> ForecastResult
        - predict_completion_probability() -> float  # P(on-time)
        - predict_completion_dates() -> Dict  # P50, P80, P95 dates
        - compute_risk_adjusted_schedule() -> Schedule
```
**Configuration Needed** (from config.py):
- `mc_iterations`: 10,000
- `effort_variance_min/mode/max`: 0.80 / 1.00 / 1.35 (triangular distribution)
- `velocity_std_dev`: 0.15
- `velocity_min/max_clamp`: 0.30 / 1.50

---

### 1.2 Monte Carlo Engine ❌
**Status:** NOT IMPLEMENTED  
**Purpose:** Run 10,000 probabilistic simulations of sprint outcomes  
**Planned Location:** `backend/app/engines/monte_carlo_engine.py`  
**Algorithm:**
```
For each of 10,000 iterations:
  1. Sample effort variance (triangular: 80%-135% of estimate)
  2. Sample velocity variance (normal: mean ± 15% std dev)
  3. Simulate sprint-by-sprint progression
  4. Identify spillovers (items exceeding sprint capacity)
  5. Record completion date and probability
Output: Distribution of completion dates with P50/P80/P95
```
**Key Classes:**
- `MonteCarloResult`: Holds histogram of completion dates
- `SimulationIteration`: Single run snapshot

---

### 1.3 Risk Engine ❌
**Status:** NOT IMPLEMENTED  
**Purpose:** Identify project and sprint-level risks with scorecards  
**Planned Location:** `backend/app/engines/risk_engine.py`  
**Risk Scoring Formula:**
```
Risk = 0.35 × schedule_risk 
      + 0.25 × resource_risk 
      + 0.25 × dependency_risk 
      + 0.15 × scope_risk

Thresholds:
  75+  = Critical (red)
  50-74 = High (orange)
  25-49 = Medium (amber)
  0-24  = Low (green)
```
**Key Deliverables:**
- **ProjectRiskResult**: Overall risk score + drivers
- **SprintRiskResult**: Per-sprint risk heatmap (NEW in V2)
- **RiskDriver**: Ranked list of factors causing risk

---

### 1.4 Recommendation Engine ❌
**Status:** NOT IMPLEMENTED  
**Purpose:** Generate rule-based recommendations to improve forecast  
**Planned Location:** `backend/app/engines/recommendation_engine.py`  
**Rules to Implement:**
```
IF on-time_probability < 0.5 THEN recommend:
  1. Descope low-priority items
  2. Resolve critical blockers first
  3. Redistribute work to underutilized resources
  4. Add contingency time to high-uncertainty items

Confidence scoring:
  - High (0.8): Rule applies to 3+ factors
  - Medium (0.5): Rule applies to 1-2 factors
  - Low (0.3): Rule speculative
```
**Key Deliverables:**
- **Recommendation**: Single action with probability delta
- **RecommendationResult**: Ranked list of recommendations

---

### 1.5 Capacity Engine ❌
**Status:** NOT IMPLEMENTED  
**Purpose:** Allocate team capacity and identify over/underutilization  
**Planned Location:** `backend/app/engines/capacity_engine.py`  
**Calculations:**
```
For each resource:
  effective_allocation = allocation_pct × availability_pct
  
Flags:
  - Overloaded: effective_allocation > 100%
  - Underutilized: effective_allocation < 60%
  - Skill mismatch: required_skill ≠ primary_skill
```
**Note:** This engine is partially detected by MetricsEngine but not as a standalone module

---

## 2. PHASE 3 ENDPOINTS (8 Not Implemented)

### 2.1 POST /api/simulate ❌
**Status:** NOT IMPLEMENTED  
**Purpose:** Run Monte Carlo simulation for baseline forecast  
**Request:**
```json
{
  "session_id": "abc123",
  "iterations": 10000  // Optional, defaults to config
}
```
**Response:**
```json
{
  "success": true,
  "data": {
    "session_id": "abc123",
    "forecast": {
      "on_time_probability": 0.34,
      "p50_date": "2026-02-14",
      "p80_date": "2026-02-21",
      "p95_date": "2026-03-07",
      "distribution": [/* histogram */]
    },
    "simulation_time_ms": 1250
  }
}
```
**Dependencies:** ForecastEngine, MonteCarloEngine

---

### 2.2 GET /api/risks ❌
**Status:** NOT IMPLEMENTED  
**Purpose:** Get project and sprint-level risk assessments  
**Request:**
```
GET /api/risks?session_id=abc123&sprint_id=4  // sprint_id optional
```
**Response:**
```json
{
  "success": true,
  "data": {
    "session_id": "abc123",
    "project_risk": {
      "overall_score": 67,
      "level": "High",
      "schedule_score": 75,
      "resource_score": 45,
      "dependency_score": 60,
      "scope_score": 30
    },
    "sprint_risks": [
      {
        "sprint_id": 4,
        "sprint_name": "Sprint 4",
        "risk_score": 78,
        "level": "Critical",
        "drivers": ["3 blocked tasks", "2 spillovers", "resource overload"]
      }
    ]
  }
}
```
**Dependencies:** RiskEngine

---

### 2.3 GET /api/recommendations ❌
**Status:** NOT IMPLEMENTED  
**Purpose:** Get ranked recommendations to improve forecast  
**Request:**
```
GET /api/recommendations?session_id=abc123&top_n=5
```
**Response:**
```json
{
  "success": true,
  "data": {
    "session_id": "abc123",
    "project_name": "TIO2",
    "baseline_on_time_prob": 0.34,
    "recommendations": [
      {
        "rank": 1,
        "action": "Descope 2 low-priority items (WI-045, WI-050)",
        "impact": "+0.18",  // 0.34 → 0.52
        "confidence": "High",
        "estimated_effort_saved": 40,
        "reason": "These items are in critical path but low priority"
      }
    ]
  }
}
```
**Dependencies:** RecommendationEngine, ForecastEngine

---

### 2.4 POST /api/simulate-recommendation ❌
**Status:** NOT IMPLEMENTED  
**Purpose:** Apply a recommendation and re-simulate forecast  
**Request:**
```json
{
  "session_id": "abc123",
  "recommendation_id": "rec-001",
  "action_type": "descope",
  "item_ids": ["WI-045", "WI-050"]
}
```
**Response:**
```json
{
  "success": true,
  "data": {
    "previous_forecast": { /* baseline */ },
    "updated_forecast": {
      "on_time_probability": 0.52,
      "p50_date": "2026-02-07",
      "delta_prob": "+0.18",
      "delta_days": "-7"
    }
  }
}
```
**Dependencies:** ForecastEngine, RecommendationEngine

---

### 2.5 POST /api/scope-change ❌
**Status:** NOT IMPLEMENTED  
**Purpose:** Descope work items and trigger re-forecast  
**Request:**
```json
{
  "session_id": "abc123",
  "item_ids": ["WI-045", "WI-050"],
  "reason": "Low business priority"
}
```
**Response:**
```json
{
  "success": true,
  "data": {
    "descoped_items": 2,
    "effort_saved_hours": 40,
    "previous_probability": 0.34,
    "new_probability": 0.52,
    "delta": "+0.18"
  }
}
```
**Side Effects:** Updates SessionStore.descoped_item_ids and project_state

---

### 2.6 GET /api/reforecast-comparison ❌
**Status:** NOT IMPLEMENTED  
**Purpose:** Compare baseline vs. current forecast (the "money shot" demo endpoint)  
**Request:**
```
GET /api/reforecast-comparison?session_id=abc123
```
**Response:**
```json
{
  "success": true,
  "data": {
    "scenarios": {
      "baseline": {
        "label": "Initial Upload",
        "on_time_probability": 0.34,
        "p50_date": "2026-02-14",
        "days_late": 18,
        "factors": {
          "spillovers": 9,
          "blockers": 5,
          "underutilized_capacity": 0
        }
      },
      "current": {
        "label": "After Recommendations",
        "on_time_probability": 0.71,
        "p50_date": "2026-01-27",
        "days_early": 2,
        "factors": {
          "spillovers": 2,
          "blockers": 1,
          "underutilized_capacity": 0
        }
      }
    },
    "delta_summary": {
      "probability_improvement": "+0.37",
      "schedule_improvement": "20 days earlier",
      "recommendations_applied": ["Descope WI-045", "Resolve BLK-001"]
    }
  }
}
```
**Dependencies:** ForecastEngine, RecommendationEngine, SessionStore

---

### 2.7 POST /api/demo/reset ❌
**Status:** NOT IMPLEMENTED  
**Purpose:** Reset system to initial state for demo restart  
**Request:**
```json
{
  "session_id": "abc123"
}
```
**Response:**
```json
{
  "success": true,
  "message": "Demo reset. Ready for restart."
}
```
**Side Effects:** 
- Clears all session state from SessionStore
- Clears recommendation history
- Resets any scope changes

---

### 2.8 POST /api/demo/load ❌
**Status:** NOT IMPLEMENTED  
**Purpose:** Pre-load demo workbook without upload  
**Request:**
```json
{
  "use_demo_workbook": true
}
```
**Response:**
```json
{
  "success": true,
  "data": {
    "session_id": "demo-001",
    "project_summary": { /* loaded project */ }
  }
}
```
**Location:** References TIO2_Sprint_Intelligence_VALIDATED.xlsx from filesystem

---

## 3. MISSING ROUTE FILES

**Expected Location:** `backend/app/api/routes/`  
**Currently Exists:**
- ✅ `upload.py` — Phase 1 POST /upload
- ✅ `phase2.py` — Phase 2 GET /metrics, /dependencies, /spillover

**Missing Files:**
- ❌ `simulate.py` — POST /simulate
- ❌ `risks.py` — GET /risks
- ❌ `recommendations.py` — GET /recommendations
- ❌ `simulate_recommendation.py` — POST /simulate-recommendation
- ❌ `scope_change.py` — POST /scope-change
- ❌ `reforecast_comparison.py` — GET /reforecast-comparison
- ❌ `demo.py` — POST /demo/reset, POST /demo/load

---

## 4. MISSING API MODELS

**File:** `backend/app/api/models_phase3.py` (DOES NOT EXIST)

Required Models:
- `ForecastResult`
- `SimulationDistribution`
- `RiskAssessment`
- `SprintRisk`
- `RiskDriver`
- `Recommendation`
- `RecommendationResult`
- `ReforecastComparison`
- `ScopeChangeLog`
- `CapacityAllocation`

**Estimated Lines:** 300-400 lines

---

## 5. FRONTEND STATUS: NOT STARTED

**Planned Structure:**
```
frontend/
├── src/
│   ├── pages/
│   │   ├── UploadPage.tsx
│   │   ├── CommandCenterPage.tsx ⭐
│   │   ├── RecommendationsPage.tsx
│   │   ├── ReforecastPage.tsx ⭐
│   │   ├── SprintRiskPage.tsx
│   │   ├── SimulationPage.tsx
│   │   └── ScopeChangePage.tsx
│   ├── components/
│   │   ├── layout/ (5 components)
│   │   ├── command-center/ (6 components)
│   │   ├── simulation/ (3 components)
│   │   ├── reforecast/ (3 components)
│   │   ├── risk/ (4 components)
│   │   ├── recommendations/ (4 components)
│   │   ├── scope/ (4 components)
│   │   └── shared/ (6 components)
│   ├── store/ (Zustand state management)
│   ├── api/ (7 client modules)
│   ├── hooks/ (5 custom hooks)
│   ├── types/ (5 TypeScript type files)
│   └── utils/ (3 utility files)
```

**Completely Missing:**
- ❌ package.json (React/Vite/TypeScript setup)
- ❌ tsconfig.json
- ❌ index.html
- ❌ vite.config.ts
- ❌ tailwind.config.ts
- ❌ **30+ React components** (estimated 2,000+ lines)
- ❌ **7 API client modules** (estimated 400+ lines)
- ❌ **5 custom hooks** (estimated 300+ lines)
- ❌ **5 type files** (estimated 250+ lines)

**Estimated Frontend LOC:** 3,000+ lines

---

## 6. CONFIGURATION & INFRASTRUCTURE

### 6.1 Environment Files ❌
**Missing:**
- ❌ `.env` file (API_URL, MC_ITERATIONS, etc.)
- ❌ `.env.example` template

### 6.2 Docker ❌
**Missing:**
- ❌ `Dockerfile` (backend)
- ❌ `docker-compose.yml` (backend + frontend)
- ❌ `.dockerignore`

### 6.3 Deployment ❌
**Missing:**
- ❌ `deploy.sh` script
- ❌ GitHub Actions CI/CD
- ❌ Heroku/Railway/Vercel configs
- ❌ Production settings

---

## 7. CONFIGURATION NOTES

### Settings Already Defined (config.py) ✓
```python
# Monte Carlo
mc_iterations = 10_000
effort_variance_min = 0.80
effort_variance_max = 1.35
velocity_std_dev = 0.15

# Blocker Impact
blocker_velocity_impact = {
    "Critical": 0.40,
    "High": 0.20,
    "Medium": 0.10,
    "Low": 0.05,
}

# Risk Weights
risk_weights = {
    "schedule": 0.35,
    "resource": 0.25,
    "dependency": 0.25,
    "scope": 0.15,
}

# Thresholds
risk_critical_threshold = 75
risk_high_threshold = 50
```

### Additional Config Needed
- Recommendation confidence thresholds
- Demo workbook path
- Session store TTL
- API rate limiting

---

## 8. DOCUMENTATION

### Existing Documentation ✓
- ✓ `backend/README.md` — Phase 1 overview
- ✓ `hackathon_requirement.md` — Complete V2 spec
- ✓ `IMPLEMENTATION_STATUS.md` — Phase 1-2 inventory
- ✓ `TEST_COVERAGE_AND_WORKBOOK_ANALYSIS.md` — Test report

### Missing Documentation ❌
- ❌ Phase 3 API specification
- ❌ Frontend development guide
- ❌ Deployment guide
- ❌ Architecture diagrams (Mermaid)
- ❌ Frontend component library docs

---

## 9. ESTIMATED EFFORT BREAKDOWN

| Component | Files | LOC | Effort (hours) |
|-----------|-------|-----|---|
| Forecast Engine | 1 | 300 | 4 |
| Monte Carlo Engine | 1 | 250 | 3 |
| Risk Engine | 1 | 200 | 2.5 |
| Recommendation Engine | 1 | 250 | 3 |
| Capacity Engine | 1 | 150 | 2 |
| Route Files (7) | 7 | 700 | 5 |
| API Models | 1 | 350 | 2.5 |
| Tests | 5 | 400 | 3 |
| **Backend Total** | **17** | **2,600** | **25.5** |
| **Frontend** | **30+** | **3,500+** | **35** |
| **Docker/Deploy** | **5** | **200** | **3** |
| **Documentation** | **3** | **300** | **2** |
| **GRAND TOTAL** | **55+** | **6,600+** | **65.5 hours** |

---

## 10. IMPLEMENTATION ROADMAP

### Critical Path for Demo
1. **Forecast Engine** (4 hrs) — Core of demo story
2. **Monte Carlo Engine** (3 hrs) — Required for forecast
3. **POST /simulate endpoint** (2 hrs) — Wire forecast to API
4. **Risk Engine** (2.5 hrs) — Show problem
5. **Recommendation Engine** (3 hrs) — Show solution
6. **GET /recommendations endpoint** (2 hrs) — Deliver recommendations
7. **POST /simulate-recommendation** (2 hrs) — Show impact
8. **GET /reforecast-comparison** (1.5 hrs) — Money shot endpoint
9. **Basic UI (React)** (8 hrs) — Minimal upload + comparison screen
10. **Demo endpoints** (1.5 hrs) — /demo/reset, /demo/load

**Minimum for 15-second demo:** 29.5 hours

### Full Implementation
Add: All 7 pages, 40+ components, comprehensive frontend, Docker, CI/CD = **65+ hours total**

---

## 11. CONFIGURATION VERIFICATION CHECKLIST

- ❌ **No .env file** — Need to create with Monte Carlo settings
- ❌ **No Docker setup** — Needed for deployment
- ❌ **No requirements.txt updates** — May need additional libraries (numpy for MC)
- ✅ **config.py** — Already configured correctly
- ✓ **Session Store** — Already implemented
- ✓ **Workbook** — Already validated

---

## 12. INCOMPLETE IMPLEMENTATIONS IN EXISTING CODE

### Search Results for TODO/FIXME
**Command:** `grep -r "TODO|FIXME|XXX|not.?implement|placeholder" backend/app --include="*.py"`

**Result:** ✓ **NO TODO COMMENTS FOUND**

The codebase is complete for Phase 1-2, with no stub implementations.

---

## SUMMARY: WHAT'S MISSING

### Engines (5)
- ❌ Forecast Engine (completion probability)
- ❌ Monte Carlo Engine (simulation)
- ❌ Risk Engine (risk identification)
- ❌ Recommendation Engine (recommendations)
- ❌ Capacity Engine (capacity allocation)

### Endpoints (8)
- ❌ POST /api/simulate
- ❌ GET /api/risks
- ❌ GET /api/recommendations
- ❌ POST /api/simulate-recommendation
- ❌ POST /api/scope-change
- ❌ GET /api/reforecast-comparison
- ❌ POST /api/demo/reset
- ❌ POST /api/demo/load

### Frontend (30+ components)
- ❌ Complete React/TypeScript application
- ❌ 7 pages + 40+ components
- ❌ State management + API clients

### Infrastructure
- ❌ Docker setup
- ❌ .env configuration
- ❌ Deployment scripts
- ❌ CI/CD pipeline
