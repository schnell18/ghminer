#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Package to process commit."""

import json
import pandas as pd

from github import Github
from datetime import datetime
from isodate import parse_datetime
from timeit import default_timer as timer
from pathlib import Path
from ..utils import load_access_token
from ..utils import load_repo_info
from ..utils.common import daterange


def _load_partial_commits(repo, branch, start, end, trace=False):
    try:
        commit_page = repo.get_commits(sha=branch, since=start, until=end)
        return (True, commit_page)
    except Exception as e:
        if trace:
            print("Fail to load commits of %s/@%s due to: %s" % (
                repo.full_name,
                branch,
                e
            ))
        return (False, None)


def persist_progress(
        owner, repo_name, default_branch, commits,
        base_dir="commit-info", progress_file="progress.csv"):
    """Save the progress of commit retrieval for resumption."""
    path = f"{base_dir}/{progress_file}"
    sub = Path(path[0:-len(progress_file)])
    sub.mkdir(parents=True, exist_ok=True)
    if not Path(path).exists():
        with open(path, 'w') as f:
            f.write("full_name,default_branch,commits,last_updated\n")

    with open(path, 'a') as f:
        f.write("%s/%s,%s,%s,%s\n" % (
            owner,
            repo_name,
            default_branch,
            commits,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ))


def load_commits(client, owner, repo_name, base_dir, trace=False):
    """Load commit objects for given repository."""
    repo = load_repo_info(client, f"{owner}/{repo_name}")
    if not repo:
        return '', 0
    else:
        commits = 0
        default_branch = repo.default_branch
        # get repo creation date
        start_date = repo.created_at.date()
        end_date = datetime.now().date()
        slice = 30

        jsons_file = f"{base_dir}/{owner}/{repo_name}/commits.json"
        sub = Path(jsons_file[0:-len('commits.json')])
        sub.mkdir(parents=True, exist_ok=True)
        with open(jsons_file, 'w') as fh_json:
            fh_json.write("\n")

        # persist mod info into files for later analysis
        csv_file = f"{base_dir}/commits.csv"
        sub = Path(csv_file[0:-len('commits.csv')])
        sub.mkdir(parents=True, exist_ok=True)
        if not Path(csv_file).exists():
            with open(csv_file, 'w') as f:
                f.write(
                    "full_name,branch,sha,author_name,author_date,verified\n"
                )

        with open(jsons_file, 'a') as fh_json:
            with open(csv_file, 'a') as fh_csv:
                for t in daterange(start_date, end_date, slice):
                    s = datetime(t[0].year, t[0].month, t[0].day, 0, 0, 0)
                    e = datetime(t[1].year, t[1].month, t[1].day, 23, 59, 59)
                    ok, page = _load_partial_commits(
                        repo, default_branch, s, e, trace
                    )
                    if ok:
                        commits += page.totalCount
                        for c in page:
                            raw_data = vars(c).get("_rawData", None)
                            if raw_data:
                                _write_csv(
                                    fh_csv, owner, repo_name,
                                    default_branch, raw_data
                                )
                                _write_json(fh_json, raw_data)

        return default_branch, commits


def _write_json(fh, raw_data):
    fh.write(f"{json.dumps(raw_data)}\n")


def _date_conv(iso_str):
    if iso_str:
        dt = parse_datetime(iso_str)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    else:
        return ""


def _write_csv(fh, owner, repo_name, default_branch, raw_data):
    author_name = ""
    author_date = None
    verified = 0
    sha = raw_data.get("sha", "")
    cmit = raw_data.get("commit", None)
    if cmit:
        authr = cmit.get("author", None)
        if authr:
            author_name = '"' + authr["name"] + '"'  # quote author name
            if not authr["date"]:
                author_date = ""
            else:
                _date_conv(authr["date"])
        veri = cmit.get("verification", None)
        if veri and veri["verified"]:
            verified = 1
    fh.write("%s/%s,%s,%s,%s,%s,%s\n" % (
        owner,
        repo_name,
        default_branch,
        sha,
        author_name,
        author_date,
        verified
    ))


# client is the Github instance
# row is a row of Pandas DataFrame
def _do_commit_fetch(client, row, base_dir, progress_file, trace=False):
    comps = row['full_name'].split('/')
    owner = comps[0]
    name = comps[1]

    t0 = timer()
    default_branch, commits = load_commits(
        client, owner, name, base_dir, trace
    )
    persist_progress(
        owner, name, default_branch, commits, base_dir, progress_file
    )
    t1 = timer()
    if trace:
        print(f"Grab commits for {owner}/{name} took {t1-t0}s")
    return commits


def grab_commits(repo_csv_file, base_dir, progress_file, trace=False):
    """Load commit objects for repositories specified in `repo_csv_file`."""
    client = Github(load_access_token(), per_page=100)
    to_check_df = pd.read_csv(repo_csv_file)

    progress_path = f"{base_dir}/{progress_file}"
    if Path(progress_path).exists():
        checked_df = pd.read_csv(progress_path)
        df2 = to_check_df.merge(checked_df, how="left", on="full_name")
        # filter already processed repos, equivalent to SQL is null
        df2 = df2.query("commits != commits")
        df2.apply(
            lambda r: _do_commit_fetch(
                client, r, base_dir, progress_file, trace
            ),
            axis=1
        )
    else:
        df2 = to_check_df
        df2.apply(
            lambda r: _do_commit_fetch(
                client, r, base_dir, progress_file, trace
            ),
            axis=1
        )
