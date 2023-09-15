#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Functions for search repositories."""

import pandas as pd

from ..utils.common import daterange
from ..utils.common import format_date
from ..utils.common import yearrange
from ..utils import load_access_token
from github import Github
from pathlib import Path
from timeit import default_timer as timer


def _search_repo_iteratively(
        client, dict_list, fork, stars, start, end, lang, topics=[]):
    fork_str = "true" if fork else "false"
    query_str = f"stars:>={stars} fork:{fork_str} created:{start}..{end}"
    if lang is not None and lang != '':
        query_str = f"lang:{lang} {query_str}"
    if topics is not None and len(topics) > 0:
        for topic in topics:
            _do_search(client, f"topic:{topic} {query_str}", dict_list)
    else:
        _do_search(client, query_str, dict_list)


def _do_search(client, query_str, dict_list):
    repositories = client.search_repositories(
        query_str, sort="stars", order="desc"
    )
    for repo in repositories:
        old_dict = vars(repo)
        dict_list.append({k: v for k, v in old_dict['_rawData'].items()})


def collect_data(
        start_year, end_year, extra_year_range,
        fork, stars, slice, subdir, lang, topics=[], trace=False):
    """Collect repository information matching specified criteria.

    Parameters
    ----------
    start_year : int
        The start year when the repositories were created
    end_year : int
        The end year when the repositories were created
    extra_year_range : tuple
        A tuple of date specified the start and end date
    fork : bool
        Whether to include forked repositories
    stars : int
        Minimal stars
    stars : slice
        Time window size in days
    subdir : str
        Directory to store the result .csv files
    topics : list
        List of topics to search, the repository matches if any of topic
        in list matches
    trace : bool
        Whether to print tracing information

    Returns
    -------
    None
    """
    sub = Path(subdir)
    sub.mkdir(exist_ok=True)
    client = Github(load_access_token(), per_page=100)
    date_ranges = []
    for t in yearrange(start_year, end_year, 2):
        date_ranges.append(t)
    if (extra_year_range is not None):
        date_ranges.append(extra_year_range)

    date_ranges = date_ranges[::-1]
    search_key = _search_key(lang, topics)
    for date_range in date_ranges:
        t0 = timer()
        dict_list = []
        for t in daterange(date_range[0], date_range[1], slice):
            _search_repo_iteratively(
                client, dict_list, fork, stars,
                format_date(t[0]), format_date(t[1]), lang, topics=topics
            )
        t1 = timer()
        if trace:
            print("Collect %s data between %s and %s took %s seconds" % (
                search_key,
                date_range[0],
                date_range[1],
                t1-t0
            ))
        df = pd.DataFrame(dict_list)
        df.to_csv("%s/%s-repo-%d-%s-%s.csv" % (
            subdir, search_key, stars, date_range[0], date_range[1]
        ))
        t2 = timer()
        if trace:
            print("Save %s data between %s and %s took %d seconds" % (
                search_key, date_range[0], date_range[1], t2-t1
            ))

    t3 = timer()
    cost_dfs = []
    for date_range in date_ranges:
        df = pd.read_csv("%s/%s-repo-%d-%s-%s.csv" % (
            subdir, search_key, stars, date_range[0], date_range[1]
        ))
        cost_dfs.append(df)
    combined = pd.concat(cost_dfs)
    combined.to_csv("%s/%s-repo-%d-combined.csv" % (
        subdir, search_key, stars
    ))
    t4 = timer()

    if trace:
        print(f"Combine and save {search_key} data took {t4-t3} seconds")


def _search_key(lang, topics):
    lng = "" if lang is None or lang == '' else lang
    tpc = ""
    if topics is not None:
        tpc = "-".join([x.replace(' ', '_') for x in topics])

    return lng or tpc if lng == "" or tpc == "" else f"{lng}_{tpc}"
