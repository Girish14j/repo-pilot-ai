from fastapi import APIRouter, HTTPException
from app.models.repo import RepoRequest, RepoData
from app.services.github_service import GitHubService

# APIRouter is like a mini FastAPI app — groups related routes together
# We'll mount it on "/api/github" in main.py
router = APIRouter(prefix="/api/github", tags=["GitHub"])

# Create one instance of the service — reused across requests
github_service = GitHubService()


@router.post("/analyze", response_model=RepoData)
def analyze_repo(request: RepoRequest):
    """
    Accepts a GitHub repo URL and returns structured repository data.
    POST /api/github/analyze
    Body: { "url": "https://github.com/owner/repo" }
    """
    try:
        repo_data = github_service.fetch_repo(request.url)
        return repo_data
    except ValueError as e:
        # ValueError = bad input (invalid URL format)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Catch-all for GitHub API failures, network errors, etc.
        raise HTTPException(status_code=500, detail=f"GitHub API error: {str(e)}")