# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2021 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.
import collections
import tempfile
import logging
import os.path
import cProfile
import pstats

from openquake.baselib import performance, general, datastore, parallel
from openquake.hazardlib import valid
from openquake.commonlib import readinput, oqvalidation, logs
from openquake.calculators import base, views
from openquake.server import dbserver

calc_path = None  # set only when the flag --slowest is given

PStatData = collections.namedtuple(
    'PStatData', 'ncalls tottime percall cumtime percall2 path')

oqvalidation.OqParam.calculation_mode.validator.choices = tuple(
    base.calculators)


def get_pstats(pstatfile, n):
    """
    Return profiling information as an RST table.

    :param pstatfile: path to a .pstat file
    :param n: the maximum number of stats to retrieve
    """
    with tempfile.TemporaryFile(mode='w+') as stream:
        ps = pstats.Stats(pstatfile, stream=stream)
        ps.sort_stats('cumtime')
        ps.print_stats(n)
        stream.seek(0)
        lines = list(stream)
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
    # 1      33.502  commands/run.py:77(_run)
    # 1      33.483  calculators/base.py:110(run)
    # 1      25.166  calculators/classical.py:115(execute)
    # 1      25.104  baselib.parallel.py:249(apply_reduce)
    # 1      25.099  calculators/classical.py:41(classical)
    # 1      25.099  hazardlib/calc/hazard_curve.py:164(classical)
    return views.rst_table(rows, header='ncalls cumtime path'.split())


def run2(job_haz, job_risk, calc_id, concurrent_tasks, pdb, reuse_input,
         loglevel, exports, params):
    """
    Run both hazard and risk, one after the other
    """
    oq = readinput.get_oqparam(job_haz, kw=params)
    hcalc = base.calculators(oq, calc_id)
    hcalc.run(concurrent_tasks=concurrent_tasks, pdb=pdb, exports=exports)
    hcalc.datastore.close()
    hc_id = hcalc.datastore.calc_id
    rcalc_id = logs.init(level=getattr(logging, loglevel.upper()))
    params['hazard_calculation_id'] = str(hc_id)
    oq = readinput.get_oqparam(job_risk, kw=params)
    rcalc = base.calculators(oq, rcalc_id)
    if reuse_input:  # enable caching
        oq.cachedir = datastore.get_datadir()
    rcalc.run(pdb=pdb, exports=exports)
    return rcalc


# run with processpool unless OQ_DISTRIBUTE is set to something else
def _run(job_inis, concurrent_tasks, calc_id, pdb, reuse_input, loglevel,
         exports, params):
    global calc_path
    assert len(job_inis) in (1, 2), job_inis
    # set the logs first of all
    calc_id = logs.init(calc_id, getattr(logging, loglevel.upper()))
    # disable gzip_input
    base.BaseCalculator.gzip_inputs = lambda self: None
    with performance.Monitor('total runtime', measuremem=True) as monitor:
        if os.environ.get('OQ_DISTRIBUTE') not in ('no', 'processpool'):
            os.environ['OQ_DISTRIBUTE'] = 'processpool'
        if len(job_inis) == 1:  # run hazard or risk
            if 'hazard_calculation_id' in params:
                hc_id = int(params['hazard_calculation_id'])
            else:
                hc_id = None
            if hc_id and hc_id < 0:  # interpret negative calculation ids
                calc_ids = datastore.get_calc_ids()
                try:
                    params['hazard_calculation_id'] = str(calc_ids[hc_id])
                except IndexError:
                    raise SystemExit(
                        'There are %d old calculations, cannot '
                        'retrieve the %s' % (len(calc_ids), hc_id))
            oqparam = readinput.get_oqparam(job_inis[0], kw=params)
            calc = base.calculators(oqparam, calc_id)
            if reuse_input:  # enable caching
                oqparam.cachedir = datastore.get_datadir()
            calc.run(concurrent_tasks=concurrent_tasks, pdb=pdb,
                     exports=exports)
        else:  # run hazard + risk
            calc = run2(
                job_inis[0], job_inis[1], calc_id, concurrent_tasks, pdb,
                reuse_input, loglevel, exports, params)

    logging.info('Total time spent: %s s', monitor.duration)
    logging.info('Memory allocated: %s', general.humansize(monitor.mem))
    print('See the output with silx view %s' % calc.datastore.filename)
    calc_path, _ = os.path.splitext(calc.datastore.filename)  # used below
    return calc


def main(job_ini,
         pdb=False,
         reuse_input=False,
         *,
         slowest: int = None,
         hc: int = None,
         param='',
         concurrent_tasks: int = None,
         exports: valid.export_formats = '',
         loglevel='info',
         calc_id='nojob'):
    """
    Run a calculation bypassing the database layer
    """
    dbserver.ensure_on()
    if param:
        params = dict(p.split('=', 1) for p in param.split(','))
    else:
        params = {}
    if hc:
        params['hazard_calculation_id'] = str(hc)
    if slowest:
        prof = cProfile.Profile()
        stmt = ('_run(job_ini, concurrent_tasks, calc_id, pdb, reuse_input, '
                'loglevel, exports, params)')
        prof.runctx(stmt, globals(), locals())
        pstat = calc_path + '.pstat'
        prof.dump_stats(pstat)
        print('Saved profiling info in %s' % pstat)
        print(get_pstats(pstat, slowest))
        return
    try:
        return _run(job_ini, concurrent_tasks, calc_id, pdb,
                    reuse_input, loglevel, exports, params)
    finally:
        parallel.Starmap.shutdown()


main.job_ini = dict(help='calculation configuration file '
                    '(or files, space-separated)', nargs='+')
main.pdb = dict(help='enable post mortem debugging', abbrev='-d')
main.reuse_input = dict(help='reuse source model and exposure')
main.slowest = dict(help='profile and show the slowest operations')
main.hc = dict(help='previous calculation ID')
main.param = dict(help='override parameter with the syntax NAME=VALUE,...')
main.concurrent_tasks = dict(help='hint for the number of tasks to spawn')
main.exports = dict(help='export formats as a comma-separated string')
main.loglevel = dict(help='logging level',
                     choices='debug info warn error critical'.split())
main.calc_id = dict(help='calculation ID (if "nojob" infer it)')
