"""
Pure Python diff analyzer.
No LLM. No external dependencies beyond standard library.

Reads the raw GitHub patch format and produces structured
FileDiffAnalysis objects that AI agents can reason about.
"""

import re
from app.models.pr import (
    PRContext,
    ChangedFile,
    FileDiffAnalysis,
    PRDiffAnalysis,
)

# ─── Risk Classification Rules ────────────────────────────────────────────────
# Maps filename patterns and code keywords to risk areas
# This is deterministic — no LLM guessing needed here

FILE_RISK_RULES = {
    "security": [
        "auth", "login", "logout", "password", "token", "jwt",
        "session", "oauth", "permission", "role", "credential",
        "secret", "encrypt", "decrypt", "hash", "signature",
        "middleware", "guard", "acl",
    ],
    "database": [
        "model", "schema", "migration", "query", "repository",
        "dao", "db", "database", "sql", "orm", "entity",
        "seed", "fixture",
    ],
    "api": [
        "router", "route", "endpoint", "controller", "view",
        "handler", "api", "rest", "graphql", "webhook",
    ],
    "configuration": [
        "config", "setting", "env", "environment", "constant",
        ".env", "docker", "compose", "nginx", "gunicorn",
    ],
    "payment": [
        "payment", "billing", "invoice", "stripe", "paypal",
        "transaction", "checkout", "subscription",
    ],
    "infrastructure": [
        "deploy", "ci", "cd", "workflow", "action", "pipeline",
        "dockerfile", "kubernetes", "terraform", "ansible",
    ],
}

CODE_RISK_RULES = {
    "security": [
        "password", "token", "secret", "api_key", "apikey",
        "authenticate", "authorize", "permission", "role",
        "sql", "query", "execute", "eval", "exec",
        "subprocess", "os.system", "shell",
        "pickle", "deserializ",
    ],
    "database": [
        "select", "insert", "update", "delete", "drop", "create table",
        "db.", "cursor.", "session.", ".query(", ".filter(",
        "migrate", "transaction",
    ],
    "authentication": [
        "login", "logout", "signin", "signup", "register",
        "jwt", "bearer", "oauth", "session", "cookie",
        "password", "hash", "verify",
    ],
    "network": [
        "request", "response", "fetch", "axios", "httpx",
        "socket", "websocket", "cors", "headers",
    ],
}

# Files that indicate test coverage
TEST_PATTERNS = [
    "test_", "_test", ".test.", ".spec.",
    "/tests/", "/test/", "/__tests__/",
    "spec.py", "spec.js", "spec.ts",
]

# Files that are configuration
CONFIG_PATTERNS = [
    ".env", "config.", "settings.", "configuration.",
    "docker", "nginx", ".yaml", ".yml", ".toml",
    "makefile", "dockerfile",
]

# Dependency files
DEPENDENCY_PATTERNS = [
    "requirements", "package.json", "package-lock",
    "yarn.lock", "pipfile", "pyproject.toml",
    "gemfile", "cargo.toml", "go.mod",
]

# Risk level ordering for comparison
RISK_ORDER = {"critical": 4, "high": 3, "medium": 2, "low": 1}


