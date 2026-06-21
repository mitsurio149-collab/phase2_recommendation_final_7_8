# Recommendation Strategy Matrix

**Purpose:** Maps Risk Engine drivers to candidate mitigation strategies for Phase 3.4 Recommendation Engine

**Date:** June 12, 2026  
**Status:** Strategic Analysis (Implementation to follow)

---

## Executive Summary

| Metric | Value |
|---|---|
| Total Risk Drivers Identified | 27 |
| Actionable Drivers | 26 (96%) |
| Non-Actionable Drivers | 1 (4%) |
| Recommendation Types | 7 |
| Coverage | 100% (all drivers mappable) |

---

## Driver Actionability Assessment

### ✅ ACTIONABLE (26/27)

| Driver | Recommendation Types | Why Actionable |
|---|---|---|
| **Critical On-Time Probability** | Add Resource, Descope Work, Move Sprint | Low probability requires intervention |
| **Poor On-Time Probability** | Add Resource, Descope Work, Move Sprint | Majority late in simulations |
| **Moderate On-Time Probability** | Resolve Blocker, Reduce WIP, Split Task | Marginal case—targeted fixes help |
| **High Expected Delay** | Add Resource, Descope Work, Move Sprint | Concrete delay target |
| **Moderate Expected Delay** | Resolve Blocker, Split Task, Reassign Work | Smaller delays addressable |
| **High Spillover Prediction** | Add Resource, Reduce WIP, Resolve Blocker | Predictable overflow |
| **Moderate Spillover Risk** | Resolve Blocker, Reduce WIP, Split Task | Early intervention prevents cascade |
| **Tight Critical Path** | Split Task, Parallelize (reassign), Resolve Blocker | Zero-slack chain fixable |
| **High Dependency Density** | Split Task, Reassign Work, Resolve Blocker | Complexity addressable |
| **Moderate Dependency Density** | Split Task, Reassign Work | Decomposition works |
| **Long Critical Path Chain** | Split Task, Reassign Work, Parallelize | Chain breakable |
| **Moderate Critical Path Length** | Resolve Blocker, Reduce WIP | Small chain manageable |
| **Dependency Bottlenecks** | Reassign Work, Resolve Blocker, Add Resource | Bottleneck owners removable |
| **Deep Blocker Cascade** | Resolve Blocker, Add Resource | Root blocker resolution cascades |
| **Extreme Team Overload** | Add Resource, Reassign Work, Descope Work | Immediate relief needed |
| **High Team Overload** | Add Resource, Reduce WIP, Resolve Blocker | Capacity shortage addressable |
| **Velocity Degradation** | Resolve Blocker, Reduce WIP, Add Resource | Performance decline reversible |
| **High Active Blocker Count** | Resolve Blocker, Add Resource, Reassign Work | Blockers have owners/solutions |
| **Team Allocation Imbalance** | Reassign Work, Add Resource | Load balancing possible |
| **Major Estimate Inflation** | Descope Work, Reassign Work, Split Task | Scope decisions available |
| **Moderate Estimate Inflation** | Split Task, Reassign Work | Decomposition helps |
| **High Historical Spillover** | Reduce WIP, Resolve Blocker, Add Resource | Pattern indicates root causes |
| **Moderate Spillover Pattern** | Reduce WIP, Resolve Blocker | Manageable with focus |
| **High Blocked Item Rate** | Resolve Blocker, Add Resource, Reassign Work | Blocker resolution is primary |
| **High Not-Started Item Volume** | Add Resource, Reduce WIP, Move Sprint | Late-stage work addressable |

### ❌ NON-ACTIONABLE (1/27)

| Driver | Reason | Notes |
|---|---|---|
| **Moderate On-Time Probability (0.50-0.75 range)** | Symptom, not root cause | Indicates underlying issues (see SCHEDULE + other categories) |

---

## Recommendation Type → Impact Analysis

### 1. RESOLVE BLOCKER (Highest Impact)

**Effective Against:** 12 drivers  
**Impact Potential:** ⭐⭐⭐⭐⭐ (5/5)  
**Implementation Time:** Hours to days  
**Risk Reduction:** 15-25% per blocker

#### Direct Mappings:
- Deep Blocker Cascade (root cause fix)
- High Active Blocker Count (direct fix)
- Moderate Spillover Risk (prevents cascade)
- Moderate On-Time Probability (underlying cause)
- Moderate Critical Path Length (enables CP item progress)
- Velocity Degradation (removes blocker-induced slowdown)
- High Blocked Item Rate (directly targets blocked items)
- Tight Critical Path (enables critical path item progress)
- Dependency Bottlenecks (if bottleneck is a blocker)
- High Team Overload (frees team time)
- Extreme Team Overload (frees team time)

#### Why #1 Impact:
- Blockers are the ONLY driver affecting team velocity immediately
- One resolved blocker can unblock 3-5 downstream items (cascade relief)
- Visible, measurable impact
- No scope negotiation needed
- Direct delay reduction: 2-5 days per critical blocker

#### Example Impact:
```
Current: 7 active blockers, 35% on-time probability
Resolve 2 critical blockers → +12% on-time probability (47%)
Resolve 4 total blockers → +25% on-time probability (60%)
```

---

### 2. ADD RESOURCE (High Impact)

**Effective Against:** 10 drivers  
**Impact Potential:** ⭐⭐⭐⭐ (4/5)  
**Implementation Time:** Days to weeks (hiring)  
**Risk Reduction:** 10-20% per resource added

#### Direct Mappings:
- Extreme Team Overload (reduces utilization to acceptable)
- High Team Overload (increases capacity)
- Critical On-Time Probability (adds velocity)
- Poor On-Time Probability (increases capacity for catch-up)
- High Expected Delay (increases sprint velocity)
- High Active Blocker Count (dedicated blocker resolver)
- High Spillover Prediction (increased capacity absorbs overflow)
- Deep Blocker Cascade (dedicated blocker resolution)
- Dependency Bottlenecks (second person on bottleneck tasks)
- High Not-Started Item Volume (late-stage capacity)

#### Why High Impact:
- Directly increases sprint velocity
- Addresses multiple drivers simultaneously
- Measurable ROI (velocity increase ÷ resource cost)
- BUT: Hiring delay (2-4 weeks) may be too slow for critical projects

#### Example Impact:
```
Current: Velocity 100h/sprint, 1 engineer, utilization 95%
Add Resource: Velocity 150h/sprint, 2 engineers, utilization 75%
Impact: Expected delay drops 28 days → 8 days
On-time probability: 35% → 75%
```

