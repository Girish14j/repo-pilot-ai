from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.github_service import GitHubService
from app.models.pr import PRContext
from app.services.diff_analyzer import DiffAnalyzer
from app.models.pr import PRContext, PRDiffAnalysis

router = APIRouter(prefix="/api/pr", tags=["Pull Request Review"])

github_service = GitHubService()


class PRRequest(BaseModel):
    """Request body for PR analysis endpoints."""
    url: str  # e.g. "https://github.com/owner/repo/pull/42"


@router.post("/ingest", response_model=PRContext)
def ingest_pr(request: PRRequest):
    """
    Stage 1: PR Ingestion

    Takes a GitHub PR URL and returns structured PR data.
    No AI review yet — just clean data extraction.

    POST /api/pr/ingest
    Body: { "url": "https://github.com/owner/repo/pull/42" }
    """
    try:
        pr_context = github_service.fetch_pr(request.url)
        return pr_context

    except ValueError as e:
        # Bad URL format
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PR ingestion error: {str(e)}")

@router.post("/analyze-diff", response_model=PRDiffAnalysis)
def analyze_diff(request: PRRequest):
    """
    Stage 2: PR Diff Analysis.

    Fetches the PR then analyzes every changed file:
    - Extracts added/removed lines
    - Detects risk areas (security, auth, database, etc.)
    - Calculates risk level per file and overall
    - Identifies changed functions/classes
    - Flags test, config, and dependency files

    No AI involved — pure deterministic analysis.

    POST /api/pr/analyze-diff
    Body: { "url": "https://github.com/owner/repo/pull/42" }
    """
    try:
        pr_context = github_service.fetch_pr(request.url)
        diff_analysis = diff_analyzer.analyze_pr(pr_context)

        return diff_analysis

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PR diff analysis error: {str(e)}")

@router.get("/health")
def pr_health():
    """Confirms the PR review system is online."""
    return {"status": "ok", "service": "RepoPilot PR Review", "stage": 1}