import os
from openai import RateLimitError, APIConnectionError, APIStatusError
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

class SecurityAnalysis(BaseModel):
    score: int
    vulnerabilities: List[str]
    owasp_concerns: List[str]
    good_practices: List[str]
    critical_fixes: List[str]
    summary: str

def security_agent(state: RepoState) -> dict:
    """
    Node 4: Security Agent

    Responsibility: Scan for security vulnerabilities using OWASP Top 10 as reference.
    This is where RAG adds the most value — real OWASP knowledge injected into the prompt.

    Inputs from state:  repo_data
    Outputs to state:   security_analysis
    """

    print("Secruity Agent: Scanning for vulnerabilities...")

    if not state.get("repo_data"):
        return{
            "security_analysis": None,
            "completed_agents": state.get("completed_agents", []),
            "errors": state.get("errors", []) + ["Security Agent skipped: no repo_data"],
        }

    repo_data = state["repo_data"]
    readme = (repo_data.get("readme") or "")[:2000]
    file_tree = repo_data.get("file_tree", [])[:150]
    file_tree_str = "\n".join(file_tree)


    # RAG: retrieve OWASP knowledge — this is the core value of RAG here
    # The agent checks against actual OWASP standards, not just LLM intuition
    owasp_knowledge = retrieve(
        query="Security vulnerabilities authentication injection access control",
        topic="owasp",
        k=4
    )

    parser = JsonOutputParser(pydantic_object=SecurityAnalysis)

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """You are a senior application security engineer (AppSec).
You scan codebases for security vulnerabilities using OWASP standards.
You are specific — you reference actual files and patterns you see.
You never give generic advice. Every concern must reference something real in the repo.

OWASP SECURITY REFERENCES:
{rag_context}

Respond ONLY with valid JSON:
{format_instructions}"""
        ),
        (
            "human",
            """Perform a security analysis of this repository.

Repository: {full_name}
Language: {language}
Description: {description}

FILE STRUCTURE:
{file_tree}

README / DOCS:
{readme}

Using the OWASP references provided:
1. What specific vulnerabilities are likely present based on the code structure?
2. Which OWASP categories are most relevant to this project?
3. What security practices are already in place (good practices)?
4. What are the most critical fixes needed?

Score 0-10 where 10 = no security concerns found."""
        )
    ])

    try:
        payload = {
            "format_instructions": parser.get_format_instructions(),
            "rag_context": owasp_knowledge,
            "full_name": repo_data.get("full_name", "Unknown"),
            "language": repo_data.get("language", "Unknown"),
            "description": repo_data.get("description", "No description"),
            "file_tree": file_tree_str,
            "readme": readme,
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
                print(f"⚠️  Model {model} unavailable ({type(e).__name__}), trying next...")
                last_error = e
        if result is None:
            raise last_error or RuntimeError("All models exhausted")

        print(f"Security Agent: Score {result.get('score', 'N/A')}/10")

        return {
            "security_analysis": result,
            "completed_agents": state.get("completed_agents", []) + ["security_agent"],
            "errors": state.get("errors", []),
        }

    except Exception as e:
        error_msg = f"Security Agent failed: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "security_analysis": None,
            "completed_agents": state.get("completed_agents", []),
            "errors": state.get("errors", []) + [error_msg],
        }