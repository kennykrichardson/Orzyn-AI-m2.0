# ============================================================
# ORZYN AI m2.0
# Developer Intelligence
# ============================================================

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from backend.orzyn import(
    client,
    get_active_repository,
)

CONTRIBUTORS_QUERY = """
query(
    $owner:String!,
    $name:String!
){

repository(

    owner:$owner,

    name:$name

){

mentionableUsers(

    first:100

){

nodes{

login

name

company

location

bio

url

avatarUrl

followers{

totalCount

}

repositories{

totalCount

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
class DeveloperProfile:

    username: str

    name: str

    company: str | None

    location: str | None

    bio: str | None

    profile_url: str

    avatar_url: str

    followers: int

    repositories: int

def build_developer(node: dict) -> DeveloperProfile:

    return DeveloperProfile(

        username=node["login"],

        name=node["name"] or "",

        company=node["company"],

        location=node["location"],

        bio=node["bio"],

        profile_url=node["url"],

        avatar_url=node["avatarUrl"],

        followers=node["followers"]["totalCount"],

        repositories=node["repositories"]["totalCount"]

    )

def fetch_developers() -> list[DeveloperProfile]:

    repo = get_active_repository()

    result = client.execute(
        CONTRIBUTORS_QUERY,
        {
            "owner": repo.owner,
            "name": repo.repository,
        },
    )

    nodes = (
        result["repository"]
              ["mentionableUsers"]
              ["nodes"]
    )

    return [
        build_developer(node)
        for node in nodes
    ]

def developers_dataframe(
    developers: list[DeveloperProfile],
) -> pd.DataFrame:

    return pd.DataFrame(
        [
            {
                "Username": developer.username,
                "Name": developer.name,
                "Followers": developer.followers,
                "Repositories": developer.repositories,
                "Company": developer.company,
                "Location": developer.location,
                "Profile": developer.profile_url,
            }
            for developer in developers
        ]
    )

def developer_statistics(
    developers: list[DeveloperProfile],
) -> dict:

    if not developers:
        return {}

    top_developer = max(
        developers,
        key=lambda developer: developer.followers,
    )

    dataframe = developers_dataframe(developers)

    return {

        "total_developers": len(developers),

        "top_developer": top_developer,

        "average_followers": dataframe["Followers"].mean(),

        "average_repositories": dataframe["Repositories"].mean(),
    }

