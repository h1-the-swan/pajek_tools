# -*- coding: utf-8 -*-

DESCRIPTION = """Pajek Tools"""

import sys, os, time
from pathlib import Path
from datetime import datetime
from timeit import default_timer as timer
try:
    from humanfriendly import format_timespan
except ImportError:
    def format_timespan(seconds):
        return "{:.2f} seconds".format(seconds)

import logging
logging.basicConfig(format='%(asctime)s %(name)s.%(lineno)d %(levelname)s : %(message)s',
        datefmt="%H:%M:%S",
        level=logging.INFO)
# logger = logging.getLogger(__name__)
logger = logging.getLogger('__main__').getChild(__name__)

import pandas as pd
import numpy as np
from csv import QUOTE_NONE

class PajekWriter:

    """Take a network as an edgelist and output a Pajek (.net) file"""

    def __init__(self, edgelist, weighted=False, vertices_label='Vertices', edges_label=None, directed=True, citing_colname='ID', cited_colname='cited_ID'):
        """
        
        Parameters
        ----------
        edgelist : pandas dataframe
            Should have a column for citing node name and cited node name. 
            Optional column for weight.
        weighted : `bool`, optional
            Is this a weighted network?
        vertices_label : `str`, default: "Vertices"
            label to use for the vertices
        edges_label : `str`, optional
            label to use for the edges. If None, "Arcs" will be used for 
            directed networks, and "Edges" for undirected
        directed : `bool`, default: True
            Is this a directed network?
        citing_colname : `str`, default: "ID"
            Column label for the citing node name (default: "ID")
        cited_colname : `str`, default: "cited_ID"
            Column label for the cited node name (default: "cited_ID")

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

        self.df_vertices = None
        self.id_map = None

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
        """dataframe of unique node names and assigned integer node IDs

        """
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
        x = np.concatenate((self.df_edgelist[self.citing_colname], self.df_edgelist[self.cited_colname]), axis=0)
        x = np.unique(x)
        df_vertices = pd.DataFrame(x, columns=['node_name'])
        df_vertices['node_id'] = range(1, len(df_vertices)+1)
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
        self.id_map = df_vertices.set_index('node_name')['node_id']
        return self.id_map

    def write(self, outf):
        """Write the network to a Pajek (.net) file

        Parameters
        ----------
        outf : str or Path
            path to output file (will be overwritten if exists)

        """
        if not self.id_map:
            if not self.df_vertices:
                self.df_vertices = self.get_df_vertices()
            self.id_map = self.get_id_map(self.df_vertices)
        outfpath = Path(outf)
        quotechar = '"'
        with open(outfpath, 'w') as outfile:
            outfile.write('*{} {}\n'.format(self.vertices_label, self.num_vertices))
            ids_out = self.df_vertices
            ids_out['node_name'] = ids_out['node_name'].astype(str)
            ids_out['node_name'] = quotechar + ids_out['node_name'] + quotechar
            ids_out[['node_id', 'node_name']].to_csv(outfile, sep=' ', index=False, header=False, quoting=QUOTE_NONE)

            outfile.write('*{} {}\n'.format(self.edges_label, self.num_edges))

            edges_out = self.df_edgelist
            edges_out['citing_id'] = edges_out[self.citing_colname].map(self.id_map)
            edges_out['cited_id'] = edges_out[self.cited_colname].map(self.id_map)
            edges_out[['citing_id', 'cited_id']].to_csv(outfile, sep=' ', index=False, header=False)

        

def main(args):
    pass

if __name__ == "__main__":
    total_start = timer()
    logger.info(" ".join(sys.argv))
    logger.info( '{:%Y-%m-%d %H:%M:%S}'.format(datetime.now()) )
    import argparse
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument("--debug", action='store_true', help="output debugging info")
    global args
    args = parser.parse_args()
    if args.debug:
        logger.setLevel(logging.DEBUG)
        logger.debug('debug mode is on')
    else:
        logger.setLevel(logging.INFO)
    main(args)
    total_end = timer()
    logger.info('all finished. total time: {}'.format(format_timespan(total_end-total_start)))
