# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2019 GEM Foundation
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

from openquake.baselib import performance, general, sap, datastore
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


def run2(job_haz, job_risk, calc_id, concurrent_tasks, pdb, loglevel,
         exports, params):
    """
    Run both hazard and risk, one after the other
    """
    hcalc = base.calculators(readinput.get_oqparam(job_haz), calc_id)
    hcalc.run(concurrent_tasks=concurrent_tasks, pdb=pdb,
              exports=exports, **params)
    hc_id = hcalc.datastore.calc_id
    rcalc_id = logs.init(level=getattr(logging, loglevel.upper()))
    oq = readinput.get_oqparam(job_risk, hc_id=hc_id)
    rcalc = base.calculators(oq, rcalc_id)
    rcalc.run(pdb=pdb, exports=exports, **params)
    return rcalc


def _run(job_inis, concurrent_tasks, pdb, loglevel, hc, exports, params):
    global calc_path
    assert len(job_inis) in (1, 2), job_inis
    # set the logs first of all
    calc_id = logs.init(level=getattr(logging, loglevel.upper()))
    with performance.Monitor('total runtime', measuremem=True) as monitor:
        if len(job_inis) == 1:  # run hazard or risk
            if hc:
                hc_id = hc[0]
                rlz_ids = hc[1:]
            else:
                hc_id = None
                rlz_ids = ()
            oqparam = readinput.get_oqparam(job_inis[0], hc_id=hc_id)
            vars(oqparam).update(params)
            if hc_id and hc_id < 0:  # interpret negative calculation ids
                calc_ids = datastore.get_calc_ids()
                try:
                    hc_id = calc_ids[hc_id]
                except IndexError:
                    raise SystemExit(
                        'There are %d old calculations, cannot '
                        'retrieve the %s' % (len(calc_ids), hc_id))
            calc = base.calculators(oqparam, calc_id)
            calc.run(concurrent_tasks=concurrent_tasks, pdb=pdb,
                     exports=exports, hazard_calculation_id=hc_id,
                     rlz_ids=rlz_ids)
        else:  # run hazard + risk
            calc = run2(
                job_inis[0], job_inis[1], calc_id, concurrent_tasks, pdb,
                loglevel, exports, params)

    logging.info('Total time spent: %s s', monitor.duration)
    logging.info('Memory allocated: %s', general.humansize(monitor.mem))
    print('See the output with silx view %s' % calc.datastore.filename)
    calc_path, _ = os.path.splitext(calc.datastore.filename)  # used below
    return calc


@sap.script
def run(job_ini, slowest=False, hc=None, param='', concurrent_tasks=None,
        exports='', loglevel='info', pdb=None):
    """
    Run a calculation bypassing the database layer
    """
    dbserver.ensure_on()
    if param:
        params = oqvalidation.OqParam.check(
            dict(p.split('=', 1) for p in param.split(',')))
    else:
        params = {}
    if slowest:
        prof = cProfile.Profile()
        stmt = ('_run(job_ini, concurrent_tasks, pdb, loglevel, hc, '
                'exports, params)')
        prof.runctx(stmt, globals(), locals())
        pstat = calc_path + '.pstat'
        prof.dump_stats(pstat)
        print('Saved profiling info in %s' % pstat)
        print(get_pstats(pstat, slowest))
    else:
        _run(job_ini, concurrent_tasks, pdb, loglevel, hc, exports, params)


run.arg('job_ini', 'calculation configuration file '
        '(or files, space-separated)', nargs='+')
run.opt('slowest', 'profile and show the slowest operations', type=int)
run.opt('hc', 'previous calculation ID', type=valid.hazard_id)
run.opt('param', 'override parameter with the syntax NAME=VALUE,...')
run.opt('concurrent_tasks', 'hint for the number of tasks to spawn',
        type=int)
run.opt('exports', 'export formats as a comma-separated string',
        type=valid.export_formats)
run.opt('loglevel', 'logging level',
        choices='debug info warn error critical'.split())
run.flg('pdb', 'enable post mortem debugging', '-d')
