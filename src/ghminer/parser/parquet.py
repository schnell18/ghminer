#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Package for writing commit json into .parquet file."""

import pandas as pd

from os import listdir
from os.path import isfile, join
from pathlib import Path


def _load_content(gmod_path):
    if Path(gmod_path).exists():
        with open(gmod_path, 'r') as file:
            return file.read()
    return ""


def save_as_parquet(base_dir="mod-info", dest_file="commits.parquet"):
    """Save the commit json files into a .parquet file.

    The .parquet file is compressed using snappy.

    Parameters
    ----------
    base_dir : str
        The base directory where the `commits.json` files are stored
    dest_file : str
        The name of the .parquet to save.

    Returns
    -------
    None
    """
    dikt_list = []
    for owner in listdir(base_dir):
        if isfile(join(base_dir, owner)):
            continue
        for repo in listdir(join(base_dir, owner)):
            if isfile(join(base_dir, owner, repo)):
                continue
            json_path = join(base_dir, owner, repo, "commits.json")
            if isfile(json_path):
                # parse go.mod
                content = _load_content(json_path)
                dikt_list.append({
                    "repo": f"{owner}/{repo}",
                    "content": content,
                })

    df = pd.DataFrame(dikt_list)
    df.to_parquet(dest_file, compression="snappy", index=False)
