"""
============================================================
ORZYN AI m2.0
Repository Intelligence
============================================================

Purpose
-------
Transform GitHub repository data into structured intelligence.
"""

from dataclasses import dataclass, field

from backend.config import GITHUB_HEADERS
from backend.graphql_queries import client
from backend.orzyn import (
    get_active_repository,
    parse_datetime,
)



GET_REPOSITORY_QUERY = """
query($owner:String!, $name:String!){

repository(owner:$owner,name:$name){

name

description

url

homepageUrl

createdAt

updatedAt

pushedAt

diskUsage

isArchived

isFork

isPrivate

forkCount

stargazerCount

watchers{

totalCount

}

defaultBranchRef{

name

}

licenseInfo{

name

}

repositoryTopics(first:100){

nodes{

topic{

name

}

}

}

languages(

first:20,

orderBy:{

field:SIZE,

direction:DESC

}

){

edges{

size

node{

name

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

class RepositoryProfile:

    name:str

    description:str|None

    url:str

    homepage:str|None

    created_at:object

    updated_at:object

    pushed_at:object

    default_branch:str

    license:str|None

    stars:int

    forks:int

    watchers:int

    disk_usage_kb:int

    archived:bool

    visibility:str

    primary_language: str | None

    fork:bool

    topics:list[str]=field(default_factory=list)

    languages:dict[str,float]=field(default_factory=dict)



def calculate_language_percentages(
    edges: list[dict],
) -> dict[str, float]:
    
    total = sum(

        edge["size"]

        for edge in edges

    )

    if total == 0:

        return {}

    return {

        edge["node"]["name"]:

        round(

            edge["size"]/total*100,

            2

        )

        for edge in edges

    }



def build_repository_profile(
    data: dict,
) -> RepositoryProfile:
    
    repo = data["repository"]

    languages = calculate_language_percentages(
        repo["languages"]["edges"]
    )

    primary_language = (
        max(
            languages,
            key=languages.get,
        )
        if languages
        else None
    )

    return RepositoryProfile(

        name=repo["name"],

        description=repo["description"],

        url=repo["url"],

        homepage=repo["homepageUrl"],

        created_at=parse_datetime(repo["createdAt"]),

        updated_at=parse_datetime(repo["updatedAt"]),

        pushed_at=parse_datetime(repo["pushedAt"]),
    
        default_branch=repo["defaultBranchRef"]["name"],

        license=(
            repo["licenseInfo"]["name"]
            if repo["licenseInfo"]
            else None
        ),

        stars=repo["stargazerCount"],

        forks=repo["forkCount"],

        watchers=repo["watchers"]["totalCount"],
 
        disk_usage_kb=repo["diskUsage"],
 
        archived=repo["isArchived"],

        visibility=(
            "Private"
            if repo["isPrivate"]
            else "Public"
        ),

        primary_language=primary_language,

        fork=repo["isFork"],

        topics=[
            topic["topic"]["name"]
            for topic in repo["repositoryTopics"]["nodes"]
        ],

        languages=languages,

    )

def fetch_repository_profile() -> RepositoryProfile:

    repo = get_active_repository()

    data = client.execute(
        GET_REPOSITORY_QUERY,
        {
            "owner": repo.owner,
            "name": repo.repository,
        },
    )

    return build_repository_profile(data)