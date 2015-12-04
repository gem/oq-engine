#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2014, GEM Foundation

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
from __future__ import print_function
import collections
import logging
import cProfile
import pstats
import io

from openquake.baselib import performance, general
from openquake.commonlib import sap, readinput, valid, datastore
from openquake.calculators import base, views

calc_path = None  # set only when the flag --profile is given

PStatData = collections.namedtuple(
    'PStatData', 'ncalls tottime percall cumtime percall2 path')


def get_pstats(pstatfile, n):
    """
    Return profiling information as an RST table.

    :param pstatfile: path to a .pstat file
    :param n: the maximum number of stats to retrieve
    """
    stream = io.BytesIO()
    ps = pstats.Stats(pstatfile, stream=stream)
    ps.sort_stats('cumtime')
    ps.print_stats(n)
    lines = stream.getvalue().splitlines()
    for i, line in enumerate(lines):
        if line.startswith('   ncalls'):
            break
    data = []
    for line in lines[i + 2:]:
        columns = line.split()
        if len(columns) == 6:
            data.append(PStatData(*columns))
    rows = [(rec.ncalls, rec.cumtime, rec.path) for rec in data]
    # here is an example of the expected output table:
    # ====== ======= ========================================================
    # ncalls cumtime path
    # ====== ======= ========================================================
    # 1      33.502  commonlib/commands/run.py:77(_run)
    # 1      33.483  calculators/base.py:110(run)
    # 1      25.166  calculators/classical.py:115(execute)
    # 1      25.104  commonlib/parallel.py:249(apply_reduce)
    # 1      25.099  calculators/classical.py:41(classical)
    # 1      25.099  hazardlib/calc/hazard_curve.py:164(hazard_curves_per_trt)
    return views.rst_table(rows, header='ncalls cumtime path'.split())


def run2(job_haz, job_risk, concurrent_tasks, pdb, exports, monitor):
    """
    Run both hazard and risk, one after the other
    """
    hcalc = base.calculators(readinput.get_oqparam(job_haz), monitor)
    with monitor:
        hcalc.run(concurrent_tasks=concurrent_tasks, pdb=pdb, exports=exports)
        hc_id = hcalc.datastore.calc_id
        oq = readinput.get_oqparam(job_risk, hc_id=hc_id)
        rcalc = base.calculators(oq, monitor)
        rcalc.run(concurrent_tasks=concurrent_tasks, pdb=pdb, exports=exports,
                  hazard_calculation_id=hc_id)
    return rcalc


def _run(job_ini, concurrent_tasks=0, pdb=0, loglevel='info',
         hc=0, exports=''):
    global calc_path
    logging.basicConfig(level=getattr(logging, loglevel.upper()))
    job_inis = job_ini.split(',')
    assert len(job_inis) in (1, 2), job_inis
    monitor = performance.PerformanceMonitor(
        'total runtime', measuremem=True)

    if len(job_inis) == 1:  # run hazard or risk
        oqparam = readinput.get_oqparam(job_inis[0], hc_id=hc)
        if hc and hc < 0:  # interpret negative calculation ids
            calc_ids = datastore.get_calc_ids()
            try:
                hc = calc_ids[hc]
            except IndexError:
                raise SystemExit('There are %d old calculations, cannot '
                                 'retrieve the %s' % (len(calc_ids), hc))
        calc = base.calculators(oqparam, monitor)
        with monitor:
            calc.run(concurrent_tasks=concurrent_tasks, pdb=pdb,
                     exports=exports, hazard_calculation_id=hc)
    else:  # run hazard + risk
        calc = run2(
            job_inis[0], job_inis[1], concurrent_tasks, pdb, exports, monitor)

    logging.info('Total time spent: %s s', monitor.duration)
    logging.info('Memory allocated: %s', general.humansize(monitor.mem))
    monitor.flush()
    print('See the output with hdfview %s' % calc.datastore.hdf5path)
    calc_path = calc.datastore.calc_dir  # used to deduce the .pstat filename
    return calc


def run(job_ini, concurrent_tasks=None, pdb=None,
        loglevel='info', hc=None, exports='', profile=0):
    """
    Run a calculation.

    :param job_ini:
        the configuration file (or filew, comma-separated)
    :param concurrent_tasks:
        the number of concurrent tasks (0 to disable the parallelization).
    :param pdb:
        flag to enable pdb debugging on failing calculations
    :param loglevel:
        the logging level (default 'info')
    :param hc:
        ID of the previous calculation (or None)
    :param exports:
        export type, can be '', 'csv', 'xml', 'geojson' or combinations
    :param profile:
        enable Python cProfile functionality
    """
    if profile:
        prof = cProfile.Profile()
        stmt = '_run(job_ini, concurrent_tasks, pdb, loglevel, hc, exports)'
        prof.runctx(stmt, globals(), locals())
        pstat = calc_path + '.pstat'
        prof.dump_stats(pstat)
        print('Saved profiling info in %s' % pstat)
        print(get_pstats(pstat, profile))
    else:
        _run(job_ini, concurrent_tasks, pdb, loglevel, hc, exports)

parser = sap.Parser(run)
parser.arg('job_ini', 'calculation configuration file '
           '(or files, comma-separated)')
parser.opt('concurrent_tasks', 'hint for the number of tasks to spawn',
           type=int)
parser.flg('pdb', 'enable post mortem debugging', '-d')
parser.opt('loglevel', 'logging level',
           choices='debug info warn error critical'.split())
parser.opt('hc', 'previous calculation ID', type=int)
parser.opt('exports', 'export formats as a comma-separated string',
           type=valid.export_formats)
parser.opt('profile', 'enable profiling', type=int)
