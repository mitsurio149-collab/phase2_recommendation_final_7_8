# Demo Flow Payloads

Live demo run captured on 2026-06-14 against the backend at `http://127.0.0.1:8000` using the validated workbook at `reference/TIO2_Sprint_Intelligence_VALIDATED.xlsx`.

## Flow Sequence

1. `POST /api/upload`
2. `GET /api/forecast`
3. `GET /api/risk`
4. `GET /api/recommendations`
5. `POST /api/scope-change`
6. `GET /api/forecast` again for the reforecast view

## Upload Payload

Request:

```bash
curl -X POST http://127.0.0.1:8000/api/upload \
  -F "file=@reference/TIO2_Sprint_Intelligence_VALIDATED.xlsx"
```

Response:

```json
{
  "success": true,
  "data": {
    "session_id": "479f471f",
    "project_summary": {
      "project_name": "TIO2 - Telematics Gateway ECU Modernization",
      "project_manager": "Suresh Iyer",
      "customer": "Daimler Truck",
      "start_date": "2025-01-20T00:00:00",
      "target_end_date": "2025-05-11T00:00:00",
      "total_sprints": 8,
      "total_work_items": 65,
      "total_resources": 8,
      "total_dependencies": 23,
      "total_blockers": 5,
      "completed_sprints": 3
    },
    "validation_warnings": []
  },
  "message": "Workbook uploaded and parsed successfully"
}
```

## Forecast Payload

Request:

```bash
GET /api/forecast?session_id=479f471f
```

Response highlights:

```json
{
  "forecast": {
    "target_end_date": "2025-05-11T00:00:00",
    "expected_finish_date": "2025-10-25T11:57:05.403742",
    "expected_delay_days": 167.0,
    "remaining_effort_hours": 1476.683076923077,
    "completion_percentage": 0.49368863955119213,
    "projected_velocity": 92.5,
    "on_track": false
  }
}
```

## Risk Payload

Request:

```bash
GET /api/risk?session_id=479f471f
```

Response highlights:

```json
{
  "risk_analysis": {
    "overall_risk_score": 47.23615801776531,
    "overall_risk_level": "HIGH",
    "schedule_risk": {
      "score": 72.40333333333334,
      "reasons": [
        "Expected delay 167.0 days",
        "34 predicted spillover items"
      ]
    },
    "resource_risk": {
      "score": 67.625,
      "reasons": ["Team utilization 92.6%"]
    },
    "scope_risk": {
      "score": 31.665497896213182,
      "reasons": [
        "Estimate inflation 14.2%",
        "Spillover pattern 2.2 items/sprint"
      ]
    }
  }
}
```

## Recommendations Payload

Request:

```bash
GET /api/recommendations?session_id=479f471f&top_n=3
```

Response highlights:

```json
{
  "recommendations": [
    {
      "recommendation_id": "REC-005",
      "type": "Descope Work",
      "action": "Descope work item WI-047",
      "target_ids": ["WI-047"],
      "reason": "WI-047 is not started, low priority, not on the critical path, and has 20.0h effort. Removing it reduces remaining scope."
    },
    {
      "recommendation_id": "REC-004",
      "type": "Descope Work",
      "action": "Descope work item WI-065",
      "target_ids": ["WI-065"],
      "reason": "WI-065 is not started, low priority, not on the critical path, and has 8.0h effort. Removing it reduces remaining scope."
    },
    {
      "recommendation_id": "REC-008",
      "type": "Critical Path Optimization",
      "action": "Optimize critical path items: WI-048, WI-056, WI-042",
      "target_ids": ["WI-048", "WI-056", "WI-042"]
    }
  ]
}
```

## Scope Change Payload

Work items used in the demo: `WI-001`, `WI-002`.

Request:

```bash
POST /api/scope-change?session_id=479f471f
{
  "item_ids": ["WI-001", "WI-002"],
  "reason": "Demo scope reduction"
}
```

Response highlights:

```json
{
  "descoped_item_ids": ["WI-001", "WI-002"],
  "changed_item_count": 2,
  "updated_remaining_effort_hours": 722.0,
  "forecast": {
    "expected_delay_days": 167.0,
    "remaining_effort_hours": 1476.683076923077
  },
  "risk_analysis": {
    "overall_risk_score": 47.364006545114535,
    "overall_risk_level": "HIGH"
  }
}
```

## Reforecast Payload

The reforecast screen should reuse the live forecast endpoint after scope change because there is no dedicated comparison endpoint in the backend yet.

Request:

```bash
GET /api/forecast?session_id=479f471f
```

Response highlights:

```json
{
  "forecast": {
    "expected_delay_days": 167.0,
    "remaining_effort_hours": 1476.683076923077,
    "on_track": false
  }
}
```

## Frontend Narrative Focus

The first frontend screens should answer three questions directly:

1. Why are we late?
2. What should we do?
3. What if we remove scope?

Recommended screen copy direction:

- `Judge narrative`: show the project is `HIGH` risk, 167 days late, with the biggest drivers coming from schedule, spillover, and resource overload.
- `Why are we late?`: lead with the expected delay, then expose the driver stack from the risk response.
- `What should we do?`: show the top recommendations, especially descope candidates and critical-path optimization.
- `What if we remove scope?`: compare before and after state, and call out when scope removal does not materially move the forecast so the demo stays honest.
