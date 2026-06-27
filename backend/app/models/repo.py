from pydantic import BaseModel
from typing import Optional

class RepoRequest(BaseModel):
    """
    The data we expect FROM the client when they submit a repo URL.
    Pydantic will automatically validate this when FastAPI receives the request.
    """
    url: str  # e.g. "https://github.com/owner/repo"


class RepoData(BaseModel):
    """
    The structured data we extract FROM the GitHub API.
    This is what gets passed to the LLM in future steps.
    """
    owner: str
    name: str
    full_name: str                    # "owner/repo"
    description: Optional[str]        # repos may have no description
    stars: int
    forks: int
    language: Optional[str]           # primary language GitHub detects
    languages: dict                   # all languages with byte counts
    topics: list[str]                 # GitHub topic tags
    default_branch: str
    file_tree: list[str]              # all file paths in the repo
    readme: Optional[str]             # raw README content