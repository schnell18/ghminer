#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Retrieve commit information for given repositories.

This script fetches commit objects for repositories specified by in the input
.csv file, which has columns as follows:

    * full_name - repository name
    * default_branch - default branch
    * commits - number of commits in the default branch
    * last_updated - timestamp when the repository was processed

It generates a .csv file to store the progress of retrieval.
It also generates a summary .csv file with basic information of each commit:

    * full_name - repository name
    * branch - default branch
    * sha - commit sha code
    * author_name - author name
    * author_date - author date
    * verified - whether the commit is verified

The commit objects are written to .json files for each repository.

This script requires that `pandas` and `github` be installed within the
Python environment you are running this script in.

"""

# import local functions
from argparse import ArgumentParser
from ghminer.retriever import grab_commits
from ghminer.parser import save_as_parquet
from ghminer.parser import parse_xref_from_parquet
from ghminer.parser import commit_xref_finder
from ghminer.parser import comment_xref_finder


def _parse_args():
    # Create the parser
    parser = ArgumentParser(description='Github commit mining tools')
    subparsers = parser.add_subparsers(dest='subparser', required=True)

    parser_sav = subparsers.add_parser('save-parquet', aliases=['sp'])
    parser_sav.add_argument(
        '-s', '--src-dir', required=True,
        help='Path to source directory containing commits.json files')
    parser_sav.add_argument(
        '-p', '--parquet-file', required=True,
        help='Path to the .parquet file to store commits')
    parser_sav.add_argument(
        '-d', '--trace', action="store_true",
        default=False, help='Print trace messages')

    parser_sav_cmt = subparsers.add_parser(
        'save-parquet-comment', aliases=['spc'])
    parser_sav_cmt.add_argument(
        '-s', '--src-dir', required=True,
        help='Path to source directory containing comments.json files')
    parser_sav_cmt.add_argument(
        '-p', '--parquet-file', required=True,
        help='Path to the .parquet file to store comments')
    parser_sav_cmt.add_argument(
        '-d', '--trace', action="store_true",
        default=False, help='Print trace messages')

    parser_xref = subparsers.add_parser('parse-xref', aliases=['xref'])
    parser_xref.add_argument(
        '-p', '--parquet-file', required=True,
        help='Path to the .parquet files')
    parser_xref.add_argument(
        '-x', '--xref-file', required=True,
        help='Path to the .csv file to store xrefs')
    parser_xref.add_argument(
        '-d', '--trace', action="store_true",
        default=False, help='Print trace messages')

    parser_xrefc = subparsers.add_parser(
        'parse-xref-comment', aliases=['xrefc'])
    parser_xrefc.add_argument(
        '-p', '--parquet-file', required=True,
        help='Path to the .parquet files')
    parser_xrefc.add_argument(
        '-x', '--xref-file', required=True,
        help='Path to the .csv file to store xrefs')
    parser_xrefc.add_argument(
        '-d', '--trace', action="store_true",
        default=False, help='Print trace messages')

    parser_grb = subparsers.add_parser('grab-commit', aliases=['grb'])
    parser_grb.add_argument(
        '-o', '--output-dir', required=True,
        help='Path to save output files')
    parser_grb.add_argument(
        '-f', '--repo-list-file', required=True,
        help='The list of repository to retrieve commits')
    parser_grb.add_argument(
        '-d', '--trace', action="store_true", default=False,
        help='Print trace messages')
    parser_grb.add_argument(
        '--progress-file', default="progress.csv",
        help='Fail to save commit retrieval progress, default progress.csv')

    # Parse the arguments
    args = parser.parse_args()
    return args


def _save_parquet(args):
    save_as_parquet(args.src_dir, "commits.json", args.parquet_file)


def _save_parquet_comment(args):
    save_as_parquet(args.src_dir, "comments.json", args.parquet_file)


def _parse_xref(args):
    parse_xref_from_parquet(
        commit_xref_finder,
        args.parquet_file,
        args.xref_file,
        args.trace
    )


def _parse_xref_comment(args):
    parse_xref_from_parquet(
        comment_xref_finder,
        args.parquet_file,
        args.xref_file,
        args.trace
    )


def _grab_commits(args):
    repo_list_file = args.repo_list_file
    progress_file = args.progress_file
    subdir = args.output_dir
    trace = args.trace

    grab_commits(
        repo_list_file,
        base_dir=subdir,
        progress_file=progress_file,
        trace=trace
    )


if __name__ == "__main__":
    routing = {
      'save-parquet': _save_parquet,
      'sp': _save_parquet,
      'save-parquet-comment': _save_parquet_comment,
      'spc': _save_parquet_comment,
      'parse-xref': _parse_xref,
      'xref': _parse_xref,
      'parse-xref-comment': _parse_xref_comment,
      'xrefc': _parse_xref_comment,
      'grab-commit': _grab_commits,
      'grb': _grab_commits,
    }
    args = _parse_args()
    routing[args.subparser](args)
