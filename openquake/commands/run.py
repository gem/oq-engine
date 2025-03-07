# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2025 GEM Foundation
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

import logging
import os.path
import socket
import cProfile
import warnings
import getpass
from pandas.errors import SettingWithCopyWarning

from openquake.baselib import performance, general, config
from openquake.hazardlib import valid
from openquake.commonlib import logs, datastore, readinput
from openquake.calculators import base, views
from openquake.commonlib import dbapi
from openquake.engine.engine import create_jobs, run_jobs
from openquake.server import db

calc_path = None  # set only when the flag --slowest is given


# called when profiling
def _run(job_ini, concurrent_tasks, pdb, reuse_input, loglevel, exports,
         params, user_name, host=None):
    global calc_path
    if 'hazard_calculation_id' in params:
        hc_id = int(params['hazard_calculation_id'])
        if hc_id < 0:  # interpret negative calculation ids
            calc_ids = logs.get_calc_ids()
            try:
                params['hazard_calculation_id'] = calc_ids[hc_id]
            except IndexError:
                raise SystemExit(
                    'There are %d old calculations, cannot '
                    'retrieve the %s' % (len(calc_ids), hc_id))
        else:
            params['hazard_calculation_id'] = hc_id
    dic = readinput.get_params(job_ini, params)
    # set the logs first of all
    log = logs.init(dic, log_level=getattr(logging, loglevel.upper()),
                    user_name=user_name, host=host)
    logs.dbcmd('update_job', log.calc_id,
               {'status': 'executing', 'pid': os.getpid()})
    with log, performance.Monitor('total runtime', measuremem=True) as monitor:
        calc = base.calculators(log.get_oqparam(), log.calc_id)
        if reuse_input:  # enable caching
            calc.oqparam.cachedir = datastore.get_datadir()
        calc.run(concurrent_tasks=concurrent_tasks, pdb=pdb, exports=exports)

    logging.info('Total time spent: %s s', monitor.duration)
    logging.info('Memory allocated: %s', general.humansize(monitor.mem))
    calc_path, _ = os.path.splitext(calc.datastore.filename)  # used below
    return calc


def main(job_ini,
         pdb=False,
         reuse_input=False,
         *,
         slowest: int = None,
         hc: int = None,
         param=(),
         concurrent_tasks: int = None,
         exports: valid.export_formats = '',
         loglevel='info',
         nodes: int = 1):
    """
    Run a calculation
    """
    # os.environ['OQ_DISTRIBUTE'] = 'processpool'
    warnings.filterwarnings("error", category=SettingWithCopyWarning)
    user_name = getpass.getuser()

    # automatically create the user db if missing
    if (config.dbserver.host == '127.0.0.1' and
        config.dbserver.file == '~/oqdata/db.sqlite3'
        and user_name != 'openquake'):
        dbfile = os.path.expanduser(config.dbserver.file)
        if not os.path.exists(dbfile):
            db.actions.upgrade_db(dbapi.db)
    try:
        host = socket.gethostname()
    except Exception:  # gaierror
        host = None
    if param:
        params = {}
        for par in param:
            k, v = par.split('=', 1)
            params[k] = v
    else:
        params = {}
    if hc:
        if hc == -1:
            hc = logs.dbcmd('get_job', -1, user_name).id
        params['hazard_calculation_id'] = str(hc)
    if concurrent_tasks is not None:
        params['concurrent_tasks'] = str(concurrent_tasks)
    if slowest:
        prof = cProfile.Profile()
        prof.runctx('_run(job_ini[0], None, pdb, reuse_input, loglevel, '
                    'exports, params, host)', globals(), locals())
        pstat = calc_path + '.pstat'
        prof.dump_stats(pstat)
        print('Saved profiling info in %s' % pstat)
        data = performance.get_pstats(pstat, slowest)
        print(views.text_table(data, ['ncalls', 'cumtime', 'path'],
                               ext='org'))
        return
    dics = [readinput.get_params(ini) for ini in job_ini]
    for dic in dics:
        dic.update(params)
        dic['exports'] = ','.join(exports)
        if 'job_id' in dic:  # in sensitivity analysis
            logs.dbcmd('update_job', dic['job_id'],
                       {'calculation_mode': dic['calculation_mode']})
    jobs = create_jobs(dics, loglevel, hc_id=hc, user_name=user_name, host=host)
    job_id = jobs[0].calc_id
    run_jobs(jobs, nodes=nodes, precalc=True)
    return job_id


main.job_ini = dict(help='calculation configuration file '
                    '(or files, space-separated)', nargs='+')
main.pdb = dict(help='enable post mortem debugging', abbrev='-d')
main.reuse_input = dict(help='reuse source model and exposure')
main.slowest = dict(help='profile and show the slowest operations')
main.hc = dict(help='previous calculation ID')
main.param = dict(help='override parameters with TOML syntax', nargs='*')
main.concurrent_tasks = dict(help='hint for the number of tasks to spawn')
main.exports = dict(help='export formats as a comma-separated string')
main.loglevel = dict(help='logging level',
                     choices='debug info warn error critical'.split())
main.nodes=dict(help='number of worker nodes to start')
