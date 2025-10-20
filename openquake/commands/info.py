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
import os
import sys
import string
import inspect
from pprint import pprint
import unittest.mock as mock
import logging
import operator
import collections

import numpy
import pandas
from shapely.geometry import shape
from decorator import FunctionMaker

from openquake.baselib import config, hdf5
from openquake.baselib.general import groupby, gen_subclasses, humansize
from openquake.baselib.performance import Monitor
from openquake.hazardlib import nrml, imt, logictree, site, geo, lt
from openquake.hazardlib.geo.packager import fiona
from openquake.hazardlib.gsim.base import registry
from openquake.hazardlib.mfd.base import BaseMFD
from openquake.hazardlib.scalerel.base import BaseMSR
from openquake.hazardlib.source.base import BaseSeismicSource
from openquake.hazardlib.valid import pmf_map, lon_lat
from openquake.hazardlib.shakemap.parsers import get_rup_dic
from openquake.sep.classes import SecondaryPeril
from openquake.commonlib.oqvalidation import OqParam
from openquake.commonlib import readinput, logs
from openquake.risklib import asset, scientific
from openquake.calculators.export import export
from openquake.calculators.extract import extract
from openquake.calculators import base, reportwriter
from openquake.calculators.views import view, text_table
from openquake.calculators.export import DISPLAY_NAME

F32 = numpy.float32
U8 = numpy.uint8


def print_features(fiona_file):
    rows = []
    for feature in fiona_file:
        dic = dict(feature['properties'])
        dic['geom'] = shape(feature['geometry']).__class__.__name__
        header = list(dic)
        rows.append(dic.values())
    print(text_table(rows, header, ext='org'))


def print_subclass(what, cls):
    """
    Print the docstring of the given subclass, or print all available
    subclasses.
    """
    split = what.split(':')
    if len(split) == 1:
        # no subclass specified, print all
        for cls in gen_subclasses(cls):
            print(cls.__name__)
    else:
        # print the specified subclass, if known
        for cls in gen_subclasses(cls):
            if cls.__name__ == split[1]:
                print(cls.__doc__)
                break
        else:
            print('Unknown class %s' % split[1])


def print_imt(what):
    """
    Print the docstring of the given IMT, or print all available
    IMTs.
    """
    split = what.split(':')
    if len(split) == 1:
        # no IMT specified, print all
        for im in vars(imt).values():
            if inspect.isfunction(im) and is_upper(im):
                print(im.__name__)
    else:
        # print the docstring of the specified IMT, if known
        for im in vars(imt).values():
            if inspect.isfunction(im) and is_upper(im):
                if im.__name__ == split[1]:
                    print(im.__doc__)
                    break
        else:
            print('Unknown IMT %s' % split[1])


def print_gsim(what):
    """
    Print the docstring of the given GSIM, or print all available
    GSIMs.
    """
    split = what.split(':')
    if len(split) == 1:
        # no GSIM specified, print all
        for gs in sorted(registry):
            print(gs)
    else:
        # print the docstring of the specified GSIM, if known
        for gs, cls in registry.items():
            if cls.__name__ == split[1]:
                print(cls.__doc__)
                break
        else:
            print('Unknown GSIM %s' % split[1])


def print_peril(what):
    """
    Print the docstring of the given SecondaryPeril, or print all available
    subclasses
    """
    split = what.split(':')
    if len(split) == 1:
        # no peril specified, print all
        for cls in SecondaryPeril.__subclasses__():
            print(cls.__name__)
    else:
        # print the docstring of the specified class, if known
        for cls in SecondaryPeril.__subclasses__():
            if cls.__name__ == split[1]:
                print(cls.__doc__)
                break
        else:
            print('Unknown SecondaryPeril %s' % split[1])


def print_cols(lst, ncols):
    """
    Print a list of strings in right justified columns
    """
    maxlen = max(len(x) for x in lst)
    nrows = int(numpy.ceil(len(lst) / ncols))
    for r in range(nrows):
        col = []
        for c in range(ncols):
            try:
                col.append(lst[r * ncols + c].rjust(maxlen))
            except IndexError:
                col.append(' ' * maxlen)
        print(''.join(col))


def print_geohash(what):
    lon, lat = lon_lat(what.split(':')[1])
    # print(geo.utils.geohash3(F32([lon]), F32([lat])))
    arr = geo.utils.CODE32[geo.utils.geohash(F32([lon]), F32([lat]), U8(8))]
    gh = b''.join([row.tobytes() for row in arr])
    print(gh.decode('ascii'))


# tested in run-demos.sh
def print_usgs_rupture(what):
    """
    Show the parameters of a rupture downloaded from the USGS site.
    $ oq info usgs_rupture:us70006sj8
    {'lon': 74.628, 'lat': 35.5909, 'dep': 13.8, 'mag': 5.6, 'rake': 0.0}
    """
    try:
        usgs_id = what.split(':', 1)[1]
    except IndexError:
        return 'Example: oq info usgs_rupture:us70006sj8'
    dic = dict(usgs_id=usgs_id, approach='use_shakemap_fault_rup_from_usgs')
    print(get_rup_dic(dic)[1])


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
    return text_table(out)


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


choices = ['calculators', 'cfg', 'consequences', 'site_params',
           'gsim', 'imt', 'views', 'exports', 'disagg',
           'extracts', 'parameters', 'sources', 'mfd', 'msr', 'venv',
           'loss_types', 'uncertainty_types']


