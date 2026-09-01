from app.graph.state import RepoState
from app.services.code_fetcher import CodeFetcher

code_fetcher = CodeFetcher()


def code_fetcher_agent(state: RepoState) -> dict:
    """
    Node: Code Fetcher Agent

    Responsibility: Fetch actual source code files from GitHub
    and format them for downstream agents.

    This agent does NOT call an LLM — it's pure data fetching.
    Like the Final Report Agent, not every node needs AI.

    Inputs from state:  repo_data
    Outputs to state:   fetched_code, code_summary
    """
    print("Code Fetcher Agent: Fetching source files...")

    if not state.get("repo_data"):
        return {
            "fetched_code": None,
            "code_summary": None,
            "completed_agents": state.get("completed_agents", []),
            "errors": state.get("errors", []) + ["Code Fetcher skipped: no repo_data"],
        }

    repo_data = state["repo_data"]
    owner = repo_data.get("owner", "")
    repo = repo_data.get("name", "")
    file_tree = repo_data.get("file_tree", [])

    try:
        # Fetch the most important source files
        fetched_code = code_fetcher.fetch_important_files(owner, repo, file_tree)

        if not fetched_code:
            return {
                "fetched_code": {},
                "code_summary": "No source files could be fetched.",
                "completed_agents": state.get("completed_agents", []) + ["code_fetcher_agent"],
                "errors": state.get("errors", []),
            }

        # Format code into a readable string for LLM prompts
        # Each file is clearly labeled so the LLM knows which file it's reading
        code_parts = []
        for path, content in fetched_code.items():
            code_parts.append(
                f"{'='*50}\n"
                f"FILE: {path}\n"
                f"{'='*50}\n"
                f"{content}\n"
            )

        code_summary = "\n".join(code_parts)

        print(f"Code Fetcher Agent: Ready — {len(fetched_code)} files")

        return {
            "fetched_code": fetched_code,
            "code_summary": code_summary,
            "completed_agents": state.get("completed_agents", []) + ["code_fetcher_agent"],
            "errors": state.get("errors", []),
        }

    except Exception as e:
        error_msg = f"Code Fetcher Agent failed: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return {
            "fetched_code": None,
            "code_summary": None,
            "completed_agents": state.get("completed_agents", []),
            "errors": state.get("errors", []) + [error_msg],
        }