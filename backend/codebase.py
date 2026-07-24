"""
============================================================
ORZYN AI m2.0
Codebase Intelligence Engine
============================================================

Purpose
-------
Build a deterministic representation of a GitHub repository.

This module performs no AI inference.

It discovers repository metadata, determines the technology
stack, extracts representative source files, gathers project
statistics, and produces a deterministic Codebase object for
downstream analyzers.

Author
------
Kenny Richardson

Project
-------
Orzyn AI m2.0
"""

from __future__ import annotations

import base64
import json
import re

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from enum import Enum
from pathlib import PurePosixPath
from typing import Final

import requests

try:
    import tomllib
except ModuleNotFoundError:
    tomllib = None

from backend.config import GITHUB_HEADERS
from backend.orzyn import get_active_repository
from backend.repository import RepositoryProfile
from backend.commits import CommitProfile
from backend.pull_requests import PullRequestProfile
from backend.issues import IssueProfile
from backend.developer import DeveloperProfile
from backend.repository import (
    RepositoryProfile,
    fetch_repository_profile,
)

from backend.commits import (
    CommitProfile,
    fetch_commits,
)

from backend.pull_requests import (
    PullRequestProfile,
    fetch_pull_requests,
)

from backend.issues import (
    IssueProfile,
    fetch_issues,
)

from backend.developer import (
    DeveloperProfile,
    fetch_developers,
)

# ============================================================
# GitHub REST
# ============================================================

GITHUB_API: Final = "https://api.github.com"

REPOSITORY_ENDPOINT: Final = (
    GITHUB_API +
    "/repos/{owner}/{repo}"
)

TREE_ENDPOINT: Final = (
    GITHUB_API +
    "/repos/{owner}/{repo}/git/trees/{tree}?recursive=1"
)

BLOB_ENDPOINT: Final = (
    GITHUB_API +
    "/repos/{owner}/{repo}/git/blobs/{sha}"
)


SESSION = requests.Session()

SESSION.headers.update(
    GITHUB_HEADERS
)


# ============================================================
# Limits
# ============================================================

MAX_FILE_SIZE: Final = 250_000

MAX_SELECTED_FILES: Final = 12

MAX_BLOB_CACHE: Final = 1024

MAX_IMPORT_SCAN_LINES: Final = 400


# ============================================================
# Repository Types
# ============================================================

class RepositoryType(Enum):

    UNKNOWN = "Unknown"

    PYTHON = "Python"

    FASTAPI = "FastAPI"

    DJANGO = "Django"

    FLASK = "Flask"

    NODE = "Node.js"

    REACT = "React"

    NEXTJS = "Next.js"

    VUE = "Vue"

    ANGULAR = "Angular"

    JAVA = "Java"

    SPRING = "Spring Boot"

    DOTNET = ".NET"

    GO = "Go"

    RUST = "Rust"

    FLUTTER = "Flutter"


# ============================================================
# Dataclasses
# ============================================================

@dataclass(
    slots=True,
    frozen=True,
)
class RepositoryMetadata:

    owner: str

    name: str

    description: str | None

    homepage: str | None

    default_branch: str

    language: str | None

    stars: int

    forks: int


@dataclass(
    slots=True,
    frozen=True,
)
class TreeEntry:

    path: str

    sha: str

    size: int


@dataclass(
    slots=True,
)
class ManifestFiles:

    package_json: str | None = None

    pyproject: str | None = None

    requirements: str | None = None

    cargo: str | None = None

    go_mod: str | None = None

    pom: str | None = None

    gradle: str | None = None

    flutter: str | None = None


@dataclass(
    slots=True,
    frozen=True,
)
class SourceFile:

    path: str

    sha: str

    size: int

    language: str

    priority: float

    imports: tuple[str, ...]

    content: str


@dataclass(
    slots=True,
)
class ProjectStatistics:

    total_files: int = 0

    supported_files: int = 0

    ignored_files: int = 0

    language_distribution: dict[str, int] = field(
        default_factory=dict
    )


