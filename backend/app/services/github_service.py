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

    # ─── PR Methods ───────────────────────────────────────────────────────────

    def parse_pr_url(self, url: str) -> tuple[str, str, int]:
        """
        Converts a GitHub PR URL into (owner, repo, pr_number).

        Example:
        "https://github.com/tiangolo/fastapi/pull/1234"
        → ("tiangolo", "fastapi", 1234)
        """
        parts = url.strip("/").split("/")

        # Valid PR URL has format:
        # https://github.com/{owner}/{repo}/pull/{number}
        # parts: ["https:", "", "github.com", owner, repo, "pull", number]
        if len(parts) < 7 or "github.com" not in parts or "pull" not in parts:
            raise ValueError(f"Invalid GitHub PR URL: {url}")

        pull_index = parts.index("pull")
        owner = parts[pull_index - 2]
        repo = parts[pull_index - 1]

        try:
            pr_number = int(parts[pull_index + 1])
        except (IndexError, ValueError):
            raise ValueError(f"Could not extract PR number from URL: {url}")

        return owner, repo, pr_number

    def fetch_pr(self, url: str):
        """
        Main method: fetches all PR data and returns a PRContext.

        Makes 3 GitHub API calls:
        1. PR metadata (title, description, branches, author)
        2. Changed files (filenames, diffs, additions, deletions)
        3. Commits (sha, message, author, date)
        """
        # Import here to avoid circular imports
        from app.models.pr import PRContext, ChangedFile, PRCommit

        owner, repo, pr_number = self.parse_pr_url(url)

        print(f"🔍 PR Ingestion: Fetching PR #{pr_number} from {owner}/{repo}...")

        with httpx.Client(headers=self.headers, follow_redirects=True) as client:

            # ── 1. PR Metadata ─────────────────────────────────────
            pr_response = client.get(
                f"{self.BASE_URL}/repos/{owner}/{repo}/pulls/{pr_number}"
            )
            pr_response.raise_for_status()
            pr_data = pr_response.json()

            # ── 2. Changed Files ───────────────────────────────────
            # GitHub paginates this — we fetch up to 100 files
            # (GitHub's max per page for this endpoint)
            files_response = client.get(
                f"{self.BASE_URL}/repos/{owner}/{repo}/pulls/{pr_number}/files",
                params={"per_page": 100}
            )
            files_response.raise_for_status()
            files_data = files_response.json()

            # ── 3. Commits ─────────────────────────────────────────
            commits_response = client.get(
                f"{self.BASE_URL}/repos/{owner}/{repo}/pulls/{pr_number}/commits",
                params={"per_page": 100}
            )
            commits_response.raise_for_status()
            commits_data = commits_response.json()

        # ── Parse Changed Files ────────────────────────────────────
        changed_files = []
        for f in files_data:
            changed_files.append(ChangedFile(
                filename=f.get("filename", ""),
                status=f.get("status", "modified"),
                additions=f.get("additions", 0),
                deletions=f.get("deletions", 0),
                changes=f.get("changes", 0),
                # patch is the actual diff — may be None for binary/large files
                patch=f.get("patch"),
            ))

                # ── Parse Commits ──────────────────────────────────────────
        commits = []
        for c in commits_data:
            commit_data = c.get("commit") or {}
            author_data = commit_data.get("author") or {}
            commits.append(PRCommit(
                sha=c.get("sha", "")[:7],
                message=commit_data.get("message", "").split("\n")[0],
                author=author_data.get("name", "Unknown"),
                date=author_data.get("date", ""),
            ))

        # ── Parse Labels ───────────────────────────────────────────
        labels = [label.get("name", "") for label in pr_data.get("labels", [])]

        # ── Build PRContext ────────────────────────────────────────
        pr_context = PRContext(
            owner=owner,
            repo=repo,
            pr_number=pr_number,
            url=url,
            title=pr_data.get("title", ""),
            description=pr_data.get("body"),
            author=pr_data.get("user", {}).get("login", "Unknown"),
            state=pr_data.get("state", "open"),
            base_branch=pr_data.get("base", {}).get("ref", "main"),
            head_branch=pr_data.get("head", {}).get("ref", ""),
            created_at=pr_data.get("created_at", ""),
            updated_at=pr_data.get("updated_at", ""),
            changed_files=changed_files,
            commits=commits,
            total_additions=pr_data.get("additions", 0),
            total_deletions=pr_data.get("deletions", 0),
            total_files_changed=pr_data.get("changed_files", 0),
            labels=labels,
        )

        print(f"PR Ingestion: '{pr_context.title}'")
        print(f"   Files: {pr_context.total_files_changed} | "
              f"+{pr_context.total_additions} / -{pr_context.total_deletions}")
        print(f"   Commits: {len(pr_context.commits)}")

        return pr_context