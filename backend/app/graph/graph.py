from langgraph.graph import StateGraph, START, END
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


def route_after_architecture(state: RepoState) -> str:
    """
    Conditional edge router — runs after Architecture Agent.

    Reads the architecture score from state and decides the next node.
    Returns the NAME of the next node as a string.

    This is how LangGraph makes routing decisions:
    - Router function receives current state
    - Returns string matching a node name
    - LangGraph routes execution to that node
    """
    architecture = state.get("architecture_analysis") or {}
    score = architecture.get("score", 10)

    if score < 7:
        print(f"🔀 Router: Architecture score {score}/10 < 7 → Running Refactoring Agent")
        return "refactoring_agent"
    else:
        print(f"🔀 Router: Architecture score {score}/10 ≥ 7 → Skipping Refactoring Agent")
        return "documentation_agent"


def build_graph():
    """
    Assembles and compiles the LangGraph pipeline.
    
    This function is the blueprint of our entire multi-agent system.
    As we add more agents in future steps, they all get added here.
    
    Returns a compiled graph ready to be invoked.
    """

    # StateGraph is the container for our entire workflow
    # We pass RepoState so LangGraph knows the shape of the state
    graph = StateGraph(RepoState)

    # ─── Register Nodes ───────────────────────────────────────────
    # Each node has a name (string) and a function
    # The name is what we use when adding edges
    graph.add_node("repository_agent", repository_agent)
    graph.add_node("architecture_agent", architecture_agent)
    graph.add_node("documentation_agent", documentation_agent)
    graph.add_node("security_agent", security_agent)
    graph.add_node("performance_agent", performance_agent)
    graph.add_node("refactoring_agent", refactoring_agent)
    graph.add_node("interview_agent", interview_agent)
    graph.add_node("resume_agent", resume_agent)
    graph.add_node("final_report_agent", final_report_agent)

    # ─── Add Edges ────────────────────────────────────────────────
    # START → repository_agent (this is where execution begins)
    graph.add_edge(START, "repository_agent")

    # repository_agent → architecture_agent (always, no conditions yet)
    graph.add_edge("repository_agent", "architecture_agent")

    # CONDITIONAL EDGE: after architecture, route based on score
    # add_conditional_edges takes:
    #   1. The source node
    #   2. The router function
    #   3. A mapping of return values → node names (optional but explicit)
    graph.add_conditional_edges(
        "architecture_agent",
        route_after_architecture,
        {
            "refactoring_agent": "refactoring_agent",
            "documentation_agent": "documentation_agent",
        }
    )
    

    # After refactoring (if it ran) → documentation
    graph.add_edge("refactoring_agent", "documentation_agent")

    # Linear pipeline for remaining agents
    graph.add_edge("documentation_agent", "security_agent")
    graph.add_edge("security_agent", "performance_agent")
    graph.add_edge("performance_agent", "interview_agent")
    graph.add_edge("interview_agent", "resume_agent")
    graph.add_edge("resume_agent", "final_report_agent")

     # Exit point
    graph.add_edge("final_report_agent", END)

    # ─── Compile ──────────────────────────────────────────────────
    # compile() validates the graph (checks for disconnected nodes,
    # missing edges, etc.) and returns an executable object
    compiled = graph.compile()

    print("✅ Graph compiled successfully")
    return compiled


# Build the graph once when the module loads
# All API endpoints will use this single instance
repo_graph = build_graph()