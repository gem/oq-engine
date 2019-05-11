# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2019 GEM Foundation
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
import functools
import itertools
import collections
import numpy

from openquake.baselib.general import (
    humansize, groupby, countby, AccumDict, CallableDict,
    get_array, group_array)
from openquake.baselib.performance import perf_dt
from openquake.baselib.python3compat import decode
from openquake.hazardlib import valid
from openquake.hazardlib.gsim.base import ContextMaker
from openquake.commonlib import util, source, calc
from openquake.commonlib.writers import build_header, scientificformat
from openquake.calculators import getters
from openquake.calculators.extract import extract

FLOAT = (float, numpy.float32, numpy.float64)
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
        if len(tup) != len(col_sizes):
            raise ValueError('The header has %d fields but the row %d fields!'
                             % (len(col_sizes), len(tup)))
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
    totals = sum_tbl(dstore['source_info'], 'code', ['calc_time'])
    return rst_table(totals)


@view.add('slow_sources')
def view_slow_sources(token, dstore, maxrows=20):
    """
    Returns the slowest sources
    """
    info = dstore['source_info'].value
    info.sort(order='calc_time')
    return rst_table(info[::-1][:maxrows])


@view.add('contents')
def view_contents(token, dstore):
    """
    Returns the size of the contents of the datastore and its total size
    """
    try:
        desc = dstore['oqparam'].description
    except KeyError:
        desc = ''
    data = sorted((dstore.getsize(key), key) for key in dstore)
    rows = [(key, humansize(nbytes)) for nbytes, key in data]
    total = '\n%s : %s' % (
        dstore.filename, humansize(os.path.getsize(dstore.filename)))
    return rst_table(rows, header=(desc, '')) + total


@view.add('csm_info')
def view_csm_info(token, dstore):
    csm_info = dstore['csm_info']
    header = ['smlt_path', 'weight', 'gsim_logic_tree', 'num_realizations']
    rows = []
    for sm in csm_info.source_models:
        kind, num_rlzs = csm_info.classify_gsim_lt(sm)
        row = ('_'.join(sm.path), sm.weight, kind, num_rlzs)
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


def rst_links(*fnames):
    links = []
    for fname in fnames:
        bname = os.path.basename(fname)
        links.append("`%s <%s>`_" % (bname, bname))
    return ' '.join(links)


def build_links(items):
    out = []
    for key, fname in items:
        if isinstance(fname, dict):
            for k, v in fname.items():
                b = os.path.basename(v)
                out.append(('reqv:' + k, "`%s <%s>`_" % (b, b)))
        elif isinstance(fname, list):
            out.append((key, rst_links(*fname)))
        else:
            out.append((key, rst_links(fname)))
    return sorted(out)


@view.add('inputs')
def view_inputs(token, dstore):
    inputs = dstore['oqparam'].inputs.items()
    return rst_table(build_links(inputs), ['Name', 'File'])


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
        dset = dstore['task_info/' + task]
        if 'argnames' in dset.attrs:
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
    L = len(dstore.get_attr('risk_model', 'loss_types'))
    ct = oq.concurrent_tasks
    size_bytes = N * R * L * 8 * ct  # 8 byte floats
    return (
        '%d asset(s) x %d realization(s) x %d loss type(s) losses x '
        '8 bytes x %d tasks = %s' % (N, R, L, ct, humansize(size_bytes)))


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


# for event based risk and ebrisk
def portfolio_loss(dstore):
    R = dstore['csm_info'].get_num_rlzs()
    array = dstore['losses_by_event'].value
    L = array.dtype['loss'].shape[0]  # loss has shape L, T...
    data = numpy.zeros((R, L), F32)
    for row in array:
        for lti in range(L):
            data[row['rlzi'], lti] += row['loss'][lti].sum()
    return data


@view.add('portfolio_losses')
def view_portfolio_losses(token, dstore):
    """
    The losses for the full portfolio, for each realization and loss type,
    extracted from the event loss table.
    """
    oq = dstore['oqparam']
    loss_dt = oq.loss_dt()
    data = portfolio_loss(dstore).view(loss_dt)[:, 0]
    rlzids = [str(r) for r in range(len(data))]
    array = util.compose_arrays(numpy.array(rlzids), data, 'rlz')
    # this is very sensitive to rounding errors, so I am using a low precision
    return rst_table(array, fmt='%.5E')