#### Constraint:
- Only effective if bottleneck is TEAM CAPACITY, not complexity
- Won't help if problem is "too much work" split across many specialists
- Requires skills match (adding generalist to specialized team = 2x ramp time)

---

### 3. DESCOPE WORK (High Impact)

**Effective Against:** 6 drivers  
**Impact Potential:** ⭐⭐⭐⭐ (4/5)  
**Implementation Time:** Hours (decision) to days (replanning)  
**Risk Reduction:** 20-40% per 20% descope

#### Direct Mappings:
- Critical On-Time Probability (reduces required work)
- Poor On-Time Probability (reduces scope to achievable subset)
- High Expected Delay (eliminates delay-causing work)
- Major Estimate Inflation (removes inflated items)
- Moderate Estimate Inflation (removes questionable items)
- Extreme Team Overload (reduces workload to capacity)

#### Why High Impact:
- FASTEST risk reduction method
- Immediate effect (no ramp time)
- Mathematically guaranteed to improve on-time probability
- Most politically difficult (stakeholder negotiation)

#### Example Impact:
```
Current: 200 hours work, 100 hours capacity, 2 sprints
Descope 40 hours (20%): 160 hours → fits in 1.6 sprints
On-time probability: 35% → 85%
Expected delay: 28 days → 2 days
```

#### Constraint:
- Requires stakeholder agreement
- May impact delivered value
- Only works if descoped items are truly "nice to have"
- Won't solve if remaining scope is already overestimated

---

### 4. SPLIT TASK (Medium-High Impact)

**Effective Against:** 8 drivers  
**Impact Potential:** ⭐⭐⭐⭐ (4/5)  
**Implementation Time:** Days (refactoring work)  
**Risk Reduction:** 5-15% per task split

#### Direct Mappings:
- Tight Critical Path (breaks long serial chain)
- Long Critical Path Chain (decomposes chain into parallelizable segments)
- High Dependency Density (reduces complexity by decomposition)
- Moderate Dependency Density (clarifies task boundaries)
- Moderate On-Time Probability (unlocks parallelization)
- Moderate Spillover Risk (smaller tasks = more predictable)
- Moderate Expected Delay (parallelization opportunity)
- Moderate Critical Path Length (enables pipeline execution)

#### Why Medium-High Impact:
- Enables parallelization (convert serial → parallel)
- Reduces scope creep on individual tasks
- Makes estimation clearer
- BUT: Overhead from task coordination

#### Example Impact:
```
Before: Task A (40h) → Task B (40h) → Task C (40h) [Serial: 120h]
After: A1(20h) + A2(20h) || B1(25h) + B2(15h) || C1(30h) + C2(10h)
Result: 40h + 25h + 30h = 95h (parallel critical path)
Delay reduction: 25 hours (3-4 day improvement)
```

