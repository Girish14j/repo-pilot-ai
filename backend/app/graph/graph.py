from langgraph.graph import StateGraph, START, END
from app.graph.state import RepoState
from app.graph.agents.repository_agent import repository_agent
from app.graph.agents.architecture_agent import architecture_agent


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

    # ─── Add Edges ────────────────────────────────────────────────
    # START → repository_agent (this is where execution begins)
    graph.add_edge(START, "repository_agent")

    # repository_agent → architecture_agent (always, no conditions yet)
    graph.add_edge("repository_agent", "architecture_agent")

    # architecture_agent → END (graph finishes here for now)
    # We will extend this in Step 8 when we add more agents
    graph.add_edge("architecture_agent", END)

    # ─── Compile ──────────────────────────────────────────────────
    # compile() validates the graph (checks for disconnected nodes,
    # missing edges, etc.) and returns an executable object
    compiled = graph.compile()

    print("✅ Graph compiled successfully")
    return compiled


# Build the graph once when the module loads
# All API endpoints will use this single instance
repo_graph = build_graph()