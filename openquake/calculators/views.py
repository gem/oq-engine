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

import io
import os.path
import numbers
import operator
import itertools
import numpy

from openquake.baselib.general import groupby, split_in_blocks, humansize
from openquake.baselib.performance import PerformanceMonitor, perf_dt
from openquake.hazardlib.gsim.base import ContextMaker
from openquake.commonlib import parallel
from openquake.commonlib.oqvalidation import OqParam
from openquake.commonlib.datastore import view
from openquake.commonlib.writers import (
    build_header, scientificformat, write_csv)


def rst_table(data, header=None, fmt='%9.7E'):
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
        if not header:
            header = [col.split(':')[0] for col in build_header(data.dtype)]
    if header:
        col_sizes = [len(col) for col in header]
    else:
        col_sizes = [len(str(col)) for col in data[0]]
    body = []
    for row in data:
        row = tuple(scientificformat(col, fmt) for col in row)
        for (i, col) in enumerate(row):
            col_sizes[i] = max(col_sizes[i], len(col))
        body.append(row)

    sepline = ' '.join(('=' * size for size in col_sizes))
    templ = ' '.join(('%-{}s'.format(size) for size in col_sizes))
    if header:
        lines = [sepline, templ % tuple(header), sepline]
    else:
        lines = [sepline]
    for row in body:
        lines.append(templ % row)
    lines.append(sepline)
    return '\n'.join(lines)


def classify_gsim_lt(gsim_lt):
    """
    :returns: "trivial", "simple" or "complex"
    """
    num_branches = list(gsim_lt.get_num_branches().values())
    num_gsims = '(%s)' % ','.join(map(str, num_branches))
    multi_gsim_trts = sum(1 for num_gsim in num_branches if num_gsim > 1)
    if multi_gsim_trts == 0:
        return "trivial" + num_gsims
    elif multi_gsim_trts == 1:
        return "simple" + num_gsims
    else:
        return "complex" + num_gsims


@view.add('csm_info')
def view_csm_info(token, dstore):
    rlzs_assoc = dstore['rlzs_assoc']
    csm_info = rlzs_assoc.csm_info
    header = ['smlt_path', 'weight', 'source_model_file',
              'gsim_logic_tree', 'num_realizations']
    rows = []
    for sm in csm_info.source_models:
        rlzs = rlzs_assoc.rlzs_by_smodel[sm.ordinal]
        num_rlzs = len(rlzs)
        num_paths = sm.gsim_lt.get_num_paths()
        link = "`%s <%s>`_" % (sm.name, sm.name)
        row = ('_'.join(sm.path), sm.weight, link,
               classify_gsim_lt(sm.gsim_lt), '%d/%d' % (num_rlzs, num_paths))
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


@view.add('ruptures_per_trt')
def view_ruptures_per_trt(token, dstore):
    tbl = []
    header = 'source_model trt_id trt num_sources num_ruptures'.split()
    num_trts = 0
    num_sources = 0
    num_ruptures = 0
    for sm in dstore['composite_source_model']:
        for trt_model in sm.trt_models:
            num_trts += 1
            num_sources += len(trt_model.sources)
            num_ruptures += trt_model.num_ruptures
            tbl.append((sm.name, trt_model.id, trt_model.trt,
                        len(trt_model.sources), trt_model.num_ruptures))
    rows = [('#TRT models', num_trts), ('#sources', num_sources),
            ('#ruptures', num_ruptures)]
    if len(tbl) > 1:
        summary = rst_table(rows) + '\n\n'
    else:
        summary = ''
    return summary + rst_table(tbl, header=header)


@view.add('params')
def view_params(token, dstore):
    oq = OqParam.from_(dstore.attrs)
    params = ['calculation_mode', 'number_of_logic_tree_samples',
              'maximum_distance', 'investigation_time',
              'ses_per_logic_tree_path', 'truncation_level',
              'rupture_mesh_spacing', 'complex_fault_mesh_spacing',
              'width_of_mfd_bin', 'area_source_discretization',
              'random_seed', 'master_seed', 'concurrent_tasks']
    if 'risk' in oq.calculation_mode:
        params.append('avg_losses')
    return rst_table([(param, getattr(oq, param, None)) for param in params])


def build_links(items):
    out = []
    for key, fname in items:
        bname = os.path.basename(fname)
        link = "`%s <%s>`_" % (bname, bname)
        out.append((key, link))
    return sorted(out)


@view.add('inputs')
def view_inputs(token, dstore):
    inputs = OqParam.from_(dstore.attrs).inputs.copy()
    try:
        source_models = [('source', fname) for fname in inputs['source']]
        del inputs['source']
    except KeyError:  # there is no 'source' in scenario calculations
        source_models = []
    return rst_table(
        build_links(list(inputs.items()) + source_models),
        header=['Name', 'File'])

