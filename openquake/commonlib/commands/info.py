# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2016 GEM Foundation
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

from __future__ import print_function
import textwrap
import logging
from openquake.baselib.performance import PerformanceMonitor
from openquake.commonlib import sap, nrml, readinput, reportwriter
from openquake.calculators import base
from openquake.hazardlib import gsim


def print_csm_info(fname):
    """
    Parse the composite source model without instantiating the sources and
    prints information about its composition and the full logic tree
    """
    oqparam = readinput.get_oqparam(fname)
    csm = readinput.get_composite_source_model(oqparam, in_memory=False)
    print(csm.info)
    print('See https://github.com/gem/oq-risklib/blob/master/doc/'
          'effective-realizations.rst for an explanation')
    print(csm.info.get_rlzs_assoc())


# the documentation about how to use this feature can be found
# in the file effective-realizations.rst
def info(name, report=False):
    """
    Give information. You can pass the name of an available calculator,
    a job.ini file, or a zip archive with the input files.
    """
    logging.basicConfig(level=logging.INFO)
    if name in base.calculators:
        print(textwrap.dedent(base.calculators[name].__doc__.strip()))
    elif name == 'gsims':
        for gs in gsim.get_available_gsims():
            print(gs)
    elif name.endswith('.xml'):
        print(nrml.read(name).to_str())
    elif name.endswith(('.ini', '.zip')):
        with PerformanceMonitor('info', measuremem=True) as mon:
            if report:
                print('Generated', reportwriter.build_report(name))
            else:
                print_csm_info(name)
        if mon.duration > 1:
            print(mon)
    else:
        print("No info for '%s'" % name)

parser = sap.Parser(info)
parser.arg('name', 'calculator name, job.ini file or zip archive')
parser.flg('report', 'build a report in rst format')
