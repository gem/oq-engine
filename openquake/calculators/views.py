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
from __future__ import division
import io
import ast
import os.path
import numbers
import operator
import decimal
import functools
import itertools
import numpy

from openquake.baselib.general import (
    humansize, groupby, AccumDict, CallableDict)
from openquake.baselib.performance import perf_dt
from openquake.baselib.python3compat import unicode, decode
from openquake.hazardlib import valid, stats as hstats
from openquake.hazardlib.gsim.base import ContextMaker
from openquake.commonlib import util, source, calc
from openquake.commonlib.writers import (
    build_header, scientificformat, write_csv, FIVEDIGITS)

FLOAT = (float, numpy.float32, numpy.float64, decimal.Decimal)
INT = (int, numpy.uint32, numpy.int64)
F32 = numpy.float32
U32 = numpy.uint32

# a dictionary of views datastore -> array
view = CallableDict(keyfunc=lambda s: s.split(':', 1)[0])


# ########################## utility functions ############################## #

def form(value):
    """
    Format numbers in a nice way.

    >>> form(0)
    '0'
    >>> form(0.0)
    '0.0'
    >>> form(0.0001)
    '1.000E-04'
    >>> form(1003.4)
    '1,003'
    >>> form(103.4)
    '103'
    >>> form(9.3)
    '9.300'
    >>> form(-1.2)
    '-1.2'
    """
    if isinstance(value, FLOAT + INT):
        if value <= 0:
            return str(value)
        elif value < .001:
            return '%.3E' % value
        elif value < 10 and isinstance(value, FLOAT):
            return '%.3f' % value
        elif value > 1000:
            return '{:,d}'.format(int(round(value)))
        elif numpy.isnan(value):
            return 'NaN'
        else:  # in the range 10-1000
            return str(int(value))
    elif isinstance(value, bytes):
        return decode(value)
    elif isinstance(value, unicode):
        return value
    elif isinstance(value, numpy.object_):
        return str(value)
    elif hasattr(value, '__len__') and len(value) > 1:
        return ' '.join(map(form, value))
    return str(value)


def rst_table(data, header=None, fmt=None):
    """
    Build a .rst table from a matrix.
    
    >>> tbl = [['a', 1], ['b', 2]]
    >>> print(rst_table(tbl, header=['Name', 'Value']))
    ==== =====
    Name Value
    ==== =====
    a    1    
    b    2    
    ==== =====
    """
    if header is None and hasattr(data, '_fields'):
        header = data._fields
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
    fmt = functools.partial(scientificformat, fmt=fmt) if fmt else form
    for row in data:
        tup = tuple(fmt(c) for c in row)
        for (i, col) in enumerate(tup):
            col_sizes[i] = max(col_sizes[i], len(col))
        body.append(tup)

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


def sum_tbl(tbl, kfield, vfields):
    """
    Aggregate a composite array and compute the totals on a given key.

    >>> dt = numpy.dtype([('name', (bytes, 10)), ('value', int)])
    >>> tbl = numpy.array([('a', 1), ('a', 2), ('b', 3)], dt)
    >>> sum_tbl(tbl, 'name', ['value'])['value']
    array([3, 3])
    """
    pairs = [(n, tbl.dtype[n]) for n in [kfield] + vfields]
    dt = numpy.dtype(pairs + [('counts', int)])

    def sum_all(group):
        vals = numpy.zeros(1, dt)[0]
        for rec in group:
            for vfield in vfields:
                vals[vfield] += rec[vfield]
            vals['counts'] += 1
        vals[kfield] = rec[kfield]
        return vals
    rows = groupby(tbl, operator.itemgetter(kfield), sum_all).values()
    array = numpy.zeros(len(rows), dt)
    for i, row in enumerate(rows):
        for j, name in enumerate(dt.names):
            array[i][name] = row[j]
    return array


@view.add('times_by_source_class')
def view_times_by_source_class(token, dstore):
    """
    Returns the calculation times depending on the source typology
    """
    totals = sum_tbl(
        dstore['source_info'], 'source_class', ['calc_time'])
    return rst_table(totals)