@dataclass(
    slots=True,
)
class Codebase:

    metadata: RepositoryMetadata

    repository_type: RepositoryType

    framework: str

    primary_language: str |None

    manifests: ManifestFiles

    statistics: ProjectStatistics

    repository: RepositoryProfile

    commits: list[CommitProfile] = field(default_factory=list)

    pull_requests: list[PullRequestProfile] = field(default_factory=list)

    issues: list[IssueProfile] = field(default_factory=list)

    developers: list[DeveloperProfile] = field(default_factory=list)

    files: list[SourceFile] = field(default_factory=list)


# ============================================================
# Cache
# ============================================================

_BLOB_CACHE: dict[str, str] = {}


# ============================================================
# Supported Languages
# ============================================================

LANGUAGE_MAP: Final = {

    ".py": "Python",

    ".ts": "TypeScript",

    ".tsx": "TypeScript",

    ".js": "JavaScript",

    ".jsx": "JavaScript",

    ".java": "Java",

    ".go": "Go",

    ".rs": "Rust",

    ".cs": "C#",

    ".cpp": "C++",

    ".c": "C",

    ".kt": "Kotlin",

    ".php": "PHP",

    ".rb": "Ruby",

    ".swift": "Swift",

    ".scala": "Scala",

    ".html": "HTML",

    ".css": "CSS",

    ".scss": "SCSS",

    ".sql": "SQL",

    ".json": "JSON",

    ".yaml": "YAML",

    ".yml": "YAML",

    ".xml": "XML",

    ".toml": "TOML",

    ".md": "Markdown",

}


TEXT_EXTENSIONS: Final = set(
    LANGUAGE_MAP
)


IGNORED_DIRECTORIES: Final = {

    ".git",

    ".github",

    ".idea",

    ".vscode",

    ".venv",

    "venv",

    "__pycache__",

    "node_modules",

    "build",

    "dist",

    ".next",

    ".cache",

    ".pytest_cache",

    ".mypy_cache",

}


ENTRY_POINTS: Final = {

    "main.py",

    "app.py",

    "manage.py",

    "Program.cs",

    "App.tsx",

    "App.jsx",

    "main.ts",

    "main.tsx",

    "main.js",

    "main.jsx",

    "index.ts",

    "index.tsx",

    "index.js",

    "index.jsx",

}


MANIFESTS: Final = {

    "package.json",

    "pyproject.toml",

    "requirements.txt",

    "Cargo.toml",

    "go.mod",

    "pom.xml",

    "build.gradle",

    "pubspec.yaml",

}


# ============================================================
# HTTP
# ============================================================

def github_get(
    url: str,
) -> dict:

    response = SESSION.get(
        url,
        timeout=30,
    )

    if response.status_code == 401:
        raise RuntimeError(
            "GitHub authentication failed."
        )

    if response.status_code == 403:
        raise RuntimeError(
            "GitHub API rate limit exceeded."
        )

    if response.status_code == 404:
        raise RuntimeError(
            "GitHub resource not found."
        )

    response.raise_for_status()

    return response.json()


# ============================================================
# Path Helpers
# ============================================================

def extension(
    path: str,
) -> str:

    return PurePosixPath(
        path
    ).suffix.lower()


def filename(
    path: str,
) -> str:

    return PurePosixPath(
        path
    ).name


def language_of(
    path: str,
) -> str:

    return LANGUAGE_MAP.get(
        extension(path),
        "Unknown",
    )


def inside_ignored_directory(
    path: str,
) -> bool:

    return any(

        part in IGNORED_DIRECTORIES

        for part in PurePosixPath(
            path
        ).parts

    )


def supported_file(
    path: str,
    size: int,
) -> bool:

    if size <= 0:
        return False

    if size > MAX_FILE_SIZE:
        return False

    if inside_ignored_directory(
        path,
    ):
        return False

    return extension(
        path
    ) in TEXT_EXTENSIONS


# ============================================================
# Repository Discovery
# ============================================================

def fetch_repository_metadata(
) -> RepositoryMetadata:

    repository = get_active_repository()

    payload = github_get(

        REPOSITORY_ENDPOINT.format(

            owner=repository.owner,

            repo=repository.repository,

        )

    )

    return RepositoryMetadata(

        owner=payload["owner"]["login"],

        name=payload["name"],

        description=payload.get(
            "description",
        ),

        homepage=payload.get(
            "homepage",
        ),

        default_branch=payload["default_branch"],

        language=payload.get(
            "language",
        ),

        stars=payload.get(
            "stargazers_count",
            0,
        ),

        forks=payload.get(
            "forks_count",
            0,
        ),

    )

