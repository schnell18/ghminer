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


def _parse_args():
    # Create the parser
    parser = ArgumentParser(description='Github repository commit retriever')

    # Add arguments
    parser.add_argument(
        '-o', '--output-dir', required=True,
        help='Path to save output files')
    parser.add_argument(
        '-f', '--repo-list-file', required=True,
        help='The list of repository to retrieve commits')
    parser.add_argument(
        '-d', '--trace', action="store_true", default=False,
        help='Print trace messages')
    parser.add_argument(
        '--progress-file', default="progress.csv",
        help='Fail to save commit retrieval progress, default progress.csv')

    # Parse the arguments
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    print(args)

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
