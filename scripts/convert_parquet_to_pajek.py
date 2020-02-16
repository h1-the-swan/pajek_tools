# -*- coding: utf-8 -*-

DESCRIPTION = """Convert parquet edgelist (unweighted) to pajek"""

import logging
root_logger = logging.getLogger()
logger = root_logger.getChild(__name__)

import sys, os, time
from pathlib import Path
from datetime import datetime
from timeit import default_timer as timer
try:
    from humanfriendly import format_timespan
except ImportError:
    def format_timespan(seconds):
        return "{:.2f} seconds".format(seconds)

import pandas as pd
from pajek_tools import PajekWriter

def main(args):
    directed = not args.undirected
    logger.debug("Input network is {}directed".format("" if directed else "not "))
    logger.debug("Using input: {}".format(args.input))
    start = timer()
    df = pd.read_parquet(args.input)
    logger.debug("loading input took {}".format(format_timespan(timer()-start)))
    if args.citing_colname not in df.columns or args.cited_colname not in df.columns:
        raise RuntimeError("one of [citing_colname ({}), cited_colname ({})] not in df.columns ({})".format(args.citing_colname, args.cited_colname, df.columns))
    logger.debug("writing to output: {}".format(args.output))
    start = timer()
    writer = PajekWriter(df, directed=directed, citing_colname=args.citing_colname, cited_colname=args.cited_colname)
    writer.write(args.output)
    logger.debug("done writing to file. writing took {}".format(format_timespan(timer()-start)))

if __name__ == "__main__":
    total_start = timer()
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(fmt="%(asctime)s %(name)s.%(lineno)d %(levelname)s : %(message)s", datefmt="%H:%M:%S"))
    root_logger.addHandler(handler)
    logger.info(" ".join(sys.argv))
    logger.info( '{:%Y-%m-%d %H:%M:%S}'.format(datetime.now()) )
    import argparse
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument("input", help="input parquet")
    parser.add_argument("output", help="path to output parquet (.net)")
    parser.add_argument("--citing-colname", default="PaperId", help="column name for citing nodes")
    parser.add_argument("--cited-colname", default="PaperReferenceId", help="column name for cited nodes")
    parser.add_argument("--undirected", action='store_true', help="network is undirected")
    parser.add_argument("--debug", action='store_true', help="output debugging info")
    global args
    args = parser.parse_args()
    if args.debug:
        root_logger.setLevel(logging.DEBUG)
        logger.debug('debug mode is on')
    else:
        root_logger.setLevel(logging.INFO)
    main(args)
    total_end = timer()
    logger.info('all finished. total time: {}'.format(format_timespan(total_end-total_start)))