@view.add('slow_sources')
def view_slow_sources(token, dstore, maxrows=20):
    """
    Returns the slowest sources
    """
    info = dstore['source_info'].value
    info.sort(order='calc_time')
    return rst_table(info[::-1][:maxrows])


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


@view.add('contents')
def view_contents(token, dstore):
    """
    Returns the size of the contents of the datastore and its total size
    """
    oq = dstore['oqparam']
    data = sorted((dstore.getsize(key), key) for key in dstore)
    rows = [(key, humansize(nbytes)) for nbytes, key in data]
    total = '\n%s : %s' % (
        dstore.hdf5path, humansize(os.path.getsize(dstore.hdf5path)))
    return rst_table(rows, header=(oq.description, '')) + total


@view.add('csm_info')
def view_csm_info(token, dstore):
    csm_info = dstore['csm_info']
    rlzs_assoc = csm_info.get_rlzs_assoc()
    header = ['smlt_path', 'weight', 'source_model_file',
              'gsim_logic_tree', 'num_realizations']
    rows = []
    for sm in csm_info.source_models:
        num_rlzs = len(rlzs_assoc.rlzs_by_smodel[sm.ordinal])
        num_paths = sm.num_gsim_paths
        link = "`%s <%s>`_" % (sm.name, sm.name)
        row = ('_'.join(sm.path), sm.weight, link,
               classify_gsim_lt(csm_info.gsim_lt), '%d/%d' %
               (num_rlzs, num_paths))
        rows.append(row)
    return rst_table(rows, header)


@view.add('ruptures_per_trt')
def view_ruptures_per_trt(token, dstore):
    tbl = []
    header = ('source_model grp_id trt num_sources '
              'eff_ruptures tot_ruptures'.split())
    num_trts = 0
    tot_sources = 0
    eff_ruptures = 0
    tot_ruptures = 0
    source_info = dstore['source_info'].value
    csm_info = dstore['csm_info']
    r = groupby(source_info, operator.itemgetter('grp_id'),
                lambda rows: sum(r['num_ruptures'] for r in rows))
    n = groupby(source_info, operator.itemgetter('grp_id'),
                lambda rows: sum(1 for r in rows))
    for i, sm in enumerate(csm_info.source_models):
        for src_group in sm.src_groups:
            trt = source.capitalize(src_group.trt)
            er = src_group.eff_ruptures
            if er:
                num_trts += 1
                num_sources = n.get(src_group.id, 0)
                tot_sources += num_sources
                eff_ruptures += er
                ruptures = r.get(src_group.id, 0)
                tot_ruptures += ruptures
                tbl.append((sm.name, src_group.id, trt,
                            num_sources, er, ruptures))
    rows = [('#TRT models', num_trts),
            ('#sources', tot_sources),
            ('#eff_ruptures', eff_ruptures),
            ('#tot_ruptures', tot_ruptures),
            ('#tot_weight', csm_info.tot_weight), ]
    if len(tbl) > 1:
        summary = '\n\n' + rst_table(rows)
    else:
        summary = ''
    return rst_table(tbl, header=header) + summary


@view.add('short_source_info')
def view_short_source_info(token, dstore, maxrows=20):
    return rst_table(dstore['source_info'][:maxrows])


@view.add('params')
def view_params(token, dstore):
    oq = dstore['oqparam']
    params = ['calculation_mode', 'number_of_logic_tree_samples',
              'maximum_distance', 'investigation_time',
              'ses_per_logic_tree_path', 'truncation_level',
              'rupture_mesh_spacing', 'complex_fault_mesh_spacing',
              'width_of_mfd_bin', 'area_source_discretization',
              'ground_motion_correlation_model', 'random_seed', 'master_seed']
    if 'risk' in oq.calculation_mode:
        params.append('avg_losses')
    return rst_table([(param, repr(getattr(oq, param, None)))
                      for param in params])


def build_links(items):
    out = []
    for key, fname in items:
        bname = os.path.basename(fname)
        link = "`%s <%s>`_" % (bname, bname)
        out.append((key, link))
    return sorted(out)


