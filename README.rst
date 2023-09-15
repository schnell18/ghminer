=========
 ghminer
=========

A library and toolkit for MSR research.

Mining software repository has been a popular research method for quite
long time. Although github offers convenient public REST and GraphQL
API, collecting large scale dataset with long history of information
such as repository, author, bot, issues, pull request, comment is still
a non-trivial task. There are three major challenges to be solved in
order to retrieve large search results from github:

* 1000-limit issue: github API discards records beyond 1000 in the result set
  of a particular query.
* rate-limit issue: github API prevents authenticated personal accounts from
  invoking API more than 5000 times per hour.
* pagination: User has to issue multiple API calls to retrieve the complete
  query results over 100 records.


When the client exceeds the rate limit, it is disconnected with HTTP status
code 503. Without proper recover handling, data collection process is subject
to frequent interruptions.

This library and assoicated scripts are intended to help solve the three
challenges so that you can focus on the data mining rather than data
collection.

Requirements
============

* Python 3.7 over

Features
========

* Search Github repositories based on stars, fork, language and topic
* Search a large number of repositories by dividing creation time into small
  time window
* Support multiple topics with `OR` relation
* Build dataset in .csv and .parquet format
* Retrieve commit, issue comments
* Golang miner with go.mod retrieval and parsing

Setup
=====

::

  $ python -m venv /path/to/venv
  $ /path/to/venv/bin/python -m pip install ghminer

Usage
=====

To identify repositories for your MSR research, please refer to
the script `identify-repos.py`. To retrieve commits, use the script
`retrieve-commits.py`. To mine golang projects, use the script
`golang-miner`.

::

  >>> from ghminer.retriever import collect_data
  >>> collect_data(
          2022, 2023, None, True, 100, 15,
          "repo.d", "java", trace=trace
      )
