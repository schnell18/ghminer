#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tools to mine golang repositories on Github.

This script requires that `pandas` and `github` be installed within the
Python environment you are running this script in.

"""

import ghminer.parser.parquet as pp

from ghminer.parser import parse_deps_from_parquet
from ghminer.retriever import grab_gomod
from timeit import default_timer as timer
from ghminer.golang import convert_names


def main(base_dir="mod-info", progress_file="progress.csv"):
    """Run the main entry of the script."""
    grab_gomod(
        "slim.csv",
        base_dir=base_dir,
        progress_file=progress_file,
        trace=True
    )


if __name__ == "__main__":

    # TODO: add switch to convert imporant name to github name
    convert_names(
        "name-conv-module-refs.csv",
        progress_file="name-conv-progress.csv",
        trace=True
    )

    # TODO: add switch to retrieve go.mod
    # TODO: add switch to enable parse or parquet saving
    pp.save_as_parquet(base_dir="tmp1/mod-info", dest_file="gomod2.parquet")

    t0 = timer()
    parse_deps_from_parquet(
        parquet_file="gomod2.parquet",
        deps_file="dependencies-parquet2.csv",
        trace=True
    )
    t1 = timer()
    print(f"parse_deps_from_parquet() took {t1-t0}s")
    # parse_deps_from_dir(
    # base_dir="tmp1/mod-info", deps_file="dependencies-dir.csv", trace=True)
    # t2 = timer()
    # print(f"parse_deps_from_dir() took {t2-t1}s")
