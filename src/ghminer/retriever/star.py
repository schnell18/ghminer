#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Package to retrieve star history."""

import requests
import pandas as pd
from ..utils import load_access_token


def _run_query(query):
    headers = {"Authorization": f"bearer {load_access_token()}"}
    request = requests.post(
        'https://api.github.com/graphql',
        json={'query': query},
        headers=headers
    )
    if request.status_code == 200:
        return request.json()
    else:
        raise Exception(
            "Query failed with return code of {}. {}".format(
                request.status_code,
                query
            )
        )


def query_stars(owner, repo, size=100):
    """Collect star history data for given repository.

    Parameters
    ----------
    owner : str
        The owner of the repository
    repo : str
        The name of repository w/o owner
    size : int
        Number of records per page, maximium 100

    Returns
    -------
    List of dictionary
    """
    hasPreviousPage = True
    cursor = ""

    dicts = []
    while hasPreviousPage:

        query = f"""
        query {{
            repository(owner:"{owner}", name:"{repo}") {{
                stargazerCount
                nameWithOwner
                stargazers(
                    {'before: ' + '"' + cursor + '",' if cursor else ""}
                    last: {size},
                    orderBy: {{ direction: DESC, field: STARRED_AT}}) {{
                    pageInfo {{
                        startCursor
                        hasPreviousPage
                    }}
                    edges {{
                        starredAt
                    }}
                }}
            }}
        }}
        """
        result = _run_query(query)
        repo_dict = result["data"]["repository"]
        repo_dict_gazers = repo_dict["stargazers"]
        hasPreviousPage = repo_dict_gazers["pageInfo"]["hasPreviousPage"]
        cursor = repo_dict_gazers["pageInfo"]["startCursor"]
        for star in repo_dict_gazers["edges"]:
            dicts.append({
                "full_name": f"{owner}/{repo}",
                "starredAt": star["starredAt"]
            })

    return dicts


if __name__ == "__main__":
    repos = [
        # "Significant-Gravitas/AutoGPT",
        # "AUTOMATIC1111/stable-diffusion-webui",
        # "xtekky/gpt4free",
        # "Yidadaa/ChatGPT-Next-Web",
        # "AntonOsika/gpt-engineer",
        # "binary-husky/gpt_academic",
        "lencx/ChatGPT",
        # "LAION-AI/Open-Assistant",
    ]
    dicts = []
    for rep in repos:
        owner, repo = rep.split("/")
        dicts.extend(query_stars(owner, repo))
        df = pd.DataFrame(dicts)
        df.to_csv(f"{owner}_{repo}_stars.csv", index=False)