@view.add('inputs')
def view_inputs(token, dstore):
    inputs = dstore['oqparam'].inputs.copy()
    try:
        source_models = [('source', fname) for fname in inputs['source']]
        del inputs['source']
    except KeyError:  # there is no 'source' in scenario calculations
        source_models = []
    return rst_table(
        build_links(list(inputs.items()) + source_models),
        header=['Name', 'File'])


def _humansize(literal):
    dic = ast.literal_eval(decode(literal))
    if isinstance(dic, dict):
        items = sorted(dic.items(), key=operator.itemgetter(1), reverse=True)
        lst = ['%s %s' % (k, humansize(v)) for k, v in items]
        return ', '.join(lst)
    elif isinstance(dic, int):
        return humansize(dic)
    else:
        return dic


@view.add('job_info')
def view_job_info(token, dstore):
    """
    Determine the amount of data transferred from the controller node
    to the workers and back in a classical calculation.
    """
    job_info = dict(dstore.hdf5['job_info'])
    rows = [(k, _humansize(v)) for k, v in sorted(job_info.items())]
    return rst_table(rows)


@view.add('avglosses_data_transfer')
def avglosses_data_transfer(token, dstore):
    """
    Determine the amount of average losses transferred from the workers to the
    controller node in a risk calculation.
    """
    oq = dstore['oqparam']
    N = len(dstore['assetcol'])
    R = len(dstore['realizations'])
    L = len(dstore.get_attr('composite_risk_model', 'loss_types'))
    I = oq.insured_losses + 1
    ct = oq.concurrent_tasks
    size_bytes = N * R * L * I * 8 * ct  # 8 byte floats
    return (
        '%d asset(s) x %d realization(s) x %d loss type(s) x %d losses x '
        '8 bytes x %d tasks = %s' % (N, R, L, I, ct, humansize(size_bytes)))


@view.add('ebr_data_transfer')
def ebr_data_transfer(token, dstore):
    """
    Display the data transferred in an event based risk calculation
    """
    attrs = dstore['agg_loss_table'].attrs
    sent = humansize(attrs['sent'])
    received = humansize(attrs['tot_received'])
    return 'Event Based Risk: sent %s, received %s' % (sent, received)


# for scenario_risk
@view.add('totlosses')
def view_totlosses(token, dstore):
    """
    This is a debugging view. You can use it to check that the total
    losses, i.e. the losses obtained by summing the average losses on
    all assets are indeed equal to the aggregate losses. This is a
    sanity check for the correctness of the implementation.
    """
    oq = dstore['oqparam']
    tot_losses = dstore['losses_by_asset']['mean'].sum(axis=0)
    return rst_table(tot_losses.view(oq.loss_dt()), fmt='%.6E')


# for event based risk
@view.add('portfolio_loss')
def view_portfolio_loss(token, dstore):
    """
    The loss for the full portfolio, for each realization and loss type,
    extracted from the event loss table.
    """
    oq = dstore['oqparam']
    loss_dt = oq.loss_dt()
    losses_by_taxon = dstore['losses_by_taxon-rlzs']
    R = losses_by_taxon.shape[1]  # shape (T, R, L')
    data = numpy.zeros(R, loss_dt)
    rlzids = [str(r) for r in range(R)]
    for r in range(R):
        for l, lt in enumerate(loss_dt.names):
            data[r][lt] = losses_by_taxon[:, r, l].sum()
    array = util.compose_arrays(numpy.array(rlzids), data, 'rlz')
    # this is very sensitive to rounding errors, so I am using a low precision
    return rst_table(array, fmt='%.5E')


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
    dt = dstore['oqparam'].loss_dt()
    weights = dstore['realizations']['weight']
    array = dstore['avg_losses-rlzs'].value  # shape (N, R)
    if len(weights) == 1:  # one realization
        mean = array[:, 0]
    else:
        mean = hstats.compute_stats2(array, [hstats.mean_curve], weights)[:, 0]
    data = numpy.array([tuple(row) for row in mean], dt)
    assets = util.get_assets(dstore)
    losses = util.compose_arrays(assets, data)
    losses.sort()
    return rst_table(losses, fmt=FIVEDIGITS)


