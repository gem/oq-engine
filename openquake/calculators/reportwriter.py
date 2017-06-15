# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2017 GEM Foundation
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
from __future__ import print_function, unicode_literals
from openquake.baselib.python3compat import decode
import os
import sys
import ast
import mock
import time

from openquake.baselib import parallel
from openquake.baselib.general import humansize, AccumDict
from openquake.baselib.python3compat import encode
from openquake.commonlib import readinput, source
from openquake.calculators.classical import PSHACalculator
from openquake.calculators import views


def indent(text):
    return '  ' + '\n  '.join(text.splitlines())


def count_eff_ruptures(sources, srcfilter, gsims, param, monitor):
    """
    Count the effective number of ruptures contained in the given sources
    within the integration distance and return a dictionary src_group_id ->
    num_ruptures. All sources must belong to the same tectonic region type.
    """
    acc = AccumDict()
    acc.grp_id = sources[0].src_group_id
    acc.calc_times = []
    count = 0
    for src in sources:
        t0 = time.time()
        sites = srcfilter.get_close_sites(src)
        if sites is not None:
            count += src.num_ruptures
            dt = time.time() - t0
            acc.calc_times.append((src.source_id, len(sites), dt))
    acc.eff_ruptures = {acc.grp_id: count}
    return acc


class ReportWriter(object):
    """
    A particularly smart view over the datastore
    """
    title = dict(
        params='Parameters',
        inputs='Input files',
        csm_info='Composite source model',
        required_params_per_trt='Required parameters per tectonic region type',
        ruptures_per_trt='Number of ruptures per tectonic region type',
        ruptures_events='Specific information for event based',
        rlzs_assoc='Realizations per (TRT, GSIM)',
        job_info='Informational data',
        biggest_ebr_gmf='Maximum memory allocated for the GMFs',
        avglosses_data_transfer='Estimated data transfer for the avglosses',
        exposure_info='Exposure model',
        short_source_info='Slowest sources',
        task_slowest='Slowest task',
        task_info='Information about the tasks',
        times_by_source_class='Computation times by source typology',
        performance='Slowest operations',
    )

    def __init__(self, dstore):
        self.dstore = dstore
        self.oq = oq = dstore['oqparam']
        self.text = (decode(oq.description) + '\n' + '=' * len(oq.description))
        try:
            info = {decode(k): ast.literal_eval(decode(v))
                    for k, v in dict(dstore['job_info']).items()}
        except KeyError:  # job_info not in the datastore (scenario hazard)
            info = dict(hostname='localhost')
        dpath = dstore.hdf5path
        mtime = os.path.getmtime(dpath)
        host = '%s:%s' % (info['hostname'], decode(dpath))
        updated = str(time.ctime(mtime))
        versions = sorted(dstore['/'].attrs.items())
        self.text += '\n\n' + views.rst_table([[host, updated]] + versions)
        self.text += '\n\nnum_sites = %d, num_imts = %d' % (
            len(dstore['sitecol']), len(oq.imtls))

    def add(self, name, obj=None):
        """Add the view named `name` to the report text"""
        title = self.title[name]
        line = '-' * len(title)
        if obj:
            text = '\n::\n\n' + indent(str(obj))
        else:
            text = views.view(name, self.dstore)
        self.text += '\n'.join(['\n\n' + title, line, text])

    def make_report(self):
        """Build the report and return a restructed text string"""
        oq, ds = self.oq, self.dstore
        for name in ('params', 'inputs'):
            self.add(name)
        if 'csm_info' in ds:
            self.add('csm_info')
            self.add('required_params_per_trt')
        self.add('rlzs_assoc', ds['csm_info'].get_rlzs_assoc())
        if 'source_info' in ds:
            self.add('ruptures_per_trt')
        if 'job_info' in ds:
            self.add('job_info')
        if 'rup_data' in ds:
            self.add('ruptures_events')
        if oq.calculation_mode in ('event_based_risk',):
            self.add('avglosses_data_transfer')
        if 'exposure' in oq.inputs:
            self.add('exposure_info')
        if 'source_info' in ds:
            self.add('short_source_info')
            self.add('times_by_source_class')
        if 'task_info' in ds:
            self.add('task_info')
            if 'classical' in ds['task_info']:
                self.add('task_slowest')
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
    oq = readinput.get_oqparam(job_ini)
    output_dir = output_dir or os.path.dirname(job_ini)
    from openquake.calculators import base  # ugly
    calc = base.calculators(oq)
    calc.save_params()  # needed to save oqparam

    # some taken is care so that the real calculation is not run:
    # the goal is to extract information about the source management only
    p = mock.patch.object
    with p(PSHACalculator, 'core_task', count_eff_ruptures):
        if calc.pre_calculator == 'event_based_risk':
            # compute the ruptures only, not the risk
            calc.pre_calculator = 'event_based_rupture'
        calc.pre_execute()
    if hasattr(calc, '_composite_source_model'):
        calc.datastore['csm_info'] = calc.csm.info
    rw = ReportWriter(calc.datastore)
    rw.make_report()
    report = (os.path.join(output_dir, 'report.rst') if output_dir
              else calc.datastore.export_path('report.rst'))
    try:
        rw.save(report)
    except IOError as exc:  # permission error
        sys.stderr.write(str(exc) + '\n')
    return report