# ============================================================
# Repository Tree
# ============================================================

def fetch_repository_tree(
    metadata: RepositoryMetadata,
) -> list[TreeEntry]:

    payload = github_get(

        TREE_ENDPOINT.format(

            owner=metadata.owner,

            repo=metadata.name,

            tree=metadata.default_branch,

        )

    )

    entries: list[TreeEntry] = []

    for node in payload.get(
        "tree",
        [],
    ):

        if node.get("type") != "blob":
            continue

        entries.append(

            TreeEntry(

                path=node["path"],

                sha=node["sha"],

                size=node.get(
                    "size",
                    0,
                ),

            )

        )

    return entries


# ============================================================
# Blob Retrieval
# ============================================================

def fetch_blob(
    metadata: RepositoryMetadata,
    sha: str,
) -> str:

    cached = _BLOB_CACHE.get(
        sha,
    )

    if cached is not None:
        return cached

    payload = github_get(

        BLOB_ENDPOINT.format(

            owner=metadata.owner,

            repo=metadata.name,

            sha=sha,

        )

    )

    if payload.get(
        "encoding",
    ) != "base64":

        return ""

    decoded = base64.b64decode(

        payload.get(
            "content",
            "",
        )

    ).decode(

        "utf-8",

        errors="replace",

    )

    if len(
        _BLOB_CACHE
    ) < MAX_BLOB_CACHE:

        _BLOB_CACHE[
            sha
        ] = decoded

    return decoded


# ============================================================
# Manifest Discovery
# ============================================================

def discover_manifests(
    tree: list[TreeEntry],
) -> ManifestFiles:

    manifests = ManifestFiles()

    for entry in tree:

        name = filename(
            entry.path
        )

        if name == "package.json":

            manifests.package_json = entry.path

        elif name == "pyproject.toml":

            manifests.pyproject = entry.path

        elif name == "requirements.txt":

            manifests.requirements = entry.path

        elif name == "Cargo.toml":

            manifests.cargo = entry.path

        elif name == "go.mod":

            manifests.go_mod = entry.path

        elif name == "pom.xml":

            manifests.pom = entry.path

        elif name == "build.gradle":

            manifests.gradle = entry.path

        elif name == "pubspec.yaml":

            manifests.flutter = entry.path

    return manifests


def load_manifest(
    metadata: RepositoryMetadata,
    tree: list[TreeEntry],
    path: str | None,
) -> str:

    if path is None:
        return ""

    for entry in tree:

        if entry.path != path:
            continue

        return fetch_blob(

            metadata,

            entry.sha,

        )

    return ""


# ============================================================
# Manifest Parsers
# ============================================================

def parse_package_json(
    content: str,
) -> set[str]:

    if not content.strip():

        return set()

    try:

        package = json.loads(
            content
        )

    except json.JSONDecodeError:

        return set()

    dependencies: set[str] = set()

    for section in (

        "dependencies",

        "devDependencies",

        "peerDependencies",

        "optionalDependencies",

    ):

        values = package.get(
            section,
            {},
        )

        if not isinstance(
            values,
            dict,
        ):
            continue

        dependencies.update(

            dependency.lower()

            for dependency in values

        )

    return dependencies


def parse_requirements(
    content: str,
) -> set[str]:

    libraries: set[str] = set()

    for line in content.splitlines():

        line = line.strip()

        if not line:
            continue

        if line.startswith("#"):
            continue

        line = re.split(

            r"[<>=~]",

            line,

            maxsplit=1,

        )[0].strip()

        if line:

            libraries.add(
                line.lower()
            )

    return libraries


def parse_pyproject(
    content: str,
) -> set[str]:

    if not content.strip():

        return set()

    if tomllib is None:

        return parse_requirements(
            content
        )

    try:

        document = tomllib.loads(
            content
        )

    except Exception:

        return set()

    dependencies: set[str] = set()

    project = document.get(
        "project",
        {},
    )

    for dependency in project.get(
        "dependencies",
        [],
    ):

        package = re.split(

            r"[<>=~ ]",

            dependency,

            maxsplit=1,

        )[0].strip()

        if package:

            dependencies.add(
                package.lower()
            )

    optional = project.get(
        "optional-dependencies",
        {},
    )

    for values in optional.values():

        for dependency in values:

            package = re.split(

                r"[<>=~ ]",

                dependency,

                maxsplit=1,

            )[0].strip()

            if package:

                dependencies.add(
                    package.lower()
                )

    return dependencies

