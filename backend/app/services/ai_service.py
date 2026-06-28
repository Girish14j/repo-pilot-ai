import os
# to read .env
import json
import logging  
# if your application gets crashed and you want to know what happened to the system it stores in console
from openai import RateLimitError
# every ai model has a ratelimitter to handel incoming requests
from dotenv import load_dotenv
# loads .env to memory
from langchain_openai import ChatOpenAI
# langchain lets you connect with ai models
from langchain_core.prompts import ChatPromptTemplate
# langchain lets you create prompt template
from langchain_core.output_parsers import JsonOutputParser
# the ai model gives response in json format later langchain converts it to python dictionary
from app.models.repo import RepoData
from app.models.analysis import RepositoryAnalysis

logger = logging.getLogger(__name__)

load_dotenv()

# Ordered by capability — fallback down the list on 429
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


class AIService:
    """
    Responsible for all LangChain/LLM logic.
    Takes structured repo data and returns structured analysis.
    """

    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1/"

        # JsonOutputParser tells LangChain: expect JSON back, parse it automatically
        self.parser = JsonOutputParser(pydantic_object=RepositoryAnalysis)

        # The prompt template — notice the {placeholders}
        # These get filled in at runtime with actual repo data
        self.prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """You are an expert software engineer and code reviewer with 15 years of experience.
You analyze GitHub repositories and provide professional, actionable engineering insights.
You are direct, specific, and technical. You never give generic advice.

You must respond ONLY with valid JSON that matches this exact structure:
{format_instructions}"""
            ),
            (
                "human",
                """Analyze this GitHub repository and provide a thorough engineering review.

REPOSITORY INFORMATION:
- Name: {full_name}
- Description: {description}
- Primary Language: {language}
- Stars: {stars} | Forks: {forks}
- Topics: {topics}

LANGUAGES USED:
{languages}

FILE STRUCTURE:
{file_tree}

README CONTENT:
{readme}

Provide a professional analysis. Be specific — reference actual files and patterns you see.
Do not give generic advice that could apply to any project."""
            )
        ])

    def _build_chain(self, model: str):
        llm = ChatOpenAI(
            model=model,
            api_key=self.api_key,
            base_url=self.base_url,
            temperature=0.3,
        )
        return self.prompt | llm | self.parser

    def analyze_repository(self, repo_data: RepoData) -> RepositoryAnalysis:
        """
        Runs the LangChain chain with real repository data.
        Returns a validated RepositoryAnalysis object.
        """

        # File trees can be huge — we limit to 150 files to stay within token limits
        file_tree_sample = repo_data.file_tree[:150]
        file_tree_str = "\n".join(file_tree_sample)
        if len(repo_data.file_tree) > 150:
            file_tree_str += f"\n... and {len(repo_data.file_tree) - 150} more files"

        # README can also be very long — we truncate to 3000 characters
        readme_preview = (repo_data.readme or "No README found")[:3000]

        # Languages dict → readable string: "Python: 45%, JavaScript: 30%"
        total_bytes = sum(repo_data.languages.values()) or 1
        languages_str = "\n".join([
            f"- {lang}: {round((bytes_ / total_bytes) * 100, 1)}%"
            for lang, bytes_ in repo_data.languages.items()
        ])

        # invoke() runs the chain — fills in the template and calls the LLM
        # Try each free model in order, falling back on 429
        payload = {
            "format_instructions": self.parser.get_format_instructions(),
            "full_name": repo_data.full_name,
            "description": repo_data.description or "No description provided",
            "language": repo_data.language or "Unknown",
            "stars": repo_data.stars,
            "forks": repo_data.forks,
            "topics": ", ".join(repo_data.topics) or "None",
            "languages": languages_str,
            "file_tree": file_tree_str,
            "readme": readme_preview,
        }

        last_error = None
        for model in FREE_MODELS:
            try:
                logger.info("Trying model: %s", model)
                result = self._build_chain(model).invoke(payload)
                break
            except RateLimitError as e:
                logger.warning("Model %s rate limited, trying next...", model)
                last_error = e
        else:
            raise RuntimeError("All models rate limited. Try again in a minute.") from last_error

        logger.info("LLM raw result: %s", result)

        # JsonOutputParser already returns a dict — validate it directly
        if isinstance(result, RepositoryAnalysis):
            return result
        return RepositoryAnalysis.model_validate(result)