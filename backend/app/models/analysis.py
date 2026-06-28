from pydantic import BaseModel
from typing import Optional

class ScoreBreakdown(BaseModel):
    """
    Individual scores for each dimension of the repository.
    All scores are out of 10.
    """
    architecture: int
    documentation: int
    code_quality: int
    security: int
    maintainability: int

class RepositoryAnalysis(BaseModel):
    """
    The full structured output we expect from the LLM.
    Every field here maps directly to a section in our final report.
    """
    executive_summary: str        # 2-3 sentence overview
    overall_score: int            # 0-10
    scores: ScoreBreakdown        # nested scores object
    strengths: list[str]          # what the repo does well
    weaknesses: list[str]         # what needs improvement
    missing_files: list[str]      # e.g. missing .gitignore, CONTRIBUTING.md
    security_concerns: list[str]  # potential security issues
    recommendations: list[str]    # top actionable suggestions
    tech_stack_summary: str       # human-readable tech stack description