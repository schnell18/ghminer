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
from ghminer.retriever import grab_comments
from ghminer.parser import save_as_parquet
from ghminer.parser import parse_xref_from_parquet
from ghminer.parser import CommentXrefRecordReader
from ghminer.parser import CommitXrefRecordReader
from ghminer.parser import CommitSummaryRecordReader
from ghminer.parser import to_gexf


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

    parser_sc = subparsers.add_parser('summarize-commit', aliases=['sc'])
    parser_sc.add_argument(
        '-p', '--parquet-file', required=True,
        help='Path to the .parquet files')
    parser_sc.add_argument(
        '-s', '--summary-file', required=True,
        help='Path to the .csv file to store commit summary')
    parser_sc.add_argument(
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

    parser_gephi = subparsers.add_parser(
        'to-gephi', aliases=['tg'])
    parser_gephi.add_argument(
        '-x', '--xref-file', required=True,
        help='Path to the .csv file to store xrefs')
    parser_gephi.add_argument(
        '-g', '--gexf-file', required=True,
        help='Path to the gephi .gexf XML file')
    parser_gephi.add_argument(
        '--src-col-name', default="src_repo",
        help='colunm name to represent the source node, default `src_repo`')
    parser_gephi.add_argument(
        '--dest-col-name', default="dest_repo",
        help='colunm name to represent the dest node, default `dest_repo`')
    parser_gephi.add_argument(
        '--weight-col-name', default="issue_no",
        help='colunm name to indicate the weight of xref, default `issue_no`')
    parser_gephi.add_argument(
        '--weight-agg-func', default="count",
        help='aggregation function to use for xref weight, default `count`')

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
        help='File to save commit retrieval progress, default progress.csv')

    parser_grbc = subparsers.add_parser('grab-comment', aliases=['grbc'])
    parser_grbc.add_argument(
        '-o', '--output-dir', required=True,
        help='Path to save output files')
    parser_grbc.add_argument(
        '-f', '--repo-list-file', required=True,
        help='The list of repository to retrieve commits')
    parser_grbc.add_argument(
        '-d', '--trace', action="store_true", default=False,
        help='Print trace messages')
    parser_grbc.add_argument(
        '--progress-file', default="progress.csv",
        help='File to save comment retrieval progress, default progress.csv')

    # Parse the arguments
    args = parser.parse_args()
    return args


def _save_parquet(args):
    save_as_parquet(args.src_dir, "commits.json", args.parquet_file)


def _save_parquet_comment(args):
    save_as_parquet(args.src_dir, "comments.json", args.parquet_file)


def _parse_xref(args):
    parse_xref_from_parquet(
        CommitXrefRecordReader(),
        args.parquet_file,
        args.xref_file,
        args.trace
    )


def _parse_commit_summary(args):
    parse_xref_from_parquet(
        CommitSummaryRecordReader(),
        args.parquet_file,
        args.summary_file,
        args.trace
    )


def _parse_xref_comment(args):
    parse_xref_from_parquet(
        CommentXrefRecordReader(),
        args.parquet_file,
        args.xref_file,
        args.trace
    )


def _to_gephi(args):
    to_gexf(
        args.xref_file,
        args.gexf_file,
        src_col_name=args.src_col_name,
        dest_col_name=args.dest_col_name,
        weight_col_name=args.weight_col_name,
        weight_agg_func=args.weight_agg_func,
    )


def _grab_comments(args):
    repo_list_file = args.repo_list_file
    progress_file = args.progress_file
    subdir = args.output_dir
    trace = args.trace

    grab_comments(
        repo_list_file,
        base_dir=subdir,
        progress_file=progress_file,
        trace=trace
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
      'grab-commit': _grab_commits,
      'grb': _grab_commits,
      'grab-comment': _grab_comments,
      'grbc': _grab_comments,
      'save-parquet': _save_parquet,
      'sp': _save_parquet,
      'save-parquet-comment': _save_parquet_comment,
      'spc': _save_parquet_comment,
      'parse-xref': _parse_xref,
      'xref': _parse_xref,
      'parse-xref-comment': _parse_xref_comment,
      'xrefc': _parse_xref_comment,
      'summarize-commit': _parse_commit_summary,
      'sc': _parse_commit_summary,
      'to-gephi': _to_gephi,
      'tg': _to_gephi,
    }
    args = _parse_args()
    routing[args.subparser](args)
