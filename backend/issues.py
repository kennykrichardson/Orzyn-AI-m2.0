# ============================================================
# ORZYN AI m2.0
# GitHub Issues Intelligence
# ============================================================

from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
from statistics import mean

import pandas as pd

from backend.orzyn import (
    client,
    parse_datetime,
    get_active_repository,
)

ISSUES_QUERY = """
query(
    $owner:String!,
    $name:String!
){

repository(

    owner:$owner,

    name:$name

){

issues(

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

closedAt

comments{

totalCount

}

author{

login

}

labels(

    first:20

){

nodes{

name

}

}

assignees(

    first:20

){

nodes{

login

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
class IssueProfile:

    number: int

    title: str

    author: str

    state: str

    created_at: object

    closed_at: object | None

    comments: int

    labels: list[str]

    assignees: list[str]

def build_issue(
    node: dict,
) -> IssueProfile:

    author = node.get("author")

    return IssueProfile(

        number=node["number"],

        title=node["title"],

        author=author["login"] if author else "Unknown",

        state=node["state"],

        created_at=parse_datetime(
            node["createdAt"]
        ),

        closed_at=(

            parse_datetime(
                node["closedAt"]
            )

            if node["closedAt"]

            else None

        ),

        comments=node["comments"]["totalCount"],

        labels=[

            label["name"]

            for label in

            node["labels"]["nodes"]

        ],

        assignees=[

            person["login"]

            for person in

            node["assignees"]["nodes"]

        ]

    )

def fetch_issues() -> list[IssueProfile]:

    repo = get_active_repository()

    result = client.execute(
        ISSUES_QUERY,
        {
            "owner": repo.owner,
            "name": repo.repository,
        },
    )

    nodes = (
        result["repository"]
              ["issues"]
              ["nodes"]
    )

    return [
        build_issue(node)
        for node in nodes
    ]

def issues_dataframe(
    issues: list[IssueProfile],
) -> pd.DataFrame:

    return pd.DataFrame(
        [
            {
                "Issue": issue.number,
                "Title": issue.title,
                "Author": issue.author,
                "State": issue.state,
                "Comments": issue.comments,
                "Labels": ", ".join(issue.labels),
                "Assignees": ", ".join(issue.assignees),
                "Created": issue.created_at,
                "Closed": issue.closed_at,
            }
            for issue in issues
        ]
    )

def issue_statistics(
    issues: list[IssueProfile],
) -> dict:

    if not issues:
        return {}

    state_counts = Counter(
        issue.state
        for issue in issues
    )

    author_counts = Counter(
        issue.author
        for issue in issues
    )

    label_counts = Counter(
        label
        for issue in issues
        for label in issue.labels
    )

    largest_issue = max(
        issues,
        key=lambda issue: issue.comments,
    )

    return {

        "total_issues": len(issues),

        "open_issues": state_counts["OPEN"],

        "closed_issues": state_counts["CLOSED"],

        "unique_authors": len(author_counts),

        "unique_labels": len(label_counts),

        "largest_issue": largest_issue,

        "average_comments": mean(
            issue.comments
            for issue in issues
        ),

        "state_counts": dict(state_counts),

        "author_counts": dict(author_counts),

        "label_counts": dict(label_counts),
    }