@view.add('portfolio_loss')
def view_portfolio_loss(token, dstore):
    """
    The mean and stddev loss for the full portfolio for each loss type,
    extracted from the event loss table, averaged over the realizations
    """
    data = portfolio_loss(dstore)  # shape (R, L)
    loss_types = list(dstore['oqparam'].loss_dt().names)
    header = ['portfolio_loss'] + loss_types
    mean = ['mean'] + [row.mean() for row in data.T]
    stddev = ['stddev'] + [row.std(ddof=1) for row in data.T]
    return rst_table([mean, stddev], header)


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
    events_by_rlz = countby(dstore['events'].value, 'rlz')
    mult = round(num_events / num_ruptures, 3)
    lst = [('Total number of ruptures', num_ruptures),
           ('Total number of events', num_events),
           ('Rupture multiplicity', mult),
           ('Events by rlz', events_by_rlz.values())]
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
        counts[taxo[asset['taxonomy']]] += asset['number']
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
        num_assets += {k: [len(v)] for k, v in group_array(
            assets, 'taxonomy').items()}
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
        maker = ContextMaker(trt, gsims)
        distances = sorted(maker.REQUIRES_DISTANCES)
        siteparams = sorted(maker.REQUIRES_SITES_PARAMETERS)
        ruptparams = sorted(maker.REQUIRES_RUPTURE_PARAMETERS)
        tbl.append((grp_id, ' '.join(map(repr, map(repr, gsims))),
                    distances, siteparams, ruptparams))
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

    data = ['operation-duration mean stddev min max outputs'.split()]
    for task in dstore['task_info']:
        val = dstore['task_info/' + task]['duration']
        if len(val):
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


@view.add('task_hazard')
def view_task_hazard(token, dstore):
    """
    Display info about a given task. Here are a few examples of usage::

     $ oq show task_hazard:0  # the fastest task
     $ oq show task_hazard:-1  # the slowest task
    """
    tasks = set(dstore['task_info'])
    if 'source_data' not in dstore:
        return 'Missing source_data'
    if 'classical_split_filter' in tasks:
        data = dstore['task_info/classical_split_filter'].value
    else:
        data = dstore['task_info/compute_gmfs'].value
    data.sort(order='duration')
    rec = data[int(token.split(':')[1])]
    taskno = rec['taskno']
    arr = get_array(dstore['source_data'].value, taskno=taskno)
    st = [stats('nsites', arr['nsites']), stats('weight', arr['weight'])]
    sources = dstore['task_sources'][taskno - 1].split()
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
    mean = dict(extract(dstore, 'hcurves?kind=mean'))['mean']
    oq = dstore['oqparam']
    hmap = calc.make_hmap_array(mean, oq.imtls, [poe], len(mean))
    dt = numpy.dtype([('sid', U32)] + [(imt, F32) for imt in oq.imtls])
    array = numpy.zeros(len(hmap), dt)
    for i, vals in enumerate(hmap):
        array[i] = (i, ) + tuple(vals)
    array.sort(order=list(oq.imtls)[0])
    return rst_table(array[:20])


