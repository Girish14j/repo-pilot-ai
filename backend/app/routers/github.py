import logging
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.models.repo import RepoRequest, RepoData
from app.models.analysis import RepositoryAnalysis
from app.models.assistant import DeveloperAssistant
from app.services.github_service import GitHubService
from app.services.ai_service import AIService
from app.services.assistant_service import AssistantService
from app.graph.graph import repo_graph, run_graph_stream
from app.graph.chat_graph import chat_graph
from langchain_core.messages import HumanMessage

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

@router.post("/graph-analyze", response_model=dict) 
def graph_analyze(request: RepoRequest):
    """
    Runs the complete LangGraph multi-agent pipeline.
    All 9 agents run in sequence with conditional routing.
    POST /api/github/graph-analyze
    Body: { "url": "https://github.com/owner/repo" }
    """
    try:
        final_state = repo_graph.invoke({
            "repo_url": request.url,
            "repo_data": None,
            "architecture_analysis": None,
            "documentation_analysis": None,
            "security_analysis": None,
            "performance_analysis": None,
            "refactoring_suggestions": None,
            "interview_content": None,
            "resume_content": None,
            "final_report": None,
            "completed_agents": [],
            "errors": [],
        })

        return final_state.get("final_report", {
            "error": "Final report not generated",
            "completed_agents": final_state.get("completed_agents", []),
            "errors": final_state.get("errors", []),
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Graph error: {str(e)}")


@router.post("/graph-stream")
def graph_stream(request: RepoRequest):
    """
    Streams agent results as Server-Sent Events (SSE).
    Each agent emits a JSON event as soon as it finishes.
    GET /api/github/graph-stream
    """
    initial_state = {
        "repo_url": request.url,
        "repo_data": None,
        "architecture_analysis": None,
        "documentation_analysis": None,
        "security_analysis": None,
        "performance_analysis": None,
        "refactoring_suggestions": None,
        "interview_content": None,
        "resume_content": None,
        "final_report": None,
        "completed_agents": [],
        "errors": [],
    }

    # Map state keys to friendly agent names
    KEY_TO_AGENT = {
        "repo_data": "repository_agent",
        "architecture_analysis": "architecture_agent",
        "documentation_analysis": "documentation_agent",
        "security_analysis": "security_agent",
        "performance_analysis": "performance_agent",
        "refactoring_suggestions": "refactoring_agent",
        "interview_content": "interview_agent",
        "resume_content": "resume_agent",
        "final_report": "final_report_agent",
    }

    def event_generator():
        try:
            for agent_name, data, errors in run_graph_stream(request.url):
                payload = {
                    "agent": agent_name,
                    "data": data,
                    "errors": errors,
                }
                yield f"data: {json.dumps(payload)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'agent': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

class ChatStartRequest(BaseModel):
    """Request to initialize a chat session with repo context."""
    thread_id: str
    repo_context: dict  # the full_report dict from graph-analyze


class ChatMessageRequest(BaseModel):
    """Request to send a message in an existing chat session."""
    thread_id: str
    message: str


# ─── NEW: Chat Endpoints ───────────────────────────────────────────────────────

@router.post("/chat/start", response_model=dict)
def start_chat(request: ChatStartRequest):
    """
    Initialize a chat session with repository context.

    Call this once after graph-analyze completes.
    It injects the full report as context into the chat graph's memory.

    POST /api/github/chat/start
    Body: { "thread_id": "owner-repo-123", "repo_context": { ...full_report... } }
    """
    try:
        # Convert the report dict to a readable string for the LLM
        # We format it as structured text rather than raw JSON
        report = request.repo_context
        repository = report.get("repository", {})
        scores = report.get("scores", {})
        analysis = report.get("analysis", {})
        career = report.get("career", {})

        # Build a human-readable context string
        context_str = f"""REPOSITORY: {repository.get('full_name', 'Unknown')}
DESCRIPTION: {repository.get('description', 'None')}
LANGUAGE: {repository.get('language', 'Unknown')}
STARS: {repository.get('stars', 0)}
TOPICS: {', '.join(repository.get('topics', []))}

SCORES:
- Overall: {scores.get('overall', 0)}/10
- Architecture: {scores.get('architecture', 0)}/10
- Documentation: {scores.get('documentation', 0)}/10
- Security: {scores.get('security', 0)}/10
- Performance: {scores.get('performance', 0)}/10

ARCHITECTURE ANALYSIS:
{json.dumps(analysis.get('architecture', {}), indent=2)}

DOCUMENTATION ANALYSIS:
{json.dumps(analysis.get('documentation', {}), indent=2)}

SECURITY ANALYSIS:
{json.dumps(analysis.get('security', {}), indent=2)}

PERFORMANCE ANALYSIS:
{json.dumps(analysis.get('performance', {}), indent=2)}

CAREER CONTENT:
{json.dumps(career, indent=2)}"""

        # Store context in the checkpointer by updating state directly
        # We use update_state instead of invoke to avoid triggering the LLM
        config = {"configurable": {"thread_id": request.thread_id}}

        chat_graph.update_state(
            config,
            {
                "messages": [],
                "repo_context": context_str,
                "thread_id": request.thread_id,
            },
        )

        return {
            "status": "ready",
            "thread_id": request.thread_id,
            "message": "Chat session initialized. Ask anything about this repository.",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat start error: {str(e)}")


@router.post("/chat/message", response_model=dict)
def send_message(request: ChatMessageRequest):
    """
    Send a message in an existing chat session.

    The graph restores conversation history using thread_id
    and responds with full context of previous messages.

    POST /api/github/chat/message
    Body: { "thread_id": "owner-repo-123", "message": "What are the security risks?" }
    """
    try:
        config = {"configurable": {"thread_id": request.thread_id}}

        # Invoke with just the new human message
        # LangGraph restores all previous messages from memory automatically
        result = chat_graph.invoke(
            {
                "messages": [HumanMessage(content=request.message)],
                "thread_id": request.thread_id,
            },
            config=config,
        )

        # Get the last message — that's the AI's response
        messages = result.get("messages", [])
        if not messages:
            raise ValueError("No response from chat agent")

        last_message = messages[-1]

        return {
            "response": last_message.content,
            "thread_id": request.thread_id,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")