def is_upper(func):
    """
    True if the name of the function starts with an uppercase character
    """
    char = func.__name__[0]
    return char in string.ascii_uppercase


def main(what, report=False):
    """
    Give information about the passed keyword or filename
    """
    if os.environ.get('OQ_DISTRIBUTE') not in ('no', 'processpool'):
        os.environ['OQ_DISTRIBUTE'] = 'processpool'
    if what == 'calculators':
        for calc in sorted(base.calculators):
            print(calc)
    elif what == 'executing':
        fields = 'id,user_name,calculation_mode,description'
        rows = logs.dbcmd(f"SELECT {fields} FROM job WHERE status IN "
                          "('executing', 'submitted') AND is_running=1")
        print(fields.replace(',', '\t'))
        for row in rows:
            print('\t'.join(map(str, row)))
    elif what.startswith('peril'):
        print_peril(what)
    elif what.startswith('gsim'):
        print_gsim(what)
    elif what.startswith('imt'):
        print_imt(what)
    elif what.startswith('usgs_rupture'):
        print_usgs_rupture(what)
    elif what == 'views':
        for name in sorted(view):
            print(name)
    elif what == 'exports':
        dic = groupby(export, operator.itemgetter(0),
                      lambda group: [r[1] for r in group])
        items = [(DISPLAY_NAME.get(exporter, '?'), exporter, formats)
                 for exporter, formats in dic.items()]
        n = 0
        for dispname, exporter, formats in sorted(items):
            print(dispname, '"%s"' % exporter, formats)
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
    elif what == 'loss_types':
        ltypes = [ltype for ltype in scientific.LOSSTYPE
                  if '+' not in ltype and '_ins' not in ltype]
        for ltype in sorted(ltypes):
            print(ltype)
    elif what == 'uncertainty_types':
        uncs = [unc for unc in lt.apply_uncertainty if unc != 'dummy']
        uncs.extend(lt.NOAPPLY_UNCERTAINTIES)
        for i, unc in enumerate(sorted(uncs), 1):
            print('%02d' % i, unc)
    elif what.startswith('mfd'):
        print_subclass(what, BaseMFD)
    elif what.startswith('msr'):
        print_subclass(what, BaseMSR)
    elif what.startswith('geohash'):
        print_geohash(what)
    elif what == 'venv':
        print(sys.prefix)
    elif what == 'cfg':
        print('Looking at the following paths (the last wins)')
        for path in config.paths:
            print(path)
    elif what == 'site_params':
        print_cols(sorted(site.site_param_dt), 4)
    elif what == 'sources':
        pairs = sorted((cls.__name__, cls.code)
                       for cls in gen_subclasses(BaseSeismicSource)
                       if hasattr(cls, 'code'))
        for i, (name, code) in enumerate(pairs, 1):
            print('%02d' % i, code.decode('ascii'), name)
    elif what == 'disagg':
        for out in pmf_map:
            print(out)
    elif what == 'consequences':
        known = scientific.KNOWN_CONSEQUENCES
        print('The following %d consequences are implemented:' % len(known))
        for cons in known:
            print(cons)
    elif os.path.isdir(what) and report:
        with Monitor('info', measuremem=True) as mon:
            with mock.patch.object(logging.root, 'info'):  # reduce logging
                do_build_reports(what)
        print(mon)
    elif what.endswith('.csv'):
        [rec] = hdf5.sniff([what])
        df = pandas.read_csv(what, skiprows=rec.skip)
        if len(df) > 25:
            dots = pandas.DataFrame({col: ['...'] for col in df.columns})
            df = pandas.concat([df[:10], dots, df[-10:]])
        print(text_table(df, ext='org'))
    elif what.endswith('.xml'):
        node = nrml.read(what)
        tag = node[0].tag
        if tag.endswith('sourceModel'):
            print(source_model_info([node]))
        elif tag.endswith('exposureModel'):
            _exp, df = asset.read_exp_df(what)
            print(node.to_str())
            print(df.set_index('id')[[
                'lon', 'lat', 'taxonomy', 'value-structural']])
        elif tag.endswith('logicTree'):
            bset = node[0][0]
            if bset.tag.endswith("logicTreeBranchingLevel"):
                bset = bset[0]
            if bset.attrib['uncertaintyType'] in (
                    'sourceModel', 'extendModel'):
                sm_nodes = []
                for smpath in logictree.collect_info(what).smpaths:
                    sm_nodes.append(nrml.read(smpath))
                print(source_model_info(sm_nodes))
            elif bset.attrib['uncertaintyType'] == 'gmpeModel':
                print(logictree.GsimLogicTree(what))
        else:
            print(node.to_str())
    elif what.endswith(('.shp', '.gpkg')):
        with fiona.open(what) as f:
            print_features(f)
    elif what.endswith(('.ini', '.zip')):
        with Monitor('info', measuremem=True) as mon:
            if report:
                print('Generated', reportwriter.build_report(what))
            else:
                oq = readinput.get_oqparam(what)
                ltree = readinput.get_logic_tree(oq)
                size = humansize(oq.get_input_size())
                print('calculation_mode: %s' % oq.calculation_mode)
                print('description: %s' % oq.description)
                print('input size: %s' % size)
                for bset in ltree.branchsets:
                    pprint(bset)
        if mon.duration > 1:
            print(mon)
    elif what:
        print("No info for '%s'" % what)


main.what = 'filename or one of %s' % ', '.join(choices)
main.report = 'build rst report from job.ini file or zip archive'
