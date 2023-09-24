#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Package to parse comment info."""

import json
import re
import pandas as pd

from ..utils.common import convert_iso_date
from pathlib import Path
from timeit import default_timer as timer

XrefPat = re.compile(r"\s+((?:-|\w)+/(?:-|\w)+)#(\d+)")


def parse_xref_from_parquet(reader, parquet_file, xref_file, trace=False):
    """Parse cross references from .parquet file.

    Parameters
    ----------
    reader : RecordReader
        Instance of subclass of RecordReader
    parquet_file : str
        Path to the parquet_file
    xref_file : str
        Path to the .csv file to store the cross references
    """
    t0 = timer()
    df = pd.read_parquet(parquet_file)
    t1 = timer()
    if trace:
        print(f"loading {parquet_file} took {t1-t0} seconds")
    _prepare_csv(reader, xref_file)
    with open(xref_file, 'a') as f:
        df.apply(lambda row: _parse_record(reader, row, f, trace), axis=1)
    t2 = timer()
    if trace:
        print(f"converting to summary file took {t2-t1} seconds")


class ColumnSpec:
    """A class used to represent a column specification.

    Attributes
    ----------
    name : str
        the name of column
    quoted : bool
        whether to double quote this column

    """

    def __init__(self, name, quoted):
        """Create a instance of `ColumnSpec` object.

        Parameters
        ----------
        name : str
            the name of column
        quoted : bool
            whether to double quote this column
        """
        self._name = name
        self._quoted = quoted

    @property
    def name(self):
        """Return name."""
        return self._name

    @property
    def quoted(self):
        """Return quoted."""
        return self._quoted

    def __repr__(self):
        """Represnt this object as a string for debug purpose."""
        return f"mod: {self.name}, version: {self.quoted}"

    def __str__(self):
        """Represnt this object as a string."""
        return f"{self.name} {self.quoted}"


class RecordReader:
    """A class to process one record of commit, comment etc.

    Attributes
    ----------
    columns : list
        list of ColumnSpec the recrod is parsed into
    """

    def __init__(self, columnSpecs):
        """Create a instance of `RecordReader` object.

        Parameters
        ----------
        columnSpecs: list
            list of columns the recrod is parsed into
        """
        self._columns = columnSpecs

    def parse(self, repo, line):
        """Parse the text into columns.

        Parameters
        ----------
        repo : str
            The repo name
        line : str
            A text line representing a record, usually in JSON format

        Returns
        -------
        List of tuples of values representing columns of the record

        """
        return None

    @property
    def columns(self):
        """Return columns."""
        return self._columns

    def __repr__(self):
        """Represnt this object as a string for debug purpose."""
        return f"columns: {self.columns}"

    def __str__(self):
        """Represnt this object as a string."""
        return f"columns: {self.columns}"


class CommitSummaryRecordReader(RecordReader):
    """This class extracts xref from commit comment."""

    def __init__(self):
        """Create a instance of `CommitSummaryRecordReader` object."""
        specs = [
            ColumnSpec('sha', False),
            ColumnSpec('full_name', False),
            ColumnSpec('author_name', True),
            ColumnSpec('author_date', False),
            ColumnSpec('verified', False),
        ]
        super().__init__(specs)

    def parse(self, repo, line):
        """Parse the text into columns.

        Parameters
        ----------
        repo : str
            The repo name
        line : str
            A text line representing a record, usually in JSON format

        Returns
        -------
        List of tuples of values representing columns of the record
        """
        xrefs = []
        commit_obj = json.loads(line)
        sha = commit_obj['sha']
        author_name = commit_obj['commit']['author']['name']
        author_date = convert_iso_date(commit_obj['commit']['author']['date'])
        verified = commit_obj['commit']['verification'].get("verified", False)
        xrefs.append(
            (sha, repo, author_name, author_date, '1' if verified else '0')
        )
        return xrefs


class CommitXrefRecordReader(RecordReader):
    """This class extracts xref from commit comment."""

    def __init__(self):
        """Create a instance of `CommitXrefRecordReader` object."""
        specs = [
            ColumnSpec('id', False),
            ColumnSpec('src_repo', False),
            ColumnSpec('dest_repo', False),
            ColumnSpec('issue_no', False),
        ]
        super().__init__(specs)

    def parse(self, repo, line):
        """Parse the text into columns.

        Parameters
        ----------
        repo : str
            The repo name
        line : str
            A text line representing a record, usually in JSON format

        Returns
        -------
        List of tuples of values representing columns of the record
        """
        xrefs = []
        commit_obj = json.loads(line)
        id = commit_obj['sha']
        msg = commit_obj['commit'].get('message', '')
        for m in re.finditer(XrefPat, msg):
            if repo != m.group(1):
                xrefs.append((id, repo, m.group(1), m.group(2)))
        return xrefs


class CommentXrefRecordReader(RecordReader):
    """This class extracts xref from issue comments."""

    def __init__(self):
        """Create a instance of `CommentXrefRecordReader` object."""
        specs = [
            ColumnSpec('id', False),
            ColumnSpec('src_repo', False),
            ColumnSpec('dest_repo', False),
            ColumnSpec('issue_no', False),
        ]
        super().__init__(specs)

    def parse(self, repo, line):
        """Parse the text into columns.

        Parameters
        ----------
        repo : str
            The repo name
        line : str
            A text line representing a record, usually in JSON format

        Returns
        -------
        List of tuples of values representing columns of the record
        """
        xrefs = []
        comment_obj = json.loads(line)
        id = comment_obj['id']
        msg = comment_obj.get('body', '')
        for m in re.finditer(XrefPat, msg):
            if repo != m.group(1):
                xrefs.append((id, repo, m.group(1), m.group(2)))
        return xrefs


def _persist_records(reader, records, f):
    colSpecs = reader.columns
    for record in records:
        values = []
        for i, col in enumerate(record):
            if colSpecs[i].quoted:
                values.append(f'"{col}"')
            else:
                values.append(col)
        f.write(f"{','.join(values)}\n")


def _prepare_csv(reader, record_file):
    sub = Path(record_file[0:-len(record_file)])
    sub.mkdir(parents=True, exist_ok=True)
    if not Path(record_file).exists():
        with open(record_file, 'w') as f:
            f.write(f"{','.join([c.name for c in reader.columns])}\n")


def _parse_record(reader, row, f, trace):
    repo = row["repo"]
    lines = row["content"].split("\n")
    for line in lines:
        if line.find('{') < 0:
            continue
        try:
            records = reader.parse(repo, line)
            _persist_records(reader, records, f)
        except Exception as e:
            if trace:
                print(f"Fail to parse: {line} due to: {e}")
            continue
