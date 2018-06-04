# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2018 GEM Foundation
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
import ast
import os.path
import numbers
import operator
import decimal
import functools
import itertools
import collections
import numpy

from openquake.baselib.general import (
    humansize, groupby, DictArray, AccumDict, CallableDict)
from openquake.baselib.performance import perf_dt
from openquake.baselib.general import get_array
from openquake.baselib.python3compat import decode
from openquake.baselib.general import group_array
from openquake.hazardlib import valid
from openquake.hazardlib.gsim.base import ContextMaker
from openquake.commonlib import util, source, calc
from openquake.commonlib.writers import (
    build_header, scientificformat, FIVEDIGITS)
from openquake.calculators import getters

FLOAT = (float, numpy.float32, numpy.float64, decimal.Decimal)
INT = (int, numpy.int32, numpy.uint32, numpy.int64, numpy.uint64)
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
    '9.30000'
    >>> form(-1.2)
    '-1.2'
    """
    if isinstance(value, FLOAT + INT):
        if value <= 0:
            return str(value)
        elif value < .001:
            return '%.3E' % value
        elif value < 10 and isinstance(value, FLOAT):
            return '%.5f' % value
        elif value > 1000:
            return '{:,d}'.format(int(round(value)))
        elif numpy.isnan(value):
            return 'NaN'
        else:  # in the range 10-1000
            return str(int(value))
    elif isinstance(value, bytes):
        return decode(value)
    elif isinstance(value, str):
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
    header = ['smlt_path', 'weight', 'gsim_logic_tree', 'num_realizations']
    rows = []
    for sm in csm_info.source_models:
        num_rlzs = len(rlzs_assoc.rlzs_by_smodel[sm.ordinal])
        num_paths = sm.num_gsim_paths
        row = ('_'.join(sm.path),
               sm.weight,
               classify_gsim_lt(csm_info.gsim_lt),
               '%d/%d' % (num_rlzs, num_paths))
        rows.append(row)
    return rst_table(rows, header)


@view.add('ruptures_per_trt')
def view_ruptures_per_trt(token, dstore):
    tbl = []
    header = ('source_model grp_id trt eff_ruptures tot_ruptures'.split())
    num_trts = 0
    eff_ruptures = 0
    tot_ruptures = 0
    csm_info = dstore['csm_info']
    for i, sm in enumerate(csm_info.source_models):
        for src_group in sm.src_groups:
            trt = source.capitalize(src_group.trt)
            er = src_group.eff_ruptures
            if er:
                num_trts += 1
                eff_ruptures += er
                tbl.append(
                    (sm.name, src_group.id, trt, er, src_group.tot_ruptures))
            tot_ruptures += src_group.tot_ruptures
    rows = [('#TRT models', num_trts),
            ('#eff_ruptures', eff_ruptures),
            ('#tot_ruptures', tot_ruptures),
            ('#tot_weight', csm_info.tot_weight)]
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
              'ground_motion_correlation_model', 'minimum_intensity',
              'random_seed', 'master_seed', 'ses_seed']
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
    else:
        return str(dic)


@view.add('job_info')
def view_job_info(token, dstore):
    """
    Determine the amount of data transferred from the controller node
    to the workers and back in a classical calculation.
    """
    data = [['task', 'sent', 'received']]
    for task in dstore['task_info']:
        if task not in ('task_sources', 'source_data'):
            dset = dstore['task_info/' + task]
            argnames = dset.attrs['argnames'].split()
            totsent = dset.attrs['sent']
            sent = ['%s=%s' % (a, humansize(s))
                    for s, a in sorted(zip(totsent, argnames), reverse=True)]
            recv = dset['received'].sum()
            data.append((task, ' '.join(sent), humansize(recv)))
    return rst_table(data)


@view.add('avglosses_data_transfer')
def avglosses_data_transfer(token, dstore):
    """
    Determine the amount of average losses transferred from the workers to the
    controller node in a risk calculation.
    """
    oq = dstore['oqparam']
    N = len(dstore['assetcol'])
    R = dstore['csm_info'].get_num_rlzs()
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
    attrs = dstore['losses_by_event'].attrs
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
    R = dstore['csm_info'].get_num_rlzs()
    by_rlzi = group_array(dstore['losses_by_event'].value, 'rlzi')
    data = numpy.zeros(R, loss_dt)
    rlzids = [str(r) for r in range(R)]
    for r in range(R):
        loss = by_rlzi[r]['loss'].sum(axis=0)
        for l, lt in enumerate(loss_dt.names):
            data[r][lt] = loss[l]
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
    oq = dstore['oqparam']
    R = dstore['csm_info'].get_num_rlzs()
    if R == 1:  # one realization
        mean = dstore['avg_losses-rlzs'][:, 0]
    else:
        mean = dstore['avg_losses-stats'][:, 0]
    data = numpy.array([tuple(row) for row in mean], oq.loss_dt())
    assets = util.get_assets(dstore)
    losses = util.compose_arrays(assets, data)
    losses.sort()
    return rst_table(losses, fmt=FIVEDIGITS)


@view.add('exposure_info')
def view_exposure_info(token, dstore):
    """
    Display info about the exposure model
    """
    assetcol = dstore['assetcol/array'][:]
    taxonomies = sorted(set(dstore['assetcol'].taxonomies))
    cc = dstore['assetcol/cost_calculator']
    ra_flag = ['relative', 'absolute']
    data = [('#assets', len(assetcol)),
            ('#taxonomies', len(taxonomies)),
            ('deductibile', ra_flag[int(cc.deduct_abs)]),
            ('insurance_limit', ra_flag[int(cc.limit_abs)]),
            ]
    return rst_table(data) + '\n\n' + view_assets_by_site(token, dstore)


@view.add('ruptures_events')
def view_ruptures_events(token, dstore):
    num_ruptures = len(dstore['ruptures'])
    num_events = len(dstore['events'])
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
    std = numpy.nan if len(array) == 1 else numpy.std(array, ddof=1)
    return (name, numpy.mean(array), std,
            numpy.min(array), numpy.max(array), len(array)) + extras


@view.add('num_units')
def view_num_units(token, dstore):
    """
    Display the number of units by taxonomy
    """
    taxo = dstore['assetcol/tagcol/taxonomy'].value
    counts = collections.Counter()
    for asset in dstore['assetcol']:
        counts[taxo[asset.taxonomy]] += asset.number
    data = sorted(counts.items())
    data.append(('*ALL*', sum(d[1] for d in data)))
    return rst_table(data, header=['taxonomy', 'num_units'])


@view.add('assets_by_site')
def view_assets_by_site(token, dstore):
    """
    Display statistical information about the distribution of the assets
    """
    taxonomies = dstore['assetcol/tagcol/taxonomy'].value
    assets_by_site = dstore['assetcol'].assets_by_site()
    data = ['taxonomy mean stddev min max num_sites num_assets'.split()]
    num_assets = AccumDict()
    for assets in assets_by_site:
        num_assets += {k: [len(v)] for k, v in groupby(
            assets, operator.attrgetter('taxonomy')).items()}
    for taxo in sorted(num_assets):
        val = numpy.array(num_assets[taxo])
        data.append(stats(taxonomies[taxo], val, val.sum()))
    if len(num_assets) > 1:  # more than one taxonomy, add a summary
        n_assets = numpy.array([len(assets) for assets in assets_by_site])
        data.append(stats('*ALL*', n_assets, n_assets.sum()))
    return rst_table(data)


@view.add('required_params_per_trt')
def view_required_params_per_trt(token, dstore):
    """
    Display the parameters needed by each tectonic region type
    """
    csm_info = dstore['csm_info']
    tbl = []
    for grp_id, trt in sorted(csm_info.grp_by("trt").items()):
        gsims = csm_info.gsim_lt.get_gsims(trt)
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
        if task not in ('task_sources', 'source_data'):  # this is special
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


@view.add('task_classical')
def view_task_classical(token, dstore):
    """
    Display info about a given task. Here are a few examples of usage::

     $ oq show task_classical:0  # the fastest task
     $ oq show task_classical:-1  # the slowest task
    """
    tasks = set(dstore['task_info'])
    if 'classical' in tasks:
        data = dstore['task_info/classical'].value
    else:
        data = dstore['task_info/count_ruptures'].value
    data.sort(order='duration')
    rec = data[int(token.split(':')[1])]
    taskno = rec['taskno']
    arr = get_array(dstore['task_info/source_data'].value, taskno=taskno)
    st = [stats('nsites', arr['nsites']), stats('weight', arr['weight'])]
    sources = dstore['task_info/task_sources'][taskno - 1].split()
    srcs = set(decode(s).split(':', 1)[0] for s in sources)
    res = 'taskno=%d, weight=%d, duration=%d s, sources="%s"\n\n' % (
        taskno, rec['weight'], rec['duration'], ' '.join(sorted(srcs)))
    return res + rst_table(st, header='variable mean stddev min max n'.split())


@view.add('task_risk')
def view_task_risk(token, dstore):
    """
    Display info about a given risk task. Here are a few examples of usage::

     $ oq show task_risk:0  # the fastest task
     $ oq show task_risk:-1  # the slowest task
    """
    [key] = dstore['task_info']
    data = dstore['task_info/' + key].value
    data.sort(order='duration')
    rec = data[int(token.split(':')[1])]
    taskno = rec['taskno']
    res = 'taskno=%d, weight=%d, duration=%d s' % (
        taskno, rec['weight'], rec['duration'])
    return res


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


@view.add('flat_hcurves')
def view_flat_hcurves(token, dstore):
    """
    Display the flat hazard curves for the calculation. They are
    used for debugging purposes when comparing the results of two
    calculations. They are the mean over the sites of the mean hazard
    curves.
    """
    oq = dstore['oqparam']
    nsites = len(dstore['sitecol'])
    rlzs_assoc = dstore['csm_info'].get_rlzs_assoc()
    mean = getters.PmapGetter(dstore, rlzs_assoc).get_mean()
    array = calc.convert_to_array(mean, nsites, oq.imtls)
    res = numpy.zeros(1, array.dtype)
    for name in array.dtype.names:
        res[name] = array[name].mean()
    return rst_table(res)


@view.add('flat_hmaps')
def view_flat_hmaps(token, dstore):
    """
    Display the flat hazard maps for the calculation. They are
    used for debugging purposes when comparing the results of two
    calculations. They are the mean over the sites of the mean hazard
    maps.
    """
    oq = dstore['oqparam']
    assert oq.poes
    rlzs_assoc = dstore['csm_info'].get_rlzs_assoc()
    nsites = len(dstore['sitecol'])
    pdic = DictArray({imt: oq.poes for imt in oq.imtls})
    mean = getters.PmapGetter(dstore, rlzs_assoc).get_mean()
    hmaps = calc.make_hmap(mean, oq.imtls, oq.poes)
    array = calc.convert_to_array(hmaps, nsites, pdic)
    res = numpy.zeros(1, array.dtype)
    for name in array.dtype.names:
        res[name] = array[name].mean()
    return rst_table(res)


@view.add('dupl_sources')
def view_dupl_sources(token, dstore):
    """
    Display the duplicated sources from source_info
    """
    info = dstore['source_info']
    items = sorted(group_array(info.value, 'source_id').items())
    tbl = []
    tot_calc_time = 0
    for source_id, records in items:
        if len(records) > 1:  # dupl
            calc_time = records['calc_time'].sum()
            tot_calc_time += calc_time
            tbl.append((source_id, calc_time, len(records)))
    if tbl and info.attrs['has_dupl_sources']:
        tot = info['calc_time'].sum()
        percent = tot_calc_time / tot * 100
        m = '\nTotal calc_time in duplicated sources: %d/%d (%d%%)' % (
            tot_calc_time, tot, percent)
        return rst_table(tbl, ['source_id', 'calc_time', 'num_dupl']) + m
    else:
        return 'There are no duplicated sources'


@view.add('global_poes')
def view_global_poes(token, dstore):
    """
    Display global probabilities averaged on all sites and all GMPEs
    """
    tbl = []
    imtls = dstore['oqparam'].imtls
    header = ['grp_id'] + [str(poe) for poe in imtls.array]
    for grp in sorted(dstore['poes']):
        poes = dstore['poes/' + grp]
        nsites = len(poes)
        site_avg = sum(poes[sid].array for sid in poes) / nsites
        gsim_avg = site_avg.sum(axis=1) / poes.shape_z
        tbl.append([grp] + list(gsim_avg))
    return rst_table(tbl, header=header)


@view.add('mean_disagg')
def view_mean_disagg(token, dstore):
    """
    Display mean quantities for the disaggregation. Useful for checking
    differences between two calculations.
    """
    tbl = []
    for key, dset in sorted(dstore['disagg'].items()):
        vals = [ds.value.mean() for k, ds in sorted(dset.items())]
        tbl.append([key] + vals)
    header = ['key'] + sorted(dset)
    return rst_table(sorted(tbl), header=header)


@view.add('elt')
def view_elt(token, dstore):
    """
    Display the event loss table averaged by event
    """
    oq = dstore['oqparam']
    R = len(dstore['csm_info'].rlzs)
    dic = group_array(dstore['losses_by_event'].value, 'rlzi')
    header = oq.loss_dt().names
    tbl = []
    for rlzi in range(R):
        if rlzi in dic:
            tbl.append(dic[rlzi]['loss'].mean(axis=0))
        else:
            tbl.append([0.] * len(header))
    return rst_table(tbl, header)


@view.add('pmap')
def view_pmap(token, dstore):
    """
    Display the mean ProbabilityMap associated to a given source group name
    """
    name = token.split(':')[1]  # called as pmap:name
    pmap = {}
    rlzs_assoc = dstore['csm_info'].get_rlzs_assoc()
    pgetter = getters.PmapGetter(dstore, rlzs_assoc)
    for grp, dset in dstore['poes'].items():
        if dset.attrs['name'] == name:
            pmap = pgetter.get_mean(grp)
            break
    return str(pmap)
