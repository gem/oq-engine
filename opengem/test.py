# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""
Helper functions for our unit and smoke tests.
"""

import logging
import os
import subprocess
from opengem import computation
from opengem import producer
from opengem import flags

FLAGS = flags.FLAGS

flags.DEFINE_boolean('download_test_data', False, 
        'Fetch test data files if needed')
        
DATA_DIR = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '../tests/data'))


class ConcatComputation(computation.Computation):
    """Simple computation step that concatenates args"""
    def __init__(self, pool, cell):
        keys = ['shake', 'roll']
        super(ConcatComputation, self).__init__(pool, cell, keys)

    def _compute(self, **kw):
        return ':'.join(str(x) for x in sorted(kw.values()))


class WordProducer(producer.FileProducer):
    """Simple File parser that looks for three 
    space-separated values on each line - lat, long and value"""
    def _parse(self):
        for line in self.file:
            col, row, value = line.strip().split(' ', 2)
            yield ((int(col), int(row)), value)


def guarantee_file(path, url):
    """Based on flag, download test data file or raise error."""
    if not os.path.isfile(path):
        if not FLAGS.download_test_data:
            raise Exception("Test data does not exist")
        logging.info("Downloading test data for %s", path)
        retcode = subprocess.call(["curl", url, "-o", path])
        if retcode:
            raise Exception("Test data could not be downloaded from %s" % (url))
            