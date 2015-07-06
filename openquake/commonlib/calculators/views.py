#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2015, GEM Foundation

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

from openquake.commonlib.datastore import view
from openquake.commonlib.writers import build_header


def rst_table(data, header=None):
    """
    Build a .rst table from a matrix.
    
    >>> tbl = [['a', 1], ['b', 2]]
    >>> print rst_table(tbl, header=['Name', 'Value'])
    ==== =====
    Name Value
    ==== =====
    a    1    
    b    2    
    ==== =====
    """
    try:
        # see if data is a composite numpy array
        data.dtype.fields
    except AttributeError:
        # not a composite array
        header = header or ()
    else:
        header = header or build_header(data.dtype)
    if header:
        col_sizes = [len(col) for col in header]
    else:
        col_sizes = [len(str(col)) for col in data[0]]
    body = []
    for row in data:
        row = tuple(map(str, row))
        for (i, col) in enumerate(row):
            col_sizes[i] = max(col_sizes[i], len(col))
        body.append(row)

    sepline = ' '.join(('=' * size for size in col_sizes))
    fmt = ' '.join(('%-{}s'.format(size) for size in col_sizes))
    if header:
        lines = [sepline, fmt % tuple(header), sepline]
    else:
        lines = [sepline]
    for row in body:
        lines.append(fmt % row)
    lines.append(sepline)
    return '\n'.join(lines)


def classify_gsim_lt(gsim_lt):
    """
    :returns: "trivial", "simple" or "complex"
    """
    trt_gsims = gsim_lt.values.items()
    num_gsims = map(len, gsim_lt.values.itervalues())
    complex_trts = [trt for trt, gsims in trt_gsims if len(gsims) > 1]
    if all(n == 1 for n in num_gsims):  # one gsim per TRT
        return "trivial"
    elif len(complex_trts) == 1:
        return "simple"
    else:
        return "complex"


@view.add('csm_info')
def view_csm_info(token, dstore):
    rlzs_assoc = dstore['rlzs_assoc']
    csm_info = rlzs_assoc.csm_info
    header = ['smlt_path', 'source_model_file', 'num_trts',
              'gsim_logic_tree', 'num_gsims', 'num_realizations',
              'num_sources']
    rows = []
    for sm in csm_info.source_models:
        rlzs = rlzs_assoc.rlzs_by_smodel[sm.ordinal]
        num_rlzs = len(rlzs)
        num_branches = [n for n in sm.gsim_lt.get_num_branches().values() if n]
        num_paths = sm.gsim_lt.get_num_paths()
        num_gsims = ','.join(map(str, num_branches))
        tmodels = [tm for tm in sm.trt_models  # effective
                   if tm.trt in sm.gsim_lt.tectonic_region_types]
        row = ('_'.join(sm.path), sm.name, len(tmodels),
               classify_gsim_lt(sm.gsim_lt), num_gsims,
               '%d/%d' % (num_rlzs, num_paths), sm.num_sources)
        rows.append(row)
    return rst_table(rows, header)


@view.add('rupture_collections')
def view_rupture_collections(token, dstore):
    rlzs_assoc = dstore['rlzs_assoc']
    num_ruptures = dstore['num_ruptures']
    csm_info = rlzs_assoc.csm_info
    rows = []
    col_id = 0
    for sm in csm_info.source_models:
        for tm in sm.trt_models:
            for idx in range(sm.samples):
                nr = num_ruptures[col_id]
                if nr:
                    rows.append((col_id, '_'.join(sm.path), tm.trt, nr))
                col_id += 1
    return rst_table(rows, ['col', 'smlt_path', 'TRT', 'num_ruptures'])


@view.add('params')
def view_params(token, dstore):
    oq = dstore['oqparam']
    params = ('calculation_mode', 'number_of_logic_tree_samples',
              'maximum_distance', 'investigation_time',
              'ses_per_logic_tree_path', 'truncation_level',
              'rupture_mesh_spacing', 'complex_fault_mesh_spacing',
              'width_of_mfd_bin', 'area_source_discretization',
              'random_seed', 'master_seed')
    return rst_table([(param, getattr(oq, param)) for param in params])


def hide_fullpath(items):
    """Strip everything before oq-risklib/, if any"""
    out = []
    for name, fname in items:
        splits = fname.split('oq-risklib/')
        out.append((name, splits[1] if len(splits) == 2 else fname))
    return sorted(out)


@view.add('inputs')
def view_inputs(token, dstore):
    inputs = dstore['oqparam'].inputs.copy()
    try:
        source_models = [('source', fname) for fname in inputs['source']]
        del inputs['source']
    except KeyError:  # there is no 'source' in scenario calculations
        source_models = []
    return rst_table([['Name', 'File']] + hide_fullpath(
        inputs.items() + source_models))