# ============================================================
# Framework Detection
# ============================================================

def detect_framework(
    metadata: RepositoryMetadata,
    tree: list[TreeEntry],
    manifests: ManifestFiles,
) -> RepositoryType:

    package_dependencies = parse_package_json(

        load_manifest(

            metadata,

            tree,

            manifests.package_json,

        )

    )

    python_dependencies = (

        parse_pyproject(

            load_manifest(

                metadata,

                tree,

                manifests.pyproject,

            )

        )

        |

        parse_requirements(

            load_manifest(

                metadata,

                tree,

                manifests.requirements,

            )

        )

    )

    if manifests.pom:

        pom = load_manifest(

            metadata,

            tree,

            manifests.pom,

        ).lower()

        if (

            "spring-boot"

            in pom

        ):

            return RepositoryType.SPRING

        return RepositoryType.JAVA

    if manifests.gradle:

        gradle = load_manifest(

            metadata,

            tree,

            manifests.gradle,

        ).lower()

        if (

            "spring-boot"

            in gradle

        ):

            return RepositoryType.SPRING

        return RepositoryType.JAVA

    if manifests.flutter:

        return RepositoryType.FLUTTER

    if manifests.cargo:

        return RepositoryType.RUST

    if manifests.go_mod:

        return RepositoryType.GO

    if "next" in package_dependencies:

        return RepositoryType.NEXTJS

    if "react" in package_dependencies:

        return RepositoryType.REACT

    if "@angular/core" in package_dependencies:

        return RepositoryType.ANGULAR

    if "vue" in package_dependencies:

        return RepositoryType.VUE

    if package_dependencies:

        return RepositoryType.NODE

    if "fastapi" in python_dependencies:

        return RepositoryType.FASTAPI

    if "django" in python_dependencies:

        return RepositoryType.DJANGO

    if "flask" in python_dependencies:

        return RepositoryType.FLASK

    if manifests.pyproject:

        return RepositoryType.PYTHON

    if manifests.requirements:

        return RepositoryType.PYTHON

    language = metadata.language

    if language == "Python":

        return RepositoryType.PYTHON

    if language == "Java":

        return RepositoryType.JAVA

    if language == "Go":

        return RepositoryType.GO

    if language == "Rust":

        return RepositoryType.RUST

    return RepositoryType.UNKNOWN


# ============================================================
# Repository Statistics
# ============================================================

def build_statistics(
    tree: list[TreeEntry],
) -> ProjectStatistics:

    counter: Counter[str] = Counter()

    supported = 0

    ignored = 0

    for entry in tree:

        if supported_file(

            entry.path,

            entry.size,

        ):

            supported += 1

            language = language_of(

                entry.path,

            )

            if language != "Unknown":

                counter.update(

                    [language]

                )

        else:

            ignored += 1

    return ProjectStatistics(

        total_files=len(
            tree,
        ),

        supported_files=supported,

        ignored_files=ignored,

        language_distribution=dict(
            counter,
        ),

    )


def determine_primary_language(
    statistics: ProjectStatistics,
) -> str | None:

    if not statistics.language_distribution:

        return None

    return max(

        statistics.language_distribution,

        key=statistics.language_distribution.get,

    )


# ============================================================
# Import Extraction
# ============================================================

PYTHON_IMPORT = re.compile(

    r"^(?:from\s+([A-Za-z0-9_.]+)\s+import|import\s+([A-Za-z0-9_.]+))",

    re.MULTILINE,

)

JS_IMPORT = re.compile(

    r"""(?:import\s+.*?\s+from\s+['"]([^'"]+)['"]|require\(['"]([^'"]+)['"]\))""",

)

JAVA_IMPORT = re.compile(

    r"import\s+([A-Za-z0-9_.]+);",

)

GO_IMPORT = re.compile(

    r'"([^"]+)"',

)

