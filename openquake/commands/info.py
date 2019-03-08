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
import os
import mock
import logging
import operator
import collections
import numpy
from decorator import FunctionMaker
from openquake.baselib import sap
from openquake.baselib.general import groupby
from openquake.baselib.performance import Monitor
from openquake.baselib.parallel import get_pickled_sizes
from openquake.hazardlib import gsim, nrml, InvalidFile
from openquake.commonlib.oqvalidation import OqParam
from openquake.commonlib import readinput, logictree
from openquake.calculators.export import export
from openquake.calculators.extract import extract
from openquake.calculators import base, reportwriter
from openquake.calculators.views import view, rst_table


def source_model_info(nodes):
    """
    Extract information about NRML/0.5 source models. Returns a table
    with TRTs as rows and source classes as columns.
    """
    c = collections.Counter()
    for node in nodes:
        for src_group in node:
            trt = src_group['tectonicRegion']
            for src in src_group:
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


def print_csm_info(fname):
    """
    Parse the composite source model without instantiating the sources and
    prints information about its composition and the full logic tree
    """
    oqparam = readinput.get_oqparam(fname)
    csm = readinput.get_composite_source_model(oqparam, in_memory=False)
    print(csm.info)
    print('See http://docs.openquake.org/oq-engine/stable/'
          'effective-realizations.html for an explanation')
    rlzs_assoc = csm.info.get_rlzs_assoc()
    print(rlzs_assoc)
    dupl = [(srcs[0]['id'], len(srcs)) for srcs in csm.check_dupl_sources()]
    if dupl:
        print(rst_table(dupl, ['source_id', 'multiplicity']))
    tot, pairs = get_pickled_sizes(rlzs_assoc)
    print(rst_table(pairs, ['attribute', 'nbytes']))


def do_build_reports(directory):
    """
    Walk the directory and builds pre-calculation reports for all the
    job.ini files found.
    """
    for cwd, dirs, files in os.walk(directory):
        for f in sorted(files):
            if f in ('job.ini', 'job_h.ini', 'job_haz.ini', 'job_hazard.ini'):
                job_ini = os.path.join(cwd, f)
                logging.info(job_ini)
                try:
                    reportwriter.build_report(job_ini, cwd)
                except Exception as e:
                    logging.error(str(e))


# the documentation about how to use this feature can be found
# in the file effective-realizations.rst
@sap.script
def info(calculators, gsims, views, exports, extracts, parameters,
         report, input_file=''):
    """
    Give information. You can pass the name of an available calculator,
    a job.ini file, or a zip archive with the input files.
    """
    if calculators:
        for calc in sorted(base.calculators):
            print(calc)
    if gsims:
        for gs in gsim.get_available_gsims():
            print(gs)
    if views:
        for name in sorted(view):
            print(name)
    if exports:
        dic = groupby(export, operator.itemgetter(0),
                      lambda group: [r[1] for r in group])
        n = 0
        for exporter, formats in dic.items():
            print(exporter, formats)
            n += len(formats)
        print('There are %d exporters defined.' % n)
    if extracts:
        for key in extract:
            func = extract[key]
            if hasattr(func, '__wrapped__'):
                fm = FunctionMaker(func.__wrapped__)
            else:
                fm = FunctionMaker(func)
            print('%s(%s)%s' % (fm.name, fm.signature, fm.doc))
    if parameters:
        params = []
        for val in vars(OqParam).values():
            if hasattr(val, 'name'):
                params.append(val)
        params.sort(key=lambda x: x.name)
        for param in params:
            print(param.name)
    if os.path.isdir(input_file) and report:
        with Monitor('info', measuremem=True) as mon:
            with mock.patch.object(logging.root, 'info'):  # reduce logging
                do_build_reports(input_file)
        print(mon)
    elif input_file.endswith('.xml'):
        node = nrml.read(input_file)
        if node[0].tag.endswith('sourceModel'):
            if node['xmlns'].endswith('nrml/0.4'):
                raise InvalidFile(
                    '%s is in NRML 0.4 format, please run the following '
                    'command:\noq upgrade_nrml %s' % (
                        input_file, os.path.dirname(input_file) or '.'))
            print(source_model_info([node[0]]))
        elif node[0].tag.endswith('logicTree'):
            nodes = [nrml.read(sm_path)[0]
                     for sm_path in logictree.collect_info(input_file).smpaths]
            print(source_model_info(nodes))
        else:
            print(node.to_str())
    elif input_file.endswith(('.ini', '.zip')):
        with Monitor('info', measuremem=True) as mon:
            if report:
                print('Generated', reportwriter.build_report(input_file))
            else:
                print_csm_info(input_file)
        if mon.duration > 1:
            print(mon)
    elif input_file:
        print("No info for '%s'" % input_file)


info.flg('calculators', 'list available calculators')
info.flg('gsims', 'list available GSIMs')
info.flg('views', 'list available views')
info.flg('exports', 'list available exports')
info.flg('extracts', 'list available extracts', '-x')
info.flg('parameters', 'list all parameters in the job.ini')
info.flg('report', 'build short report(s) in rst format')
info.arg('input_file', 'job.ini file or zip archive')
