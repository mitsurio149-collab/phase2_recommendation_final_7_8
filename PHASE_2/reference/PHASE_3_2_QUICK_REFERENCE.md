# Phase 3.2 Monte Carlo Quick Reference

## What is Monte Carlo?

Monte Carlo simulation generates many possible project outcomes by introducing realistic randomness:

```
Project State:
  Remaining: 100 hours
  Velocity: 160 h/sprint (± 15% variation)
  Blockers: 10% impact (0-100% randomly applied)
  Spillover: May/may not happen

Simulation 1: Sim Result → Finish 2026-07-05
Simulation 2: Sim Result → Finish 2026-06-28 (lucky: low variation, no spillover)
Simulation 3: Sim Result → Finish 2026-07-18 (unlucky: high variation, full spillover)
...10,000 simulations...

Result:
  Best case (p10):  2026-06-25  (10% of sims)
  Likely (p50):     2026-07-03  (50% of sims, median)
  Worst case (p90): 2026-07-12  (90% of sims)
  
  On-time probability: 35% (only 3,500 of 10,000 sims ≤ 2026-06-30)
```

**Key Principle:** Target date is NEVER changed. It's a fixed business commitment.

---

## Using the API

### Basic Request
```bash
# Simple request with defaults
curl "http://localhost:8000/api/monte-carlo?session_id=proj-123"
```

### With Custom Parameters
```bash
# Specify number of simulations for speed/accuracy trade-off
curl "http://localhost:8000/api/monte-carlo?session_id=proj-123&simulations=50000"

# Use seed for reproducible results (same seed = same results)
curl "http://localhost:8000/api/monte-carlo?session_id=proj-123&seed=12345"
```

### Response Fields

```json
{
  "on_time_probability": 0.35,           // 35% chance of on-time delivery
  "on_time_risk_level": "HIGH",          // Risk classification
  
  // Confidence intervals (80% of outcomes fall between p25 and p75)
  "statistics": {
    "percentile_10": "2026-06-25",       // 10% finish before this
    "percentile_25": "2026-06-28",       // 25% finish before this
    "percentile_50": "2026-07-03",       // 50% (median, most likely)
    "percentile_75": "2026-07-08",       // 75% finish before this
    "percentile_90": "2026-07-12"        // 90% finish before this
  },
  
  // Summary scenarios
  "best_case_finish_date": "2026-06-25", // p10
  "most_likely_finish_date": "2026-07-03", // p50
  "worst_case_finish_date": "2026-07-12",  // p90
  
  "target_end_date": "2026-06-30",       // CONSTANT (never changes)
  "simulations_on_time": 3500,           // # sims finishing ≤ target
  "simulations_late": 6500,              // # sims finishing > target
}
```

---

## Risk Level Interpretation

| Risk Level | On-Time Probability | Action |
|-----------|-------------------|--------|
| **LOW** | >80% | ✅ Monitor (likely to deliver) |
| **MEDIUM** | 60-79% | ⚠️ Review plan & watch closely |
| **HIGH** | 40-59% | 🔴 Escalate (serious risk) |
| **CRITICAL** | <40% | 🚨 Immediate action needed |

---

## Variability Parameters

Control how much randomness affects outcomes:

```python
# Default (realistic)
engine = MonteCarloEngine(
    simulation_count=10000,
    velocity_std_dev_pct=0.15,        # ±15% velocity variation
    remaining_work_std_dev_pct=0.10   # ±10% work variation
)

# Conservative (wide range for worst-case planning)
engine = MonteCarloEngine(
    simulation_count=10000,
    velocity_std_dev_pct=0.30,        # ±30% velocity variation
    remaining_work_std_dev_pct=0.25   # ±25% work variation
)

# Optimistic (narrow range for best-case)
engine = MonteCarloEngine(
    simulation_count=10000,
    velocity_std_dev_pct=0.05,        # ±5% velocity variation
    remaining_work_std_dev_pct=0.03   # ±3% work variation
)
```

---

## Seed for Reproducibility

```python
# Same seed = same results (useful for testing/debugging)
engine1 = MonteCarloEngine(..., seed=42)
result1 = engine1.calculate()

engine2 = MonteCarloEngine(..., seed=42)
result2 = engine2.calculate()

# result1 and result2 are identical
```

---

## Interpretation Examples

### Example 1: LOW Risk (>80% on-time)

