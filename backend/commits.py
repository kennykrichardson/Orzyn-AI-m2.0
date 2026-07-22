"""
============================================================
ORZYN AI m2.0
Commit Intelligence
============================================================

Purpose
-------
Extract and analyze commit history for any GitHub repository.

Produces
--------
CommitProfile objects
Repository commit metrics
Developer activity metrics
Timeline statistics
"""

from collections import Counter
from dataclasses import dataclass
from datetime import datetime
import pandas as pd

from backend.orzyn import (
    client,
    get_active_repository,
    parse_datetime,
)

GET_COMMIT_HISTORY_QUERY = """
query(
    $owner:String!,
    $name:String!
){

repository(
    owner:$owner,
    name:$name
){

defaultBranchRef{

target{

... on Commit{

history(first:100){

nodes{

oid

messageHeadline

committedDate

additions

deletions

changedFilesIfAvailable

author{

name

email

user{

login

}

}

}

}

}

}

}

}

}
"""

@dataclass(
    slots=True,
    frozen=True,
)
class CommitProfile:

    sha: str

    message: str

    author: str

    username: str | None

    email: str | None

    committed_at: datetime

    additions: int

    deletions: int

    files_changed: int

def build_commit(node: dict) -> CommitProfile:

    author = node.get("author") or {}

    user = author.get("user")

    return CommitProfile(

        sha=node["oid"],

        message=node["messageHeadline"],

        author=author.get("name") or "Unknown",

        username=user.get("login") if user else None,

        email=author.get("email"),

        committed_at=parse_datetime(
            node["committedDate"]
        ),

        additions=node.get("additions", 0),

        deletions=node.get("deletions", 0),

        files_changed=node.get(
            "changedFilesIfAvailable"
        ) or 0

    )

def fetch_commits() -> list[CommitProfile]:

    repo = get_active_repository()

    result = client.execute(
        GET_COMMIT_HISTORY_QUERY,
        {
            "owner": repo.owner,
            "name": repo.repository,
        },
    )

    repository = result.get("repository")

    if repository is None:
        return []

    branch = repository.get("defaultBranchRef")

    if branch is None:
        return []

    target = branch.get("target")

    if target is None:
        return []

    history = target.get("history")

    if history is None:
        return []

    return [
        build_commit(node)
        for node in history.get("nodes", [])
    ]

def commit_statistics(
    commits: list[CommitProfile],
) -> dict:

    if not commits:
        return {}

    author_counts = Counter(
        commit.author
        for commit in commits
    )

    weekday_counts = Counter(
        commit.committed_at.strftime("%A")
        for commit in commits
    )

    hour_counts = Counter(
        commit.committed_at.hour
        for commit in commits
    )

    largest_commit = max(
        commits,
        key=lambda commit: (
            commit.additions +
            commit.deletions
        ),
    )

    first_commit = min(
        commits,
        key=lambda commit: commit.committed_at,
    )

    latest_commit = max(
        commits,
        key=lambda commit: commit.committed_at,
    )

    average_changes = sum(
        commit.additions + commit.deletions
        for commit in commits
    ) / len(commits)

    return {
        "total_commits": len(commits),
        "contributors": len(author_counts),
        "largest_commit": largest_commit,
        "average_changes": average_changes,
        "first_commit": first_commit,
        "latest_commit": latest_commit,
        "weekday_counts": dict(weekday_counts),
        "hour_counts": dict(hour_counts),
        "author_counts": dict(author_counts),
    }

def commits_dataframe(
    commits: list[CommitProfile],
):
    return pd.DataFrame(
        [
            {
                "SHA": commit.sha,
                "Message": commit.message,
                "Author": commit.author,
                "Username": commit.username,
                "Email": commit.email,
                "Additions": commit.additions,
                "Deletions": commit.deletions,
                "Total Changes": (
                    commit.additions +
                    commit.deletions
                ),
                "Files Changed": commit.files_changed,
                "Committed At": commit.committed_at,
            }
            for commit in sorted(
                commits,
                key=lambda commit: (
                    commit.additions +
                    commit.deletions
                ),
                reverse=True,
            )
        ]
    )