#### Constraint:
- Only works if tasks can be parallelized (dependencies allow)
- Adds coordination overhead (5-10% per split)
- Requires skill match (can't split specialist task without specialist)

---

### 5. REDUCE WIP (Medium Impact)

**Effective Against:** 7 drivers  
**Impact Potential:** ⭐⭐⭐ (3/5)  
**Implementation Time:** Hours (policy change)  
**Risk Reduction:** 8-12% per WIP reduction level

#### Direct Mappings:
- Velocity Degradation (context switching overhead reduced)
- High Active Blocker Count (focus on fewer items)
- High Team Overload (psychological relief, better focus)
- High Spillover Prediction (completes items faster)
- Moderate Spillover Risk (finish-before-start discipline)
- High Historical Spillover (prevents thrashing)
- Moderate On-Time Probability (quality improvement)

#### Why Medium Impact:
- No resource cost
- Immediate effect
- BUT: Requires team discipline
- Impacts only visible in 1-2 sprints

#### Example Impact:
```
Current: 8 items in progress (high context switching)
Reduce to: 4 items in progress

Impact:
- Task completion time: 8 days → 5 days (reduced context switching)
- Spillover rate: 30% → 15%
- Active blockers feel less overwhelming (fewer interrupts)
- On-time probability: +8%
```

#### Constraint:
- Requires STRONG team discipline (Agile rigor)
- Doesn't help if blocker severity dominates
- Cultural change (not technical fix)

---

### 6. REASSIGN WORK (Medium Impact)

**Effective Against:** 8 drivers  
**Impact Potential:** ⭐⭐⭐ (3/5)  
**Implementation Time:** Hours (decision) to days (context switching)  
**Risk Reduction:** 5-15% per reassignment

#### Direct Mappings:
- Team Allocation Imbalance (balances load)
- Dependency Bottlenecks (moves bottleneck to different person)
- High Dependency Density (domain expert assignment)
- Moderate Dependency Density (skill match assignment)
- Long Critical Path Chain (assigns CP items to best performer)
- Moderate Critical Path Length (prioritizes CP)
- Major Estimate Inflation (re-estimates with better estimator)
- Moderate Estimate Inflation (different perspective on scope)

#### Why Medium Impact:
- Low/no cost
- Can improve estimate accuracy (10-20%)
- Reduces context-switching (if reassign to specialist)
- BUT: Limited by team size
- May create new imbalance elsewhere

#### Example Impact:
```
Current: Junior engineer on critical path item (estimate inflation risk)
Reassign to: Senior engineer (better estimation, faster execution)
Impact:
- Estimate accuracy: 60% → 90%
- Execution speed: 25% faster
- Overall delay: -4 days
```

#### Constraint:
- Only works if team has spare capacity
- Skill matching required
- Knowledge context loss (person who knows item best?)
- Limited by team size

---

### 7. MOVE SPRINT (Lower Impact)

**Effective Against:** 3 drivers  
**Impact Potential:** ⭐⭐ (2/5)  
**Implementation Time:** Hours (decision)  
**Risk Reduction:** 0% (moves problem, not solves)

#### Direct Mappings:
- Critical On-Time Probability (trades timing risk for known date)
- Poor On-Time Probability (pushes off to next release)
- High Expected Delay (absorbs delay by extending timeline)

#### Why Lower Impact:
- Does NOT reduce delay (just moves target date)
- Acceptable ONLY if:
  - External deadline is flexible
  - Stakeholders accept new date
  - Avoids catastrophic miss
- Often used as LAST RESORT when other mitigations fail

#### Example:
```
Current: Target June 30, expected finish July 28 (28-day miss)
Recommendation: Move to August 15
Result: No risk reduction, just different deadline
```

#### When to Use:
- When on-time probability < 20% and time to resolve < 2 weeks
- As "fallback" recommendation alongside other tactics
- When marketing/sales window is flexible
- NOT as primary recommendation

---

## Impact Ranking: Expected Reduction in Delay

| Recommendation Type | Delay Reduction | Effort | Risk | Best Used For |
|---|---|---|---|---|
| 🥇 **Resolve Blocker** | 15-25% per blocker | Low-Med | Low | Deep Blocker Cascade, High Active Blockers |
| 🥈 **Descope Work** | 20-40% (20% scope) | Med-High | Med | Critical/Poor On-Time Prob, Extreme Overload |
| 🥉 **Add Resource** | 15-30% per resource | High | Med-High | High Overload, High Spillover, Not-Started Vol |
| 4️⃣ **Split Task** | 10-20% per task | Med | Low | Long CP Chain, High Dependency Density |
| 5️⃣ **Reduce WIP** | 8-12% | Low | Low | Velocity Degradation, Spillover Pattern |
| 6️⃣ **Reassign Work** | 5-15% per reassignment | Low | Low | Team Imbalance, Bottlenecks, Estimates |
| 7️⃣ **Move Sprint** | 0% (timing only) | Low | High | Last resort fallback |

---

## Recommendation Strategy Matrix (Full)

### SCHEDULE RISK DRIVERS

#### 1. Critical On-Time Probability (on_time_prob < 0.25)
```
Actionable: YES
Severity: CRITICAL (5/5)
Current State: >75% chance of missing deadline

Primary Recommendations (Priority Order):
1. DESCOPE WORK              [Impact: ⭐⭐⭐⭐⭐] [Effort: ⭐⭐⭐]
   - Remove 20-30% of scope
   - Only keep must-haves
   - Impact: Delay 28d → 5-8d

2. ADD RESOURCE              [Impact: ⭐⭐⭐⭐] [Effort: ⭐⭐⭐⭐]
   - Hire/reallocate 1-2 engineers
   - Focus on critical path
   - Impact: Delay 28d → 10-15d (if available)

3. RESOLVE BLOCKER           [Impact: ⭐⭐⭐⭐] [Effort: ⭐⭐]
   - Identify 3-5 critical blockers
   - Add resources to unblock
   - Impact: Delay 28d → 18-20d (partial)

4. MOVE SPRINT               [Impact: ⭐] [Effort: ⭐]
   - Last resort: extend deadline
   - Only if descope not available
   - Impact: Risk removed (by definition)

Secondary Recommendations:
- Split Task (parallelize)
- Reduce WIP (focus team)
- Reassign Work (get best people on CP)

Combination Impact:
- Descope (20%) + Resolve Blocker (2 critical) = 35% → 85% on-time prob
- Descope (30%) + Add Resource (1) = 35% → 95% on-time prob
```

#### 2. Poor On-Time Probability (on_time_prob: 0.25-0.50)
```
Actionable: YES
Severity: VERY_HIGH (4/5)
Current State: 50-75% chance of missing deadline

Primary Recommendations:
1. DESCOPE WORK              [Impact: ⭐⭐⭐⭐⭐] [Effort: ⭐⭐⭐]
   - Remove 10-20% of scope
   - Impact: 40% prob → 70% prob

2. ADD RESOURCE              [Impact: ⭐⭐⭐⭐] [Effort: ⭐⭐⭐⭐]
   - Temporary or contract
   - Impact: 40% prob → 65% prob

3. RESOLVE BLOCKER           [Impact: ⭐⭐⭐⭐] [Effort: ⭐⭐]
   - 2-3 key blockers
   - Impact: 40% prob → 55% prob

Secondary: Split Task, Reduce WIP, Reassign Work
```

#### 3. Moderate On-Time Probability (on_time_prob: 0.50-0.75)
```
Actionable: MARGINALLY (underlying issues present)
Severity: HIGH (3/5)
Current State: 25-50% chance of missing deadline

Primary Recommendations:
1. RESOLVE BLOCKER           [Impact: ⭐⭐⭐⭐] [Effort: ⭐⭐]
   - Target 2 blockers
   - Impact: 65% prob → 80% prob

2. REDUCE WIP                [Impact: ⭐⭐⭐] [Effort: ⭐]
   - Focus on completing items
   - Impact: 65% prob → 75% prob

3. SPLIT TASK                [Impact: ⭐⭐⭐⭐] [Effort: ⭐⭐⭐]
   - Parallelize if possible
   - Impact: 65% prob → 85% prob

Note: This is SYMPTOM driver. Root causes in other categories.
```

#### 4. High Expected Delay (delay_days > 30)
```
Actionable: YES
Severity: CRITICAL (5/5)
Current State: Will miss by 4+ weeks

Primary Recommendations:
1. DESCOPE WORK              [Impact: ⭐⭐⭐⭐⭐] [Effort: ⭐⭐⭐]
   - Scale: 20% descope → 8-day reduction
   - Scale: 30% descope → 12-day reduction
   - Impact: 30d delay → 15-18d delay

2. ADD RESOURCE              [Impact: ⭐⭐⭐⭐] [Effort: ⭐⭐⭐⭐]
   - Increases sprint velocity
   - Impact: 30d delay → 15-20d delay

3. SPLIT TASK                [Impact: ⭐⭐⭐⭐] [Effort: ⭐⭐⭐]
   - Unlock parallelization
   - Impact: 30d delay → 20-24d delay

4. RESOLVE BLOCKER           [Impact: ⭐⭐⭐⭐] [Effort: ⭐⭐]
   - Each critical blocker = 3-5 days
   - Impact: 30d delay → 20-25d delay

Combination:
- Descope (20%) + Resolve Blocker (2) = 30d → 10-12d
```

#### 5. Moderate Expected Delay (delay_days: 10-30)
```
Actionable: YES
Severity: VERY_HIGH (4/5)
Current State: Will miss by 1-4 weeks

Primary Recommendations:
1. RESOLVE BLOCKER           [Impact: ⭐⭐⭐⭐] [Effort: ⭐⭐]
   - Target 2-3 blockers
   - Impact: 20d delay → 8-12d

2. SPLIT TASK                [Impact: ⭐⭐⭐⭐] [Effort: ⭐⭐⭐]
   - Parallelize work
   - Impact: 20d delay → 12-16d

3. REASSIGN WORK             [Impact: ⭐⭐⭐] [Effort: ⭐⭐]
   - Give to faster performer
   - Impact: 20d delay → 15-18d

Secondary: Reduce WIP, Add Resource
```

#### 6. High Spillover Prediction (spillovers >= 10)
```
Actionable: YES
Severity: VERY_HIGH (4/5)
Current State: 10+ items will carry over (multiply delays)

Primary Recommendations:
1. ADD RESOURCE              [Impact: ⭐⭐⭐⭐] [Effort: ⭐⭐⭐⭐]
   - Increase sprint capacity
   - Complete more items
   - Impact: 15 spillovers → 5 spillovers

2. REDUCE WIP                [Impact: ⭐⭐⭐] [Effort: ⭐]
   - Focus on completion
   - Impact: 15 spillovers → 8 spillovers

3. RESOLVE BLOCKER           [Impact: ⭐⭐⭐⭐] [Effort: ⭐⭐]
   - Blockers cause spillover
   - Impact: 15 spillovers → 8-10 spillovers

Secondary: Split Task, Descope Work
```

#### 7. Moderate Spillover Risk (spillovers: 5-10)
```
Actionable: YES
Severity: HIGH (3/5)
Current State: 5-10 items will overflow

Primary Recommendations:
1. RESOLVE BLOCKER           [Impact: ⭐⭐⭐⭐] [Effort: ⭐⭐]
   - Unblock in-flight work
   - Impact: 7 spillovers → 3-4 spillovers

2. REDUCE WIP                [Impact: ⭐⭐⭐] [Effort: ⭐]
   - Complete faster
   - Impact: 7 spillovers → 4-5 spillovers

3. SPLIT TASK                [Impact: ⭐⭐⭐⭐] [Effort: ⭐⭐⭐]
   - Smaller tasks complete faster
   - Impact: 7 spillovers → 3-4 spillovers

Secondary: Add Resource
```

#### 8. Tight Critical Path (cp_utilization > 90%)
```
Actionable: YES
Severity: HIGH (3/5)
Current State: Critical path has <10% slack (no buffer)

Primary Recommendations:
1. SPLIT TASK                [Impact: ⭐⭐⭐⭐] [Effort: ⭐⭐⭐]
   - Break long serial chain
   - Parallelize segments
   - Impact: Breaks tight path into 2-3 parallel threads

2. RESOLVE BLOCKER           [Impact: ⭐⭐⭐⭐] [Effort: ⭐⭐]
   - Blocking items on CP
   - Impact: Unblocks CP → faster progression

3. REASSIGN WORK             [Impact: ⭐⭐⭐] [Effort: ⭐⭐]
   - Faster performer on CP
   - Impact: Reduces critical path duration 10-15%

Secondary: Add Resource to CP tasks
```

---

### DEPENDENCY RISK DRIVERS

#### 9. High Dependency Density (dep_ratio > 2.5)
```
Actionable: YES
Severity: VERY_HIGH (4/5)
Current State: 2.5+ dependencies per item (very complex)

Primary Recommendations:
1. SPLIT TASK                [Impact: ⭐⭐⭐⭐] [Effort: ⭐⭐⭐⭐]
   - Decompose large tasks
   - Reduce dependency requirements
   - Impact: dep_ratio 3.0 → 2.0

2. REASSIGN WORK             [Impact: ⭐⭐⭐] [Effort: ⭐⭐]
   - Specialist assignment (fewer handoffs)
   - Impact: dep_ratio 3.0 → 2.7

3. RESOLVE BLOCKER           [Impact: ⭐⭐⭐⭐] [Effort: ⭐⭐]
   - Remove blocking dependencies
   - Impact: Enables parallel execution

Secondary: Reduce WIP, Move Sprint
```

#### 10. Moderate Dependency Density (dep_ratio: 1.5-2.5)
```
Actionable: YES
Severity: HIGH (3/5)
Current State: 1.5-2.5 dependencies per item (moderate complexity)

Primary Recommendations:
1. SPLIT TASK                [Impact: ⭐⭐⭐⭐] [Effort: ⭐⭐⭐]
   - Clearer task boundaries
   - Reduce implicit dependencies
   - Impact: dep_ratio 2.0 → 1.5

2. REASSIGN WORK             [Impact: ⭐⭐⭐] [Effort: ⭐⭐]
   - Reduce handoffs
   - Impact: dep_ratio 2.0 → 1.8

Secondary: Resolve Blocker
```

#### 11. Long Critical Path Chain (cp_items > 10)
```
Actionable: YES
Severity: VERY_HIGH (4/5)
Current State: 10+ item serial chain (no parallelization)

Primary Recommendations:
1. SPLIT TASK                [Impact: ⭐⭐⭐⭐] [Effort: ⭐⭐⭐⭐]
   - Break into parallel workstreams
   - Convert serial → parallel
   - Example: A→B→C→D→E→F→G→H→I→J→K
            Becomes: (A→B→C) || (D→E→F) || (G→H) || (I→J→K)
   - Impact: 11 items serial (110h) → 3-4 parallel (40h)

2. REASSIGN WORK             [Impact: ⭐⭐⭐] [Effort: ⭐⭐]
   - Fastest person on each segment
   - Impact: 110h → 90h (30% faster)

3. ADD RESOURCE              [Impact: ⭐⭐⭐⭐] [Effort: ⭐⭐⭐⭐]
   - Parallel workstream leads
   - Impact: Enables 3-way parallelization

Secondary: Resolve Blocker on CP items
```

#### 12. Moderate Critical Path Length (cp_items: 5-10)
```
Actionable: YES
Severity: HIGH (3/5)
Current State: 5-10 item chain (some parallelization possible)

Primary Recommendations:
1. RESOLVE BLOCKER           [Impact: ⭐⭐⭐⭐] [Effort: ⭐⭐]
   - Blocking CP items
   - Impact: Unlocks progression

2. REDUCE WIP                [Impact: ⭐⭐⭐] [Effort: ⭐]
   - Focus on CP completion
   - Impact: Faster CP throughput

3. SPLIT TASK                [Impact: ⭐⭐⭐⭐] [Effort: ⭐⭐⭐]
   - Break into 2-3 parallel tracks
   - Impact: 8 items → 5-6 parallel

Secondary: Reassign to best performer
```

#### 13. Dependency Bottlenecks (5+ predecessors)
```
Actionable: YES
Severity: HIGH (3/5)
Current State: N items have 5+ dependencies on them

Primary Recommendations:
1. REASSIGN WORK             [Impact: ⭐⭐⭐] [Effort: ⭐⭐]
   - Put bottleneck owner's best performer
   - They become gating item for 5+ other tasks
   - Impact: Faster bottleneck → unblocks dependents

2. ADD RESOURCE              [Impact: ⭐⭐⭐⭐] [Effort: ⭐⭐⭐⭐]
   - Second person on bottleneck
   - Or: Add person to parallelize dependent work
   - Impact: Bottleneck completes faster

3. RESOLVE BLOCKER           [Impact: ⭐⭐⭐⭐] [Effort: ⭐⭐]
   - If bottleneck itself is blocked
   - Impact: Cascades to all 5+ dependents

Secondary: Split Task (break bottleneck into sub-tasks)
```

#### 14. Deep Blocker Cascade (cascade_depth > 5)
```
Actionable: YES (CRITICAL)
Severity: CRITICAL (5/5)
Current State: One blocker affects 5+ levels of downstream items

Primary Recommendations:
1. RESOLVE BLOCKER           [Impact: ⭐⭐⭐⭐⭐] [Effort: ⭐⭐⭐]
   - Root cause: Resolve root blocker
   - Impact: Cascades relief through all 5+ levels
   - Example: Blocker blocks B, B blocks C,D,E, C blocks F,G,H...
             Resolve blocker → entire chain unblocks

2. ADD RESOURCE              [Impact: ⭐⭐⭐⭐] [Effort: ⭐⭐⭐]
   - Dedicated blocker resolution resource
   - Impact: Faster root resolution

3. REASSIGN WORK             [Impact: ⭐⭐⭐] [Effort: ⭐⭐]
   - Best troubleshooter on root blocker
   - Impact: Reduces resolution time 30-50%

Note: This is HIGHEST priority for Recommendation Engine
      One recommendation can fix 5+ other drivers
```

---

### RESOURCE RISK DRIVERS

#### 15. Extreme Team Overload (utilization > 0.95)
```
Actionable: YES
Severity: CRITICAL (5/5)
Current State: Team 95%+ allocated (no buffer)

Primary Recommendations:
1. ADD RESOURCE              [Impact: ⭐⭐⭐⭐⭐] [Effort: ⭐⭐⭐⭐]
   - Must add resources
   - Target: Bring utilization to 75-85%
   - Impact: 95% util → 75% util = 20% capacity gain

2. DESCOPE WORK              [Impact: ⭐⭐⭐⭐⭐] [Effort: ⭐⭐⭐]
   - Remove 15-20% of scope
   - Impact: 95% util → 75-80% util

3. REDUCE WIP                [Impact: ⭐⭐⭐] [Effort: ⭐]
   - Strict WIP limit
   - Doesn't solve but improves morale
   - Impact: Better quality, fewer context switches

Combination:
- Add Resource (1) + Reduce WIP = 95% → 78% util + better flow

Note: Can't ignore—teams at 95% are at breaking point
```

#### 16. High Team Overload (utilization: 0.85-0.95)
```
Actionable: YES
Severity: VERY_HIGH (4/5)
Current State: Team 85-95% allocated (limited buffer)

Primary Recommendations:
1. ADD RESOURCE              [Impact: ⭐⭐⭐⭐] [Effort: ⭐⭐⭐⭐]
   - Add 1 engineer
   - Impact: 90% util → 65-75% util

2. REDUCE WIP                [Impact: ⭐⭐⭐] [Effort: ⭐]
   - WIP limit to prevent context switching
   - Impact: 90% util effective → 80% (less friction)

3. RESOLVE BLOCKER           [Impact: ⭐⭐⭐⭐] [Effort: ⭐⭐]
   - Each blocker resolution frees capacity
   - Impact: 90% util → 85% util per blocker

Secondary: Reassign, Reduce WIP
```

#### 17. Velocity Degradation (trend < -0.10)
```
Actionable: YES
Severity: VERY_HIGH (4/5)
Current State: Velocity down >10% sprint-over-sprint

Primary Recommendations:
1. RESOLVE BLOCKER           [Impact: ⭐⭐⭐⭐] [Effort: ⭐⭐]
   - Blockers cause velocity loss
   - Clear blockers → velocity recovers
   - Impact: Velocity -20% → -5% → 0% recovery

2. REDUCE WIP                [Impact: ⭐⭐⭐] [Effort: ⭐]
   - High WIP causes context switching
   - Impact: Velocity -20% → -12% (partial recovery)

3. ADD RESOURCE              [Impact: ⭐⭐⭐] [Effort: ⭐⭐⭐⭐]
   - If degradation due to capacity squeeze
   - Impact: Velocity recovers if fresh capacity helps

Investigation Needed: Why degrading?
- Blockers? → Resolve Blocker
- WIP chaos? → Reduce WIP
- Team burnout? → Add Resource or Descope
- Technical debt? → Split Task + Refactor
```

#### 18. High Active Blocker Count (blockers > 5)
```
Actionable: YES
Severity: VERY_HIGH (4/5)
Current State: 5+ open blockers at any time

Primary Recommendations:
1. RESOLVE BLOCKER           [Impact: ⭐⭐⭐⭐⭐] [Effort: ⭐⭐⭐]
   - Dedicate resources to blocker resolution
   - Target: 2-3 blockers/sprint resolved
   - Impact: 8 blockers → 2-3 blockers in 1-2 sprints

2. ADD RESOURCE              [Impact: ⭐⭐⭐⭐] [Effort: ⭐⭐⭐⭐]
   - Dedicated blocker resolver
   - Person whose job is removing blockers
   - Impact: 8 blockers → 0-2 in 2 weeks

3. REASSIGN WORK             [Impact: ⭐⭐⭐] [Effort: ⭐⭐]
   - Best troubleshooter on each blocker
   - Impact: 8 blockers resolved faster

Secondary: Reduce WIP (less WIP = fewer concurrent blockers)
```

#### 19. Team Allocation Imbalance (variance > 0.30)
```
Actionable: YES
Severity: MEDIUM (2/5)
Current State: Team members allocated very unevenly

Primary Recommendations:
1. REASSIGN WORK             [Impact: ⭐⭐⭐] [Effort: ⭐⭐]
   - Rebalance allocation
   - Move work from 100% to 60% person
   - Impact: variance 0.40 → 0.15

2. ADD RESOURCE              [Impact: ⭐⭐] [Effort: ⭐⭐⭐⭐]
   - Hire to cover gap
   - Only if needs skill match
   - Impact: May not help if allocation asymmetry is intentional

Note: May be INTENTIONAL (senior doing reviews, others coding)
      Verify before recommending change
```

---

### SCOPE RISK DRIVERS

#### 20. Major Estimate Inflation (inflation > 20%)
```
Actionable: YES
Severity: VERY_HIGH (4/5)
Current State: Items estimated 20%+ higher than original

Primary Recommendations:
1. DESCOPE WORK              [Impact: ⭐⭐⭐⭐⭐] [Effort: ⭐⭐⭐]
   - Remove inflated items
   - Keep only items with good estimates
   - Impact: Total effort down 15-20%

2. REASSIGN WORK             [Impact: ⭐⭐⭐] [Effort: ⭐⭐]
   - Have senior estimate inflated items
   - Impact: Reduces estimates 10-15%

3. SPLIT TASK                [Impact: ⭐⭐⭐⭐] [Effort: ⭐⭐⭐]
   - Break large inflated items
   - Clearer scope = better estimates
   - Impact: Clarifies true effort, may reveal padding

Investigation:
- Is inflation real (scope grew)? → Descope
- Or estimation error? → Reassign + Re-estimate
- Or risk padding? → Split tasks to clarify
```

#### 21. Moderate Estimate Inflation (inflation: 10-20%)
```
Actionable: YES
Severity: HIGH (3/5)
Current State: Items estimated 10-20% high

Primary Recommendations:
1. REASSIGN WORK             [Impact: ⭐⭐⭐] [Effort: ⭐⭐]
   - Re-estimate with domain expert
   - Impact: Reduces padding 5-10%

2. SPLIT TASK                [Impact: ⭐⭐⭐⭐] [Effort: ⭐⭐⭐]
   - Break down large items
   - Clarifies scope
   - Impact: Better estimates, may find padding

3. DESCOPE WORK              [Impact: ⭐⭐⭐⭐] [Effort: ⭐⭐]
   - If inflation justified
   - Remove lower-value inflated items
   - Impact: Total effort down 5-10%
```

#### 22. High Historical Spillover (carryover > 3.0)
```
Actionable: YES
Severity: VERY_HIGH (4/5)
Current State: Average 3+ items carry over each sprint (pattern)

Primary Recommendations:
1. REDUCE WIP                [Impact: ⭐⭐⭐] [Effort: ⭐]
   - Prevent overcommitment
   - WIP limit strictly enforced
   - Impact: Carryover 4.0 → 2.0 items/sprint

2. RESOLVE BLOCKER           [Impact: ⭐⭐⭐⭐] [Effort: ⭐⭐]
   - Blockers cause spillover
   - Resolve each = 1-2 fewer spillovers
   - Impact: Carryover 4.0 → 2.5 items/sprint

3. ADD RESOURCE              [Impact: ⭐⭐⭐⭐] [Effort: ⭐⭐⭐⭐]
   - Increase sprint capacity
   - Complete more items
   - Impact: Carryover 4.0 → 1.5 items/sprint

Root Cause:
- Blockers? → Resolve Blocker
- Overcommitment? → Reduce WIP
- Capacity? → Add Resource
```

#### 23. Moderate Spillover Pattern (carryover: 1.5-3.0)
```
Actionable: YES
Severity: HIGH (3/5)
Current State: 1.5-3.0 items carry over each sprint

Primary Recommendations:
1. REDUCE WIP                [Impact: ⭐⭐⭐] [Effort: ⭐]
   - Prevent overload
   - Impact: Carryover 2.5 → 1.5 items/sprint

2. RESOLVE BLOCKER           [Impact: ⭐⭐⭐⭐] [Effort: ⭐⭐]
   - Blocking items
   - Impact: Carryover 2.5 → 1.0 items/sprint

Secondary: Split Task (smaller tasks complete faster)
```

#### 24. High Blocked Item Rate (blocked > 15%)
```
Actionable: YES
Severity: VERY_HIGH (4/5)
Current State: 15%+ of items are currently blocked

Primary Recommendations:
1. RESOLVE BLOCKER           [Impact: ⭐⭐⭐⭐⭐] [Effort: ⭐⭐⭐]
   - MUST resolve blocking issues
   - Impact: 20% blocked → 5% blocked

2. ADD RESOURCE              [Impact: ⭐⭐⭐⭐] [Effort: ⭐⭐⭐⭐]
   - Dedicated unblocking resources
   - Impact: 20% blocked → 5% blocked faster

3. REASSIGN WORK             [Impact: ⭐⭐⭐] [Effort: ⭐⭐]
   - Put blocker resolution experts on them
   - Impact: 20% blocked → 10% blocked

Note: High blocked rate is CRITICAL—work can't progress
```

#### 25. High Not-Started Item Volume (not_started > 40%)
```
Actionable: YES
Severity: VERY_HIGH (4/5)
Current State: 40%+ of work items not yet started (late in project)

Primary Recommendations:
1. ADD RESOURCE              [Impact: ⭐⭐⭐⭐] [Effort: ⭐⭐⭐⭐]
   - Increase capacity to start more items
   - Impact: Can cover more not-started items

2. REDUCE WIP                [Impact: ⭐⭐⭐] [Effort: ⭐]
   - Complete current items faster
   - Start not-started items sooner
   - Impact: Reduce in-progress, start new items

3. SPLIT TASK                [Impact: ⭐⭐⭐⭐] [Effort: ⭐⭐⭐]
   - Break not-started items into smaller pieces
   - Smaller = easier to start and complete
   - Impact: More items starable

Investigation:
- Why not started yet? Blocked? → Resolve Blocker
- Capacity? → Add Resource
- Interdependencies? → Split Task / Reassign
```

---

## Composite Recommendation Scenarios

### Scenario A: Critical On-Time Probability (35%) + High Expected Delay (28 days)

**Current State:**
- On-time probability: 35% (75% will miss)
- Expected delay: 28 days
- Risk drivers: Critical Schedule Risk

**Recommended Sequence:**

**Phase 1 (Week 1) - Immediate Relief (Emergency)**
```
1. Resolve Blocker (Priority: Top 3 critical blockers)
   - Identify blockers affecting critical path
   - Resource: 1 dedicated person
   - Target: 5-7 day improvement
   
2. Reduce WIP
   - Implement strict WIP limit (max 3 items/person)
   - Impact: 2-3 day improvement (from focus)
   
Combined Impact after Week 1: 28d delay → 18-20d delay
```

**Phase 2 (Week 2-3) - Structural Changes**
```
1. Descope Work (20% scope reduction)
   - Identify lowest-value items
   - Negotiate with stakeholders
   - Impact: 8-10 day improvement
   
2. Split Task (parallelize long chain)
   - Identify serial critical path items
   - Break into 2-3 parallel workstreams
   - Impact: 5-7 day improvement

Combined Impact after Phase 2: 28d delay → 5-10d delay
```

**Phase 3 (Fallback) - Resource Addition**
```
If Phases 1-2 insufficient:
- Add temporary resource
- Target: Critical path tasks
- Impact: 3-5 additional days saved
- Total: 28d delay → 2-7d delay
```

**Result:**
- Descope (20%) + Resolve Blocker (3) + Split Task (CP chain)
  = 35% on-time prob → 80-90% on-time prob

---

### Scenario B: Long Critical Path Chain (12 items) + High Dependency Density (2.8 deps/item)

**Current State:**
- Critical path: 12 items in serial (zero parallelization)
- Dependency density: High (2.8 deps/item)
- Expected impact: Tight schedule

**Recommended Sequence:**

**Phase 1 - Decomposition**
```
1. Split Task (break 12-item chain)
   - Segment A: items 1-4 (parallel path 1)
   - Segment B: items 5-8 (parallel path 2)
   - Segment C: items 9-12 (parallel path 3)
   - Impact: 120h serial → 50h parallel (3-4x improvement)

2. Reassign Work
   - Path 1 → Best performer
   - Path 2 → Second best
   - Path 3 → Third best
   - Impact: Each path runs 30% faster

Combined Impact: Critical path time 15 days → 6-8 days
```

**Phase 2 - Dependency Reduction**
```
1. Reassign to specialists
   - Reduce handoff dependencies
   - Impact: dep_ratio 2.8 → 2.3

2. Resolve Blocker
   - Blocks on split tasks
   - Impact: Each path unblocked
```

**Result:**
- 12-item serial chain → 3 parallel streams
- Dependency density: 2.8 → 2.2
- Schedule impact: 28-day delay → 8-12 day delay

---

### Scenario C: Extreme Team Overload (95%) + High Active Blockers (8) + Velocity Degradation (-20%)

**Current State:**
- Utilization: 95% (no buffer)
- Active blockers: 8 items blocked
- Velocity trend: -20% last sprint (declining)
- Impact: Perfect storm

**Recommended Sequence:**

**Immediate (Days 1-2):**
```
1. Resolve Blocker (Top 3 blockers NOW)
   - Escalate if needed
   - Target: 2-3 day resolution
   - Impact: 8 blockers → 5 blockers, velocity recovers 5%

2. Reduce WIP (Emergency WIP limit)
   - Max 2 items per person
   - Impact: Velocity recovers 3% (from focus)
```

**Short-term (Week 1):**
```
1. ADD RESOURCE (MUST add person)
   - Dedicated blocker resolver
   - OR: Additional developer to take some load
   - Impact: Utilization 95% → 75%, blockers resolve faster

2. RESOLVE BLOCKER (remaining 5)
   - With additional resource support
   - Target: Complete by end of week
```

**Medium-term (Week 2+):**
```
1. Ongoing Reduce WIP
   - Maintain discipline
   - Impact: Prevents velocity from degrading further

2. Monitor Velocity Recovery
   - Should return to baseline once blockers clear
   - If not → investigate root cause (burnout? tech debt?)
```

**Result:**
- Utilization: 95% → 75% (add resource)
- Blockers: 8 → 0 (resolve blocker)
- Velocity: -20% → +5% recovery (2 sprints)

---

## Implementation Priority Matrix

```
Recommendation Type | Use When | Priority Level
──────────────────────────────────────────────────
RESOLVE BLOCKER      | ANY blocker present | 🔴 P0 (Always first)
DESCOPE WORK         | On-time prob < 50% | 🔴 P0 (Critical urgency)
ADD RESOURCE         | Utilization > 85%  | 🟠 P1 (High urgency)
SPLIT TASK           | CP chain > 8 items | 🟠 P1 (Medium-high)
REDUCE WIP           | Spillover > 3/sprint | 🟡 P2 (Medium)
REASSIGN WORK        | Imbalance/estimates| 🟡 P2 (Nice to have)
MOVE SPRINT          | All else fails     | 🔵 P3 (Last resort)
```

---

## Mapping Summary Table

| Risk Driver | Primary Recommendation | Secondary | Tertiary | Impact |
|---|---|---|---|---|
| Critical On-Time Prob | Descope | Add Resource | Resolve Blocker | ⭐⭐⭐⭐⭐ |
| Poor On-Time Prob | Descope | Add Resource | Resolve Blocker | ⭐⭐⭐⭐⭐ |
| Moderate On-Time Prob | Resolve Blocker | Reduce WIP | Split Task | ⭐⭐⭐⭐ |
| High Expected Delay | Descope | Add Resource | Split Task | ⭐⭐⭐⭐⭐ |
| Moderate Expected Delay | Resolve Blocker | Split Task | Reassign | ⭐⭐⭐⭐ |
| High Spillover | Add Resource | Reduce WIP | Resolve Blocker | ⭐⭐⭐⭐ |
| Moderate Spillover | Resolve Blocker | Reduce WIP | Split Task | ⭐⭐⭐ |
| Tight Critical Path | Split Task | Resolve Blocker | Reassign | ⭐⭐⭐⭐ |
| High Dep Density | Split Task | Reassign | Resolve Blocker | ⭐⭐⭐⭐ |
| Moderate Dep Density | Split Task | Reassign | - | ⭐⭐⭐ |
| Long CP Chain | Split Task | Reassign | Add Resource | ⭐⭐⭐⭐⭐ |
| Moderate CP Length | Resolve Blocker | Reduce WIP | Split Task | ⭐⭐⭐ |
| Dep Bottlenecks | Reassign | Add Resource | Resolve Blocker | ⭐⭐⭐ |
| Deep Blocker Cascade | Resolve Blocker | Add Resource | Reassign | ⭐⭐⭐⭐⭐ |
| Extreme Overload | Add Resource | Descope | Reduce WIP | ⭐⭐⭐⭐⭐ |
| High Overload | Add Resource | Reduce WIP | Resolve Blocker | ⭐⭐⭐⭐ |
| Velocity Degradation | Resolve Blocker | Reduce WIP | Add Resource | ⭐⭐⭐⭐ |
| High Blocker Count | Resolve Blocker | Add Resource | Reassign | ⭐⭐⭐⭐⭐ |
| Allocation Imbalance | Reassign | Add Resource | - | ⭐⭐ |
| Major Inflation | Descope | Reassign | Split Task | ⭐⭐⭐⭐ |
| Moderate Inflation | Reassign | Split Task | Descope | ⭐⭐⭐ |
| High Spillover Pattern | Reduce WIP | Resolve Blocker | Add Resource | ⭐⭐⭐ |
| Moderate Spillover Pattern | Reduce WIP | Resolve Blocker | - | ⭐⭐ |
| High Blocked Rate | Resolve Blocker | Add Resource | Reassign | ⭐⭐⭐⭐⭐ |
| High Not-Started Vol | Add Resource | Reduce WIP | Split Task | ⭐⭐⭐⭐ |

---

## Key Insights for Phase 3.4 Implementation

### 1. Resolve Blocker is PRIMARY Recommendation

**Appears in:** 12/25 drivers (48%)  
**Average Impact:** 15-25% delay reduction per blocker  
**Cost:** Low  
**Implementation:** Hours to days  

**Why:**
- Blockers are direct productivity killers
- One resolved blocker unblocks multiple downstream items (cascade effect)
- Visible impact on team morale
- No stakeholder negotiation needed

**Phase 3.4 Should:**
- Always check for blockers first
- Suggest top 3 critical blockers to resolve
- Show impact: "Resolve X blocker → +Y% on-time probability"

---

### 2. Descope Work is HIGH-IMPACT but HIGH-FRICTION

**Appears in:** 6/25 drivers (24%)  
**Average Impact:** 20-40% delay reduction (if 20% scope removed)  
**Cost:** Moderate (negotiation)  
**Implementation:** Days to weeks (stakeholder approval)  

**Why:**
- Mathematically guaranteed to reduce delay
- Fastest path to on-time delivery
- Requires stakeholder buy-in (difficult)

**Phase 3.4 Should:**
- Suggest ONLY if other options exhausted
- Provide impact calculations: "Remove 20% scope → on-time prob 35% → 85%"
- Suggest low-value items first
- Show 3-tier descope: 10%, 20%, 30% scenarios

---

### 3. Add Resource is SILVER BULLET but SLOW

**Appears in:** 10/25 drivers (40%)  
**Average Impact:** 15-30% delay reduction per resource  
**Cost:** High (hiring/reallocation)  
**Implementation:** 2-4 weeks (ramp-up time)  

**Why:**
- Directly increases capacity
- Addresses multiple drivers (utilization, spillover, not-started items)
- BUT: Too slow for immediate crisis

**Phase 3.4 Should:**
- Always suggest if utilization > 85%
- Calculate: "Add 1 resource → velocity +25% → delay drops X days"
- Estimate ramp-up time (new person slower first 1-2 sprints)
- Show realistic timeline: "Benefits visible in Sprint N+3"

---

### 4. Split Task Enables Parallelization

**Appears in:** 8/25 drivers (32%)  
**Average Impact:** 10-20% delay reduction (if 20-30% parallelizable)  
**Cost:** Medium (refactoring work)  
**Implementation:** 3-5 days (planning + replanning)  

**Why:**
- Converts serial → parallel work
- Unlocks critical path parallelization (biggest potential gains)
- Requires careful task boundary definition

**Phase 3.4 Should:**
- Suggest for long CP chains (>8 items)
- Show parallelization opportunity: "Convert 10h serial → 6h parallel"
- Recommend 2-3 parallel workstreams max (coordination overhead)

---

### 5. Reduce WIP is Continuous Improvement

**Appears in:** 7/25 drivers (28%)  
**Average Impact:** 8-12% improvement (varies)  
**Cost:** Low (cultural change)  
**Implementation:** Immediate (policy change)  

**Why:**
- No financial cost
- Reduces context switching overhead
- BUT: Requires sustained discipline

**Phase 3.4 Should:**
- Suggest as "foundational" recommendation
- Easy "quick win" alongside other tactics
- Impact: "WIP limit 5→3 items → spillover 20% → 10%"

---

### 6. Reassign Work is Fine-Tuning

**Appears in:** 8/25 drivers (32%)  
**Average Impact:** 5-15% improvement (varies)  
**Cost:** Low (zero financial)  
**Implementation:** Hours (decision + context switch)  

**Why:**
- Immediate effect
- Useful for estimate/balance issues
- Limited by team size

**Phase 3.4 Should:**
- Suggest after bigger moves
- Useful for "last 5-10% improvement"
- Show: "Reassign to senior → estimate 60% → 90% accuracy"

---

### 7. Move Sprint is LAST RESORT

**Appears in:** 3/25 drivers (12%)  
**Average Impact:** 0% (moves problem, doesn't solve)  
**Cost:** High (political)  
**Implementation:** Variable (stakeholder decision)  

**Why:**
- Doesn't reduce delay
- Acceptable only if timeline flexible
- Often used when all else fails

**Phase 3.4 Should:**
- Suggest ONLY if on-time prob < 20% AND:
  - No other options available
  - External deadline is flexible
  - OR: As fallback alongside other tactics
- Show: "Baseline: delay 28d, deadline June 30" → "New deadline: August 15"

---

## Recommendation Engine Architecture Implications

### Input Validation Layer
```
RiskResult → Check Drivers → Score Priority

IF Critical On-Time Prob (35%) AND High Blocker Count (8)
→ Recommend: [Resolve Blocker, Reduce WIP, Descope]

IF Long CP Chain (12) AND High Dep Density (2.8)
→ Recommend: [Split Task, Reassign, Parallelize]
```

### Recommendation Scoring
```
Each recommendation gets:
1. Impact Score (0-100): How much delay reduction?
2. Effort Score (0-100): Cost/difficulty of implementation
3. Time to Resolution (days/weeks): When will impact be visible?
4. Risk Score (0-100): Likelihood it will work

Engine ranks by: (Impact - Effort - Risk) / Time
Best recommendation = highest score
```

### Output Format for Phase 3.4
```
{
  "primary_recommendation": {
    "type": "Resolve Blocker",
    "target_blockers": ["B1", "B3", "B5"],  // Top 3 critical
    "expected_impact": "28d delay → 18d delay",
    "probability": 0.85,
    "time_to_resolution": "3-5 days",
    "effort": "Low",
    "dependencies": []
  },
  "secondary_recommendations": [
    {
      "type": "Descope Work",
      "scope_reduction": 0.20,
      "expected_impact": "28d delay → 8d delay",
      "items_to_descope": ["WI-045", "WI-067", "WI-089"],
      ...
    },
    ...
  ],
  "combination_scenario": {
    "sequence": ["Resolve Blocker (week 1)", "Descope (week 2)", "Split Task (parallel)"],
    "cumulative_impact": "28d delay → 3-5d delay",
    "on_time_probability": "35% → 85%"
  }
}
```

---

**Strategy Matrix Complete**

Ready for Phase 3.4 Recommendation Engine implementation.