block_dt = numpy.dtype([('num_srcs', numpy.uint32),
                        ('weight', numpy.float32)])


def get_data_transfer(dstore):
    """
    Determine the amount of data transferred from the controller node
    to the workers and back in a classical calculation.

    :param dstore: a :class:`openquake.commonlib.datastore.DataStore` instance
    :returns: (block_info, to_send_forward, to_send_back)
    """
    oqparam = OqParam.from_(dstore.attrs)
    sitecol = dstore['sitecol']
    rlzs_assoc = dstore['rlzs_assoc']
    info = dstore['job_info']
    sources = dstore['composite_source_model'].get_sources()
    num_gsims_by_trt = groupby(rlzs_assoc, operator.itemgetter(0),
                               lambda group: sum(1 for row in group))
    gsims_assoc = rlzs_assoc.gsims_by_trt_id
    to_send_forward = 0
    to_send_back = 0
    block_info = []
    for block in split_in_blocks(sources, oqparam.concurrent_tasks or 1,
                                 operator.attrgetter('weight'),
                                 operator.attrgetter('trt_model_id')):
        num_gsims = num_gsims_by_trt.get(block[0].trt_model_id, 0)
        back = info['n_sites'] * info['n_levels'] * info['n_imts'] * num_gsims
        to_send_back += back * 8  # 8 bytes per float
        args = (block, sitecol, gsims_assoc, PerformanceMonitor(''))
        to_send_forward += sum(len(p) for p in parallel.pickle_sequence(args))
        block_info.append((len(block), block.weight))
    return numpy.array(block_info, block_dt), to_send_forward, to_send_back


@view.add('source_data_transfer')
def source_data_transfer(token, dstore):
    """
    Determine the amount of data transferred from the controller node
    to the workers and back in a classical calculation.
    """
    block_info, to_send_forward, to_send_back = get_data_transfer(dstore)
    tbl = [
        ('Number of tasks to generate', len(block_info)),
        ('Estimated sources to send', humansize(to_send_forward)),
        ('Estimated hazard curves to receive', humansize(to_send_back))]
    return rst_table(tbl)


@view.add('avglosses_data_transfer')
def avglosses_data_transfer(token, dstore):
    """
    Determine the amount of average losses transferred from the workers to the
    controller node in a risk calculation.
    """
    oq = OqParam.from_(dstore.attrs)
    N = len(dstore['assetcol'])
    R = len(dstore['rlzs_assoc'].realizations)
    L = len(dstore['riskmodel'].loss_types)
    ct = oq.concurrent_tasks
    size_bytes = N * R * L * 2 * 8 * ct  # two 8 byte floats, loss and ins_loss
    return ('%d asset(s) x %d realization(s) x %d loss type(s) x 2 losses x '
            '8 bytes x %d tasks = %s' % (N, R, L, ct, humansize(size_bytes)))


# this is used by the ebr calculator
@view.add('old_avg_losses')
def view_old_avg_losses(token, dstore):
    stats = 'specific/loss_curves-stats' in dstore
    group = (dstore['specific/loss_curves-stats'] if stats
             else dstore['specific/loss_curves-rlzs'])
    loss_types = group.dtype.names
    assets = dstore['assetcol']['asset_ref']

    data_by_lt = {}
    for lt in loss_types:
        loss_curves = group[lt]['mean'] if stats else group[lt]['rlz-000']
        data = loss_curves.value['avg']
        data_by_lt[lt] = dict(zip(assets, data))
    dt_list = [('asset_ref', '|S100')] + [(str(ltype), numpy.float32)
                                          for ltype in sorted(data_by_lt)]
    avg_loss_dt = numpy.dtype(dt_list)
    losses = numpy.zeros(len(data_by_lt[lt]), avg_loss_dt)
    for lt, loss_by_asset in data_by_lt.items():
        assets = sorted(loss_by_asset)
        losses[lt] = [loss_by_asset[a] for a in assets]
    losses['asset_ref'] = assets
    return rst_table(losses)


# for scenario_risk
@view.add('totlosses')
def view_totlosses(token, dstore):
    """
    This is a debugging view. You can use it to check that the total
    losses, i.e. the losses obtained by summing the average losses on
    all assets are indeed equal to the aggregate losses. This is a
    sanity check for the correctness of the implementation.
    """
    avglosses = dstore['loss_map-rlzs'].value
    dtlist = [('%s-%s' % (name, stat), float)
              for name in avglosses.dtype.names
              for stat in ('mean', 'mean_ins')]
    zero = numpy.zeros(avglosses.shape[1:], numpy.dtype(dtlist))
    for name in avglosses.dtype.names:
        for stat in ('mean', 'mean_ins'):
            for rec in avglosses:
                zero['%s-%s' % (name, stat)] += rec[name][stat]
    return rst_table(zero)


