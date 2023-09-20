#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Package to retrieve comment."""

import json
import pandas as pd

from github import Github
from datetime import datetime
from timeit import default_timer as timer
from pathlib import Path
from ..utils import load_access_token
from ..utils import load_repo_info


def _load_partial_comments(repo, trace=False):
    try:
        comment_page = repo.get_issues_comments(
            sort='updated', direction='desc'
        )
        return (True, comment_page)
    except Exception as e:
        if trace:
            print("Fail to load comments of %s due to: %s" % (
                repo.full_name,
                e
            ))
        return (False, None)


def persist_progress(
        owner, repo_name, comments, base_dir, progress_file):
    """Save the progress of comment retrieval for resumption."""
    path = f"{base_dir}/{progress_file}"
    sub = Path(path[0:-len(progress_file)])
    sub.mkdir(parents=True, exist_ok=True)
    if not Path(path).exists():
        with open(path, 'w') as f:
            f.write("full_name,comments,last_updated\n")

    with open(path, 'a') as f:
        f.write("%s/%s,%s,%s\n" % (
            owner,
            repo_name,
            comments,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ))


def load_comments(client, owner, repo_name, base_dir, trace=False):
    """Load comment objects for given repository."""
    repo = load_repo_info(client, f"{owner}/{repo_name}")
    if not repo:
        return '', 0
    else:
        comments = 0
        jsons_file = f"{base_dir}/{owner}/{repo_name}/comments.json"
        sub = Path(jsons_file[0:-len('comments.json')])
        sub.mkdir(parents=True, exist_ok=True)
        with open(jsons_file, 'w') as fh_json:
            fh_json.write("\n")

        with open(jsons_file, 'a') as fh_json:
            ok, page = _load_partial_comments(repo, trace)
            if ok:
                comments += page.totalCount
                for c in page:
                    raw_data = vars(c).get("_rawData", None)
                    if raw_data:
                        _write_json(fh_json, raw_data)

        return comments


def _write_json(fh, raw_data):
    fh.write(f"{json.dumps(raw_data)}\n")


# client is the Github instance
# row is a row of Pandas DataFrame
def _do_comment_fetch(client, row, base_dir, progress_file, trace=False):
    comps = row['full_name'].split('/')
    owner = comps[0]
    name = comps[1]

    t0 = timer()
    comments = load_comments(
        client, owner, name, base_dir, trace
    )
    persist_progress(
        owner, name, comments, base_dir, progress_file
    )
    t1 = timer()
    if trace:
        print(f"Grab comments for {owner}/{name} took {t1-t0}s")
    return comments


def grab_comments(repo_csv_file, base_dir, progress_file, trace=False):
    """Load comment objects for repositories specified in `repo_csv_file`."""
    client = Github(load_access_token(), per_page=100)
    to_check_df = pd.read_csv(repo_csv_file)

    progress_path = f"{base_dir}/{progress_file}"
    if Path(progress_path).exists():
        checked_df = pd.read_csv(progress_path)
        df2 = to_check_df.merge(checked_df, how="left", on="full_name")
        # filter already processed repos, equivalent to SQL is null
        df2 = df2.query("comments != comments")
        df2.apply(
            lambda r: _do_comment_fetch(
                client, r, base_dir, progress_file, trace
            ),
            axis=1
        )
    else:
        df2 = to_check_df
        df2.apply(
            lambda r: _do_comment_fetch(
                client, r, base_dir, progress_file, trace
            ),
            axis=1
        )
