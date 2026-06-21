#!/usr/bin/env python3
"""
Test what the UI receives from API endpoints.
"""

import sys
sys.path.insert(0, '/workspaces/hack_2026_step1/backend')

from app.parsers import WorkbookParser
from app.storage import store
from app.engines.metrics_engine import MetricsEngine
from app.api.models_phase2 import MetricsResponse
import json

workbook_path = '/workspaces/hack_2026_step1/TIO2_Sprint_Intelligence_VALIDATED.xlsx'

print("=" * 80)
print("SIMULATING API RESPONSES")
print("=" * 80)

# Step 1: Parse
print("\n[STEP 1] Parsing workbook...")
parser = WorkbookParser(workbook_path)
project_state = parser.parse()
print(f"✓ Parsed: {len(project_state.dependencies)} deps, {len(project_state.blockers)} blockers")

# Step 2: Store in session (simulating upload endpoint)
print("\n[STEP 2] Storing in session...")
session_id = store.create_session(project_state)
print(f"✓ Session ID: {session_id}")

# Step 3: Retrieve from session (simulating what an API endpoint would do)
print("\n[STEP 3] Retrieving from session...")
retrieved_state = store.get_project_state(session_id)
print(f"✓ Retrieved: {len(retrieved_state.dependencies)} deps, {len(retrieved_state.blockers)} blockers")

# Step 4: Calculate metrics (like /metrics endpoint)
print("\n[STEP 4] Calculating metrics...")
metrics_engine = MetricsEngine(retrieved_state)
metrics = metrics_engine.calculate()

# Step 5: Build MetricsResponse (like phase2.py does)
print("\n[STEP 5] Building MetricsResponse...")
response = MetricsResponse(
    session_id=session_id,
    project_name=retrieved_state.project_info.project_name,
    total_items=metrics.total_items,
    completed_items=metrics.completed_items,
    in_progress_items=metrics.in_progress_items,
    blocked_items=metrics.blocked_items,
    completion_pct=metrics.completion_pct,
    total_effort_hours=metrics.total_effort_hours,
    remaining_effort_hours=metrics.remaining_effort_hours,
    completed_effort_hours=metrics.completed_effort_hours,
    planned_total_velocity=metrics.planned_total_velocity,
    actual_avg_velocity=metrics.actual_avg_velocity,
    velocity_variance=metrics.velocity_variance,
    team_size=metrics.team_size,
    avg_allocation_pct=metrics.avg_allocation_pct,
    avg_availability_pct=metrics.avg_availability_pct,
    underutilized_count=metrics.underutilized_resource_count,
    active_blocker_count=metrics.active_blocker_count,
    blocker_velocity_impact=metrics.estimated_blocker_velocity_impact,
    current_sprint_number=metrics.current_sprint_number,
    completed_sprints=metrics.completed_sprints,
    dependency_count=metrics.dependency_count,
    expected_spillover_items=int(metrics.expected_spillover_items),
)

# Step 6: Show as JSON (what the UI would see)
print("\n[STEP 6] JSON response (what UI receives):")
response_dict = response.model_dump()

# Pretty print the relevant fields
print(f"\n  Key metrics:")
print(f"    - dependency_count: {response_dict.get('dependency_count')}")
print(f"    - active_blocker_count: {response_dict.get('active_blocker_count')}")
print(f"    - expected_spillover_items: {response_dict.get('expected_spillover_items')}")

# Show the full JSON
print(f"\n  Full response JSON structure:")
print(json.dumps(response_dict, indent=2, default=str))

# Step 7: Check if fields are missing or 0
print("\n[STEP 7] Field value check:")
if response_dict.get('dependency_count') == 0:
    print("  ⚠ dependency_count is 0!")
else:
    print(f"  ✓ dependency_count = {response_dict.get('dependency_count')}")

if response_dict.get('active_blocker_count') == 0:
    print("  ⚠ active_blocker_count is 0!")
else:
    print(f"  ✓ active_blocker_count = {response_dict.get('active_blocker_count')}")

if response_dict.get('expected_spillover_items') == 0:
    print("  ⚠ expected_spillover_items is 0!")
else:
    print(f"  ✓ expected_spillover_items = {response_dict.get('expected_spillover_items')}")

print("\n" + "=" * 80)
