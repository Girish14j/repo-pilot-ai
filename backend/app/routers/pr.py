from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.github_service import GitHubService
from app.models.pr import PRContext

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


@router.get("/health")
def pr_health():
    """Confirms the PR review system is online."""
    return {"status": "ok", "service": "RepoPilot PR Review", "stage": 1}