def sum_table(records):
    """
    Used to compute summaries. The records are assumed to have numeric
    fields, except the first field which is ignored, since it typically
    contains a label. Here is an example:

    >>> sum_table([('a', 1), ('b', 2)])
    ['total', 3]
    """
    size = len(records[0])
    result = [None] * size
    firstrec = records[0]
    for i in range(size):
        if isinstance(firstrec[i], (numbers.Number, numpy.ndarray)):
            result[i] = sum(rec[i] for rec in records)
        else:
            result[i] = 'total'
    return result


# this is used by the ebr calculator
@view.add('mean_avg_losses')
def view_mean_avg_losses(token, dstore):
    assets = dstore['assetcol'].value['asset_ref']
    try:
        array = dstore['avg_losses-stats']  # shape (S, N, 2)
        data = array[0, :, :]  # shape (N, 2)
    except KeyError:
        array = dstore['avg_losses-rlzs']  # shape (N, R, 2)
        data = array[:, 0, :]  # shape (N, 2)
    loss_types = dstore['riskmodel'].loss_types
    header = ['asset_ref'] + loss_types
    losses = [[a] + [numpy.zeros(2)] * len(loss_types) for a in assets]
    for lti, lt in enumerate(loss_types):
        for aid, pair in enumerate(data[lt]):
            losses[aid][lti + 1] = pair  # loss, ins_loss
    losses.sort()
    if len(losses) > 1:
        losses.append(sum_table(losses))
    return rst_table(losses, header=header, fmt='%8.6E')


@view.add('exposure_info')
def view_exposure_info(token, dstore):
    """
    Display info about the exposure model
    """
    assetcol = dstore['assetcol'][:]
    taxonomies = dstore['taxonomies'][:]
    counts = numpy.zeros(len(taxonomies), numpy.uint32)
    for ass in assetcol:
        tax_idx = ass['taxonomy']
        counts[tax_idx] += 1
    tbl = zip(taxonomies, counts)
    data = [('#assets', len(assetcol)),
            ('#taxonomies', len(taxonomies))]
    return rst_table(data) + '\n\n' + rst_table(
        tbl, header=['Taxonomy', '#Assets'])


@view.add('assetcol')
def view_assetcol(token, dstore):
    """
    Display the exposure in CSV format
    """
    assetcol = dstore['assetcol'].value
    sitemesh = dstore['sitemesh'].value
    taxonomies = dstore['taxonomies'].value
    header = list(assetcol.dtype.names)
    columns = [None] * len(header)
    for i, field in enumerate(header):
        if field == 'taxonomy':
            columns[i] = taxonomies[assetcol[field]]
        elif field == 'site_id':
            header[i] = 'lon_lat'
            columns[i] = sitemesh[assetcol[field]]
        else:
            columns[i] = assetcol[field]
    return write_csv(io.StringIO(), [header] + list(zip(*columns)), fmt='%s')


@view.add('fullreport')
def view_fullreport(token, dstore):
    """
    Display an .rst report about the computation
    """
    # avoid circular imports
    from openquake.commonlib.reportwriter import ReportWriter
    return ReportWriter(dstore).make_report()


@view.add('performance')
def view_performance(token, dstore):
    """
    Display performance information
    """
    data = sorted(dstore['performance_data'], key=operator.itemgetter(0))
    out = []
    for operation, group in itertools.groupby(data, operator.itemgetter(0)):
        counts = 0
        time = 0
        mem = 0
        for _operation, time_sec, memory_mb, counts_ in group:
            counts += counts_
            time += time_sec
            mem = max(mem, memory_mb)
        out.append((operation, time, mem, counts))
    out.sort(key=operator.itemgetter(1), reverse=True)  # sort by time
    return rst_table(numpy.array(out, perf_dt), fmt='%s')


@view.add('required_params_per_trt')
def view_required_params_per_trt(token, dstore):
    """
    Display the parameters needed by each tectonic region type
    """
    gsims_per_trt_id = sorted(dstore['rlzs_assoc'].gsims_by_trt_id.items())
    tbl = []
    for trt_id, gsims in gsims_per_trt_id:
        maker = ContextMaker(gsims)
        distances = maker.REQUIRES_DISTANCES
        siteparams = maker.REQUIRES_SITES_PARAMETERS
        ruptparams = maker.REQUIRES_RUPTURE_PARAMETERS
        tbl.append((trt_id, gsims, distances, siteparams, ruptparams))
    return rst_table(
        tbl, header='trt_id gsims distances siteparams ruptparams'.split())
