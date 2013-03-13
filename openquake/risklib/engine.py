#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2010-2013, GEM foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

"""
A minimal engine using the risklib calculators
"""
from __future__ import print_function
import sys
import traceback
import logging
import time
import multiprocessing
from concurrent import futures
from openquake.risklib import calculators, readers


def chop(sequence, chunksize):
    "Split a sequence in chunks"
    totalsize = len(sequence)
    nchunks, rest = divmod(totalsize, chunksize)
    for i in xrange(nchunks):
        yield sequence[i * chunksize: (i + 1) * chunksize]
    if rest:
        yield sequence[(i + 1) * chunksize:]


# not a method, so it can be easily pickled
def runsafe(executorcls, func, *args, **kw):
    """
    Run a function and returns a triplet (result, exc, traceback).
    If there is an exception the result is the exception type, otherwise
    exc and traceback are None. The traceback is always None if the executorcls
    is ProcessPoolExecutor, to avoid pickle issues (tracebacks are not
    pickeable).
    """
    try:
        res = func(*args, **kw)
    except Exception:
        etype, exc, tb = sys.exc_info()
        if issubclass(executorcls, futures.ProcessPoolExecutor):
            # tracebacks are not pickeable :-(
            traceback.print_tb(tb)
            tb = None
        return etype, exc, tb
    else:
        return res, None, None


def getname(func):
    try:
        return func.__name__
    except AttributeError:
        return '<%s>' % func.__class__.__name__


class BaseRunner(object):
    """
    Implements the basic functionality of the parallel runner, but
    runs everything in the current process; should used to debug
    issues in the parallel runner.
    """
    def __init__(self, chunksize=None,
                 agg=lambda acc, res: acc + res, acc=None,
                 logger=None, executor=None):
        self.chunksize = chunksize
        self.agg = agg
        self.acc = [] if acc is None else acc
        self.log = logger or logging.getLogger(__name__)
        self.cpu_count = cc = multiprocessing.cpu_count()
        self.executor = executor or futures.ThreadPoolExecutor(cc)

    def run(self, func, sequence, *args, **kw):
        chunksize = self.chunksize or (len(sequence) // self.cpu_count + 1)
        acc = self.acc
        t0 = time.time()
        lst = list(chop(sequence, chunksize))
        nchunks = len(lst)
        self.log.info('Starting %s (sequential)', getname(func))
        for chunkno, chunk in enumerate(lst):
            res, exc, tb = runsafe(
                self.executor.__class__, func, chunk, *args, **kw)
            if exc is not None:
                err = 'in future %s: %s' % (chunkno, exc)
                raise res, err, tb
            acc = self.agg(acc, res)
            self.log.info('Processed chunk %d, progress=%0.3f>',
                          chunkno, float(chunkno + 1) / nchunks)
        self.log.info('Finished %s (sequential) in %f seconds',
                      getname(func), time.time() - t0)
        return acc


class Runner(BaseRunner):
    """
    Parallel runner.
    """
    def run(self, func, sequence, *args, **kw):
        chunksize = self.chunksize or (len(sequence) // self.cpu_count + 1)
        acc = self.acc
        t0 = time.time()
        self.log.info('Starting %s (parallel)', getname(func))

        futs = []
        for chunkno, chunk in enumerate(chop(sequence, chunksize)):
            fut = self.executor.submit(
                runsafe, self.executor.__class__, func, chunk, *args, **kw)
            fut.chunkno = chunkno
            futs.append(fut)

        nchunks = len(futs)
        for i, fut in enumerate(futures.as_completed(futs)):
            res, exc, tb = fut.result()
            if exc is not None:
                err = 'in future %s: %s' % (fut.chunkno, exc)
                raise res, err, tb
            acc = self.agg(acc, res)
            self.log.info('Processed chunk %d, progress=%0.3f>',
                          fut.chunkno, float(i + 1) / nchunks)
        self.log.info('Finished %s (parallel) in %f seconds', getname(func),
                      time.time() - t0)
        return acc


def run_calc(path, config='job.ini'):
    inp = readers.read_calculator_input(path, config)
    calculator = calculators.registry[inp['calculation_mode']]
    with futures.ProcessPoolExecutor() as ex:
        calculator(inp, BaseRunner(executor=ex))

if __name__ == '__main__':
    run_calc(sys.argv[1])
