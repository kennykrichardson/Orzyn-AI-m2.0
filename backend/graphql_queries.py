"""
============================================================
ORZYN AI m2.0
GraphQL Utilities
============================================================

Purpose
-------
Shared GraphQL helper functions.
"""

from __future__ import annotations

from backend.orzyn import (
    client,
    get_active_repository,
)

RATE_LIMIT_QUERY = """
query {

    rateLimit {

        limit
        remaining
        cost
        resetAt

    }

}
"""

REPOSITORY_QUERY = """
query(
    $owner:String!,
    $name:String!
){

repository(

    owner:$owner,

    name:$name

){

    name

    description

    stargazerCount

    forkCount

    url

    isPrivate

}

}
"""

PAGINATION_QUERY = """
query(
    $owner:String!,
    $name:String!,
    $after:String
){

repository(

    owner:$owner,

    name:$name

){

issues(

    first:100,

    after:$after

){

nodes{

number

title

}

pageInfo{

hasNextPage

endCursor

}

}

}

}
"""


def fetch_rate_limit() -> dict:

    return client.execute(
        RATE_LIMIT_QUERY
    )


def fetch_repository_metadata() -> dict:

    repo = get_active_repository()

    return client.execute(
        REPOSITORY_QUERY,
        {
            "owner": repo.owner,
            "name": repo.repository,
        },
    )


def fetch_issue_pages() -> list[dict]:

    repo = get_active_repository()

    return list(
        client.paginate(
            PAGINATION_QUERY,
            {
                "owner": repo.owner,
                "name": repo.repository,
            },
            [
                "repository",
                "issues",
            ],
        )
    )