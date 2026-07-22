# ============================================================
# Orzyn AI
# Pull Request Intelligence
# ============================================================

from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
from statistics import mean
from datetime import datetime

import pandas as pd

from backend.orzyn import (
    client,
    parse_datetime,
    get_active_repository,
)

PULL_REQUEST_QUERY = """
query(
    $owner:String!,
    $name:String!
){

repository(
    owner:$owner,
    name:$name
){

pullRequests(

    first:100,

    orderBy:{
        field:CREATED_AT,
        direction:DESC
    }

){

nodes{

number

title

state

createdAt

mergedAt

closedAt

isDraft

additions

deletions

changedFiles

commits{

totalCount

}

reviews{

totalCount

}

comments{

totalCount

}

author{

login

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
class PullRequestProfile:

    number: int

    title: str

    author: str

    state: str

    created_at: datetime

    merged_at: datetime | None

    closed_at: datetime | None

    additions: int

    deletions: int

    changed_files: int

    commits: int

    reviews: int

    comments: int

    merged: bool

    draft: bool

def build_pull_request(node: dict) -> PullRequestProfile:

    author = node.get("author")

    return PullRequestProfile(

        number=node["number"],

        title=node["title"],

        author=author["login"] if author else "Unknown",

        state=node["state"],

        created_at=parse_datetime(
            node["createdAt"]
        ),

        merged_at=(
            parse_datetime(node["mergedAt"])
            if node["mergedAt"]
            else None
        ),

        closed_at=(
            parse_datetime(node["closedAt"])
            if node["closedAt"]
            else None
        ),

        additions=node["additions"],

        deletions=node["deletions"],

        changed_files=node["changedFiles"],

        commits=node["commits"]["totalCount"],

        reviews=node["reviews"]["totalCount"],

        comments=node["comments"]["totalCount"],

        merged=node["mergedAt"] is not None,

        draft=node["isDraft"]

    )

def fetch_pull_requests() -> list[PullRequestProfile]:

    repo = get_active_repository()

    result = client.execute(
        PULL_REQUEST_QUERY,
        {
            "owner": repo.owner,
            "name": repo.repository,
        },
    )

    nodes = (
        result["repository"]
              ["pullRequests"]
              ["nodes"]
    )

    return [
        build_pull_request(node)
        for node in nodes
    ]

def pull_requests_dataframe(
    pull_requests: list[PullRequestProfile],
) -> pd.DataFrame:

    return pd.DataFrame(
        [
            {
                "PR": pr.number,
                "Title": pr.title,
                "Author": pr.author,
                "State": pr.state,
                "Additions": pr.additions,
                "Deletions": pr.deletions,
                "Total Changes": pr.additions + pr.deletions,
                "Files": pr.changed_files,
                "Commits": pr.commits,
                "Reviews": pr.reviews,
                "Comments": pr.comments,
                "Draft": pr.draft,
            }
            for pr in pull_requests
        ]
    )

def pull_request_statistics(
    pull_requests: list[PullRequestProfile],
) -> dict:

    if not pull_requests:
        return {}

    state_counts = Counter(
        pr.state
        for pr in pull_requests
    )

    author_counts = Counter(
        pr.author
        for pr in pull_requests
    )

    largest_pr = max(
        pull_requests,
        key=lambda pr: pr.additions + pr.deletions,
    )

    return {

        "total_pull_requests": len(pull_requests),

        "merged": sum(
            pr.merged
            for pr in pull_requests
        ),

        "open": state_counts["OPEN"],

        "closed": state_counts["CLOSED"],

        "draft": sum(
            pr.draft
            for pr in pull_requests
        ),

        "unique_authors": len(author_counts),

        "largest_pull_request": largest_pr,

        "average_changes": mean(
            pr.additions + pr.deletions
            for pr in pull_requests
        ),

        "state_counts": dict(state_counts),

        "author_counts": dict(author_counts),
    }