```
on_time_probability: 0.92
on_time_risk_level: LOW

Best case:      2026-06-15
Most likely:    2026-06-20
Worst case:     2026-06-28
Target:         2026-06-30  ✅ Very likely to meet

Recommended action: Continue monitoring, low escalation risk
```

### Example 2: HIGH Risk (40-59% on-time)

```
on_time_probability: 0.45
on_time_risk_level: HIGH

Best case:      2026-06-25
Most likely:    2026-07-05
Worst case:     2026-07-20
Target:         2026-06-30  ⚠️ Only 45% chance to meet

Recommended action: Escalate, review scope, plan contingencies
```

### Example 3: CRITICAL Risk (<40% on-time)

```
on_time_probability: 0.15
on_time_risk_level: CRITICAL

Best case:      2026-07-10
Most likely:    2026-07-25
Worst case:     2026-08-15
Target:         2026-06-30  🚨 Only 15% chance to meet

Recommended action: Immediate escalation, reduce scope, or change deadline
```

---

## Common Queries

### "What's the best/worst case?"
Use `best_case_finish_date` and `worst_case_finish_date`.

### "What will most likely happen?"
Use `most_likely_finish_date` (the p50 median).

### "What range covers 80% of outcomes?"
Use percentiles: 80% of outcomes fall between `p10` and `p90`.

### "What's the probability of hitting the deadline?"
Use `on_time_probability` (as percentage).

### "How do I classify the risk?"
Use `on_time_risk_level` (LOW/MEDIUM/HIGH/CRITICAL).

### "Can I get the same results again?"
Yes, use the same `seed` parameter.

---

## Integration Tips

### Dashboard
```python
# Show risk indicator with color coding
color_map = {
    "LOW": "green",
    "MEDIUM": "yellow",
    "HIGH": "orange",
    "CRITICAL": "red"
}

dashboard.display(
    title=f"On-Time Probability: {mc_result.on_time_probability:.0%}",
    color=color_map[mc_result.on_time_risk_level]
)
```

### Alerts
```python
if mc_result.on_time_risk_level in ["HIGH", "CRITICAL"]:
    send_slack_alert(
        f"🚨 {mc_result.project_name} at risk: "
        f"{mc_result.on_time_probability:.0%} probability of on-time delivery"
    )
```

### Reports
```python
print(f"Target:     {mc_result.target_end_date}")
print(f"Best case:  {mc_result.best_case_finish_date}")
print(f"Most likely: {mc_result.most_likely_finish_date}")
print(f"Worst case: {mc_result.worst_case_finish_date}")
print(f"Risk level: {mc_result.on_time_risk_level}")
```

---

## Comparison: Deterministic vs. Probabilistic

| Aspect | Phase 3.1 (Deterministic) | Phase 3.2 (Monte Carlo) |
|--------|--------------------------|----------------------|
| **Output** | Single finish date | Distribution of dates |
| **Use Case** | Quick estimate | Risk assessment |
| **Example** | "July 5" | "35% chance by June 30" |
| **Confidence** | Point estimate | Confidence intervals |
| **Risk** | Not quantified | Probability-based |
| **Decision** | "On track?" | "How much risk?" |

**Use both:** Phase 3.1 for quick forecasts, Phase 3.2 for risk decisions.

---

## Technical Details

- **Algorithm:** Monte Carlo simulation with normal distribution for velocity/work
- **Randomness:** Velocity ±15%, remaining work ±10%, blockers 0-100%, spillover 0-100%
- **Percentiles:** Calculated from sorted simulation results
- **On-time probability:** (# simulations ≤ target_date) / total_simulations
- **Performance:** 10,000 simulations ≈ 400ms; configurable for speed/accuracy
- **Reproducibility:** Same seed produces identical results
- **Target Date:** NEVER modified (constant business commitment)

---

## FAQ

**Q: Why does my result change each time I call it?**
A: Without a seed, random sampling produces different results. Use `seed` parameter for reproducibility.

**Q: Should I trust the worst case date?**
A: Worst case (p90) means 90% of outcomes are better. It's pessimistic but realistic for planning.

**Q: What if on-time probability is 0%?**
A: All simulations show late delivery. Consider scope reduction or deadline extension.

**Q: Can I use different variability parameters?**
A: Yes, but defaults (±15% velocity, ±10% work) are empirically validated.

**Q: How many simulations do I need?**
A: 10,000 is standard. Use 1,000 for quick estimates, 50,000 for critical decisions.
