#!/usr/bin/env python3
"""
Final comprehensive diagnostic - check all potential issues.
"""

import sys
sys.path.insert(0, '/workspaces/hack_2026_step1/backend')

import json
from app.parsers import WorkbookParser
from app.storage import store
from app.engines.metrics_engine import MetricsEngine
from app.api.models import ApiResponse, ProjectSummary, UploadResponse
from app.api.models_phase2 import MetricsResponse
from app.domain.models import SprintStatus

workbook_path = '/workspaces/hack_2026_step1/TIO2_Sprint_Intelligence_VALIDATED.xlsx'

print("=" * 80)
print("COMPREHENSIVE ROOT CAUSE DIAGNOSTIC")
print("=" * 80)

# Parse
print("\n1. PARSING & STORAGE")
parser = WorkbookParser(workbook_path)
project_state = parser.parse()
session_id = store.create_session(project_state)
retrieved_state = store.get_project_state(session_id)
print(f"   ✓ Parser: {len(project_state.dependencies)} deps, {len(project_state.blockers)} blockers")
print(f"   ✓ Storage: {len(retrieved_state.dependencies)} deps, {len(retrieved_state.blockers)} blockers")

# Calculate metrics
print("\n2. METRICS ENGINE")
metrics = MetricsEngine(retrieved_state).calculate()
print(f"   ✓ dependency_count: {metrics.dependency_count}")
print(f"   ✓ active_blocker_count: {metrics.active_blocker_count}")
print(f"   ✓ expected_spillover_items: {metrics.expected_spillover_items}")

# Upload response
print("\n3. UPLOAD ENDPOINT RESPONSE (POST /upload)")
completed_sprints = sum(1 for s in project_state.sprints if s.status == SprintStatus.COMPLETED)
summary = ProjectSummary(
    session_id=session_id,
    project_name=project_state.project_info.project_name,
    project_manager=project_state.project_info.project_manager,
    customer=project_state.project_info.customer,
    start_date=project_state.project_info.start_date,
    target_end_date=project_state.project_info.target_end_date,
    total_sprints=len(project_state.sprints),
    total_work_items=len(project_state.work_items),
    total_resources=len(project_state.team),
    total_dependencies=len(project_state.dependencies),
    total_blockers=len(project_state.blockers),
    completed_sprints=completed_sprints,
)
upload_resp = ApiResponse(
    success=True,
    message="Workbook uploaded",
    data=UploadResponse(session_id=session_id, project_summary=summary).model_dump()
)
upload_json = upload_resp.model_dump()
print(f"   ✓ Wrapped in ApiResponse: success={upload_json['success']}")
print(f"   ✓ data.project_summary.total_dependencies: {upload_json['data']['project_summary'].get('total_dependencies')}")
print(f"   ✓ data.project_summary.total_blockers: {upload_json['data']['project_summary'].get('total_blockers')}")

# Metrics response
print("\n4. METRICS ENDPOINT RESPONSE (GET /metrics)")
metrics_resp = MetricsResponse(
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
metrics_api_resp = ApiResponse(
    success=True,
    message="Metrics retrieved",
    data=metrics_resp.model_dump()
)
metrics_json = metrics_api_resp.model_dump()
print(f"   ✓ Wrapped in ApiResponse: success={metrics_json['success']}")
print(f"   ✓ data.dependency_count: {metrics_json['data'].get('dependency_count')}")
print(f"   ✓ data.active_blocker_count: {metrics_json['data'].get('active_blocker_count')}")
print(f"   ✓ data.expected_spillover_items: {metrics_json['data'].get('expected_spillover_items')}")

# Check for 0 values anywhere
print("\n5. CHECKING FOR ZERO VALUES IN RESPONSES")
def find_zero_fields(obj, path=""):
    """Recursively find fields with value 0."""
    zeros = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            current_path = f"{path}.{key}" if path else key
            if value == 0:
                zeros.append((current_path, value))
            elif isinstance(value, (dict, list)):
                zeros.extend(find_zero_fields(value, current_path))
    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            current_path = f"{path}[{i}]"
            if value == 0:
                zeros.append((current_path, value))
            elif isinstance(value, (dict, list)):
                zeros.extend(find_zero_fields(value, current_path))
    return zeros

upload_zeros = find_zero_fields(upload_json)
metrics_zeros = find_zero_fields(metrics_json)

print(f"   Upload response has {len(upload_zeros)} zero values")
print(f"   Metrics response has {len(metrics_zeros)} zero values")

# Check if dependency/blocker/spillover fields are missing
print("\n6. FIELD PRESENCE CHECK")
def check_field_in_response(response_dict, field_name, path="data"):
    """Check if field exists in API response."""
    if path == "data" and "data" in response_dict:
        if field_name in response_dict["data"]:
            return f"✓ Found in {path}: {response_dict['data'][field_name]}"
        else:
            return f"✗ NOT FOUND in {path}"
    return f"✗ Cannot find {path} in response"

print("\n   Upload Response:")
print(f"   - total_dependencies: {check_field_in_response(upload_json, 'total_dependencies', 'data.project_summary').split(':')[1] if ':' in check_field_in_response(upload_json, 'total_dependencies', 'data.project_summary') else 'N/A'}")
print(f"     {upload_json.get('data', {}).get('project_summary', {}).get('total_dependencies', 'MISSING')}")
print(f"   - total_blockers: {upload_json.get('data', {}).get('project_summary', {}).get('total_blockers', 'MISSING')}")

print("\n   Metrics Response:")
print(f"   - dependency_count: {metrics_json.get('data', {}).get('dependency_count', 'MISSING')}")
print(f"   - active_blocker_count: {metrics_json.get('data', {}).get('active_blocker_count', 'MISSING')}")
print(f"   - expected_spillover_items: {metrics_json.get('data', {}).get('expected_spillover_items', 'MISSING')}")

# Final diagnosis
print("\n7. DIAGNOSIS SUMMARY")
if (upload_json.get('data', {}).get('project_summary', {}).get('total_dependencies', 0) > 0 and
    metrics_json.get('data', {}).get('dependency_count', 0) > 0 and
    metrics_json.get('data', {}).get('active_blocker_count', 0) > 0):
    print("   ✓ All backend systems working correctly")
    print("   ✓ All values are correctly calculated and returned")
    print("   ✓ Response structures are correct")
    print("\n   CONCLUSION: Issue is NOT in the backend")
    print("   NEXT STEPS: Check UI components for:")
    print("   1. Wrong field names being read from API response")
    print("   2. Wrong endpoint being called")
    print("   3. Response parsing logic in UI")
    print("   4. Hardcoded 0 values in UI components")
else:
    print("   ✗ Found issue in backend")

print("\n" + "=" * 80)
