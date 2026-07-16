import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel
from typing import List
from app.graph.state import RepoState

load_dotenv()


class InterviewContent(BaseModel):
    technical_questions: List[str]
    behavioral_questions: List[str]
    system_design_questions: List[str]
    suggested_answers_hints: List[str]
    topics_to_study: List[str]


def interview_agent(state: RepoState) -> dict:
    """
    Node 7: Interview Agent

    Responsibility: Generate interview questions specific to
    the technologies and patterns used in this repository.

    Inputs from state:  repo_data, architecture_analysis
    Outputs to state:   interview_content
    """
    print("🎯 Interview Agent: Generating interview questions...")

    if not state.get("repo_data"):
        return {
            "interview_content": None,
            "completed_agents": state.get("completed_agents", []),
            "errors": state.get("errors", []) + ["Interview Agent skipped: no repo_data"],
        }

    repo_data = state["repo_data"]
    architecture = state.get("architecture_analysis") or {}
    patterns = architecture.get("patterns_detected", [])
    languages = list(repo_data.get("languages", {}).keys())
    topics = repo_data.get("topics", [])

    llm = ChatOpenAI(
        model="meta-llama/llama-3.3-70b-instruct:free",
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1/",
        temperature=0.4,
    )
    parser = JsonOutputParser(pydantic_object=InterviewContent)

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """You are a senior technical interviewer at a top tech company.
You generate highly specific interview questions based on actual project details.
Your questions reveal deep understanding — not surface-level knowledge.
Never generate generic questions. Every question must reference something specific.

Respond ONLY with valid JSON:
{format_instructions}"""
        ),
        (
            "human",
            """Generate interview questions for a developer who built this project.

Repository: {full_name}
Description: {description}
Languages: {languages}
Architectural Patterns Used: {patterns}
Topics/Tags: {topics}

Generate:
1. technical_questions: 5 deep technical questions about implementation choices
2. behavioral_questions: 3 behavioral questions about challenges faced
3. system_design_questions: 3 system design questions based on this project's domain
4. suggested_answers_hints: Brief hints for answering the technical questions
5. topics_to_study: Technologies/concepts to review before an interview about this project"""
        )
    ])

    try:
        result = (prompt | llm | parser).invoke({
            "format_instructions": parser.get_format_instructions(),
            "full_name": repo_data.get("full_name", "Unknown"),
            "description": repo_data.get("description", "No description"),
            "languages": ", ".join(languages),
            "patterns": ", ".join(patterns) if patterns else "Not analyzed",
            "topics": ", ".join(topics) if topics else "None",
        })

        print(f"✅ Interview Agent: Generated {len(result.get('technical_questions', []))} questions")

        return {
            "interview_content": result,
            "completed_agents": state.get("completed_agents", []) + ["interview_agent"],
            "errors": state.get("errors", []),
        }

    except Exception as e:
        error_msg = f"Interview Agent failed: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "interview_content": None,
            "completed_agents": state.get("completed_agents", []),
            "errors": state.get("errors", []) + [error_msg],
        }