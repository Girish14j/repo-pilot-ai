import httpx
import os
import base64
from dotenv import load_dotenv

load_dotenv()

# Files we should always try to fetch first
# These tell us the most about code quality
PRIORITY_PATTERNS = [
    # Entry points
    "main.py", "app.py", "server.py", "index.py",
    "index.js", "index.ts", "server.js", "server.ts",
    "main.js", "main.ts",

    # Config files
    "settings.py", "config.py", "config.js", "config.ts",

    # Common important folders
    "routes", "routers", "controllers",
    "services", "handlers", "core",
    "models", "schemas", "entities",
    "middleware", "utils", "helpers",
]

# Files we should never fetch — binary, generated, or irrelevant
SKIP_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico",
    ".pdf", ".zip", ".tar", ".gz",
    ".pyc", ".pyo", ".pyd",
    ".lock", ".sum",
    ".min.js", ".min.css",
    ".map",
}

SKIP_FOLDERS = {
    "node_modules", ".git", "venv", ".venv",
    "__pycache__", ".next", "dist", "build",
    ".pytest_cache", "coverage",
}

# Token budget — total characters of code we'll send to LLM
MAX_TOTAL_CHARS = 12000
MAX_FILE_CHARS = 2000   # max chars per file
MAX_FILES = 10           # max number of files to fetch


class CodeFetcher:
    """
    Fetches actual source code from GitHub repositories.
    Uses smart prioritization to stay within LLM token limits.
    """

    def __init__(self):
        token = os.getenv("GITHUB_TOKEN")
        self.headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if token:
            self.headers["Authorization"] = f"Bearer {token}"

    def should_skip(self, path: str) -> bool:
        """
        Returns True if we should skip this file.
        Checks extension and folder name.
        """
        # Check if any skip folder is in the path
        parts = path.lower().split("/")
        for part in parts:
            if part in SKIP_FOLDERS:
                return True

        # Check extension
        for ext in SKIP_EXTENSIONS:
            if path.lower().endswith(ext):
                return True

        return False

    def priority_score(self, path: str) -> int:
        """
        Returns a priority score for a file.
        Higher score = fetch this file first.
        """
        path_lower = path.lower()
        score = 0

        for pattern in PRIORITY_PATTERNS:
            if pattern in path_lower:
                score += 10

        # Prefer files closer to root (shorter path = more important)
        depth = path.count("/")
        score -= depth

        # Prefer Python and JavaScript files
        if path.endswith((".py", ".ts", ".js", ".tsx", ".jsx")):
            score += 5

        return score

    def fetch_file_content(
        self,
        client: httpx.Client,
        owner: str,
        repo: str,
        path: str
    ) -> str | None:
        """
        Fetches and decodes a single file's content.
        Returns None if fetch fails.
        """
        try:
            response = client.get(
                f"https://api.github.com/repos/{owner}/{repo}/contents/{path}",
                follow_redirects=True,
            )

            if response.status_code != 200:
                return None

            data = response.json()

            # Skip files that are too large (GitHub won't return content)
            if data.get("size", 0) > 100000:  # 100KB limit
                return None

            content_b64 = data.get("content", "")
            if not content_b64:
                return None

            # Decode base64 content
            decoded = base64.b64decode(content_b64).decode("utf-8", errors="ignore")

            # Truncate to max file chars
            if len(decoded) > MAX_FILE_CHARS:
                decoded = decoded[:MAX_FILE_CHARS] + f"\n... (truncated, {len(decoded)} total chars)"

            return decoded

        except Exception:
            return None

    def fetch_important_files(
        self,
        owner: str,
        repo: str,
        file_tree: list[str]
    ) -> dict[str, str]:
        """
        Main method: fetches the most important source files.

        Returns a dict of {file_path: file_content}
        """
        # Filter out files we should skip
        candidates = [
            path for path in file_tree
            if not self.should_skip(path)
        ]

        # Sort by priority score — highest first
        candidates.sort(key=self.priority_score, reverse=True)

        # Take top candidates
        top_candidates = candidates[:30]  # consider top 30, fetch up to MAX_FILES

        fetched = {}
        total_chars = 0

        with httpx.Client(headers=self.headers, follow_redirects=True) as client:
            for path in top_candidates:
                # Stop if we've hit our limits
                if len(fetched) >= MAX_FILES:
                    break
                if total_chars >= MAX_TOTAL_CHARS:
                    break

                content = self.fetch_file_content(client, owner, repo, path)

                if content:
                    fetched[path] = content
                    total_chars += len(content)
                    print(f"  [Fetched] {path} ({len(content)} chars)")

        print(f"  [Code Fetcher] {len(fetched)} files, {total_chars} total chars")
        return fetched