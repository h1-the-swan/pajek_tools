# -*- coding: utf-8 -*-

DESCRIPTION = """Pajek Tools"""

import sys, os, time, gc
from pathlib import Path
from typing import Optional
from datetime import datetime
from timeit import default_timer as timer

try:
    from humanfriendly import format_timespan
except ImportError:

    def format_timespan(seconds):
        return "{:.2f} seconds".format(seconds)


import logging

# logging.basicConfig(format='%(asctime)s %(name)s.%(lineno)d %(levelname)s : %(message)s',
#         datefmt="%H:%M:%S",
#         level=logging.INFO)
# logger = logging.getLogger(__name__)
# logger = logging.getLogger('__main__').getChild(__name__)
logger = logging.getLogger(__name__)
# logger.addHandler(logging.NullHandler())

import pandas as pd
import numpy as np
from csv import QUOTE_NONE


class PajekWriter:

    """Take a network as an edgelist and output a Pajek (.net) file"""

    def __init__(
        self,
        edgelist: pd.DataFrame,
        weighted: bool = False,
        vertices_label: str = "Vertices",
        edges_label: Optional[str] = None,
        directed: bool = True,
        citing_colname: str = "ID",
        cited_colname: str = "cited_ID",
        weight_colname: str = "weight",
        dtype: str = "str",
    ):
        """

        Parameters
        ----------
        edgelist : pandas dataframe
            Should have a column for citing node name and cited node name.
            Optional column for weight.
        weighted : `bool`, optional
            Is this a network with weighted edges?
        vertices_label : `str`, default: "Vertices"
            label to use for the vertices
        edges_label : `str`, optional
            label to use for the edges. If None, "Arcs" will be used for
            directed networks, and "Edges" for undirected
        directed : `bool`, default: True
            Is this a directed network?
        citing_colname : `str`, default: "ID"
            Column label for the citing node name
        cited_colname : `str`, default: "cited_ID"
            Column label for the cited node name
        weight_colname : `str`, default: "weight"
            Column label for the edge weight, if this is a weighted network
        dtype: 'str', default: "str"
            Data type for the citing/cited ID columns

        """
        self.df_edgelist = edgelist
        self.weighted = weighted
        self.vertices_label = vertices_label
        self.directed = directed
        if edges_label:
            self.edges_label = edges_label
        else:
            if self.directed:
                self.edges_label = "Arcs"
            else:
                self.edges_label = "Edges"
        self.citing_colname = citing_colname
        self.cited_colname = cited_colname
        self.weight_colname = weight_colname
        self.dtype = dtype

        self.df_edgelist[citing_colname] = self.df_edgelist[citing_colname].astype(self.dtype)
        self.df_edgelist[cited_colname] = self.df_edgelist[cited_colname].astype(self.dtype)

        self.df_vertices = None
        self.id_map = None

        logger.debug("PajekWriter initialized")

    @property
    def df_edgelist(self):
        """
        edgelist : pandas dataframe
            Should have a column for citing node name and cited node name.
            Optional column for weight.
        self.df_edgelist = self.

        """
        return self._df_edgelist

    @df_edgelist.setter
    def df_edgelist(self, value):
        self._df_edgelist = value
        if self._df_edgelist is not None:
            self.num_edges = len(self.df_edgelist)

    @property
    def df_vertices(self):
        """dataframe of unique node names and assigned integer node IDs"""
        return self._df_vertices

    @df_vertices.setter
    def df_vertices(self, value):
        self._df_vertices = value
        if self._df_vertices is not None:
            self.num_vertices = len(self.df_vertices)

    def get_df_vertices(self):
        """Get a dataframe of unique node names and assinged integer node IDs

        Returns
        -------
        Pandas dataframe

        """
        logger.debug("getting vertices dataframe...")
        x = np.concatenate(
            (
                self.df_edgelist[self.citing_colname],
                self.df_edgelist[self.cited_colname],
            ),
            axis=0,
        )
        x = np.unique(x)
        df_vertices = pd.DataFrame(x, columns=["node_name"])
        df_vertices["node_id"] = range(1, len(df_vertices) + 1)
        df_vertices["node_name"] = df_vertices["node_name"].astype(self.dtype)
        self.df_vertices = df_vertices
        return self.df_vertices

    def get_id_map(self, df_vertices):
        """Get a pandas Series mapping node name to assigned integer node ID

        Parameters
        ----------
        df_vertices : Pandas DataFrame
            dataframe with 'node_name' and 'node_id' columns

        Returns
        -------
        Pandas Series

        """
        logger.debug("getting ID map...")
        self.id_map = df_vertices.set_index("node_name")["node_id"]
        return self.id_map

    def write(self, outf, chunksize: int = 10000000, on_err: Optional[str] = None):
        """Write the network to a Pajek (.net) file

        Parameters
        ----------
        outf : str or Path
            path to output file (will be overwritten if exists)

        """
        if self.id_map is None:
            if self.df_vertices is None:
                self.df_vertices = self.get_df_vertices()
            self.id_map = self.get_id_map(self.df_vertices)
        self.df_edgelist["citing_id"] = self.df_edgelist[self.citing_colname].map(
            self.id_map
        )
        self.df_edgelist["cited_id"] = self.df_edgelist[self.cited_colname].map(
            self.id_map
        )
        outfpath = Path(outf)
        quotechar = '"'
        logger.debug("opening output file: {}".format(outfpath))
        with open(outfpath, "w", newline="\n") as outfile:
            logger.debug("writing {} vertices...".format(self.num_vertices))
            outfile.write("*{} {}\n".format(self.vertices_label, self.num_vertices))
            self.df_vertices["node_name"] = (
                quotechar + self.df_vertices["node_name"].astype(str) + quotechar
            )
            self.df_vertices[["node_id", "node_name"]].to_csv(
                outfile,
                sep=" ",
                index=False,
                header=False,
                quoting=QUOTE_NONE,
                line_terminator="\n",
                chunksize=chunksize,
            )

            logger.debug("writing {} edges...".format(self.num_edges))
            outfile.write("*{} {}\n".format(self.edges_label, self.num_edges))

            outcols = ["citing_id", "cited_id"]
            if self.weighted:
                outcols.append(self.weight_colname)
            try:
                self.df_edgelist[outcols].to_csv(
                    outfile,
                    sep=" ",
                    index=False,
                    header=False,
                    quoting=QUOTE_NONE,
                    line_terminator="\n",
                    chunksize=chunksize,
                )
            except MemoryError:
                if on_err == "ckpt_and_raise":
                    logger.debug(
                        "MemoryError encountered. Attempting to save pickle before raising exception."
                    )
                    gc.collect()
                    fpath_ckpt = outfpath.parent.joinpath(
                        "memerr_edgelist_ckpt_pandas.pickle"
                    )
                    logger.debug("saving df_edgelist to {}".format(fpath_ckpt))
                    self.df_edgelist.to_pickle(fpath_ckpt)
                raise


def main(args):
    pass


if __name__ == "__main__":
    total_start = timer()
    logger.info(" ".join(sys.argv))
    logger.info("{:%Y-%m-%d %H:%M:%S}".format(datetime.now()))
    import argparse

    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument("--debug", action="store_true", help="output debugging info")
    global args
    args = parser.parse_args()
    if args.debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("debug mode is on")
    else:
        logger.setLevel(logging.INFO)
    main(args)
    total_end = timer()
    logger.info(
        "all finished. total time: {}".format(format_timespan(total_end - total_start))
    )