RUST_IMPORT = re.compile(

    r"use\s+([A-Za-z0-9_:]+)",

)


def extract_imports(
    language: str,
    content: str,
) -> tuple[str, ...]:

    snippet = "\n".join(

        content.splitlines()[

            :MAX_IMPORT_SCAN_LINES

        ]

    )

    imports: set[str] = set()

    if language == "Python":

        for left, right in PYTHON_IMPORT.findall(
            snippet,
        ):

            imports.add(
                left or right
            )

    elif language in {

        "JavaScript",

        "TypeScript",

    }:

        for left, right in JS_IMPORT.findall(
            snippet,
        ):

            imports.add(
                left or right
            )

    elif language == "Java":

        imports.update(

            JAVA_IMPORT.findall(
                snippet,
            )

        )

    elif language == "Go":

        imports.update(

            GO_IMPORT.findall(
                snippet,
            )

        )

    elif language == "Rust":

        imports.update(

            RUST_IMPORT.findall(
                snippet,
            )

        )

    return tuple(

        sorted(
            imports
        )

    )

# ============================================================
# File Classification
# ============================================================

CATEGORY_WEIGHTS: Final = {

    "manifest": 1000,

    "readme": 950,

    "entry": 900,

    "configuration": 850,

    "routing": 825,

    "core": 800,

    "source": 700,

    "test": 250,

    "documentation": 150,

    "other": 100,

}


def classify_file(
    path: str,
) -> str:

    name = filename(
        path
    )

    lower = path.lower()

    if name in MANIFESTS:

        return "manifest"

    if name == "README.md":

        return "readme"

    if name in ENTRY_POINTS:

        return "entry"

    if any(

        keyword in lower

        for keyword in (

            "config",

            "settings",

            ".env",

            "vite.config",

            "next.config",

            "webpack",

            "tailwind.config",

            "tsconfig",

        )

    ):

        return "configuration"

    if any(

        keyword in lower

        for keyword in (

            "router",

            "routes",

            "urls.py",

        )

    ):

        return "routing"

    if "/src/" in lower:

        return "source"

    if "/core/" in lower:

        return "core"

    if "/test/" in lower:

        return "test"

    if "/tests/" in lower:

        return "test"

    if extension(
        path
    ) == ".md":

        return "documentation"

    return "other"


# ============================================================
# File Priority
# ============================================================

def file_priority(
    entry: TreeEntry,
) -> float:

    score = float(

        CATEGORY_WEIGHTS.get(

            classify_file(
                entry.path,
            ),

            0,

        )

    )

    language = language_of(
        entry.path
    )

    if language in {

        "Python",

        "TypeScript",

        "JavaScript",

        "Java",

        "Go",

        "Rust",

        "C#",

    }:

        score += 35

    score += min(

        entry.size / 512,

        60,

    )

    depth = len(

        PurePosixPath(
            entry.path
        ).parts

    )

    score -= depth * 2

    return score


# ============================================================
# Source File Builder
# ============================================================

def build_source_file(
    metadata: RepositoryMetadata,
    entry: TreeEntry,
) -> SourceFile:

    content = fetch_blob(

        metadata,

        entry.sha,

    )

    language = language_of(
        entry.path
    )

    return SourceFile(

        path=entry.path,

        sha=entry.sha,

        size=entry.size,

        language=language,

        priority=file_priority(
            entry,
        ),

        imports=extract_imports(

            language,

            content,

        ),

        content=content,

    )


# ============================================================
# Candidate Discovery
# ============================================================

def candidate_files(
    tree: list[TreeEntry],
) -> list[TreeEntry]:

    return [

        entry

        for entry in tree

        if supported_file(

            entry.path,

            entry.size,

        )

    ]


def ranked_candidates(
    tree: list[TreeEntry],
) -> list[TreeEntry]:

    return sorted(

        candidate_files(
            tree,
        ),

        key=file_priority,

        reverse=True,

    )


# ============================================================
# Representative Selection
# ============================================================

