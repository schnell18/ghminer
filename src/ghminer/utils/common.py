#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Common functions to serve other packages.

This module includes common functions such as:

    * configuration
    * date arithmetic
    * generic repository access

"""

import configparser
from datetime import date, timedelta


def load_access_token():
    """Load the github API access token from config file.

    Parameters
    ----------
    None

    Returns
    -------
    str
        the github access token
    """
    parser = configparser.ConfigParser()
    parser.read('credential.ini')
    section = parser['github']
    return section['access_token']


def load_repo_info(client, repo_name):
    """Access the github repository specified by `repo_name`.

    Parameters
    ----------
    None

    Returns
    -------
    Repository object
        the repository object
    """
    try:
        return client.get_repo(repo_name)
    except Exception as e:
        print(f"Fail to locate {repo_name} due to: {e}")
        return None


def daterange(start_date, end_date, slice):
    """Divide date range into smaller sub ranges.

    Parameters
    ----------
    start_date: date
        the start date of the range
    end_date: date
        the end date of the range, inclusive
    slice: int
        the size of time window in days

    Returns
    -------
    iteratable
        the list of sub date ranges as iteratable objects
    """
    tot_days = int((end_date - start_date).days) + 1
    periods = tot_days // slice
    remainder = tot_days % slice
    for n in range(periods):
        s = start_date + timedelta(n * slice)
        e = s + timedelta(slice - 1)
        yield (s, e)
    if remainder != 0:
        s = start_date + timedelta(periods * slice)
        e = s + timedelta(remainder - 1)
        yield (s, e)


def yearrange(start_year, end_year, slice):
    """Divide year range into smaller sub ranges.

    Parameters
    ----------
    start_year: int
        the start year of the range
    end_year: int
        the end year of the range, inclusive
    slice: int
        the size of time window in years

    Returns
    -------
    iteratable
        the list of sub date ranges as iteratable objects
    """
    tot = end_year - start_year + 1
    periods = tot // slice
    remainder = tot % slice
    for n in range(periods):
        s = start_year + n * slice
        e = s + slice - 1
        yield (date(s, 1, 1), date(e, 12, 31))
    if remainder != 0:
        s = start_year + periods * slice
        e = s + remainder - 1
        yield (date(s, 1, 1), date(e, 12, 31))


def format_date(d):
    """Format date object into `YYYY-MM-DD` format.

    Parameters
    ----------
    d: date
        the date object

    Returns
    -------
    str
        the string representing date in `YYYY-MM-DD` format
    """
    return d.strftime("%Y-%m-%d")
