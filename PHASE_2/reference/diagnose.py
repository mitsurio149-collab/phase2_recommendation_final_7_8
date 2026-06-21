#!/usr/bin/env python3
"""
Diagnostic script to trace data flow through parsing pipeline.
"""

import sys
sys.path.insert(0, '/workspaces/hack_2026_step1/backend')

from app.parsers import WorkbookParser
from app.engines.metrics_engine import MetricsEngine
from app.storage import SessionStore

# File path
workbook_path = '/workspaces/hack_2026_step1/TIO2_Sprint_Intelligence_VALIDATED.xlsx'

print("=" * 80)
print("SPRINT WHISPERER DIAGNOSTICS")
print("=" * 80)

# Step 1: Parse workbook
print("\n[STEP 1] Parsing workbook...")
try:
    parser = WorkbookParser(workbook_path)
    project_state = parser.parse()
    print("✓ Parsing successful")
except Exception as e:
    print(f"✗ Parsing failed: {e}")
    sys.exit(1)

# Step 2: Check raw parsed data
print("\n[STEP 2] Raw parsed data:")
print(f"  - Work Items:     {len(project_state.work_items)}")
print(f"  - Dependencies:   {len(project_state.dependencies)}")
print(f"  - Blockers:       {len(project_state.blockers)}")
print(f"  - Sprint Actuals: {len(project_state.actuals)}")

# Step 3: Check if lists are populated
print("\n[STEP 3] Data presence check:")

if project_state.dependencies:
    print(f"  ✓ Dependencies populated:")
    for dep in project_state.dependencies[:3]:
        print(f"    - {dep.dependency_id}: {dep.predecessor_item_id} -> {dep.successor_item_id}")
    if len(project_state.dependencies) > 3:
        print(f"    ... and {len(project_state.dependencies) - 3} more")
else:
    print(f"  ✗ Dependencies empty - ISSUE HERE!")

if project_state.blockers:
    print(f"  ✓ Blockers populated:")
    for blocker in project_state.blockers[:3]:
        print(f"    - {blocker.blocker_id}: {blocker.description} (status={blocker.status})")
    if len(project_state.blockers) > 3:
        print(f"    ... and {len(project_state.blockers) - 3} more")
else:
    print(f"  ✗ Blockers empty - ISSUE HERE!")

if project_state.actuals:
    print(f"  ✓ Sprint Actuals populated:")
    for actual in project_state.actuals[:3]:
        print(f"    - Sprint {actual.sprint_number}: {actual.carryover_count} carryover items")
    if len(project_state.actuals) > 3:
        print(f"    ... and {len(project_state.actuals) - 3} more")
else:
    print(f"  ✗ Sprint Actuals empty - may not have historical data")

# Step 4: Calculate metrics
print("\n[STEP 4] Calculating metrics...")
try:
    metrics_engine = MetricsEngine(project_state)
    metrics = metrics_engine.calculate()
    print("✓ Metrics calculated")
except Exception as e:
    print(f"✗ Metrics calculation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 5: Check metrics output
print("\n[STEP 5] Metrics results:")
print(f"  - Dependency Count:         {metrics.dependency_count}")
print(f"  - Active Blocker Count:     {metrics.active_blocker_count}")
print(f"  - Expected Spillover Items: {metrics.expected_spillover_items}")

# Step 6: Root cause analysis
print("\n[STEP 6] Root Cause Analysis:")

if len(project_state.dependencies) == 0 and metrics.dependency_count == 0:
    print("  ⚠ Dependencies: Data is missing from PARSING stage")
    print("    - Check if 'Dependencies' sheet exists in workbook")
    print("    - Check if data starts at row 3 (after title and headers)")
    
elif len(project_state.dependencies) > 0 and metrics.dependency_count == 0:
    print("  ⚠ Dependencies: Data LOST between ProjectState and Metrics")
    print("    - Check if ProjectState is being modified")
    print("    - Check if MetricsEngine is using wrong field")
    
elif len(project_state.dependencies) > 0 and metrics.dependency_count > 0:
    print("  ✓ Dependencies: Data is correct")
else:
    print("  ⚠ Dependencies: Unexpected state")

if len(project_state.blockers) == 0 and metrics.active_blocker_count == 0:
    print("  ⚠ Blockers: Data is missing from PARSING stage")
    print("    - Check if 'Blockers' sheet exists in workbook")
    print("    - Check if data starts at row 3 (after title and headers)")
    
elif len(project_state.blockers) > 0 and metrics.active_blocker_count == 0:
    print("  ⚠ Blockers: Data LOST between ProjectState and Metrics")
    print("    - Check if all blockers have 'actual_resolution_date' set (which would make them inactive)")
    print("    - Current blocker statuses:")
    for blocker in project_state.blockers[:3]:
        print(f"      - {blocker.blocker_id}: status={blocker.status}, actual_resolution_date={blocker.actual_resolution_date}")
    
elif len(project_state.blockers) > 0 and metrics.active_blocker_count > 0:
    print("  ✓ Blockers: Data is correct")
else:
    print("  ⚠ Blockers: Unexpected state")

# Print spillover calculation details
print("\n[STEP 7] Spillover Calculation Details:")
print(f"  - Total Sprint Actuals: {len(project_state.actuals)}")
if project_state.actuals:
    carryover_totals = sum(a.carryover_count for a in project_state.actuals)
    print(f"  - Sum of carryover_count: {carryover_totals}")
    print(f"  - Calculated spillover: {metrics.expected_spillover_items}")
    if carryover_totals != metrics.expected_spillover_items:
        print("  ⚠ Spillover calculation mismatch!")

print("\n" + "=" * 80)