def select_representative_files(
    metadata: RepositoryMetadata,
    tree: list[TreeEntry],
) -> list[SourceFile]:

    ranked = ranked_candidates(
        tree
    )

    selected: list[SourceFile] = []

    used_categories: set[str] = set()

    used_paths: set[str] = set()

    for entry in ranked:

        category = classify_file(
            entry.path
        )

        if category in used_categories:

            continue

        selected.append(

            build_source_file(

                metadata,

                entry,

            )

        )

        used_categories.add(
            category
        )

        used_paths.add(
            entry.path
        )

        if len(
            selected
        ) >= MAX_SELECTED_FILES:

            return selected

    for entry in ranked:

        if entry.path in used_paths:

            continue

        selected.append(

            build_source_file(

                metadata,

                entry,

            )

        )

        if len(
            selected
        ) >= MAX_SELECTED_FILES:

            break

    return selected


# ============================================================
# Dependency Graph
# ============================================================

def build_dependency_graph(
    files: list[SourceFile],
) -> dict[str, tuple[str, ...]]:

    graph: dict[
        str,
        tuple[str, ...],
    ] = {}

    for source in files:

        graph[
            source.path
        ] = source.imports

    return graph


# ============================================================
# Project Summary
# ============================================================

def summarize_repository(
    files: list[SourceFile],
) -> dict[str, int]:

    summary: defaultdict[
        str,
        int,
    ] = defaultdict(int)

    for source in files:

        summary[
            source.language
        ] += 1

    return dict(
        summary
    )

# ============================================================
# Codebase Builder
# ============================================================

def build_codebase() -> Codebase:

    metadata = fetch_repository_metadata()

    tree = fetch_repository_tree(
        metadata,
    )

    manifests = discover_manifests(
        tree,
    )

    repository_type = detect_framework(

        metadata,

        tree,

        manifests,

    )

    statistics = build_statistics(
        tree,
    )

    primary_language = determine_primary_language(
        statistics,
    )

    files = select_representative_files(

        metadata,

        tree,

    )

    repository = fetch_repository_profile()

    commits = fetch_commits()

    pull_requests = fetch_pull_requests()

    issues = fetch_issues()

    developers = fetch_developers()

    return Codebase(

        metadata=metadata,

        repository_type=repository_type,

        framework=repository_type.value,
    
        primary_language=primary_language,

        manifests=manifests,

        statistics=statistics,

        repository=repository,

        commits=commits,

        pull_requests=pull_requests,

        issues=issues,

        developers=developers,

        files=files,

)


# ============================================================
# Public API
# ============================================================

def fetch_codebase() -> Codebase:

    """
    Build a deterministic representation of the
    active GitHub repository.

    No AI inference is performed here.

    Every analyzer receives the exact same
    repository representation.
    """

    return build_codebase()


# ============================================================
# Utility Functions
# ============================================================

def repository_languages(
    codebase: Codebase,
) -> tuple[str, ...]:

    return tuple(

        sorted(

            codebase.statistics.language_distribution,

        )

    )


def repository_imports(
    codebase: Codebase,
) -> dict[str, tuple[str, ...]]:

    return build_dependency_graph(
        codebase.files,
    )


def repository_summary(
    codebase: Codebase,
) -> dict[str, object]:

    return {

        "owner": codebase.metadata.owner,

        "repository": codebase.metadata.name,

        "framework": codebase.framework,

        "primary_language": codebase.primary_language,

        "stars": codebase.metadata.stars,

        "forks": codebase.metadata.forks,

        "supported_files": (
            codebase.statistics.supported_files
        ),

        "ignored_files": (
            codebase.statistics.ignored_files
        ),

        "selected_files": len(
            codebase.files,
        ),

    }


# ============================================================
# Exports
# ============================================================

__all__ = [

    "RepositoryType",

    "RepositoryMetadata",

    "TreeEntry",

    "ManifestFiles",

    "ProjectStatistics",

    "SourceFile",

    "Codebase",

    "fetch_repository_metadata",

    "fetch_repository_tree",

    "discover_manifests",

    "detect_framework",

    "build_statistics",

    "determine_primary_language",

    "candidate_files",

    "ranked_candidates",

    "classify_file",

    "file_priority",

    "build_source_file",

    "select_representative_files",

    "build_dependency_graph",

    "summarize_repository",

    "repository_languages",

    "repository_imports",

    "repository_summary",

    "build_codebase",

    "fetch_codebase",

]