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
    assert chunksize > 0, chunksize
    totalsize = len(sequence)
    nchunks, rest = divmod(totalsize, chunksize)
    for i in xrange(nchunks):
        yield sequence[i * chunksize: (i + 1) * chunksize]
    if rest:
        yield sequence[(i + 1) * chunksize:]


# not a method, so it can be easily pickled
def runsafe(traceback_on, func, *args, **kw):
    """
    Run a function and returns a triplet (result, exc, traceback).
    If there is an exception the result is the exception type, otherwise
    exc and traceback are None. The traceback can be ignored to avoid
    pickle issues (tracebacks are not pickeable).
    """
    try:
        res = func(*args, **kw)
    except Exception:
        etype, exc, tb = sys.exc_info()
        if not traceback_on:
            traceback.print_tb(tb)
            tb = None
        return etype, exc, tb
    else:
        return res, None, None


def getname(func):
    "The name of a callable"
    try:
        return func.__name__
    except AttributeError:
        return '<%s>' % func.__class__.__name__


class FakeFuture(object):
    "A replacement for a real :class:concurrent.futures.Future object"
    def __init__(self, thunk):
        self.thunk = thunk

    def result(self):
        return self.thunk


class BaseRunner(object):
    """
    Implements the basic functionality of the parallel runner, but
    runs everything in the current process; should be used to debug
    issues in the parallel runner.
    """
    def __init__(self, chunksize=None,
                 agg=lambda acc, res: acc + res, seed=None,
                 logger=None, executor=None):
        self.chunksize = chunksize
        self.agg = agg
        self.seed = [] if seed is None else seed
        self.log = logger or logging.getLogger(__name__)
        self.cpu_count = cc = multiprocessing.cpu_count()
        self.executor = executor or futures.ThreadPoolExecutor(cc)

    def __enter__(self):
        self.executor.__enter__()
        return self

    def __exit__(self, etype, exc, tb):
        self.executor.__exit__(etype, exc, tb)

    def todo(self, func, chunks, args, kw):
        "Returns the operations to perform (iterator over futures)"
        traceback_on = True
        for chunkno, chunk in enumerate(chunks):
            ff = FakeFuture(
                lambda: runsafe(traceback_on, func, chunk, *args, **kw))
            ff.chunkno = chunkno
            yield ff

    def run(self, func, sequence, *args, **kw):
        chunksize = self.chunksize or (len(sequence) // self.cpu_count + 1)
        acc = self.seed
        t0 = time.time()
        chunks = list(chop(sequence, chunksize))
        nchunks = len(chunks)
        self.log.info(
            'Started %s with %s, processing %d elements in %d chunks of '
            'a most %d elements', getname(func), self.__class__.__name__,
            len(sequence), nchunks, chunksize)
        todo = self.todo(func, chunks, args, kw)
        for i, fut in enumerate(todo):
            res, exc, tb = fut.result()
            if exc is not None:
                err = 'in chunk %s: %s' % (fut.chunkno, exc)
                raise res, err, tb
            acc = self.agg(acc, res)
            self.log.info('Processed chunk %d, progress=%0.3f>',
                          fut.chunkno, float(i + 1) / nchunks)
        self.log.info('Finished %s in %f seconds',
                      getname(func), time.time() - t0)
        return acc


class Runner(BaseRunner):
    """
    Parallel runner. It is able to run any callable with signature
    (sequence, *args, **kw) in parallel, by splitting the sequence
    in chunks and by submitting each chunk to the executor. By default the
    results are collected together with the `+` operator, i.e. if the
    callable returns a list the final result is the total list obtained
    by summing the chunks result. It is possible however to pass a different
    aggregation function and a different seed.
    """
    def todo(self, func, chunks, args, kw):
        "Returns the operations to perform (iterator over futures)"
        traceback_on = isinstance(self.executor, futures.ThreadPoolExecutor)
        futs = []
        for chunkno, chunk in enumerate(chunks):
            fut = self.executor.submit(
                runsafe, traceback_on, func, chunk, *args, **kw)
            fut.chunkno = chunkno
            futs.append(fut)
        for fut in futures.as_completed(futs):
            yield fut


def run_calc(path, config='job.ini'):
    """
    Reads the input in path (which can be a directory or a zip archive)
    and performs the risk calculation. The calculation is inferred from
    the calculation_mode parameter in the configuration file, which must
    be present in the input directory/archive.
    """
    inp = readers.read_calculator_input(path, config)
    calculator = calculators.registry[inp['calculation_mode']]
    with Runner(executor=futures.ProcessPoolExecutor()) as runner:
        calculator(inp, runner)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    run_calc(*sys.argv[1:])
