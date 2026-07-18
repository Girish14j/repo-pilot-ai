import os
from openai import RateLimitError, APIConnectionError, APIStatusError
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from app.graph.chat_state import ChatState

load_dotenv()

FREE_MODELS = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "nousresearch/hermes-3-llama-3.1-405b:free",
    "nvidia/nemotron-3-ultra-550b-a55b:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "openai/gpt-oss-120b:free",
    "openai/gpt-oss-20b:free",
    "qwen/qwen3-coder:free",
    "google/gemma-4-31b-it:free",
    "meta-llama/llama-3.2-3b-instruct:free",
]


def chat_node(state: ChatState) -> dict:
    repo_context = state.get("repo_context", "No repository context available.")

    system_message = SystemMessage(content=f"""You are RepoPilot AI — an expert software engineering assistant.

You have already analyzed a GitHub repository and have full context about it.
Answer questions specifically about this repository. Be technical, specific, and helpful.
Reference actual details from the analysis when answering.

REPOSITORY ANALYSIS CONTEXT:
{repo_context}

Guidelines:
- Always reference specific findings from the analysis
- Be concise but thorough
- If asked to generate content (resume bullets, cover letter, etc.), do it fully
- If asked something not covered in the analysis, say so honestly
- Use markdown formatting for code blocks and lists""")

    all_messages = [system_message] + state.get("messages", [])

    response = None
    last_error = None
    for model in FREE_MODELS:
        try:
            llm = ChatOpenAI(
                model=model,
                api_key=os.getenv("OPENROUTER_API_KEY"),
                base_url="https://openrouter.ai/api/v1/",
                temperature=0.5,
            )
            response = llm.invoke(all_messages)
            break
        except (RateLimitError, APIConnectionError, APIStatusError) as e:
            print(f"⚠️  Chat model {model} unavailable ({type(e).__name__}), trying next...")
            last_error = e

    if response is None:
        raise last_error or RuntimeError("All chat models exhausted")

    return {"messages": [response]}


def build_chat_graph():
    """
    Builds the conversational chat graph with memory.

    Key difference from the analysis graph:
    - Uses MemorySaver checkpointer for persistence
    - compile() receives the checkpointer
    - invoke() receives a config with thread_id
    """

    graph = StateGraph(ChatState)

    # Single node — the chat agent
    graph.add_node("chat_node", chat_node)

    # Simple linear flow — no conditions needed for chat
    graph.add_edge(START, "chat_node")
    graph.add_edge("chat_node", END)

    # MemorySaver is an in-memory checkpointer
    # It saves state after every node run
    # When you invoke with the same thread_id, it restores previous state
    memory = MemorySaver()

    # Pass checkpointer to compile() — this is what enables memory
    compiled = graph.compile(checkpointer=memory)

    print("✅ Chat graph compiled with memory")
    return compiled


# Single instance — memory persists for the lifetime of the server
chat_graph = build_chat_graph()