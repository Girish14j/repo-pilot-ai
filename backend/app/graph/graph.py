from concurrent.futures import ThreadPoolExecutor, as_completed
from app.graph.state import RepoState
from app.graph.agents.repository_agent import repository_agent
from app.graph.agents.architecture_agent import architecture_agent
from app.graph.agents.documentation_agent import documentation_agent
from app.graph.agents.security_agent import security_agent
from app.graph.agents.performance_agent import performance_agent
from app.graph.agents.refactoring_agent import refactoring_agent
from app.graph.agents.interview_agent import interview_agent
from app.graph.agents.resume_agent import resume_agent
from app.graph.agents.final_report_agent import final_report_agent


def run_graph(repo_url: str) -> dict:
    """
    Runs all agents with maximum parallelism:

    Step 1: repository_agent  (must run first — fetches data)
    Step 2: architecture_agent + documentation_agent +
            security_agent + performance_agent  (parallel)
    Step 3: refactoring_agent (only if arch score < 7) +
            interview_agent + resume_agent  (parallel)
    Step 4: final_report_agent  (assembles everything)
    """
    state: RepoState = {
        "repo_url": repo_url,
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

    # ── Step 1: Repository Agent ──────────────────────────────────
    result = repository_agent(state)
    state.update(result)
    if not state.get("repo_data"):
        return state  # Can't proceed without repo data

    # ── Step 2: Parallel analysis agents ─────────────────────────
    analysis_agents = [
        architecture_agent,
        documentation_agent,
        security_agent,
        performance_agent,
    ]
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(fn, state): fn.__name__ for fn in analysis_agents}
        for future in as_completed(futures):
            try:
                result = future.result()
                # Merge completed_agents lists properly
                new_agents = [
                    a for a in result.get("completed_agents", [])
                    if a not in state["completed_agents"]
                ]
                state["completed_agents"] = state["completed_agents"] + new_agents
                state["errors"] = state["errors"] + [
                    e for e in result.get("errors", [])
                    if e not in state["errors"]
                ]
                # Update the specific analysis key
                for key in ["architecture_analysis", "documentation_analysis",
                            "security_analysis", "performance_analysis"]:
                    if result.get(key) is not None:
                        state[key] = result[key]
            except Exception as e:
                state["errors"].append(f"{futures[future]} crashed: {str(e)}")

    # ── Step 3: Conditional refactoring + career agents (parallel) ─
    arch = state.get("architecture_analysis") or {}
    arch_score = arch.get("score", 10)

    step3_agents = [interview_agent, resume_agent]
    if arch_score < 7:
        step3_agents.append(refactoring_agent)

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(fn, state): fn.__name__ for fn in step3_agents}
        for future in as_completed(futures):
            try:
                result = future.result()
                new_agents = [
                    a for a in result.get("completed_agents", [])
                    if a not in state["completed_agents"]
                ]
                state["completed_agents"] = state["completed_agents"] + new_agents
                state["errors"] = state["errors"] + [
                    e for e in result.get("errors", [])
                    if e not in state["errors"]
                ]
                for key in ["interview_content", "resume_content", "refactoring_suggestions"]:
                    if result.get(key) is not None:
                        state[key] = result[key]
            except Exception as e:
                state["errors"].append(f"{futures[future]} crashed: {str(e)}")

    # ── Step 4: Final Report ──────────────────────────────────────
    result = final_report_agent(state)
    state.update(result)

    return state


def run_graph_stream(repo_url: str):
    """
    Generator version — yields (agent_name, data) tuples as each agent completes.
    Used by the SSE streaming endpoint.
    """
    state: RepoState = {
        "repo_url": repo_url,
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

    KEY_MAP = {
        "repository_agent": "repo_data",
        "architecture_agent": "architecture_analysis",
        "documentation_agent": "documentation_analysis",
        "security_agent": "security_analysis",
        "performance_agent": "performance_analysis",
        "refactoring_agent": "refactoring_suggestions",
        "interview_agent": "interview_content",
        "resume_agent": "resume_content",
        "final_report_agent": "final_report",
    }

    # Step 1
    result = repository_agent(state)
    state.update(result)
    yield "repository_agent", state.get("repo_data"), state.get("errors", [])
    if not state.get("repo_data"):
        return

    # Step 2 — parallel
    analysis_agents = [architecture_agent, documentation_agent, security_agent, performance_agent]
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(fn, state): fn for fn in analysis_agents}
        for future in as_completed(futures):
            fn = futures[future]
            agent_name = fn.__name__
            try:
                result = future.result()
                data_key = KEY_MAP[agent_name]
                new_agents = [a for a in result.get("completed_agents", []) if a not in state["completed_agents"]]
                state["completed_agents"] += new_agents
                state["errors"] += [e for e in result.get("errors", []) if e not in state["errors"]]
                if result.get(data_key) is not None:
                    state[data_key] = result[data_key]
                yield agent_name, state.get(data_key), result.get("errors", [])
            except Exception as e:
                yield agent_name, None, [str(e)]

    # Step 3 — parallel
    arch_score = (state.get("architecture_analysis") or {}).get("score", 10)
    step3 = [interview_agent, resume_agent]
    if arch_score < 7:
        step3.append(refactoring_agent)

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(fn, state): fn for fn in step3}
        for future in as_completed(futures):
            fn = futures[future]
            agent_name = fn.__name__
            try:
                result = future.result()
                data_key = KEY_MAP[agent_name]
                new_agents = [a for a in result.get("completed_agents", []) if a not in state["completed_agents"]]
                state["completed_agents"] += new_agents
                state["errors"] += [e for e in result.get("errors", []) if e not in state["errors"]]
                if result.get(data_key) is not None:
                    state[data_key] = result[data_key]
                yield agent_name, state.get(data_key), result.get("errors", [])
            except Exception as e:
                yield agent_name, None, [str(e)]

    # Step 4
    result = final_report_agent(state)
    state.update(result)
    yield "final_report_agent", state.get("final_report"), state.get("errors", [])


# Keep repo_graph for backward compatibility with graph-analyze endpoint
class _GraphCompat:
    def invoke(self, initial_state: dict) -> dict:
        return run_graph(initial_state["repo_url"])

    def stream(self, initial_state: dict, **kwargs):
        """Yields LangGraph-style {node_name: {data_key: value}} chunks."""
        KEY_MAP = {
            "repository_agent": "repo_data",
            "architecture_agent": "architecture_analysis",
            "documentation_agent": "documentation_analysis",
            "security_agent": "security_analysis",
            "performance_agent": "performance_analysis",
            "refactoring_agent": "refactoring_suggestions",
            "interview_agent": "interview_content",
            "resume_agent": "resume_content",
            "final_report_agent": "final_report",
        }
        for agent_name, data, errors in run_graph_stream(initial_state["repo_url"]):
            data_key = KEY_MAP.get(agent_name, "data")
            yield {agent_name: {data_key: data, "errors": errors, "completed_agents": [agent_name]}}


repo_graph = _GraphCompat()
print("✅ Graph compiled successfully")
