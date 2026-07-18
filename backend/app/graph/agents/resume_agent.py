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
    "openai/gpt-oss-120b:free",
    "openai/gpt-oss-20b:free",
    "qwen/qwen3-coder:free",
    "google/gemma-4-31b-it:free",
    "meta-llama/llama-3.2-3b-instruct:free",
]


class ResumeContent(BaseModel):
    resume_bullets: List[str]
    ats_description: str
    linkedin_post: str
    key_achievements: List[str]
    skills_demonstrated: List[str]


def resume_agent(state: RepoState) -> dict:
    """
    Node 8: Resume Agent

    Responsibility: Generate ATS-optimized career content
    based on what was actually built in the repository.

    Inputs from state:  repo_data, architecture_analysis
    Outputs to state:   resume_content
    """
    print("Resume Agent: Generating career content...")

    if not state.get("repo_data"):
        return {
            "resume_content": None,
            "completed_agents": state.get("completed_agents", []),
            "errors": state.get("errors", []) + ["Resume Agent skipped: no repo_data"],
        }

    repo_data = state["repo_data"]
    architecture = state.get("architecture_analysis") or {}
    patterns = architecture.get("patterns_detected", [])
    languages = list(repo_data.get("languages", {}).keys())

    parser = JsonOutputParser(pydantic_object=ResumeContent)

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """You are an expert technical resume writer and career coach.
You transform GitHub projects into compelling career content.
Your resume bullets start with strong action verbs and include technologies.
Your LinkedIn posts are conversational, human, and engaging — not corporate.

Respond ONLY with valid JSON:
{format_instructions}"""
        ),
        (
            "human",
            """Generate career content for a developer who built this project.

Repository: {full_name}
Description: {description}
Stars: {stars}
Languages: {languages}
Architectural Patterns: {patterns}
Topics: {topics}

Generate:
1. resume_bullets: 5 ATS-optimized bullets starting with action verbs
2. ats_description: 3-sentence project description for job applications
3. linkedin_post: Ready-to-post update (first person, conversational, 3 paragraphs + hashtags)
4. key_achievements: 3 specific technical achievements from this project
5. skills_demonstrated: Technical skills a recruiter would extract from this project"""
        )
    ])

    try:
        payload = {
            "format_instructions": parser.get_format_instructions(),
            "full_name": repo_data.get("full_name", "Unknown"),
            "description": repo_data.get("description", "No description"),
            "stars": repo_data.get("stars", 0),
            "languages": ", ".join(languages),
            "patterns": ", ".join(patterns) if patterns else "Standard architecture",
            "topics": ", ".join(repo_data.get("topics", [])) or "None",
        }
        result = None
        last_error = None
        for model in FREE_MODELS:
            try:
                llm = ChatOpenAI(model=model, api_key=os.getenv("OPENROUTER_API_KEY"),
                                 base_url="https://openrouter.ai/api/v1/", temperature=0.6)
                result = (prompt | llm | parser).invoke(payload)
                break
            except (RateLimitError, APIConnectionError, APIStatusError) as e:
                last_error = e
        if result is None:
            raise last_error or RuntimeError("All models exhausted")

        print(f"Resume Agent: Generated career content")

        return {
            "resume_content": result,
            "completed_agents": state.get("completed_agents", []) + ["resume_agent"],
            "errors": state.get("errors", []),
        }

    except Exception as e:
        error_msg = f"Resume Agent failed: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "resume_content": None,
            "completed_agents": state.get("completed_agents", []),
            "errors": state.get("errors", []) + [error_msg],
        }