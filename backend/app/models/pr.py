from pydantic import BaseModel
from typing import Optional


class ChangedFile(BaseModel):
    filename: str
    status: str
    additions: int
    deletions: int
    changes: int
    patch: Optional[str] = None


class PRCommit(BaseModel):
    """
    All fields have defaults — GitHub commit structure
    can vary and we never want ingestion to crash
    because of a missing commit field.
    """
    sha: str = ""
    message: str = ""
    author: str = "Unknown"
    date: str = ""


class PRContext(BaseModel):
    owner: str
    repo: str
    pr_number: int
    url: str
    title: str
    description: Optional[str] = None
    author: str
    state: str
    base_branch: str
    head_branch: str
    created_at: str
    updated_at: str
    changed_files: list[ChangedFile]
    commits: list[PRCommit]
    total_additions: int
    total_deletions: int
    total_files_changed: int
    labels: list[str] = []


class FileDiffAnalysis(BaseModel):
    """
    Structured analysis of a single changed file.
    This is the clean representation we pass to AI agents
    instead of the raw noisy patch format.
    """
    filename: str
    status: str                    # added, modified, deleted, renamed

    # What lines actually changed
    added_lines: list[str]         # the actual added line content
    removed_lines: list[str]       # the actual removed line content

    # What code symbols changed
    # We detect these from the @@ ... @@ context in the patch
    symbols_changed: list[str]     # function/class names near the change

    # Risk classification
    risk_areas: list[str]          # e.g. ["security", "authentication", "database"]
    risk_level: str                # "critical", "high", "medium", "low"

    # File type flags — help agents know what they're reviewing
    is_test_file: bool
    is_config_file: bool
    is_dependency_file: bool       # package.json, requirements.txt etc

    # Size of change
    additions: int
    deletions: int


class PRDiffAnalysis(BaseModel):
    """
    Complete diff analysis for the entire PR.
    This is what flows into the AI review agents.
    """
    pr_number: int
    total_files: int

    # Categorized file lists
    added_files: list[str]
    modified_files: list[str]
    deleted_files: list[str]

    # Per-file analysis
    file_analyses: list[FileDiffAnalysis]

    # PR-level risk assessment
    overall_risk_level: str        # highest risk across all files
    risk_areas_touched: list[str]  # all unique risk areas across all files

    # Useful flags for routing decisions later
    touches_authentication: bool
    touches_database: bool
    touches_security: bool
    touches_tests: bool
    touches_dependencies: bool
    touches_config: bool

    # Human readable summary
    change_summary: str