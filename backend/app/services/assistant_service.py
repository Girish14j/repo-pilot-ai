import os
import logging
from openai import RateLimitError
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from app.models.repo import RepoData
from app.models.assistant import DeveloperAssistant

load_dotenv()

logger = logging.getLogger(__name__)

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


class AssistantService:
    """
    Generates career-focused content from repository data.
    Single responsibility: help developers present their work professionally.
    """

    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1/"
        self.parser = JsonOutputParser(pydantic_object=DeveloperAssistant)

        self.prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """You are an expert technical recruiter and career coach with 15 years 
of experience helping software engineers land jobs at top tech companies.

You specialize in translating GitHub projects into compelling career content.
You write ATS-optimized resumes, engaging LinkedIn posts, and sharp interview prep.

Your content is always:
- Specific (references actual technologies and patterns from the project)
- Quantified where possible (uses action verbs + metrics)
- Professional but human (not robotic or generic)

You must respond ONLY with valid JSON matching this structure:
{format_instructions}"""
            ),
            (
                "human",
                """Generate professional career content for a developer who built this project.

REPOSITORY: {full_name}
DESCRIPTION: {description}
PRIMARY LANGUAGE: {language}
TECHNOLOGIES: {languages}
TOPICS/TAGS: {topics}
STARS: {stars}

FILE STRUCTURE (shows what was actually built):
{file_tree}

README:
{readme}

INSTRUCTIONS:
- resume_bullets: 4-6 bullet points starting with strong action verbs (Built, Designed, 
  Implemented, Engineered, Developed). Include technologies. Make them ATS-friendly.
- ats_description: One 3-4 sentence paragraph describing the project for a resume 
  or job application. Mention key technologies and what problem it solves.
- interview_questions: 5 technical questions an interviewer would likely ask about 
  this specific project. Make them specific to what was actually built.
- readme_improvements: 3-5 concrete, specific suggestions to improve this README.
  Reference what is actually missing or weak.
- feature_suggestions: 3-5 features that would meaningfully improve this project.
  Be specific — not generic advice like 'add tests'.
- linkedin_post: A ready-to-post LinkedIn update about this project. 
  3-4 short paragraphs. Conversational, not corporate. Include 3-5 relevant hashtags 
  at the end. Write in first person as if the developer is posting it."""
            )
        ])

    def _build_chain(self, model: str):
        llm = ChatOpenAI(
            model=model,
            api_key=self.api_key,
            base_url=self.base_url,
            temperature=0.7,
        )
        return self.prompt | llm | self.parser

    def generate_content(self, repo_data: RepoData) -> DeveloperAssistant:
        """
        Runs the assistant chain with repository data.
        Returns structured career content as a validated Pydantic model.
        """

        # Same data preparation as ai_service — limit size to stay within token limits
        file_tree_sample = repo_data.file_tree[:100]
        file_tree_str = "\n".join(file_tree_sample)

        readme_preview = (repo_data.readme or "No README found")[:2000]

        total_bytes = sum(repo_data.languages.values()) or 1
        languages_str = ", ".join([
            f"{lang} ({round((bytes_ / total_bytes) * 100, 1)}%)"
            for lang, bytes_ in repo_data.languages.items()
        ])

        last_error = None
        for model in FREE_MODELS:
            try:
                logger.info("AssistantService trying model: %s", model)
                result = self._build_chain(model).invoke({
                    "format_instructions": self.parser.get_format_instructions(),
                    "full_name": repo_data.full_name,
                    "description": repo_data.description or "No description provided",
                    "language": repo_data.language or "Unknown",
                    "stars": repo_data.stars,
                    "topics": ", ".join(repo_data.topics) or "None",
                    "languages": languages_str,
                    "file_tree": file_tree_str,
                    "readme": readme_preview,
                })
                break
            except RateLimitError as e:
                logger.warning("Model %s rate limited, trying next...", model)
                last_error = e
        else:
            raise RuntimeError("All models rate limited. Try again in a minute.") from last_error

        if isinstance(result, DeveloperAssistant):
            return result
        return DeveloperAssistant.model_validate(result)