#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Package to convert golang module import name to github repository."""

import pandas as pd
import requests
import re

from html.parser import HTMLParser
from datetime import datetime
from timeit import default_timer as timer
from pathlib import Path
from requests.exceptions import ConnectionError
from requests.exceptions import SSLError
from requests.exceptions import TooManyRedirects


class GoImportMetaHTMLParser(HTMLParser):
    """
    A class to to parse the go-import meta tag in HTTP response.

    ...

    Attributes
    ----------
    github_name: str
        the gith repository name of the module using non-github prefix name

    """

    def __init__(self):
        """Create a instance of `GoImportMetaHTMLParser` object."""
        super().__init__()
        self._github_name = ""

    @property
    def github_name(self):
        """Return github name."""
        return self._github_name

    def feed(self, text):
        """Override to reset github name."""
        self._gith_name = ""
        super().feed(text)

    def handle_starttag(self, tag, attrs):
        """Override to handle meta tag."""
        self._gith_name = ""
        if tag == "meta":
            imports_found = [
                attr for attr in attrs
                if attr[0] == "name" and attr[1] == "go-import"
            ]
            contents = [
                attr[1] for attr in attrs if attr[0] == "content"]
            if imports_found and contents:
                comps = re.split(r"\s+", contents[0])
                if len(comps) == 3:
                    idx = comps[2].find("//")
                    if idx < 0:
                        self._github_name = comps[2]
                    else:
                        self._github_name = comps[2][idx+2:]


def _persist_progress(
        module, github_name, fail_reason, base_dir, progress_file):
    # persist mod info into files for later analysis
    mod_file = f"{base_dir}/{progress_file}"
    sub = Path(mod_file[0:-len(progress_file)])
    sub.mkdir(parents=True, exist_ok=True)
    if not Path(mod_file).exists():
        with open(mod_file, 'w') as f:
            f.write("module,github_name,fail_reason,last_updated\n")

    with open(mod_file, 'a') as f:
        f.write(
            "%s,%s,%s,%s\n" % (
                module,
                github_name if github_name else '-',
                fail_reason,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
        )


def _parse_gopkgin_path(module):
    comps = module.split('/')
    user = None
    pkg_ver = None
    if len(comps) == 2:
        pkg_ver = comps[1]
    else:
        user = comps[1]
        pkg_ver = comps[2]

    pkg, ver = pkg_ver.split('.')
    return user, pkg, ver


# client is the Github instance
# row is a row of Pandas DataFrame
def _convert_name(parser, module, base_dir, progress_file, trace=False):
    t0 = timer()
    github_name = ""
    fail_reason = ""
    try:
        if trace:
            print(f"work on {module}")
        # handle gopkg.in with static conversion according to the rules
        # published on https://labix.org/gopkg.in
        if module.startswith("gopkg.in"):
            user, pkg, _ = _parse_gopkgin_path(module)
            if not user:
                user = f"go-{pkg}"
            github_name = f"github.com/{user}/{pkg}"
        else:
            q = {"go-get": "1"}
            request_url = f"https://{module}"
            resp = requests.get(request_url, params=q, allow_redirects=True)
            parser.feed(resp.text)
            github_name = parser.github_name

    except ConnectionError as e:
        fail_reason = "ConnectionError"
        print(f"fail to convert {module} to github name due to {e}")
    except SSLError as e:
        fail_reason = "SSLError"
        print(f"fail to convert {module} to github name due to {e}")
    except TooManyRedirects as e:
        fail_reason = "TooManyRedirects"
        print(f"fail to convert {module} to github name due to {e}")
    except Exception as e:
        print(type(e))
        print(f"fail to convert {module} to github name due to {e}")
    finally:
        _persist_progress(
            module, github_name, fail_reason, base_dir, progress_file)

    t1 = timer()
    if trace:
        print(f"Convert {module} to {github_name} took {t1-t0}s")
    return github_name


def convert_names(repo_csv_file, progress_file, trace=False):
    """Convert import name in `repo_csv_file` to github name.

    Parameters
    ----------
    repo_csv_file : str
        The import name list file
    progress_file : str
        The name of .csv file to store progress
    trace : bool
        Whether to print tracing messages

    Returns
    -------
    None
    """
    base_dir = "."
    parser = GoImportMetaHTMLParser()
    to_check_df = pd.read_csv(repo_csv_file)

    progress_path = f"{base_dir}/{progress_file}"
    if Path(progress_path).exists():
        checked_df = pd.read_csv(progress_path)
        df2 = to_check_df.merge(checked_df, how="left", on="module")
        # filter already processed repos, equivalent to SQL is null
        df2 = df2.query("github_name != github_name")
        if not df2.empty:
            df2.apply(
                lambda r: _convert_name(
                    parser, r["module"], base_dir, progress_file, trace
                ),
                axis=1
            )
    else:
        df2 = to_check_df
        df2.apply(
            lambda r: _convert_name(
                parser, r["module"], base_dir, progress_file, trace
            ),
            axis=1
        )
