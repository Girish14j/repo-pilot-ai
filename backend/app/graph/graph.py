from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Iterable

from langgraph.graph import StateGraph, START, END

from app.graph.state import RepoState
from app.graph.agents.repository_agent import repository_agent
from app.graph.agents.code_fetcher_agent import code_fetcher_agent
from app.graph.agents.architecture_agent import architecture_agent
from app.graph.agents.documentation_agent import documentation_agent
from app.graph.agents.security_agent import security_agent
from app.graph.agents.performance_agent import performance_agent
from app.graph.agents.refactoring_agent import refactoring_agent
from app.graph.agents.code_quality_agent import code_quality_agent
from app.graph.agents.optimization_agent import optimization_agent
from app.graph.agents.interview_agent import interview_agent
from app.graph.agents.resume_agent import resume_agent
from app.graph.agents.final_report_agent import final_report_agent


def route_after_architecture(state: RepoState) -> str:
    """Fallback-aware routing: if architecture is missing, weak, or failed, keep the flow safe."""
    architecture = state.get("architecture_analysis") or {}
    score = architecture.get("score")

    if score is None:
        print("[Router] Architecture result missing -> running career fallback")
        return "career_only"

    if score < 7:
        print(f"[Router] Architecture score {score}/10 < 7 -> running refactor + career agents in parallel")
        return "refactor_and_career"

    print(f"[Router] Architecture score {score}/10 >= 7 -> running career agents only")
    return "career_only"


def _merge_agent_result(state: RepoState, result: dict) -> RepoState:
    completed = state.get("completed_agents", [])
    merged = [
        agent for agent in result.get("completed_agents", [])
        if agent not in completed
    ]
    state["completed_agents"] = completed + merged

    existing_errors = state.get("errors", [])
    state["errors"] = existing_errors + [
        err for err in result.get("errors", []) if err not in existing_errors
    ]

    for key in [
        "repo_data",
        "fetched_code",
        "code_summary",
        "architecture_analysis",
        "documentation_analysis",
        "security_analysis",
        "performance_analysis",
        "refactoring_suggestions",
        "code_quality_analysis",
        "optimization_analysis",
        "interview_content",
        "resume_content",
        "final_report",
    ]:
        value = result.get(key)
        if value is not None:
            state[key] = value

    return state


def _run_parallel_agents(state: RepoState, agents: Iterable[Callable[[RepoState], dict]]) -> RepoState:
    local_state = state.copy()
    agent_list = list(agents)
    if not agent_list:
        return local_state

    with ThreadPoolExecutor(max_workers=max(1, len(agent_list))) as executor:
        futures = {executor.submit(func, local_state): func.__name__ for func in agent_list}
        for future in as_completed(futures):
            agent_name = futures[future]
            try:
                result = future.result()
                local_state = _merge_agent_result(local_state, result)
            except Exception as exc:
                local_state["errors"] = local_state.get("errors", []) + [
                    f"{agent_name} crashed: {str(exc)}"
                ]

    return local_state


def run_parallel_analysis(state: RepoState) -> RepoState:
    """Runs the architecture / docs / security / performance agents concurrently."""
    return _run_parallel_agents(state, [
        architecture_agent,
        documentation_agent,
        security_agent,
        performance_agent,
    ])


def run_parallel_career(state: RepoState) -> RepoState:
    """Runs interview/resume generation in parallel, with refactoring optionally included."""
    route = route_after_architecture(state)
    agents = [interview_agent, resume_agent]
    if route == "refactor_and_career":
        agents = [refactoring_agent, *agents]
    return _run_parallel_agents(state, agents)


def run_parallel_code_analysis(state: RepoState) -> RepoState:
    """Runs code quality and optimization checks concurrently."""
    return _run_parallel_agents(state, [
        code_quality_agent,
        optimization_agent,
    ])


def run_graph(repo_url: str) -> dict:
    initial_state: RepoState = {
        "repo_url": repo_url,
        "repo_data": None,
        "fetched_code": None,
        "code_summary": None,
        "architecture_analysis": None,
        "documentation_analysis": None,
        "security_analysis": None,
        "performance_analysis": None,
        "refactoring_suggestions": None,
        "code_quality_analysis": None,
        "optimization_analysis": None,
        "interview_content": None,
        "resume_content": None,
        "final_report": None,
        "completed_agents": [],
        "errors": [],
    }
    return repo_graph.invoke(initial_state)


def run_graph_stream(repo_url: str):
    """Compatibility generator for SSE endpoints. Yields agent-name/data/error tuples."""
    state: RepoState = {
        "repo_url": repo_url,
        "repo_data": None,
        "fetched_code": None,
        "code_summary": None,
        "architecture_analysis": None,
        "documentation_analysis": None,
        "security_analysis": None,
        "performance_analysis": None,
        "refactoring_suggestions": None,
        "code_quality_analysis": None,
        "optimization_analysis": None,
        "interview_content": None,
        "resume_content": None,
        "final_report": None,
        "completed_agents": [],
        "errors": [],
    }

    result = repository_agent(state)
    state = _merge_agent_result(state, result)
    yield "repository_agent", state.get("repo_data"), state.get("errors", [])
    if not state.get("repo_data"):
        return

    result = code_fetcher_agent(state)
    state = _merge_agent_result(state, result)
    yield "code_fetcher_agent", state.get("code_summary"), state.get("errors", [])

    state = run_parallel_analysis(state)
    for agent_name, key in [
        ("architecture_agent", "architecture_analysis"),
        ("documentation_agent", "documentation_analysis"),
        ("security_agent", "security_analysis"),
        ("performance_agent", "performance_analysis"),
    ]:
        yield agent_name, state.get(key), state.get("errors", [])

    state = run_parallel_career(state)
    for agent_name, key in [
        ("refactoring_agent", "refactoring_suggestions"),
        ("interview_agent", "interview_content"),
        ("resume_agent", "resume_content"),
    ]:
        if state.get(key) is not None:
            yield agent_name, state.get(key), state.get("errors", [])

    state = run_parallel_code_analysis(state)
    for agent_name, key in [
        ("code_quality_agent", "code_quality_analysis"),
        ("optimization_agent", "optimization_analysis"),
    ]:
        yield agent_name, state.get(key), state.get("errors", [])

    result = final_report_agent(state)
    state = _merge_agent_result(state, result)
    yield "final_report_agent", state.get("final_report"), state.get("errors", [])


def build_graph():
    graph = StateGraph(RepoState)

    graph.add_node("repository_agent", repository_agent)
    graph.add_node("code_fetcher_agent", code_fetcher_agent)
    graph.add_node("parallel_analysis", run_parallel_analysis)
    graph.add_node("parallel_career", run_parallel_career)
    graph.add_node("parallel_code_analysis", run_parallel_code_analysis)
    graph.add_node("final_report_agent", final_report_agent)

    graph.add_edge(START, "repository_agent")
    graph.add_edge("repository_agent", "code_fetcher_agent")
    graph.add_edge("code_fetcher_agent", "parallel_analysis")

    graph.add_conditional_edges(
        "parallel_analysis",
        route_after_architecture,
        {
            "refactor_and_career": "parallel_career",
            "career_only": "parallel_career",
        },
    )

    graph.add_edge("parallel_career", "parallel_code_analysis")
    graph.add_edge("parallel_code_analysis", "final_report_agent")
    graph.add_edge("final_report_agent", END)

    print("Graph compiled successfully")
    return graph.compile()


repo_graph = build_graph()
