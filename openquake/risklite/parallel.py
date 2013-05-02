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
from openquake.concurrent import futures
from openquake.risklite import calculators, readers

log = logging.getLogger(__name__)


def chop(sequence, chunksize):
    "Split a sequence in chunks"
    assert chunksize > 0, chunksize
    totalsize = len(sequence)
    nchunks, rest = divmod(totalsize, chunksize)
    i = -1
    for i in xrange(nchunks):
        yield sequence[i * chunksize: (i + 1) * chunksize]
    if rest:
        yield sequence[(i + 1) * chunksize:]


# not a method, so it can be easily pickled
def runsafe(traceback_off, func, *args, **kw):
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
        if traceback_off:
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
    "A replacement for a real :class:openquake.concurrent.futures.Future object"
    def __init__(self, thunk):
        self.thunk = thunk

    def result(self):
        return self.thunk()


class FakeExecutor(object):
    def __init__(self):
        self._max_workers = 1


class BaseRunner(object):
    """
    Implements the basic functionality of the parallel runner, but
    runs everything in the current process; should be used to debug
    issues in the parallel runner (the advantage is that the pdb works).
    """
    def __init__(self, executor=FakeExecutor(), chunksize=None,
                 agg=lambda acc, res: acc + res, seed=None):
        self.executor = executor
        self.chunksize = chunksize
        self.poolsize = executor._max_workers
        self.agg = agg
        self.seed = [] if seed is None else seed

    def futures(self, func, chunks, args, kw):
        "Returns the operations to perform (iterator over futures)"
        traceback_off = False
        for chunkno, chunk in enumerate(chunks):
            ff = FakeFuture(
                lambda: runsafe(traceback_off, func, chunk, *args, **kw))
            ff.chunkno = chunkno
            yield ff

    def processed_future(self, fut, progress):
        "Hook invoked every time a future has been processed"
        log.info('Processed chunk %d, progress=%0.3f>', fut.chunkno, progress)

    def run(self, func, sequence, *args, **kw):
        """
        Apply ``func`` to the arguments (the first beeing a sequence)
        and collect the results. See the documentation in doc/risklite.rst
        """
        nelements = len(sequence)
        chunksize = self.chunksize or (nelements // self.poolsize + 1)
        chunks = list(chop(sequence, chunksize))
        nchunks = len(chunks)
        reslist = [None] * nchunks  # chunk accumulator
        for i, fut in enumerate(self.futures(func, chunks, args, kw)):
            res, exc, tb = fut.result()
            if exc is not None:
                err = 'in chunk %s: %s' % (fut.chunkno, exc)
                raise res, err, tb
            reslist[fut.chunkno] = res
            self.processed_future(fut, progress=float(i + 1) / nchunks)
        return reduce(self.agg, reslist, self.seed)

    def __repr__(self):
        return '<%s(%s(%d))>' % (
            self.__class__.__name__, self.executor.__class__.__name__,
            self.poolsize)


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
    def futures(self, func, chunks, args, kw):
        "Returns the operations to perform (iterator over futures)"
        traceback_off = isinstance(self.executor, futures.ProcessPoolExecutor)
        chunkno = 0
        for chunkset in chop(chunks, self.poolsize):
            # fill the pool with a set of chunks
            futs = []
            for chunk in chunkset:
                fut = self.executor.submit(
                    runsafe, traceback_off, func, chunk, *args, **kw)
                fut.chunkno = chunkno
                futs.append(fut)
                chunkno += 1
            # perform the computation of the chunkset
            for fut in futures.as_completed(futs):
                yield fut


def run_calc(path, runner, config='job.ini'):
    """
    Reads the input in path (which can be a directory or a zip archive)
    and performs the risk calculation. The calculation is inferred from
    the calculation_mode parameter in the configuration file, which must
    be present in the input directory/archive.
    """
    inp = readers.read_calculator_input(path, config)
    inp['calculator'] = calculators.registry[inp['calculation_mode']]
    inp['calculator'](inp, runner)
    return inp
