from pydantic import BaseModel
from typing import Optional

class ChangedFile(BaseModel):
    """
    Represents a single file changed in the PR.
    GitHub returns this for every file in the PR diff.
    """

    filename: str
    status: str
    additions : int
    deletions :int
    changes : int
    patch : Optional[str]


class PRCommit(BaseModel):
    """
    Represents a single commit in the PR.
    """
    sha : str
    messages : str
    author : str
    date : str


class PRContext(BaseModel):
    """
    The complete structured representation of a Pull Request.

    This is the equivalent of RepoData for PRs —
    everything downstream agents need in one clean object.
    """
    owner: str
    repo: str
    pr_number: int
    url: str

    title: str
    description: Optional[str]
    author: str
    state: str              
    base_branch: str        
    head_branch: str        
    created_at: str
    updated_at: str

    changed_files: list[ChangedFile]
    commits: list[PRCommit]

    # Summary stats
    total_additions: int
    total_deletions: int
    total_files_changed: int

    # Labels if any
    labels: list[str]