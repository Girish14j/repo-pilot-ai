from typing import Annotated, Optional
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


class ChatState(TypedDict):
    """
    State for the conversational chat graph.

    Key difference from RepoState:
    - messages uses add_messages reducer — appends instead of overwrites
    - repo_context is injected once and persists across all messages
    - thread_id identifies the conversation session
    """

    # Annotated tells LangGraph to use add_messages reducer
    # This means new messages are APPENDED to existing ones
    # not replaced — this is how conversation history works
    messages: Annotated[list, add_messages]

    # Injected once from the full report — persists in memory
    repo_context: Optional[str]

    # Identifies this conversation session
    thread_id: str