# this is used by the classical calculator
@view.add('loss_curves_avg')
def view_loss_curves_avg(token, dstore):
    """
    Returns the average losses computed from the loss curves; for each
    asset shows all realizations.
    """
    array = dstore['loss_curves-rlzs'].value  # shape (N, R)
    n, r = array.shape
    lt_dt = numpy.dtype([(lt, numpy.float32, r) for lt in array.dtype.names])
    avg = numpy.zeros(n, lt_dt)
    for lt in array.dtype.names:
        array_lt = array[lt]
        for i, row in enumerate(array_lt):
            avg[lt][i] = row['avg']
    assets = util.get_assets(dstore)
    losses = util.compose_arrays(assets, avg)
    return rst_table(losses, fmt='%8.6E')


@view.add('exposure_info')
def view_exposure_info(token, dstore):
    """
    Display info about the exposure model
    """
    assetcol = dstore['assetcol/array'][:]
    taxonomies = dstore['assetcol/taxonomies'][:]
    cc = dstore['assetcol/cost_calculator']
    ra_flag = ['relative', 'absolute']
    data = [('#assets', len(assetcol)),
            ('#taxonomies', len(taxonomies)),
            ('deductibile', ra_flag[int(cc.deduct_abs)]),
            ('insurance_limit', ra_flag[int(cc.limit_abs)]),
            ]
    return rst_table(data) + '\n\n' + view_assets_by_site(token, dstore)


@view.add('assetcol')
def view_assetcol(token, dstore):
    """
    Display the exposure in CSV format
    """
    assetcol = dstore['assetcol'].value
    taxonomies = dstore['assetcol/taxonomies'].value
    header = list(assetcol.dtype.names)
    columns = [None] * len(header)
    for i, field in enumerate(header):
        if field == 'taxonomy':
            columns[i] = taxonomies[assetcol[field]]
        else:
            columns[i] = assetcol[field]
    return write_csv(io.StringIO(), [header] + list(zip(*columns)))


@view.add('ruptures_events')
def view_ruptures_events(token, dstore):
    num_ruptures = sum(len(v) for v in dstore['ruptures'].values())
    num_events = sum(len(v) for v in dstore['events'].values())
    mult = round(num_events / num_ruptures, 3)
    lst = [('Total number of ruptures', num_ruptures),
           ('Total number of events', num_events),
           ('Rupture multiplicity', mult)]
    return rst_table(lst)


@view.add('fullreport')
def view_fullreport(token, dstore):
    """
    Display an .rst report about the computation
    """
    # avoid circular imports
    from openquake.calculators.reportwriter import ReportWriter
    return ReportWriter(dstore).make_report()


