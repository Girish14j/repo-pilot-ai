import logging
from fastapi import APIRouter, HTTPException
from app.models.repo import RepoRequest, RepoData
from app.models.analysis import RepositoryAnalysis
from app.models.assistant import DeveloperAssistant
from app.services.github_service import GitHubService
#  Go to GitHub and collect repository information.
from app.services.ai_service import AIService
# Read the repository information and review it like a senior software engineer.
from app.services.assistant_service import AssistantService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/github", tags=["GitHub"])

github_service = GitHubService()
ai_service = AIService()
assistant_service = AssistantService()


@router.post("/analyze", response_model=RepoData)
def analyze_repo(request: RepoRequest):
    """Fetch raw repository data from GitHub."""
    try:
        return github_service.fetch_repo(request.url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GitHub API error: {str(e)}")


@router.post("/review", response_model=RepositoryAnalysis)
def review_repo(request: RepoRequest):
    """
    Full pipeline: fetch repo data from GitHub, then analyze it with AI.
    POST /api/github/review
    Body: { "url": "https://github.com/owner/repo" }
    """
    try:
        # Step 1: get repo data
        repo_data = github_service.fetch_repo(request.url)

        # Step 2: pass it to the AI service
        analysis = ai_service.analyze_repository(repo_data)

        return analysis
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Review pipeline failed")
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")


@router.post("/assistant", response_model = DeveloperAssistant)
def assist_repo(request: RepoRequest):
    """
    Full pipeline: fetch repo data then generate career content.
    POST /api/github/assist
    Body: { "url": "https://github.com/owner/repo" }
    """
    try:
        # Fetch repo data — same as review endpoint
        repo_data = github_service.fetch_repo(request.url)

        #Pass to assistant service instead of analysis service
        content = assistant_service.generate_content(repo_data)

        return content
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Assistant pipeline failed")
        raise HTTPException(status_code=500, detail=f"Assistant error: {str(e)}")


@router.post("/full-report", response_model=dict)
def full_report(request: RepoRequest):
    """
    Runs BOTH the analysis and assistant chains and returns everything.
    This is what the frontend will call in one shot.
    POST /api/github/full-report
    Body: { "url": "https://github.com/owner/repo" }
    """
    try:
        # Fetch once — reuse for both chains
        repo_data = github_service.fetch_repo(request.url)

        # Run both AI chains with the same data
        analysis = ai_service.analyze_repository(repo_data)
        assistant = assistant_service.generate_content(repo_data)

        # Return everything in one response
        return {
            "repo": repo_data.model_dump(),
            "analysis": analysis.model_dump(),
            "assistant": assistant.model_dump(),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Assistant pipeline failed")
        raise HTTPException(status_code=500, detail=f"Report error: {str(e)}")
