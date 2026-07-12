from typing import Optional, Any
from typing_extensions import TypedDict

class RepoState(TypedDict):
    """
    The Shared state that flows through every node in the graph.

    TypeDict is like a types Python Dictonary.
    Every field here is something a node can read or write.

    Optional means the field starts as None and gets filled in as
    as the graph executes node by node.
    Any means the value could be any type (str, list, dict, etc)
    """
    
    #input - provided by the user before the graph starts
    repo_url: str

    #Filled in by repository Agent
    repo_data: Optional[dict]

    # Filled in by Architecture Agent
    architecture_analysis: Optional[dict]

    # Filled in by Documentation Agent (Step 8)
    documentation_analysis: Optional[dict]

    # Filled in by Security Agent (Step 8)
    security_analysis: Optional[dict]

    # Filled in by Performance Agent (Step 8)
    performance_analysis: Optional[dict]

    # Filled in by Refactoring Agent (Step 8)
    refactoring_suggestions: Optional[dict]

    # Filled in by Interview Agent (Step 8)
    interview_content: Optional[dict]

    # Filled in by Resume Agent (Step 8)
    resume_content: Optional[dict]

    # Filled in by Final Report Agent (Step 8)
    final_report: Optional[dict]

    # Tracks which agents have run — useful for debugging
    completed_agents: list[str]

    # Collects errors from any agent without crashing the graph
    errors: list[str]