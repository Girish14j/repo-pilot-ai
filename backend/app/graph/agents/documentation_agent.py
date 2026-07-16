import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel
from typing import List
from app.graph.state import RepoState
from app.rag.retriever import retrieve

load_dotenv()

class DocumentationAnalysis(BaseModel):
    score: int
    has_readme: bool
    missing_sections: List[str]
    strengths: List[str]
    improvements: List[str]
    summary: str


def documentation_agent(state: RepoState) -> dict:
    """
    Node 3: Documentation Agent

    Responsibility: Analyze README quality and documentation coverage.
    Uses RAG to retrieve documentation best practices.

    Inputs from state:  repo_data
    Outputs to state:   documentation_analysis
    """
    print(" Docummentation Agent: Analyzing documentation quality...")

    if not state.get("repo_data"):
        return {
            "documentation_analysis": None,
            "completed_agemts": state.get("completed_agents", []),
            "errors": state.get("errors", []) + ["Missing repo_data for documentation analysis."],
        }

    repo_data = state["repo_data"]
    readme = (repo_data.get("readme") or "No README found.")[:3000]  # Limit to first 3000 characters
    file_tree = repo_data.get("file_tree", [])[:100]  # Limit to first 100 files
    file_tree_str = "\n".join(file_tree) if file_tree else "No files found."

    #RAG: retrieve best practices for documentation
    doc_knowledge = retrieve(
        query="README best practices missing sections documentation quality",
        topic="documentation",
        k=3
    )

    llm = ChatOpenAI(
        model="meta-llama/llama-3.3-70b-instruct:free",
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1/",
        temperature=0.2,
    )

    parser = JsonOutputParser(pydantic_object=DocumentationAnalysis)

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """You are a technical writer and documentation expert.
You evaluate README files and project documentation against professional standards.

DOCUMENTATION STANDARDS:
{rag_context}

Respond ONLY with valid JSON:
{format_instructions}"""
        ),
        (
            "human",
            """Analyze the documentation for this repository.

Repository: {full_name}
File Tree:
{file_tree}

README CONTENT:
{readme}

Evaluate:
1. Does the README cover all essential sections?
2. What critical sections are missing?
3. Is the documentation sufficient for a new developer to get started?
4. Score 0-10 based on documentation completeness and quality."""
        )
    ])


    try:
        result = (prompt | llm | parser).invoke({
             #below information is sent to the prompt
            "format_instructions": parser.get_format_instructions(),
            "rag_context": doc_knowledge,
            "full_name": repo_data.get("full_name", "Unknown"),
            "file_tree": file_tree_str,
            "readme": readme,
        })


        print(f" Documentation Agent: Score {result.get('score', 'N/A')}/10")

        return{
            "documentation_analysis": result,
            "completed_agents": state.get("completed_agents", []) + ["documentation_agent"],
            "errors": state.get("errors", []),
        }

    except Exception as e:
        error_msg = f"Documentation Agent failed: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "documentation_analysis": None,
            "completed_agents": state.get("completed_agents", []),
            "errors": state.get("errors", []) + [error_msg],
        }