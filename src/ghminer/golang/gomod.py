#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Retrieve golang repository objects."""

import pandas as pd

import semver
from github import Github
from datetime import datetime
from timeit import default_timer as timer
from pathlib import Path
from ..utils import load_access_token
from ..utils import load_repo_info


# semver comparison
def _semver_sort(ver_list):
    svers = [
        semver.version.Version.parse(
            v[1:] if v.startswith("v") else v
        )
        for v in ver_list
    ]
    svers.sort(reverse=True)
    return [f"v{sv}" for sv in svers]


def load_gomod(repo, path, version):
    """Retrieve the content of `go.mod` file."""
    try:
        content = repo.get_contents(path, ref=version)
        return (True, content)
    except Exception as e:
        print(f"Fail to load {repo.full_name}/{path}@{version} due to: {e}")
        return (False, None)


def load_subdirs(repo, version):
    """Search in sub directory, descend one level."""
    try:
        contents = repo.get_contents(".", ref=version)
        return [
            c.name for c in contents
            if c.type == 'dir' and not c.name.startswith('.')
        ]
    except Exception as e:
        print("Fail to load sub directories of %s@%s due to: %s" % (
            repo.full_name,
            version,
            e
        ))
        return []


def persist_gomod(
        owner, repo_name, version, content, gmod_path, base_dir):
    """Persist mod info into files for later analysis."""
    mod_file = f"{base_dir}/{owner}/{repo_name}/{version}/{gmod_path}"
    sub = Path(mod_file[0:-len('go.mod')])
    sub.mkdir(parents=True, exist_ok=True)
    with open(mod_file, 'wb') as f:
        f.write(content)


def _persist_progress(
        owner, repo_name, use_module, latest_ver, base_dir, progress_file):
    # persist mod info into files for later analysis
    mod_file = f"{base_dir}/{progress_file}"
    sub = Path(mod_file[0:-len(progress_file)])
    sub.mkdir(parents=True, exist_ok=True)
    if not Path(mod_file).exists():
        with open(mod_file, 'w') as f:
            f.write("full_name,use_module,latest_version,last_updated\n")

    with open(mod_file, 'a') as f:
        f.write("%s/%s,%s,%s,%s\n" % (
            owner,
            repo_name,
            1 if use_module else 0,
            latest_ver,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ))


def load_mod_info(client, owner, repo_name, base_dir="mod-info"):
    """Load all `go.mod` file for all published versions."""
    repo = load_repo_info(client, f"{owner}/{repo_name}")
    if not repo:
        return False, ""
    else:
        mod_count = 0
        # try all tagged versions plus latest version on default branch
        # content = repo.get_contents("go.mod", ref="v0.3.0")
        tags = repo.get_tags()
        vers = [
            t.name for t in tags
            if t.name.startswith('v')
            and semver.version.Version.is_valid(t.name[1:])
        ]
        if len(vers) == 0:
            vers.append(repo.default_branch)
        else:
            # sort vers according to semver
            vers = _semver_sort(vers)

        latest_ver = vers[0]
        for ver in vers:
            ok, content = load_gomod(repo, "go.mod", ver)
            if ok:
                persist_gomod(
                    owner, repo_name, ver,
                    content.decoded_content, "go.mod", base_dir
                )
                mod_count += 1
            else:
                subdirs = load_subdirs(repo, ver)
                for subdir in subdirs:
                    gmod_path = f"{subdir}/go.mod"
                    ok, content = load_gomod(repo, gmod_path, ver)
                    if ok:
                        persist_gomod(
                            owner, repo_name, ver,
                            content.decoded_content, gmod_path, base_dir)
                        mod_count += 1
                        break
                else:
                    break
        return mod_count > 0, latest_ver


# client is the Github instance
# row is a row of Pandas DataFrame
def _do_mod_check(client, row, base_dir, progress_file, trace=False):
    comps = row['full_name'].split('/')
    owner = comps[0]
    name = comps[1]

    t0 = timer()
    use_module, latest_ver = load_mod_info(client, owner, name, base_dir)
    _persist_progress(
        owner, name, use_module, latest_ver, base_dir, progress_file
    )
    t1 = timer()
    if trace:
        print(f"Grab gomod for {owner}/{name} took {t1-t0}s")
    return use_module


def grab_gomod(repo_csv_file, base_dir, progress_file, trace=False):
    """Retrieve all `go.mod` for repositories given in `repo_csv_file`."""
    client = Github(load_access_token(), per_page=100)
    to_check_df = pd.read_csv(repo_csv_file)

    progress_path = f"{base_dir}/{progress_file}"
    if Path(progress_path).exists():
        checked_df = pd.read_csv(progress_path)
        df2 = to_check_df.merge(checked_df, how="left", on="full_name")
        # filter already processed repos, equivalent to SQL is null
        df2 = df2.query("use_module != use_module")
        df2.apply(
            lambda r: _do_mod_check(client, r, base_dir, progress_file, trace),
            axis=1
        )
    else:
        df2 = to_check_df
        df2.apply(
            lambda r: _do_mod_check(client, r, base_dir, progress_file, trace),
            axis=1
        )


def load_latest_ver(client, owner, repo_name):
    """Retrieve the latest version for given repository."""
    repo = load_repo_info(client, f"{owner}/{repo_name}")
    if repo:
        # try all tagged versions plus latest version on default branch
        # content = repo.get_contents("go.mod", ref="v0.3.0")
        tags = repo.get_tags()
        vers = [
            t.name for t in tags
            if t.name.startswith('v')
            and semver.version.Version.is_valid(t.name[1:])
        ]
        if len(vers) == 0:
            vers.append(repo.default_branch)
        else:
            vers = _semver_sort(vers)
        return vers[0]

    return ""


def _do_version_check(client, row, base_dir, progress_file, trace=False):
    comps = row['full_name'].split('/')
    owner = comps[0]
    name = comps[1]
    use_module = row['use_module']

    t0 = timer()
    latest_ver = load_latest_ver(client, owner, name, base_dir)
    _persist_progress(
        owner, name, use_module, latest_ver, base_dir, progress_file
    )
    t1 = timer()
    if trace:
        print(f"Grab latest version for {owner}/{name} took {t1-t0}s")
    return latest_ver


def grab_latest_version(
        base_dir="mod-info",
        old_progress_file="progress.csv",
        progress_file="new_progress.csv",
        trace=False):
    """Retrieve latest version of given repository in `old_progress_file`."""
    client = Github(load_access_token(), per_page=100)

    progress_path = f"{base_dir}/{old_progress_file}"
    df_old = pd.read_csv(progress_path)
    df_old.apply(
        lambda r: _do_version_check(
            client, r, base_dir, progress_file, trace
        ),
        axis=1
    )
