import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel
from typing import List
from app.graph.state import RepoState
from app.rag.retriever import retrieve

load_dotenv()


class RefactoringAnalysis(BaseModel):
    priority_refactors: List[str]
    quick_wins: List[str]
    long_term_improvements: List[str]
    estimated_impact: str
    summary: str


def refactoring_agent(state: RepoState) -> dict:
    """
    Node 6 (CONDITIONAL): Refactoring Agent

    This node only runs if architecture score < 7.
    If score >= 7, this node is skipped entirely.

    Responsibility: Provide specific refactoring suggestions
    grounded in SOLID principles and Clean Architecture.

    Inputs from state:  repo_data, architecture_analysis
    Outputs to state:   refactoring_suggestions
    """
    print("🔧 Refactoring Agent: Generating refactoring suggestions...")

    if not state.get("repo_data"):
        return {
            "refactoring_suggestions": None,
            "completed_agents": state.get("completed_agents", []),
            "errors": state.get("errors", []) + ["Refactoring Agent skipped: no repo_data"],
        }

    repo_data = state["repo_data"]
    architecture = state.get("architecture_analysis") or {}
    violations = architecture.get("violations", [])
    file_tree = repo_data.get("file_tree", [])[:100]
    file_tree_str = "\n".join(file_tree)

    # RAG: retrieve SOLID + Clean Architecture for grounded suggestions
    solid_knowledge = retrieve(
        query="refactoring SOLID principles clean code improvements",
        topic="solid",
        k=3
    )

    llm = ChatOpenAI(
        model="meta-llama/llama-3.3-70b-instruct:free",
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1/",
        temperature=0.3,
    )
    parser = JsonOutputParser(pydantic_object=RefactoringAnalysis)

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """You are a senior software engineer specializing in code refactoring.
You provide specific, actionable refactoring suggestions grounded in SOLID principles.

SOLID REFERENCES:
{rag_context}

Respond ONLY with valid JSON:
{format_instructions}"""
        ),
        (
            "human",
            """Generate refactoring suggestions for this repository.

Repository: {full_name}
Language: {language}

KNOWN ARCHITECTURAL VIOLATIONS:
{violations}

FILE STRUCTURE:
{file_tree}

Provide:
1. Priority refactors — what must be fixed first (highest impact)
2. Quick wins — small changes with immediate improvement
3. Long-term improvements — larger structural changes worth planning
4. Estimated impact — what will improve after these refactors"""
        )
    ])

    try:
        result = (prompt | llm | parser).invoke({
            "format_instructions": parser.get_format_instructions(),
            "rag_context": solid_knowledge,
            "full_name": repo_data.get("full_name", "Unknown"),
            "language": repo_data.get("language", "Unknown"),
            "violations": "\n".join(violations) if violations else "None identified",
            "file_tree": file_tree_str,
        })

        print(f"✅ Refactoring Agent: Generated suggestions")

        return {
            "refactoring_suggestions": result,
            "completed_agents": state.get("completed_agents", []) + ["refactoring_agent"],
            "errors": state.get("errors", []),
        }

    except Exception as e:
        error_msg = f"Refactoring Agent failed: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "refactoring_suggestions": None,
            "completed_agents": state.get("completed_agents", []),
            "errors": state.get("errors", []) + [error_msg],
        }