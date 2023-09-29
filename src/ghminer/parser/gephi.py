#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Package to convert cross references into gephi graph data file."""

import pandas as pd

from datetime import datetime
from hashlib import md5
from ghminer import __version__


def to_gexf(
        xref_file, gxef_file,
        src_col_name="src_repo",
        dest_col_name="dest_repo",
        weight_col_name="issue_no",
        weight_agg_func="count"):
    """
    Convert projects cross references to gephi gexf XML file.

    Parameters
    ----------
    xref_file : str
        the .csv containing at least name of source and destination node,
        weight of the cross reference
    gxef_file : str
        the .gxef file to generate, it uses the gephi 1.3 schema version
    src_col_name : str(optional)
        the column name in .csv file to represent the source node, default
        `src_repo`
    dest_col_name : str(optional)
        the column name in .csv file to represent the destination node,
        default `dest_repo`
    weight_col_name : str(optional)
        the column name in .csv file to represent the weight of xref, default
        `issue_no`
    weight_agg_func : str(optional)
        the name of function to aggregate the weight of xref, default `count`
    """
    df = pd.read_csv(xref_file)
    df = df.drop_duplicates()
    df = df.groupby([src_col_name, dest_col_name])
    df = df.agg(
        refs=pd.NamedAgg(column=weight_col_name, aggfunc=weight_agg_func)
    )
    df = df.sort_values("refs", ascending=False)
    _to_gexf(df, gxef_file)


def _to_gexf(df, file_name):
    header = f"""<?xml version="1.0" encoding="UTF-8"?>
<gexf xmlns="http://gexf.net/1.3" version="1.3">
  <meta lastmodifieddate="{datetime.now().strftime('%Y-%m-%d')}">
    <creator>ghminer {__version__}</creator>
    <keyowords>AI Github</keyowords>
    <description>Github AI projects cross reference data</description>
  </meta>
  <graph mode="static" defaultedgetype="directed">
"""

    footer = """
  </graph>
</gexf>
"""

    with open(file_name, "w") as f:
        f.write(header)
        f.write("    <nodes>\n")
        for ind in df.index:
            src, dest = ind
            f.write(f'      <node id="{src}" label="{src}" />\n')
            f.write(f'      <node id="{dest}" label="{dest}" />\n')
        f.write("    </nodes>\n")
        f.write("    <edges>\n")
        for ind in df.index:
            src, dest = ind
            edge_id = md5(bytes(f"{src}-{dest}", "utf-8")).hexdigest()
            weight = df['refs'][ind]
            f.write(
                '      <edge id="%s" source="%s" target="%s" weight="%s" />\n'
                % (edge_id, src, dest, weight)
            )
        f.write("    </edges>\n")
        f.write(footer)