@view.add('global_hcurves')
def view_global_hcurves(token, dstore):
    """
    Display the global hazard curves for the calculation. They are
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


@view.add('dupl_sources_time')
def view_dupl_sources_time(token, dstore):
    """
    Display the time spent computing duplicated sources
    """
    info = dstore['source_info']
    items = sorted(group_array(info.value, 'source_id').items())
    tbl = []
    tot_time = 0
    for source_id, records in items:
        if len(records) > 1:  # dupl
            calc_time = records['calc_time'].sum()
            tot_time += calc_time + records['split_time'].sum()
            tbl.append((source_id, calc_time, len(records)))
    if tbl and info.attrs.get('has_dupl_sources'):
        tot = info['calc_time'].sum() + info['split_time'].sum()
        percent = tot_time / tot * 100
        m = '\nTotal time in duplicated sources: %d/%d (%d%%)' % (
            tot_time, tot, percent)
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


@view.add('global_hmaps')
def view_global_hmaps(token, dstore):
    """
    Display the global hazard maps for the calculation. They are
    used for debugging purposes when comparing the results of two
    calculations. They are the mean over the sites of the mean hazard
    maps.
    """
    oq = dstore['oqparam']
    dt = numpy.dtype([('%s-%s' % (imt, poe), F32)
                      for imt in oq.imtls for poe in oq.poes])
    array = dstore['hmaps/mean'].value.view(dt)[:, 0]
    res = numpy.zeros(1, array.dtype)
    for name in array.dtype.names:
        res[name] = array[name].mean()
    return rst_table(res)


@view.add('global_gmfs')
def view_global_gmfs(token, dstore):
    """
    Display GMFs averaged on everything for debugging purposes
    """
    imtls = dstore['oqparam'].imtls
    row = dstore['gmf_data/data']['gmv'].mean(axis=0)
    return rst_table([row], header=imtls)


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
    grp = token.split(':')[1]  # called as pmap:grp
    pmap = {}
    rlzs_assoc = dstore['csm_info'].get_rlzs_assoc()
    pgetter = getters.PmapGetter(dstore, rlzs_assoc)
    pmap = pgetter.get_mean(grp)
    return str(pmap)


@view.add('act_ruptures_by_src')
def view_act_ruptures_by_src(token, dstore):
    """
    Display the actual number of ruptures by source in event based calculations
    """
    data = dstore['ruptures'].value[['srcidx', 'serial']]
    counts = sorted(countby(data, 'srcidx').items(),
                    key=operator.itemgetter(1), reverse=True)
    src_info = dstore['source_info'].value[['grp_id', 'source_id']]
    table = [['src_id', 'grp_id', 'act_ruptures']]
    for srcidx, act_ruptures in counts:
        src = src_info[srcidx]
        table.append([src['source_id'], src['grp_id'], act_ruptures])
    return rst_table(table)


Source = collections.namedtuple('Source', 'source_id code geom num_ruptures')


def all_equal(records):
    rec0 = records[0]
    for rec in records[1:]:
        for v1, v2 in zip(rec0, rec):
            if isinstance(v1, numpy.ndarray):  # field geom
                if len(v1) != len(v2):
                    return False
                for name in v1.dtype.names:
                    if not numpy.allclose(v1[name], v2[name]):
                        return False
            elif v1 != v2:
                return False
    return True


@view.add('dupl_sources')
def view_dupl_sources(token, dstore):
    """
    Show the sources with the same ID and the truly duplicated sources
    """
    fields = ['source_id', 'code', 'gidx1', 'gidx2', 'num_ruptures']
    dic = group_array(dstore['source_info'].value[fields], 'source_id')
    sameid = []
    dupl = []
    for source_id, group in dic.items():
        if len(group) > 1:  # same ID sources
            sources = []
            for rec in group:
                geom = dstore['source_geom'][rec['gidx1']:rec['gidx2']]
                src = Source(source_id, rec['code'], geom, rec['num_ruptures'])
                sources.append(src)
            if all_equal(sources):
                dupl.append(source_id)
            sameid.append(source_id)
    if not dupl:
        return ''
    msg = str(dupl) + '\n'
    msg += ('Found %d source(s) with the same ID and %d true duplicate(s)'
            % (len(sameid), len(dupl)))
    fakedupl = set(sameid) - set(dupl)
    if fakedupl:
        msg += '\nHere is a fake duplicate: %s' % fakedupl.pop()
    return msg


@view.add('extreme_groups')
def view_extreme_groups(token, dstore):
    """
    Show the source groups contributing the most to the highest IML
    """
    data = dstore['disagg_by_grp'].value
    data.sort(order='extreme_poe')
    return rst_table(data[::-1])


@view.add('gmvs_to_hazard')
def view_gmvs_to_hazard(token, dstore):
    """
    Show the number of GMFs over the highest IML
    """
    args = token.split(':')[1:]  # called as view_gmvs_to_hazard:sid:rlz
    if not args:
        sid, rlz = 0, 0
    elif len(args) == 1:  # only sid specified
        sid, rlz = int(args[0]), 0
    else:
        sid, rlz = int(args[0]), int(args[1])
    assert sid in dstore['sitecol'].sids
    assert rlz < dstore['csm_info'].get_num_rlzs()
    oq = dstore['oqparam']
    num_ses = oq.ses_per_logic_tree_path
    data = dstore['gmf_data/data'].value
    data = data[(data['sid'] == sid) & (data['rlzi'] == rlz)]
    tbl = []
    gmv = data['gmv']
    for imti, (imt, imls) in enumerate(oq.imtls.items()):
        for iml in imls:
            # same algorithm as in _gmvs_to_haz_curve
            exceeding = numpy.sum(gmv[:, imti] >= iml)
            poe = 1 - numpy.exp(- exceeding / num_ses)
            tbl.append((sid, rlz, imt, iml, exceeding, poe))
    return rst_table(tbl, ['sid', 'rlz', 'imt', 'iml', 'num_exceeding', 'poe'])
