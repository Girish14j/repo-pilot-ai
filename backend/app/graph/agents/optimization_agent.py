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
    "meta-llama/llama-3.3-70b-instruct",
    "nousresearch/hermes-3-llama-3.1-405b",
    "nvidia/nemotron-3-ultra-550b",
    "nvidia/nemotron-3-super-120b",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "qwen/qwen3-coder",
    "google/gemma-4-31b-it",
    "meta-llama/llama-3.2-3b-instruct",
]


class OptimizationSuggestion(BaseModel):
    file: str
    current_pattern: str    # what the code is doing now
    optimized_pattern: str  # what it should do instead
    impact: str             # "performance", "memory", "readability", "security"
    effort: str             # "low", "medium", "high"
    explanation: str


class OptimizationAnalysis(BaseModel):
    suggestions: List[OptimizationSuggestion]
    quick_wins: List[str]        # low effort, high impact changes
    performance_score: int       # 0-10
    readability_score: int       # 0-10
    summary: str


def optimization_agent(state: RepoState) -> dict:
    """
    Node: Optimization Agent

    Responsibility: Find specific optimization opportunities
    in the actual source code — performance, memory, readability.

    Unlike the Performance Agent (which guesses from structure),
    this agent reads real code and gives specific suggestions.

    Inputs from state:  code_summary, repo_data
    Outputs to state:   optimization_analysis
    """
    print("Optimization Agent: Finding optimization opportunities...")

    if not state.get("code_summary"):
        return {
            "optimization_analysis": None,
            "completed_agents": state.get("completed_agents", []),
            "errors": state.get("errors", []) + ["Optimization Agent skipped: no code fetched"],
        }

    code_summary = state["code_summary"]
    repo_data = state.get("repo_data", {})
    language = repo_data.get("language", "Unknown")

    parser = JsonOutputParser(pydantic_object=OptimizationAnalysis)

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """You are a performance engineering expert who specializes in 
code optimization across Python, JavaScript, and TypeScript.

You read actual code and find specific optimization opportunities.
You always provide the current pattern AND the optimized alternative.
You never suggest vague improvements — every suggestion is concrete and actionable.

Effort levels:
- low: less than 30 minutes to implement
- medium: half a day of work
- high: requires significant refactoring

Impact types:
- performance: makes the code faster
- memory: reduces memory usage
- readability: makes code easier to understand and maintain
- security: makes the code safer

Respond ONLY with valid JSON:
{format_instructions}"""
        ),
        (
            "human",
            """Find optimization opportunities in this source code.

Repository: {full_name}
Language: {language}

SOURCE CODE:
{code}

Look for:
1. Inefficient loops or data structures
2. Unnecessary database/API calls (N+1 patterns)
3. Missing caching opportunities
4. Synchronous operations that should be async
5. Large functions that should be split
6. Repeated code that should be extracted
7. Inefficient string operations
8. Memory leaks or unnecessary object creation
9. Missing error handling
10. Overly complex logic that can be simplified

For each suggestion provide:
- The exact file it applies to
- What the current pattern looks like
- What the optimized pattern should look like
- The impact type and effort level"""
        )
    ])

    try:
        payload = {
            "format_instructions": parser.get_format_instructions(),
            "full_name": repo_data.get("full_name", "Unknown"),
            "language": language,
            "code": code_summary,
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
                print(f"[WARN] Model {model} unavailable ({type(e).__name__}), trying next...")
                last_error = e

        if result is None:
            raise last_error or RuntimeError("All models exhausted")

        suggestion_count = len(result.get("suggestions", []))
        print(f"Optimization Agent: {suggestion_count} optimization opportunities found")

        return {
            "optimization_analysis": result,
            "completed_agents": state.get("completed_agents", []) + ["optimization_agent"],
            "errors": state.get("errors", []),
        }

    except Exception as e:
        error_msg = f"Optimization Agent failed: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return {
            "optimization_analysis": None,
            "completed_agents": state.get("completed_agents", []),
            "errors": state.get("errors", []) + [error_msg],
        }