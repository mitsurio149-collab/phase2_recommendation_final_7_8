#!/usr/bin/env python3
"""
Test upload endpoint response.
"""

import sys
sys.path.insert(0, '/workspaces/hack_2026_step1/backend')

from app.parsers import WorkbookParser
from app.storage import store
from app.api.models import ProjectSummary, UploadResponse, ApiResponse
from app.domain.models import SprintStatus
import json

workbook_path = '/workspaces/hack_2026_step1/TIO2_Sprint_Intelligence_VALIDATED.xlsx'

print("=" * 80)
print("UPLOAD ENDPOINT RESPONSE SIMULATION")
print("=" * 80)

# Step 1: Parse
print("\n[STEP 1] Parsing workbook...")
parser = WorkbookParser(workbook_path)
project_state = parser.parse()
print(f"✓ Parsed successfully")

# Step 2: Store in session
print("\n[STEP 2] Storing in session...")
session_id = store.create_session(project_state)
print(f"✓ Stored with session_id: {session_id}")

# Step 3: Build upload response (like upload.py does)
print("\n[STEP 3] Building upload response...")

# Count completed sprints
completed_sprints = sum(
    1 for s in project_state.sprints
    if s.status == SprintStatus.COMPLETED
)

project_summary = ProjectSummary(
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

upload_response = UploadResponse(
    session_id=session_id,
    project_summary=project_summary,
    validation_warnings=[],
)

api_response = ApiResponse(
    success=True,
    message="Workbook uploaded and parsed successfully",
    data=upload_response.model_dump(),
)

# Step 4: Show response
print("\n[STEP 4] Response:")
response_dict = api_response.model_dump()

# Check key fields
summary = response_dict['data']['project_summary']
print(f"\n  Project Summary (in upload response):")
print(f"    - total_dependencies: {summary.get('total_dependencies')}")
print(f"    - total_blockers: {summary.get('total_blockers')}")
print(f"    - total_work_items: {summary.get('total_work_items')}")

# Step 5: Show full JSON
print(f"\n[STEP 5] Full response JSON:")
print(json.dumps(response_dict, indent=2, default=str))

print("\n" + "=" * 80)