def performance_view(dstore):
    """
    Returns the performance view as a numpy array.
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
    return numpy.array(out, perf_dt)


@view.add('performance')
def view_performance(token, dstore):
    """
    Display performance information
    """
    return rst_table(performance_view(dstore))


def stats(name, array, *extras):
    """
    Returns statistics from an array of numbers.

    :param name: a descriptive string
    :returns: (name, mean, std, min, max, len)
    """
    return (name, numpy.mean(array), numpy.std(array, ddof=1),
            numpy.min(array), numpy.max(array), len(array)) + extras


@view.add('assets_by_site')
def view_assets_by_site(token, dstore):
    """
    Display statistical information about the distribution of the assets
    """
    assets_by_site = dstore['assetcol'].assets_by_site()
    data = ['taxonomy mean stddev min max num_sites num_assets'.split()]
    num_assets = AccumDict()
    for assets in assets_by_site:
        num_assets += {k: [len(v)] for k, v in groupby(
            assets, operator.attrgetter('taxonomy')).items()}
    for taxo in sorted(num_assets):
        val = numpy.array(num_assets[taxo])
        data.append(stats(taxo, val, val.sum()))
    if len(num_assets) > 1:  # more than one taxonomy, add a summary
        n_assets = numpy.array([len(assets) for assets in assets_by_site])
        data.append(stats('*ALL*', n_assets, n_assets.sum()))
    return rst_table(data)


@view.add('required_params_per_trt')
def view_required_params_per_trt(token, dstore):
    """
    Display the parameters needed by each tectonic region type
    """
    gsims_per_grp_id = sorted(
        dstore['csm_info'].get_rlzs_assoc().gsims_by_grp_id.items())
    tbl = []
    for grp_id, gsims in gsims_per_grp_id:
        maker = ContextMaker(gsims)
        distances = sorted(maker.REQUIRES_DISTANCES)
        siteparams = sorted(maker.REQUIRES_SITES_PARAMETERS)
        ruptparams = sorted(maker.REQUIRES_RUPTURE_PARAMETERS)
        tbl.append((grp_id, gsims, distances, siteparams, ruptparams))
    return rst_table(
        tbl, header='grp_id gsims distances siteparams ruptparams'.split(),
        fmt=scientificformat)


@view.add('task_info')
def view_task_info(token, dstore):
    """
    Display statistical information about the tasks performance.
    It is possible to get full information about a specific task
    with a command like this one, for a classical calculation::

      $ oq show task_info:classical
    """
    args = token.split(':')[1:]  # called as task_info:task_name
    if args:
        [task] = args
        array = dstore['task_info/' + task].value
        rduration = array['duration'] / array['weight']
        data = util.compose_arrays(rduration, array, 'rduration')
        data.sort(order='duration')
        return rst_table(data)

    data = ['operation-duration mean stddev min max num_tasks'.split()]
    for task in dstore['task_info']:
        val = dstore['task_info/' + task]['duration']
        data.append(stats(task, val))
    if len(data) == 1:
        return 'Not available'
    return rst_table(data)


@view.add('task_durations')
def view_task_durations(token, dstore):
    """
    Display the raw task durations. Here is an example of usage::

      $ oq show task_durations:classical
    """
    task = token.split(':')[1]  # called as task_duration:task_name
    array = dstore['task_info/' + task]['duration']
    return '\n'.join(map(str, array))


@view.add('task_slowest')
def view_task_slowest(token, dstore):
    """
    Display info about the slowest classical task.
    """
    i = dstore['task_info/classical']['duration'].argmax()
    taskno, weight, duration = dstore['task_info/classical'][i]
    sources = dstore['task_sources'][taskno - 1].split()
    srcs = set(decode(s).split(':', 1)[0] for s in sources)
    return 'taskno=%d, weight=%d, duration=%d s, sources="%s"' % (
        taskno, weight, duration, ' '.join(sorted(srcs)))


@view.add('hmap')
def view_hmap(token, dstore):
    """
    Display the highest 20 points of the mean hazard map. Called as
    $ oq show hmap:0.1  # 10% PoE
    """
    try:
        poe = valid.probability(token.split(':')[1])
    except IndexError:
        poe = 0.1
    try:
        mean = dstore['hcurves/mean']
    except KeyError:  # there is a single realization
        mean = dstore['hcurves/rlz-000']
    oq = dstore['oqparam']
    hmap = calc.make_hmap(mean, oq.imtls, [poe])
    items = sorted([(hmap[sid].array.sum(), sid) for sid in hmap])[-20:]
    dt = numpy.dtype([('sid', U32)] + [(imt, F32) for imt in oq.imtls])
    array = numpy.zeros(len(items), dt)
    for i, (maxvalue, sid) in enumerate(reversed(items)):
        array[i] = (sid, ) + tuple(hmap[sid].array[:, 0])
    return rst_table(array)


@view.add('synthetic_hcurves')
def view_synthetic_hcurves(token, dstore):
    """
    Display the synthetic hazard curves for the calculation. They are
    used for debugging purposes when comparing the results of two
    calculations, they have no physical meaning. They are the simple mean
    of the PoEs arrays over source groups, gsims and number of sites.
    """
    oq = dstore['oqparam']
    nsites = len(dstore['sitecol'])
    array = numpy.zeros(len(oq.imtls.array), F32)
    ngroups = 0
    for sm in dstore['csm_info'].source_models:
        for src_group in sm.src_groups:
            grp_id = src_group.id
            try:
                pmap = dstore['poes/grp-%02d' % grp_id]
            except KeyError:
                continue
            ngroups += 1
            for sid in pmap:
                array += pmap[sid].array.sum(axis=1) / pmap.shape_z
    array /= (ngroups * nsites)
    return oq.imtls.new(array)
