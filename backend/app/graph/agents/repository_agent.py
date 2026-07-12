import os
from dotenv import load_dotenv
from app.graph.state import RepoState
from app.services.github_service import GitHubService

load_dotenv()

github_service = GitHubService()

def repository_agent(state: RepoState) -> dict:
    """
    Node 1: Repository Agent
    Responsibility: Fetch all raw data from GitHub and store it in state.
    This is the only node that touches the GitHub API.
    All other agents read repo_data from state — they never call GitHub directly.
    
    Inputs from state:  repo_url
    Outputs to state:   repo_data, completed_agents, errors
    """

    print("🔍 Repository Agent: Fetching repository data...")

    try:
        repo_data = github_service.fetch_repo(state["repo_url"])

        print(f"✅ Repository Agent: Fetched {repo_data.full_name}")

        return{
            # Convert Pydantic model to dict so it can be stored in state
            "repo_data": repo_data.model_dump(),

            # Append this agent to the completed list
            # We use list concatenation instead of .append() because
            # state updates must return new objects, not mutate existing ones
            "completed_agents": state.get("completed_agents", []) + ["repository_agent"],

            "errors": state.get("errors", []),
        }
    except Exception as e:
        print(f"❌ Repository Agent: Error fetching repository data: {e}")

        return {
            "repo_data": None,
            "completed_agents": state.get("completed_agents", []),
            "errors": state.get("errors", []) + [f"Repository Agent error: {e}"],
        }