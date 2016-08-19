# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2016 GEM Foundation
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
import mock
import time
import logging


from openquake.baselib.general import humansize
from openquake.baselib.python3compat import encode
from openquake.commonlib import readinput, datastore, source, parallel


def indent(text):
    return '  ' + '\n  '.join(text.splitlines())


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
        task_info='Information about the tasks',
        times_by_source_class='Computation times by source typology',
        performance='Slowest operations',
    )

    def __init__(self, dstore):
        self.dstore = dstore
        self.oq = oq = dstore['oqparam']
        self.text = (decode(oq.description) + '\n' + '=' * len(oq.description))
        info = dstore['job_info']
        dpath = dstore.hdf5path
        mtime = os.path.getmtime(dpath)
        self.text += '\n\n%s:%s updated %s' % (
            info.hostname, decode(dpath), time.ctime(mtime))
        # NB: in the future, the sitecol could be transferred as
        # an array by leveraging the HDF5 serialization protocol;
        # for the moment however the size of the
        # data to transfer is given by the usual pickle
        sitecol_size = humansize(len(parallel.Pickled(dstore['sitecol'])))
        self.text += '\n\nnum_sites = %d, sitecol = %s' % (
            len(dstore['sitecol']), sitecol_size)

    def add(self, name, obj=None):
        """Add the view named `name` to the report text"""
        title = self.title[name]
        line = '-' * len(title)
        if obj:
            text = '\n::\n\n' + indent(str(obj))
        else:
            text = datastore.view(name, self.dstore)
        self.text += '\n'.join(['\n\n' + title, line, text])

    def make_report(self):
        """Build the report and return a restructed text string"""
        oq, ds = self.oq, self.dstore
        for name in ('params', 'inputs'):
            self.add(name)
        if 'composite_source_model' in ds:
            self.add('csm_info')
            self.add('required_params_per_trt')
        self.add('rlzs_assoc', ds['csm_info'].get_rlzs_assoc())
        if 'composite_source_model' in ds:
            self.add('ruptures_per_trt')
        if 'scenario' not in oq.calculation_mode:
            self.add('job_info')
        if oq.calculation_mode in ('event_based_rupture', 'event_based',
                                   'event_based_risk'):
            self.add('ruptures_events')
        if oq.calculation_mode in ('event_based_risk',):
            self.add('biggest_ebr_gmf')
            self.add('avglosses_data_transfer')
        if 'exposure' in oq.inputs:
            self.add('exposure_info')
        if 'source_info' in ds:
            self.add('short_source_info')
            self.add('times_by_source_class')
        if 'performance_data' in ds:
            self.add('task_info')
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
    # some taken is care so that the real calculation is not run:
    # the goal is to extract information about the source management only
    with mock.patch.object(
            calc.__class__, 'core_task', source.count_eff_ruptures):
        calc.pre_execute()
    with mock.patch.object(logging.root, 'info'):  # reduce logging
        calc.execute()
    calc.save_params()
    rw = ReportWriter(calc.datastore)
    rw.make_report()
    report = (os.path.join(output_dir, 'report.rst') if output_dir
              else calc.datastore.export_path('report.rst'))
    try:
        rw.save(report)
    except IOError as exc:  # permission error
        sys.stderr.write(str(exc) + '\n')
    return report
