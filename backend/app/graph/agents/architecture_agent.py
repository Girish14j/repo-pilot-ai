import os
from openai import RateLimitError
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel
from typing import List
from app.graph.state import RepoState
from app.rag.retriever import retrieve

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


class ArchitectureAnalysis(BaseModel):
    """
    Structured output from the Architecture Agent.
    Defined here because it's specific to this agent.
    """
    score: int                          # 0-10
    patterns_detected: List[str]        # e.g. ["MVC", "Repository Pattern"]
    violations: List[str]               # e.g. ["God class in main.py"]
    strengths: List[str]
    recommendations: List[str]
    summary: str


def architecture_agent(state: RepoState) -> dict:
    """
    Node 2: Architecture Agent

    Responsibility: Analyze the repository's folder structure,
    detect architectural patterns, and identify violations.

    Inputs from state:  repo_data
    Outputs to state:   architecture_analysis, completed_agents, errors
    """
    print("🏗️  Architecture Agent: Analyzing architecture...")

    # Safety check — if repository agent failed, skip this agent
    if not state.get("repo_data"):
        error_msg = "Architecture Agent skipped: no repo_data in state"
        print(f"⚠️  {error_msg}")
        return {
            "architecture_analysis": None,
            "completed_agents": state.get("completed_agents", []),
            "errors": state.get("errors", []) + [error_msg],
        }

    repo_data = state["repo_data"]

    # Prepare file tree for the prompt
    file_tree = repo_data.get("file_tree", [])[:150]
    file_tree_str = "\n".join(file_tree)

    # ── RAG: Retrieve relevant knowledge ──────────────────────────
    # Instead of relying only on LLM training data, we retrieve
    # specific SOLID and Clean Architecture knowledge to inject
    solid_knowledge = retrieve(
        query="SOLID principles violations in code structure",
        topic="solid",
        k=3
    )
    architecture_knowledge = retrieve(
        query="clean architecture folder structure best practices",
        topic="clean_architecture",
        k=2
    )
    # Combine both into one context block
    rag_context = f"{solid_knowledge}\n\n{architecture_knowledge}"
    print(f"📚 Architecture Agent: Retrieved {len(rag_context)} chars of RAG context")
    # ──────────────────────────────────────────────────────────────

    parser = JsonOutputParser(pydantic_object=ArchitectureAnalysis)

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """You are a senior software architect with 15 years of experience.
You analyze repository structures and identify architectural patterns, violations, and improvements.
You are specific — you reference actual files and folders you see.
You understand MVC, Clean Architecture, SOLID principles, Repository Pattern, 
Service Layer pattern, and other common patterns.

Respond ONLY with valid JSON:
{format_instructions}"""
        ),
        (
            "human",
            """Analyze the architecture of this repository.

Repository: {full_name}
Primary Language: {language}
Description: {description}

FILE STRUCTURE:
{file_tree}

Analyze:
1. What architectural patterns are being used?
2. Are there any architectural violations or anti-patterns?
3. Is the folder structure clean and scalable?
4. What specific improvements would make this more maintainable?

Score the architecture from 0-10 where:
10 = Production-ready, follows best practices perfectly
7-9 = Good structure with minor issues
4-6 = Functional but needs improvement
0-3 = Significant architectural problems"""
        )
    ])

    try:
        payload = {
            "format_instructions": parser.get_format_instructions(),
            "full_name": repo_data.get("full_name", "Unknown"),
            "language": repo_data.get("language", "Unknown"),
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
            except RateLimitError as e:
                print(f"⚠️  Model {model} rate limited, trying next...")
                last_error = e

        if result is None:
            raise last_error or RuntimeError("All models rate limited")

        print(f"✅ Architecture Agent: Score {result.get('score', 'N/A')}/10")

        return {
            "architecture_analysis": result,
            "completed_agents": state.get("completed_agents", []) + ["architecture_agent"],
            "errors": state.get("errors", []),
        }

    except Exception as e:
        error_msg = f"Architecture Agent failed: {str(e)}"
        print(f"❌ {error_msg}")

        return {
            "architecture_analysis": None,
            "completed_agents": state.get("completed_agents", []),
            "errors": state.get("errors", []) + [error_msg],
        }