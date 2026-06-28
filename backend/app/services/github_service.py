import httpx
import os
import base64
from dotenv import load_dotenv
from app.models.repo import RepoData

load_dotenv()  # reads .env file into environment variables


class GitHubService:
    """
    Responsible for all communication with the GitHub REST API.
    Single responsibility: fetch and return structured repo data.
    """

    BASE_URL = "https://api.github.com"

    def __init__(self):
        token = os.getenv("GITHUB_TOKEN")

        # These headers are sent with every GitHub API request
        self.headers = {
            "Accept": "application/vnd.github+json",  # GitHub's recommended header
            "X-GitHub-Api-Version": "2022-11-28",
        }

        # Only add Authorization if a token exists
        # Without it, we're limited to 60 req/hour
        if token:
            self.headers["Authorization"] = f"Bearer {token}"

    def parse_url(self, url: str) -> tuple[str, str]:
        """
        Converts a GitHub URL into (owner, repo_name).
        Example: "https://github.com/tiangolo/fastapi" → ("tiangolo", "fastapi")
        """
        # Strip trailing slashes and split on "/"
        parts = url.strip("/").split("/")

        # A valid GitHub repo URL has at least 5 parts:
        # ["https:", "", "github.com", "owner", "repo"]
        if len(parts) < 5 or "github.com" not in parts:
            raise ValueError(f"Invalid GitHub URL: {url}")

        owner = parts[-2]
        repo = parts[-1]
        return owner, repo

    def fetch_repo(self, url: str) -> RepoData:
        """
        Main method: fetches all relevant data for a repository.
        Uses httpx (sync version) to make HTTP calls to GitHub API.
        """
        owner, repo = self.parse_url(url)

        # httpx.Client is the synchronous HTTP client
        # "with" ensures the connection is properly closed after
        with httpx.Client(headers=self.headers, follow_redirects=True) as client:

            # 1. Core repo metadata
            repo_response = client.get(f"{self.BASE_URL}/repos/{owner}/{repo}")
            repo_response.raise_for_status()  # raises exception if 4xx or 5xx
            repo_data = repo_response.json()

            # 2. All languages used in the repo
            lang_response = client.get(f"{self.BASE_URL}/repos/{owner}/{repo}/languages")
            lang_response.raise_for_status()
            languages = lang_response.json()

            # 3. Full file tree (recursive=1 means all subdirectories too)
            tree_response = client.get(
                f"{self.BASE_URL}/repos/{owner}/{repo}/git/trees/{repo_data['default_branch']}",
                params={"recursive": "1"},
            )
            tree_response.raise_for_status()
            tree_data = tree_response.json()

            # Extract only file paths (not directories) from the tree
            file_tree = [
                item["path"]
                for item in tree_data.get("tree", [])
                if item["type"] == "blob"  # "blob" = file, "tree" = directory
            ]

            # 4. README content (optional — not all repos have one)
            readme_content = None
            try:
                readme_response = client.get(
                    f"{self.BASE_URL}/repos/{owner}/{repo}/readme"
                )
                if readme_response.status_code == 200:
                    readme_data = readme_response.json()
                    # GitHub returns README content as base64-encoded string
                    readme_content = base64.b64decode(
                        readme_data["content"]
                    ).decode("utf-8")
            except Exception:
                pass  # README is optional — silently skip if missing

        # Build and return a validated Pydantic model
        return RepoData(
            owner=owner,
            name=repo_data["name"],
            full_name=repo_data["full_name"],
            description=repo_data.get("description"),
            stars=repo_data["stargazers_count"],
            forks=repo_data["forks_count"],
            language=repo_data.get("language"),
            languages=languages,
            topics=repo_data.get("topics", []),
            default_branch=repo_data["default_branch"],
            file_tree=file_tree,
            readme=readme_content,
        )