class DiffAnalyzer:
    """
    Analyzes GitHub PR diffs and produces structured risk assessments.
    Pure Python — no LLM calls.
    """

    def analyze_pr(self, pr_context: PRContext) -> PRDiffAnalysis:
        """
        Main method: analyzes all changed files in a PR.
        Returns a complete PRDiffAnalysis.
        """
        print(f"🔎 Diff Analyzer: Analyzing {len(pr_context.changed_files)} files...")

        file_analyses = []
        added_files = []
        modified_files = []
        deleted_files = []
        all_risk_areas = set()
        highest_risk = "low"

        for changed_file in pr_context.changed_files:
            analysis = self._analyze_file(changed_file)
            file_analyses.append(analysis)

            # Categorize by status
            if changed_file.status == "added":
                added_files.append(changed_file.filename)
            elif changed_file.status == "deleted":
                deleted_files.append(changed_file.filename)
            else:
                modified_files.append(changed_file.filename)

            # Accumulate risk areas
            all_risk_areas.update(analysis.risk_areas)

            # Track highest risk level
            if RISK_ORDER.get(analysis.risk_level, 0) > RISK_ORDER.get(highest_risk, 0):
                highest_risk = analysis.risk_level

        risk_areas_list = sorted(all_risk_areas)

        # Build PR-level flags
        touches_auth = any(
            "authentication" in fa.risk_areas or "security" in fa.risk_areas
            for fa in file_analyses
        )
        touches_db = any("database" in fa.risk_areas for fa in file_analyses)
        touches_security = any("security" in fa.risk_areas for fa in file_analyses)
        touches_tests = any(fa.is_test_file for fa in file_analyses)
        touches_deps = any(fa.is_dependency_file for fa in file_analyses)
        touches_config = any(fa.is_config_file for fa in file_analyses)

        # Build human readable summary
        summary = self._build_summary(
            pr_context=pr_context,
            added_files=added_files,
            modified_files=modified_files,
            deleted_files=deleted_files,
            risk_areas=risk_areas_list,
            highest_risk=highest_risk,
        )

        print(f"✅ Diff Analyzer: Risk level = {highest_risk.upper()}")
        print(f"   Risk areas: {', '.join(risk_areas_list) or 'none detected'}")
        print(f"   Files: +{len(added_files)} added, "
              f"~{len(modified_files)} modified, "
              f"-{len(deleted_files)} deleted")

        return PRDiffAnalysis(
            pr_number=pr_context.pr_number,
            total_files=len(pr_context.changed_files),
            added_files=added_files,
            modified_files=modified_files,
            deleted_files=deleted_files,
            file_analyses=file_analyses,
            overall_risk_level=highest_risk,
            risk_areas_touched=risk_areas_list,
            touches_authentication=touches_auth,
            touches_database=touches_db,
            touches_security=touches_security,
            touches_tests=touches_tests,
            touches_dependencies=touches_deps,
            touches_config=touches_config,
            change_summary=summary,
        )

    def _analyze_file(self, changed_file: ChangedFile) -> FileDiffAnalysis:
        """
        Analyzes a single changed file.
        Extracts added/removed lines, symbols, and risk areas.
        """
        filename = changed_file.filename
        filename_lower = filename.lower()
        patch = changed_file.patch or ""

        # ── Extract added and removed lines from patch ─────────────
        added_lines = []
        removed_lines = []

        for line in patch.split("\n"):
            if line.startswith("+") and not line.startswith("+++"):
                # Added line — strip the leading + and whitespace
                added_lines.append(line[1:].strip())
            elif line.startswith("-") and not line.startswith("---"):
                # Removed line — strip the leading - and whitespace
                removed_lines.append(line[1:].strip())

        # Filter empty lines
        added_lines = [l for l in added_lines if l]
        removed_lines = [l for l in removed_lines if l]

        # ── Extract symbol names from @@ ... @@ context ────────────
        # The @@ line often includes the function/class name:
        # "@@ -23,6 +23,8 @@ def login(username, password):"
        symbols_changed = self._extract_symbols(patch)

        # ── Classify file type ─────────────────────────────────────
        is_test = any(p in filename_lower for p in TEST_PATTERNS)
        is_config = any(p in filename_lower for p in CONFIG_PATTERNS)
        is_dependency = any(p in filename_lower for p in DEPENDENCY_PATTERNS)

        # ── Detect risk areas ──────────────────────────────────────
        risk_areas = self._detect_risk_areas(
            filename_lower=filename_lower,
            added_lines=added_lines,
            removed_lines=removed_lines,
        )

        # ── Calculate risk level ───────────────────────────────────
        risk_level = self._calculate_risk_level(
            risk_areas=risk_areas,
            is_config=is_config,
            is_dependency=is_dependency,
            additions=changed_file.additions,
            deletions=changed_file.deletions,
            status=changed_file.status,
        )

        return FileDiffAnalysis(
            filename=filename,
            status=changed_file.status,
            added_lines=added_lines[:50],    # cap at 50 lines to avoid huge objects
            removed_lines=removed_lines[:50],
            symbols_changed=symbols_changed,
            risk_areas=sorted(risk_areas),
            risk_level=risk_level,
            is_test_file=is_test,
            is_config_file=is_config,
            is_dependency_file=is_dependency,
            additions=changed_file.additions,
            deletions=changed_file.deletions,
        )

    def _extract_symbols(self, patch: str) -> list[str]:
        """
        Extracts function/class names from the @@ context in a patch.

        Git includes the enclosing function/class name in the @@ line:
        "@@ -23,6 +23,8 @@ def login(username, password):"
                                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^
        We extract that part.
        """
        symbols = []

        # Match the @@ line and capture everything after the second @@
        # Pattern: @@ -num,num +num,num @@ optional_symbol
        pattern = r"@@[^@]+@@\s*(.+)"

        for match in re.finditer(pattern, patch):
            context = match.group(1).strip()
            if context:
                # Extract just the function/class name
                # "def login(username, password):" → "login"
                # "class UserService:" → "UserService"
                name_match = re.search(
                    r"(?:def|class|function|async def|const|let|var)\s+(\w+)",
                    context
                )
                if name_match:
                    symbols.append(name_match.group(1))
                elif len(context) < 60:
                    # Short enough to include as-is
                    symbols.append(context)

        return list(set(symbols))  # deduplicate

    def _detect_risk_areas(
        self,
        filename_lower: str,
        added_lines: list[str],
        removed_lines: list[str],
    ) -> list[str]:
        """
        Detects risk areas based on:
        1. Filename patterns (fast, deterministic)
        2. Code content patterns (what was added/removed)
        """
        detected = set()

        # Check filename against risk rules
        for risk_area, keywords in FILE_RISK_RULES.items():
            if any(kw in filename_lower for kw in keywords):
                detected.add(risk_area)

        # Check code content against risk rules
        all_changed_code = " ".join(added_lines + removed_lines).lower()
        for risk_area, keywords in CODE_RISK_RULES.items():
            if any(kw in all_changed_code for kw in keywords):
                detected.add(risk_area)

        return list(detected)

    def _calculate_risk_level(
        self,
        risk_areas: list[str],
        is_config: bool,
        is_dependency: bool,
        additions: int,
        deletions: int,
        status: str,
    ) -> str:
        """
        Calculates overall risk level for a single file.

        Rules (in priority order):
        - Security + auth changes → high
        - Config or dependency changes → high
        - Database changes → medium
        - Large deletions → medium (deletions are risky)
        - Small additions only → low
        """
        # Critical: security + auth together
        if "security" in risk_areas and "authentication" in risk_areas:
            return "critical"

        # High: security, auth, config, or dependencies
        if (
            "security" in risk_areas
            or "authentication" in risk_areas
            or is_config
            or is_dependency
        ):
            return "high"

        # High: large changes to database or payment code
        if "database" in risk_areas or "payment" in risk_areas:
            if additions + deletions > 20:
                return "high"
            return "medium"

        # Medium: any risk area detected
        if risk_areas:
            return "medium"

        # Medium: large deletions (removing code is risky)
        if deletions > 30:
            return "medium"

        # Low: everything else
        return "low"

    def _build_summary(
        self,
        pr_context: PRContext,
        added_files: list[str],
        modified_files: list[str],
        deleted_files: list[str],
        risk_areas: list[str],
        highest_risk: str,
    ) -> str:
        """
        Builds a human-readable summary of the PR changes.
        Used in the final report and as context for AI agents.
        """
        parts = []

        parts.append(
            f"PR #{pr_context.pr_number} '{pr_context.title}' "
            f"by {pr_context.author} — "
            f"{pr_context.head_branch} → {pr_context.base_branch}"
        )

        change_parts = []
        if added_files:
            change_parts.append(f"{len(added_files)} file(s) added")
        if modified_files:
            change_parts.append(f"{len(modified_files)} file(s) modified")
        if deleted_files:
            change_parts.append(f"{len(deleted_files)} file(s) deleted")

        if change_parts:
            parts.append("Changes: " + ", ".join(change_parts))

        parts.append(
            f"Total: +{pr_context.total_additions} additions, "
            f"-{pr_context.total_deletions} deletions"
        )

        if risk_areas:
            parts.append(f"Risk areas: {', '.join(risk_areas)}")

        parts.append(f"Overall risk level: {highest_risk.upper()}")

        return " | ".join(parts)
