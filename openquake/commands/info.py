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
import os
import sys
import unittest.mock as mock
import logging
import operator
import collections
import numpy
from decorator import FunctionMaker
from openquake.baselib.general import groupby, gen_subclasses
from openquake.baselib.performance import Monitor
from openquake.hazardlib import gsim, nrml, imt
from openquake.hazardlib.mfd.base import BaseMFD
from openquake.hazardlib.source.base import BaseSeismicSource
from openquake.commonlib.oqvalidation import OqParam
from openquake.commonlib import readinput, logictree
from openquake.calculators.export import export
from openquake.calculators.extract import extract
from openquake.calculators import base, reportwriter
from openquake.calculators.views import view, rst_table


def source_model_info(sm_nodes):
    """
    Extract information about source models. Returns a table
    with TRTs as rows and source classes as columns.
    """
    c = collections.Counter()
    for sm in sm_nodes:
        groups = [sm[0]] if sm['xmlns'].endswith('nrml/0.4') else sm[0]
        for group in groups:
            grp_trt = group.get('tectonicRegion')
            for src in group:
                trt = src.get('tectonicRegion', grp_trt)
                src_class = src.tag.split('}')[1]
                c[trt, src_class] += 1
    trts, classes = zip(*c)
    trts = sorted(set(trts))
    classes = sorted(set(classes))
    dtlist = [('TRT', (bytes, 30))] + [(name, int) for name in classes]
    out = numpy.zeros(len(trts) + 1, dtlist)  # +1 for the totals
    for i, trt in enumerate(trts):
        out[i]['TRT'] = trt
        for src_class in classes:
            out[i][src_class] = c[trt, src_class]
    out[-1]['TRT'] = 'Total'
    for name in out.dtype.names[1:]:
        out[-1][name] = out[name][:-1].sum()
    return rst_table(out)


def do_build_reports(directory):
    """
    Walk the directory and builds pre-calculation reports for all the
    job.ini files found.
    """
    for cwd, dirs, files in os.walk(directory):
        for f in sorted(files):
            if f in ('job.ini', 'job_h.ini', 'job_haz.ini',
                     'job_hazard.ini'):
                job_ini = os.path.join(cwd, f)
                logging.warning(job_ini)
                try:
                    reportwriter.build_report(job_ini, cwd)
                except Exception as e:
                    logging.error(str(e))


choices = ['calculators', 'gsims', 'imts', 'views', 'exports',
           'extracts', 'parameters', 'sources', 'mfds', 'venv']


def main(what, report=False):
    """
    Give information about the passed keyword or filename
    """
    if os.environ.get('OQ_DISTRIBUTE') not in ('no', 'processpool'):
        os.environ['OQ_DISTRIBUTE'] = 'processpool'
    if what == 'calculators':
        for calc in sorted(base.calculators):
            print(calc)
    elif what == 'gsims':
        for gs in gsim.get_available_gsims():
            print(gs)
    elif what == 'imts':
        for im in gen_subclasses(imt.IMT):
            print(im.__name__)
    elif what == 'views':
        for name in sorted(view):
            print(name)
    elif what == 'exports':
        dic = groupby(export, operator.itemgetter(0),
                      lambda group: [r[1] for r in group])
        n = 0
        for exporter, formats in dic.items():
            print(exporter, formats)
            n += len(formats)
        print('There are %d exporters defined.' % n)
    elif what == 'extracts':
        for key in extract:
            func = extract[key]
            if hasattr(func, '__wrapped__'):
                fm = FunctionMaker(func.__wrapped__)
            elif hasattr(func, 'func'):  # for partial objects
                fm = FunctionMaker(func.func)
            else:
                fm = FunctionMaker(func)
            print('%s(%s)%s' % (fm.name, fm.signature, fm.doc))
    elif what == 'parameters':
        docs = OqParam.docs()
        names = set()
        for val in vars(OqParam).values():
            if hasattr(val, 'name'):
                names.add(val.name)
        params = sorted(names)
        for param in params:
            print(param)
            print(docs[param])
    elif what == 'mfds':
        for cls in gen_subclasses(BaseMFD):
            print(cls.__name__)
    elif what == 'venv':
        print(sys.prefix)
    elif what == 'sources':
        for cls in gen_subclasses(BaseSeismicSource):
            print(cls.__name__)
    elif os.path.isdir(what) and report:
        with Monitor('info', measuremem=True) as mon:
            with mock.patch.object(logging.root, 'info'):  # reduce logging
                do_build_reports(what)
        print(mon)
    elif what.endswith('.xml'):
        node = nrml.read(what)
        if node[0].tag.endswith('sourceModel'):
            print(source_model_info([node]))
        elif node[0].tag.endswith('logicTree'):
            sm_nodes = []
            for smpath in logictree.collect_info(what).smpaths:
                sm_nodes.append(nrml.read(smpath))
            print(source_model_info(sm_nodes))
        else:
            print(node.to_str())
    elif what.endswith(('.ini', '.zip')):
        with Monitor('info', measuremem=True) as mon:
            if report:
                print('Generated', reportwriter.build_report(what))
            else:
                print(readinput.get_oqparam(what).json())
        if mon.duration > 1:
            print(mon)
    elif what:
        print("No info for '%s'" % what)


main.what = 'filename or one of %s' % ', '.join(choices)
main.report = 'build rst report from job.ini file or zip archive'
