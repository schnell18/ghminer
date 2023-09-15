#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tools to mine golang repositories on Github.

This script requires that `pandas` and `github` be installed within the
Python environment you are running this script in.

"""

import ghminer.parser.parquet as pp

from argparse import ArgumentParser
from ghminer.parser import parse_deps_from_parquet
from ghminer.golang import convert_names
from ghminer.golang import grab_gomod
from timeit import default_timer as timer


def _parse_args():
    # Create the parser
    parser = ArgumentParser(description='Golang Github mining tools')
    subparsers = parser.add_subparsers(dest='subparser', required=True)

    # convert-names arguments
    parser_cvt = subparsers.add_parser('convert-names', aliases=['cvt'])
    parser_cvt.set_defaults(func=_convert_names)
    parser_cvt.add_argument(
        '-s', '--source-file', required=True,
        help='Path to source file')
    parser_cvt.add_argument(
        '-p', '--progress-file', required=True,
        help='Path to progress file, acting as result file')
    parser_cvt.add_argument(
        '-d', '--trace', action="store_true",
        default=False, help='Print trace messages')

    # save-parquet arguments
    parser_pqt = subparsers.add_parser('save-parquet', aliases=['spqt'])
    parser_pqt.set_defaults(func=_save_parquet)
    parser_pqt.add_argument(
        '-s', '--source-dir', required=True,
        help='Path to source directory containing go.mod files')
    parser_pqt.add_argument(
        '-p', '--parquet-file', required=True,
        help='Path to parquet file')

    # parse-parquet arguments
    parser_psp = subparsers.add_parser('parse-parquet', aliases=['pp'])
    parser_psp.set_defaults(func=_parse_parquet)
    parser_psp.add_argument(
        '-s', '--source-file', required=True,
        help='Path to source .parquet file')
    parser_psp.add_argument(
        '-o', '--output-file', required=True,
        help='Path to result .csv file')
    parser_psp.add_argument(
        '-d', '--trace', action="store_true",
        default=False, help='Print trace messages')

    # parse-parquet arguments
    parser_grb = subparsers.add_parser('grab-go-mod', aliases=['grb'])
    parser_grb.set_defaults(func=_grab_go_mod)
    parser_grb.add_argument(
        '-s', '--source-file', required=True,
        help='Path to repository list file')
    parser_grb.add_argument(
        '-o', '--output-dir', required=True,
        help='Diretory to save go.mod files')
    parser_grb.add_argument(
        '-p', '--progress-file', required=True,
        help='Path to progress file, acting as result file')
    parser_grb.add_argument(
        '-d', '--trace', action="store_true",
        default=False, help='Print trace messages')

    # Parse the arguments
    args = parser.parse_args()
    return args


def _convert_names(args):
    convert_names(
        args.source_file,
        progress_file=args.progress_file,
        trace=args.trace
    )


def _save_parquet(args):
    pp.save_as_parquet(
        base_dir=args.source_dir,
        dest_file=args.parquet_file
    )


def _parse_parquet(args):
    t0 = timer()
    parse_deps_from_parquet(
        parquet_file=args.source_file,
        deps_file=args.output_file,
        trace=args.trace
    )
    t1 = timer()
    print(f"parse_deps_from_parquet() took {t1-t0}s")


def _grab_go_mod(args):
    t0 = timer()
    grab_gomod(
        args.source_file,
        base_dir=args.output_dir,
        progress_file=args.progress_file,
        trace=args.trace
    )
    t1 = timer()
    print(f"grab_gomod() took {t1-t0}s")


if __name__ == "__main__":
    routing = {
      'convert-names': _convert_names,
      'cvt': _convert_names,
      'save-parquet': _save_parquet,
      'spqt': _save_parquet,
      'parse-parquet': _parse_parquet,
      'pp': _parse_parquet,
      'grab-go-mod': _grab_go_mod,
      'grb': _grab_go_mod,
    }
    args = _parse_args()
    routing[args.subparser](args)
