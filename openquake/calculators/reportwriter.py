# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2021 GEM Foundation
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

# 2015.06.26 13:21:50 CEST
"""
Utilities to build a report writer generating a .rst report for a calculation
"""
import os
import sys
import logging
from openquake.baselib import parallel
from openquake.baselib.python3compat import encode, decode
from openquake.commonlib import readinput, logs
from openquake.calculators import views


def indent(text):
    return '  ' + '\n  '.join(text.splitlines())


class ReportWriter(object):
    """
    A particularly smart view over the datastore
    """
    title = {
        'params': 'Parameters',
        'inputs': 'Input files',
        'full_lt': 'Composite source model',
        'required_params_per_trt':
        'Required parameters per tectonic region type',
        'ruptures_events': 'Specific information for event based',
        'job_info': 'Data transfer',
        'biggest_ebr_gmf': 'Maximum memory allocated for the GMFs',
        'avglosses_data_transfer': 'Estimated data transfer for the avglosses',
        'exposure_info': 'Exposure model',
        'slow_sources': 'Slowest sources',
        'task:start_classical:0': 'Fastest task',
        'task:start_classical:-1': 'Slowest task',
        'task_info': 'Information about the tasks',
        'eff_ruptures': 'Computation times by source typology',
        'performance': 'Slowest operations',
    }

    def __init__(self, dstore):
        self.dstore = dstore
        self.oq = oq = dstore['oqparam']
        self.text = (decode(oq.description) + '\n' + '=' * len(oq.description))
        try:
            num_rlzs = dstore['full_lt'].get_num_rlzs()
        except KeyError:
            num_rlzs = '?'
        versions = sorted(dstore['/'].attrs.items())
        self.text += '\n\n' + views.rst_table(versions)
        self.text += '\n\nnum_sites = %d, num_levels = %d, num_rlzs = %s' % (
            len(dstore['sitecol']), oq.imtls.size, num_rlzs)

    def add(self, name, obj=None):
        """Add the view named `name` to the report text"""
        if obj:
            text = '\n::\n\n' + indent(str(obj))
        else:
            text = views.view(name, self.dstore)
        if text:
            title = self.title[name]
            line = '-' * len(title)
            self.text += '\n'.join(['\n\n' + title, line, text])

    def make_report(self):
        """Build the report and return a restructed text string"""
        oq, ds = self.oq, self.dstore
        for name in ('params', 'inputs'):
            self.add(name)
        if 'full_lt' in ds:
            self.add('full_lt')
            if ds['full_lt'].sm_rlzs[0].name != 'scenario':
                # required_params_per_trt makes no sense for GMFs from file
                self.add('required_params_per_trt')
        if 'rup_data' in ds:
            self.add('ruptures_events')
        if oq.calculation_mode in ('event_based_risk',):
            self.add('avglosses_data_transfer')
        if 'exposure' in oq.inputs:
            self.add('exposure_info')
        if 'source_info' in ds:
            self.add('slow_sources')
            self.add('eff_ruptures')
        if 'task_info' in ds:
            self.add('task_info')
            tasks = set(ds['task_info']['taskname'])
            if 'start_classical' in tasks:
                self.add('task:start_classical:0')
                self.add('task:start_classical:-1')
            self.add('job_info')
        if 'performance_data' in ds:
            self.add('performance')
        return self.text

    def save(self, fname):
        """Save the report"""
        with open(fname, 'wb') as f:
            f.write(encode(self.text))


def build_report(job_ini, output_dir=None):
    """
    Write a `report.csv` file with information about the calculation
    without running it

    :param job_ini:
        full pathname of the job.ini file
    :param output_dir:
        the directory where the report is written (default the input directory)
    """
    calc_id = logs.init()
    oq = readinput.get_oqparam(job_ini)
    if 'source_model_logic_tree' in oq.inputs:
        oq.calculation_mode = 'preclassical'
    oq.ground_motion_fields = False
    output_dir = output_dir or os.path.dirname(job_ini)
    from openquake.calculators import base  # ugly
    calc = base.calculators(oq, calc_id)
    calc.save_params()  # needed to save oqparam

    # some taken is care so that the real calculation is not run:
    # the goal is to extract information about the source management only
    calc.pre_execute()
    if oq.calculation_mode == 'preclassical':
        calc.execute()
    logging.info('Making the .rst report')
    rw = ReportWriter(calc.datastore)
    try:
        rw.make_report()
    finally:
        parallel.Starmap.shutdown()
    report = (os.path.join(output_dir, 'report.rst') if output_dir
              else calc.datastore.export_path('report.rst'))
    try:
        rw.save(report)
    except IOError as exc:  # permission error
        sys.stderr.write(str(exc) + '\n')
    readinput.exposure = None  # ugly hack
    return report
