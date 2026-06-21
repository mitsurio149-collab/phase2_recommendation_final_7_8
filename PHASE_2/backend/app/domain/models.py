"""
Sprint Whisperer Domain Models

Pydantic v2 models representing the core domain objects.
These map directly to the workbook structure.
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List
from datetime import datetime, date
from enum import Enum


# ──────────────────────────────────────────────────────────────────────────────
# ENUMS (Domain Value Types)
# ──────────────────────────────────────────────────────────────────────────────


class SkillLevel(str, Enum):
    """Team member skill level."""
    JUNIOR = "Junior"
    INTERMEDIATE = "Intermediate"
    MID = "Mid"
    SENIOR = "Senior"
    ADVANCED = "Advanced"
    EXPERT = "Expert"


class WorkItemType(str, Enum):
    """Work item type classification."""
    FEATURE = "Feature"
    STORY = "Story"
    TASK = "Task"
    BUG = "Bug"
    SPIKE = "Spike"
    DEFECT = "Defect"


class Priority(str, Enum):
    """Work item priority level."""
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class WorkItemStatus(str, Enum):
    """Status of a work item."""
    NOT_STARTED = "Not Started"
    IN_PROGRESS = "In Progress"
    DONE = "Done"
    COMPLETED = "Completed"
    BLOCKED = "Blocked"
    SPILLOVER = "Spillover"


class SprintStatus(str, Enum):
    """Sprint execution status."""
    NOT_STARTED = "Not Started"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"


class BlockerSeverity(str, Enum):
    """Blocker severity level."""
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class BlockerCategory(str, Enum):
    VENDOR = "Vendor"
    HARDWARE = "Hardware"
    SPECIFICATION = "Specification"
    RESOURCE = "Resource"
    ENVIRONMENT = "Environment"
    SECURITY = "Security"
    COMPLIANCE = "Compliance"
    LAB_ISSUE = "Lab Issue"
    HARDWARE_PROCUREMENT = "Hardware / Procurement"
    EXTERNAL_TEAM_DEPENDENCY = "External Team Dependency"
    AWAITING_VALIDATION = "Awaiting Validation"
    TOOL_ISSUE = "Tool Issue"
    LICENSE_UNAVAILABLE = "License Unavailable"
    PEOPLE_DEPENDENCY = "People Dependency"
    APPROVAL_PENDING = "Approval Pending"
    OTHER = "Other"


class BlockerStatus(str, Enum):
    """Blocker resolution status."""
    OPEN = "Open"
    RESOLVED = "Resolved"


class DependencyType(str, Enum):
    """Type of task dependency."""
    FINISH_TO_START = "Finish-To-Start"
    START_TO_START = "Start-To-Start"


# ──────────────────────────────────────────────────────────────────────────────
# DOMAIN MODELS
# ──────────────────────────────────────────────────────────────────────────────


class ProjectInfo(BaseModel):
    """Project metadata and schedule information."""
    
    project_name: str = Field(..., min_length=1, description="Project name")
    sponsor: str = Field(..., description="Project sponsor name")
    business_unit: str = Field(..., description="Business unit")
    project_manager: str = Field(..., description="Project manager name")
    start_date: datetime = Field(..., description="Project start date")
    release_date: Optional[datetime] = Field(None, description="Optional project release date")
    target_end_date: datetime = Field(..., description="Target completion date")
    sprint_duration_days: int = Field(
        ..., ge=1, le=30, description="Length of each sprint in days"
    )
    methodology: str = Field(..., description="Development methodology (e.g., Agile Scrum)")
    customer: str = Field(..., description="Customer organization name")
    status: str = Field(..., description="Project status (Active, On Hold, Completed)")
    
    @field_validator("target_end_date")
    def validate_end_after_start(cls, v: datetime, info):
        """Target end date must be after start date."""
        if "start_date" in info.data:
            if v <= info.data["start_date"]:
                raise ValueError("Target end date must be after start date")
        return v

    @field_validator("release_date")
    def validate_release_date(cls, v: Optional[datetime], info):
        """Release date, when present, must sit between start and target dates."""
        if v is None:
            return v

        start_date = info.data.get("start_date")

        if start_date and v < start_date:
            raise ValueError("Release date must be on or after start date")
        return v

    @model_validator(mode="after")
    def validate_release_within_schedule(self):
        """Release date, when present, must sit between start and target dates."""
        if self.release_date is not None and self.release_date > self.target_end_date:
            raise ValueError("Release date must be on or before target end date")
        return self

    def forecast_anchor_date(self) -> datetime:
        """Return the preferred date anchor for forecast calculations."""
        return self.start_date or self.release_date or self.target_end_date or datetime.utcnow()


class Resource(BaseModel):
    """Team member with skills and availability."""
    
    resource_id: str = Field(..., description="Unique resource identifier (derived from name)")
    name: str = Field(..., description="Resource full name")
    role: str = Field(..., description="Job role/title")
    primary_skill: str = Field(..., description="Primary technical skill")
    secondary_skill: Optional[str] = Field(None, description="Secondary technical skill")
    skill_level: SkillLevel = Field(..., description="Skill proficiency level")
    allocation_pct: float = Field(
        ..., ge=0.0, le=1.0, description="Allocation percentage (0.0-1.0)"
    )
    availability_pct: float = Field(
        ..., ge=0.0, le=1.0, description="Availability percentage (0.0-1.0)"
    )
    daily_capacity_hrs: float = Field(
        default=8.0, ge=0.0, le=24.0, description="Daily work capacity in hours"
    )
    notes: Optional[str] = Field(None, description="Additional notes about resource")


class Sprint(BaseModel):
    """Sprint schedule and planning information."""
    
    sprint_id: str = Field(..., description="Unique sprint identifier (e.g., SPR-1)")
    sprint_name: str = Field(..., description="Sprint name (e.g., Sprint 1)")
    sprint_number: int = Field(..., ge=1, description="Sequential sprint number")
    start_date: datetime = Field(..., description="Sprint start date")
    end_date: datetime = Field(..., description="Sprint end date")
    working_days: int = Field(..., ge=1, le=31, description="Working days in sprint")
    sprint_goal: str = Field(..., description="Sprint goal/theme")
    status: SprintStatus = Field(..., description="Current sprint status")
    planned_velocity_hrs: float = Field(..., ge=0, description="Planned velocity in hours")
    carryover_count: int = Field(default=0, ge=0, description="Items carried from previous sprint")
    
    @field_validator("end_date")
    def validate_end_after_start(cls, v: datetime, info):
        """End date must be after start date."""
        if "start_date" in info.data:
            if v <= info.data["start_date"]:
                raise ValueError("Sprint end date must be after start date")
        return v


class WorkItem(BaseModel):
    """Individual work item (task, story, feature)."""
    
    item_id: str = Field(..., description="Unique work item identifier (e.g., WI-001)")
    title: str = Field(..., min_length=1, description="Work item title")
    work_type: WorkItemType = Field(..., description="Type of work (Feature, Story, Task, Bug)")
    assigned_sprint: str = Field(..., description="Sprint ID where item is assigned")
    original_sprint: Optional[str] = Field(None, description="Sprint where item was originally planned")
    assigned_resource: Optional[str] = Field(None, description="Resource ID of assignee")
    required_skill: str = Field(..., description="Primary skill required")
    priority: Priority = Field(..., description="Priority level")
    estimated_effort_hrs: float = Field(..., gt=0, description="Estimated effort in hours")
    current_estimate_hrs: float = Field(..., gt=0, description="Current estimate in hours")
    actual_effort_hrs: float = Field(default=0.0, ge=0, description="Actual hours spent")
    remaining_effort_hrs: float = Field(default=0.0, ge=0, description="Remaining hours")
    progress_pct: float = Field(default=0.0, ge=0.0, le=1.0, description="Progress percentage (0.0-1.0)")
    status: WorkItemStatus = Field(..., description="Current work item status")
    is_scope_changed: bool = Field(default=False, description="Whether scope has changed")
    scope_change_reason: Optional[str] = Field(None, description="Reason for scope change")


class Dependency(BaseModel):
    """Task dependency (relationships between work items)."""
    
    dependency_id: str = Field(..., description="Unique dependency identifier")
    predecessor_item_id: str = Field(..., description="Predecessor work item ID")
    successor_item_id: str = Field(..., description="Successor work item ID")
    dependency_type: DependencyType = Field(..., description="Type of dependency")
    is_on_critical_path: bool = Field(default=False, description="Whether on critical path")
    lag_days: int = Field(default=0, ge=0, description="Lag/lead time in days")
    notes: Optional[str] = Field(None, description="Dependency notes")


class Blocker(BaseModel):
    """Issue blocking task completion."""
    
    blocker_id: str = Field(..., description="Unique blocker identifier")
    related_item_id: str = Field(..., description="Primary affected work item ID")
    impacted_item_ids: List[str] = Field(..., description="All impacted work item IDs")
    description: str = Field(..., min_length=1, description="Blocker description")
    severity: BlockerSeverity = Field(..., description="Blocker severity")
    status: BlockerStatus = Field(..., description="Blocker resolution status")
    owner: Optional[str] = Field(None, description="Resource responsible for resolution")
    raised_date: datetime = Field(..., description="Date blocker was raised")
    target_resolution_date: Optional[datetime] = Field(None, description="Target resolution date")
    actual_resolution_date: Optional[datetime] = Field(None, description="Actual resolution date")
    category: BlockerCategory = Field(BlockerCategory.OTHER, description="Blocker category")
    notes: Optional[str] = Field(None, description="Additional blocker notes")


class SprintActual(BaseModel):
    """Actual performance data from a completed/in-progress sprint."""
    
    sprint_id: str = Field(..., description="Sprint identifier")
    sprint_number: int = Field(..., ge=1, description="Sprint number for ordering")
    planned_effort_hrs: float = Field(..., ge=0, description="Planned hours for sprint")
    actual_effort_hrs: float = Field(..., ge=0, description="Actual hours completed")
    variance_hrs: float = Field(default=0.0, description="Variance in hours")
    tasks_planned: int = Field(..., ge=0, description="Number of tasks planned")
    tasks_completed: int = Field(..., ge=0, description="Number of tasks completed")
    completion_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="Completion rate (0.0-1.0)")
    carryover_count: int = Field(default=0, ge=0, description="Tasks carried to next sprint")
    scope_change_hours: float = Field(default=0.0, ge=0, description="Hours added via scope changes")
    blocker_impact_hrs: float = Field(default=0.0, ge=0, description="Hours lost to blockers")
    notes: Optional[str] = Field(None, description="Sprint notes")


# ──────────────────────────────────────────────────────────────────────────────
# COMPOSITE MODELS
# ──────────────────────────────────────────────────────────────────────────────


class ProjectState(BaseModel):
    """
    Complete project state - the result of parsing and validating the workbook.
    This is the canonical representation of a project in Sprint Whisperer.
    """
    
    project_id: str = Field(..., description="Unique session/project identifier")
    project_info: ProjectInfo = Field(..., description="Project metadata")
    team: List[Resource] = Field(..., description="Team members")
    sprints: List[Sprint] = Field(..., description="Sprint schedule")
    work_items: List[WorkItem] = Field(..., description="All work items")
    dependencies: List[Dependency] = Field(..., description="Task dependencies")
    blockers: List[Blocker] = Field(..., description="Active and resolved blockers")
    actuals: List[SprintActual] = Field(..., description="Historical sprint actuals")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When state was created")
    
    @field_validator("team")
    def validate_team_not_empty(cls, v: List[Resource]) -> List[Resource]:
        """Team must not be empty."""
        if not v:
            raise ValueError("Project must have at least one team member")
        return v
    
    @field_validator("sprints")
    def validate_sprints_not_empty(cls, v: List[Sprint]) -> List[Sprint]:
        """Must have at least one sprint."""
        if not v:
            raise ValueError("Project must have at least one sprint")
        return v
    
    @field_validator("work_items")
    def validate_work_items_not_empty(cls, v: List[WorkItem]) -> List[WorkItem]:
        """Must have at least one work item."""
        if not v:
            raise ValueError("Project must have at least one work item")
        return v
