import os
from openai import RateLimitError, APIConnectionError, APIStatusError
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel
from typing import List, Optional
from app.graph.state import RepoState
from app.rag.retriever import retrieve

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


class CodeIssue(BaseModel):
    file: str
    issue: str
    severity: str        # "critical", "warning", "suggestion"
    line_hint: Optional[str]  # approximate location if detectable
    fix: str             # concrete fix suggestion


class CodeQualityAnalysis(BaseModel):
    score: int
    issues: List[CodeIssue]
    good_patterns: List[str]
    overall_assessment: str
    top_3_fixes: List[str]  # most important fixes in priority order


def code_quality_agent(state: RepoState) -> dict:
    """
    Node: Code Quality Agent

    Responsibility: Read actual source code and identify
    real code quality issues — not guesses from file names.

    This is the agent that makes RepoPilot genuinely useful
    for code review, not just structural analysis.

    Inputs from state:  code_summary, repo_data
    Outputs to state:   code_quality_analysis
    """
    print("Code Quality Agent: Analyzing source code...")

    if not state.get("code_summary"):
        return {
            "code_quality_analysis": None,
            "completed_agents": state.get("completed_agents", []),
            "errors": state.get("errors", []) + ["Code Quality Agent skipped: no code fetched"],
        }

    code_summary = state["code_summary"]
    repo_data = state.get("repo_data", {})
    language = repo_data.get("language", "Unknown")

    # RAG: retrieve language-specific best practices
    quality_knowledge = retrieve(
        query=f"code quality best practices {language} clean code patterns",
        topic="solid",
        k=3
    )

    parser = JsonOutputParser(pydantic_object=CodeQualityAnalysis)

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """You are a senior software engineer doing a real code review.
You read actual source code and find real issues — not guesses.
You are specific: reference exact file names, function names, and patterns you see.
You never make up issues that aren't visible in the code.

ENGINEERING REFERENCES:
{rag_context}

Severity levels:
- critical: security risk, data loss risk, or will cause bugs
- warning: code smell, maintainability issue, or anti-pattern  
- suggestion: improvement that would make code cleaner or faster

Respond ONLY with valid JSON:
{format_instructions}"""
        ),
        (
            "human",
            """Review this source code for quality issues.

Repository: {full_name}
Primary Language: {language}

SOURCE CODE:
{code}

For each issue found:
1. Name the exact file
2. Describe the specific issue you can see in the code
3. Assign severity (critical/warning/suggestion)
4. Give a concrete fix

Also identify good patterns you see — don't only look for problems.
Score 0-10 where 10 = excellent code quality throughout."""
        )
    ])

    try:
        payload = {
            "format_instructions": parser.get_format_instructions(),
            "rag_context": quality_knowledge,
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
                    temperature=0.1,
                )
                result = (prompt | llm | parser).invoke(payload)
                break
            except (RateLimitError, APIConnectionError, APIStatusError) as e:
                print(f"[WARN] Model {model} unavailable ({type(e).__name__}), trying next...")
                last_error = e

        if result is None:
            raise last_error or RuntimeError("All models exhausted")

        issue_count = len(result.get("issues", []))
        print(f"Code Quality Agent: Score {result.get('score', 'N/A')}/10 — {issue_count} issues found")

        return {
            "code_quality_analysis": result,
            "completed_agents": state.get("completed_agents", []) + ["code_quality_agent"],
            "errors": state.get("errors", []),
        }

    except Exception as e:
        error_msg = f"Code Quality Agent failed: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return {
            "code_quality_analysis": None,
            "completed_agents": state.get("completed_agents", []),
            "errors": state.get("errors", []) + [error_msg],
        }