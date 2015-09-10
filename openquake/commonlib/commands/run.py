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
import logging

from openquake.baselib import performance, general
from openquake.commonlib import sap, readinput, valid, datastore
from openquake.calculators import base


def run2(job_haz, job_risk, concurrent_tasks, pdb, exports, monitor):
    """
    Run both hazard and risk, one after the other
    """
    hcalc = base.calculators(readinput.get_oqparam(job_haz), monitor)
    with monitor:
        monitor.monitor_dir = hcalc.datastore.calc_dir
        hcalc.run(concurrent_tasks=concurrent_tasks, pdb=pdb, exports=exports)
        hc_id = hcalc.datastore.calc_id
        oq = readinput.get_oqparam(job_risk, hc_id=hc_id)
        rcalc = base.calculators(oq, monitor)
        monitor.monitor_dir = rcalc.datastore.calc_dir
        rcalc.run(concurrent_tasks=concurrent_tasks, pdb=pdb, exports=exports,
                  hazard_calculation_id=hc_id)
    return rcalc


def run(job_ini, concurrent_tasks=None, pdb=None,
        loglevel='info', hc=None, exports=''):
    """
    Run a calculation. Optionally, set the number of concurrent_tasks
    (0 to disable the parallelization).
    """
    logging.basicConfig(level=getattr(logging, loglevel.upper()))
    job_inis = job_ini.split(',')
    assert len(job_inis) in (1, 2), job_inis
    monitor = performance.Monitor('total', measuremem=True)

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
        monitor.monitor_dir = calc.datastore.calc_dir
        with monitor:
            calc.run(concurrent_tasks=concurrent_tasks, pdb=pdb,
                     exports=exports, hazard_calculation_id=hc)
    else:  # run hazard + risk
        calc = run2(
            job_inis[0], job_inis[1], concurrent_tasks, pdb, exports, monitor)

    logging.info('Total time spent: %s s', monitor.duration)
    logging.info('Memory allocated: %s', general.humansize(monitor.mem))
    monitor.flush()
    print('See the output with hdfview %s/output.hdf5' %
          calc.datastore.calc_dir)
    return calc

parser = sap.Parser(run)
parser.arg('job_ini', 'calculation configuration file '
           '(or files, comma-separated)')
parser.opt('concurrent_tasks', 'hint for the number of tasks to spawn',
           type=int)
parser.flg('pdb', 'enable post mortem debugging')
parser.opt('loglevel', 'logging level',
           choices='debug info warn error critical'.split())
parser.opt('hc', 'previous calculation ID', type=int)
parser.opt('exports', 'export formats as a comma-separated string',
           type=valid.export_formats)
