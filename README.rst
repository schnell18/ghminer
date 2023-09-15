=========
 ghminer
=========

A library for MSR research.


Requirements
============

* Python 3.7 over

Features
========

* Search and extract Github repositories to build dataset in .csv and .parquet format.
* Retrieve commit, issue comments
* Parse golang go.mod file
* Work with Github's API rate limit, pagination
* Confine search results below 1000

Setup
=====

::

  $ python -m venv /path/to/venv
  $ /path/to/venv/bin/python -m pip install ghminer

Usage
=====

To identify repositories for your MSR research, please refer to
the script `identify-repos.py`. To retrieve commits, use the script
`retrieve-commits.py`.

::

  $ /path/to/venv/bin/python
  >>> import ghminer
  >>> ghminer.version.__version__
  >>>

