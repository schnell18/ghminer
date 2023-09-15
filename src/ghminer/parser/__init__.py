"""Package to proccess file format."""

import pandas as pd
# from pygobuildinfo import get_go_mod
# from os import listdir
# from os.path import join, isdir
from pathlib import Path
from .gomod import GoMod

__all__ = [
    "parse_deps_from_dir"
    "parse_deps_from_parquet",
]


def persist_deps(module, version, deps, f):
    for pair in deps:
        f.write(f"{module},{pair[0]},{version},{pair[1]},{pair[2]}\n")


def _prepare_csv(deps_file="dependencies.csv"):
    sub = Path(deps_file[0:-len(deps_file)])
    sub.mkdir(parents=True, exist_ok=True)
    if not Path(deps_file).exists():
        with open(deps_file, 'w') as f:
            f.write("full_name,public_name,version,dep_module,dep_version\n")


def _parse_record(row, f):
    mod = GoMod(row["content"])
    deps = [
        (mod.module_path, req.module, req.version)
        for req in mod.requires if not req.indirect
    ]
    persist_deps(row["repo"], row["version"], deps, f)


def parse_deps_from_parquet(parquet_file, deps_file, trace=False):
    df = pd.read_parquet(parquet_file)
    _prepare_csv(deps_file)
    with open(deps_file, 'a') as f:
        df.apply(lambda row: _parse_record(row, f), axis=1)
