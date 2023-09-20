#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Package to parse comment info."""

import json
import re
import pandas as pd

from pathlib import Path


XrefPat = re.compile(r"\s+((?:-|\w)+/(?:-|\w)+)#(\d+)")


def _persist_deps(repo, deps, f):
    for pair in deps:
        f.write(f"{pair[0]},{repo},{pair[1]},{pair[2]}\n")


def _prepare_csv(deps_file="xref.csv"):
    sub = Path(deps_file[0:-len(deps_file)])
    sub.mkdir(parents=True, exist_ok=True)
    if not Path(deps_file).exists():
        with open(deps_file, 'w') as f:
            f.write("id,src_repo,dest_repo,issue_no\n")


def _extract_xref(func, repo, content, trace=False):
    xrefs = []
    lines = content.split("\n")
    for line in lines:
        if line.find('{') < 0:
            continue
        try:
            id, msg = func(line)
            for m in re.finditer(XrefPat, msg):
                if repo != m.group(1):
                    xrefs.append((id, m.group(1), m.group(2)))
        except Exception as e:
            if trace:
                print(f"Fail to parse: {line} due to: {e}")
            continue

    return xrefs


def _parse_record(func, row, f, trace):
    deps = _extract_xref(func, row["repo"], row["content"], trace=trace)
    _persist_deps(row["repo"], deps, f)


def comment_xref_finder(line):
    """Extract id and potential cross reference from issue comment."""
    comment_obj = json.loads(line)
    id = comment_obj['id']
    msg = comment_obj.get('body', '')
    return id, msg


def commit_xref_finder(line):
    """Extract id and potential cross reference from issue commit."""
    commit_obj = json.loads(line)
    id = commit_obj['sha']
    msg = commit_obj['commit'].get('message', '')
    return id, msg


def parse_xref_from_parquet(func, parquet_file, xref_file, trace=False):
    """Parse cross references from .parquet file.

    Parameters
    ----------
    parquet_file : str
        Path to the parquet_file
    xref_file : str
        Path to the .csv file to store the cross references
    """
    df = pd.read_parquet(parquet_file)
    _prepare_csv(xref_file)
    with open(xref_file, 'a') as f:
        df.apply(lambda row: _parse_record(func, row, f, trace), axis=1)
