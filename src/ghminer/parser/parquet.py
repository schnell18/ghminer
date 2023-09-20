#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Package for writing commit json into .parquet file."""

import pandas as pd
import sys

from os import listdir
from os.path import isfile, join
from pathlib import Path
from ..utils import eprint


def _load_content(file_path):
    if Path(file_path).exists():
        with open(file_path, 'r') as file:
            return file.read()
    return ""


def save_as_parquet(base_dir, file_name, dest_file):
    """Save the commit json files into a .parquet file.

    The .parquet file is compressed using snappy.

    Parameters
    ----------
    base_dir : str
        The base directory where the json files are stored
    file_name: str
        The name of the json file to capture
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
            json_path = join(base_dir, owner, repo, file_name)
            if isfile(json_path):
                content = _load_content(json_path)
                dikt_list.append({
                    "repo": f"{owner}/{repo}",
                    "content": content,
                })

    if len(dikt_list) == 0:
        eprint(f"No {file_name} files found!")
        sys.exit(1)

    df = pd.DataFrame(dikt_list)
    df.to_parquet(dest_file, compression="snappy", index=False)
