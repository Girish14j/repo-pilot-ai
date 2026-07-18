import os
from openai import RateLimitError, APIConnectionError, APIStatusError
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel
from typing import List
from app.graph.state import RepoState

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


class PerformanceAnalysis(BaseModel):
    score: int
    potential_bottlenecks: List[str]
    good_practices: List[str]
    recommendations: List[str]
    summary: str


def performance_agent(state: RepoState) -> dict:
    """
    Node 5: Performance Agent

    Responsibility: Identify potential performance bottlenecks from
    code structure, dependencies, and architectural patterns.
    No RAG here — LLM training data is sufficient for performance patterns.

    Inputs from state:  repo_data
    Outputs to state:   performance_analysis
    """
    print("Perforamce Agent: Analyzing performance...")

    if not state.get("repo_data"):
        return {
            "performance_analysis": None,
            "completed_agents": state.get("completed_agents", []),
            "errors": state.get("errors", []) + ["Performance Agent skipped: no repo_data"],
        }

    repo_data = state["repo_data"]
    file_tree = repo_data.get("file_tree", [])[:150]
    file_tree_str = "\n".join(file_tree)
    languages = repo_data.get("languages", {})
    total_bytes = sum(languages.values()) or 1
    languages_str = ", ".join([
        f"{lang} ({round((b / total_bytes) * 100, 1)}%)"
        for lang, b in languages.items()
    ])
     
    parser = JsonOutputParser(pydantic_object=PerformanceAnalysis)

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """You are a performance engineering expert.
You identify potential performance bottlenecks from code structure and architecture.
You are specific — reference actual files and patterns you observe.

Respond ONLY with valid JSON:
{format_instructions}"""
        ),
        (
            "human",
            """Analyze potential performance issues in this repository.

Repository: {full_name}
Languages: {languages}
Description: {description}

FILE STRUCTURE:
{file_tree}

Analyze:
1. Are there signs of N+1 query problems (multiple service/db calls in loops)?
2. Is caching considered anywhere in the structure?
3. Are there signs of synchronous operations that should be async?
4. Any large file uploads or processing without streaming?
5. Database connection pooling considerations?

Score 0-10 where 10 = excellent performance architecture."""
        )
    ])

    try:
        payload = {
            "format_instructions": parser.get_format_instructions(),
            "full_name": repo_data.get("full_name", "Unknown"),
            "languages": languages_str,
            "description": repo_data.get("description", "No description"),
            "file_tree": file_tree_str,
        }
        result = None
        last_error = None
        for model in FREE_MODELS:
            try:
                llm = ChatOpenAI(
                    model=model,
                    api_key=os.getenv("OPENROUTER_API_KEY"),
                    base_url="https://openrouter.ai/api/v1/",
                    temperature=0.2,
                )
                result = (prompt | llm | parser).invoke(payload)
                break
            except (RateLimitError, APIConnectionError, APIStatusError) as e:
                print(f"⚠️  Model {model} unavailable ({type(e).__name__}), trying next...")
                last_error = e
        if result is None:
            raise last_error or RuntimeError("All models exhausted")

        print(f"✅ Performance Agent: Score {result.get('score', 'N/A')}/10")

        return {
            "performance_analysis": result,
            "completed_agents": state.get("completed_agents", []) + ["performance_agent"],
            "errors": state.get("errors", []),
        }

    except Exception as e:
        error_msg = f"Performance Agent failed: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "performance_analysis": None,
            "completed_agents": state.get("completed_agents", []),
            "errors": state.get("errors", []) + [error_msg],
        }