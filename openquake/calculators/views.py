# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2020 GEM Foundation
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

import io
import ast
import os.path
import numbers
import operator
import functools
import collections
import numpy

from openquake.baselib.general import (
    humansize, countby, AccumDict, CallableDict,
    get_array, group_array, fast_agg, fast_agg3)
from openquake.baselib.performance import performance_view
from openquake.baselib.python3compat import encode, decode
from openquake.hazardlib.gsim.base import ContextMaker
from openquake.commonlib import util, calc
from openquake.commonlib.writers import (
    build_header, scientificformat, write_csv)
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
    '1_003'
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
            return '{:_d}'.format(int(round(value)))
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


@view.add('times_by_source_class')
def view_times_by_source_class(token, dstore):
    """
    Returns the calculation times depending on the source typology
    """
    totals = fast_agg3(dstore['source_info']['code', 'calc_time'],
                       'code', ['calc_time'])
    return rst_table(totals)


@view.add('slow_sources')
def view_slow_sources(token, dstore, maxrows=20):
    """
    Returns the slowest sources
    """
    info = dstore['source_info']['source_id', 'code', 'multiplicity',
                                 'calc_time', 'num_sites', 'eff_ruptures']
    info = info[info['eff_ruptures'] > 0]
    info.sort(order='calc_time')
    data = numpy.zeros(len(info), [(nam, object) for nam in info.dtype.names])
    for name in info.dtype.names:
        data[name] = info[name]
    data['num_sites'] /= data['eff_ruptures']
    return rst_table(data[::-1][:maxrows])


@view.add('slow_ruptures')
def view_slow_ruptures(token, dstore, maxrows=25):
    """
    Show the slowest ruptures
    """
    fields = ['code', 'n_occ', 'mag', 'grp_id']
    rups = dstore['ruptures'][()][fields]
    time = dstore['gmf_data/time_by_rup'][()]
    arr = util.compose_arrays(rups, time)
    arr = arr[arr['nsites'] > 0]
    arr.sort(order='time')
    return rst_table(arr[-maxrows:])


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


@view.add('full_lt')
def view_full_lt(token, dstore):
    full_lt = dstore['full_lt']
    if full_lt.num_samples == 0:
        num_rlzs = full_lt.gsim_lt.get_num_paths()
    header = ['smlt_path', 'weight', 'num_realizations']
    rows = []
    for sm in full_lt.sm_rlzs:
        if full_lt.num_samples:
            num_rlzs = sm.samples
        row = ('_'.join(sm.lt_path), sm.weight, num_rlzs)
        rows.append(row)
    return rst_table(rows, header)


@view.add('eff_ruptures')
def view_eff_ruptures(token, dstore):
    header = ['num_ruptures', 'eff_ruptures']
    info = dstore['source_info']['num_ruptures', 'eff_ruptures']
    return rst_table([[info['num_ruptures'].sum(),
                       info['eff_ruptures'].sum()]], header)


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
              'pointsource_distance',
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
    task_info = dstore['task_info'][()]
    task_sent = ast.literal_eval(dstore['task_sent'][()])
    for task, dic in task_sent.items():
        sent = sorted(dic.items(), key=operator.itemgetter(1), reverse=True)
        sent = ['%s=%s' % (k, humansize(v)) for k, v in sent[:3]]
        recv = get_array(task_info, taskname=encode(task))['received'].sum()
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
    R = dstore['full_lt'].get_num_rlzs()
    L = len(dstore.get_attr('risk_model', 'loss_types'))
    ct = oq.concurrent_tasks
    size_bytes = N * R * L * 8 * ct  # 8 byte floats
    return (
        '%d asset(s) x %d realization(s) x %d loss type(s) losses x '
        '8 bytes x %d tasks = %s' % (N, R, L, ct, humansize(size_bytes)))


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
    tot_losses = dstore['avg_losses-rlzs'][()].sum(axis=0)
    return rst_table(tot_losses.view(oq.loss_dt()), fmt='%.6E')


# for event based risk and ebrisk
def portfolio_loss(dstore):
    R = dstore['full_lt'].get_num_rlzs()
    array = dstore['losses_by_event'][()]
    L, = array.dtype['loss'].shape  # loss has shape L
    data = numpy.zeros((R, L), F32)
    for row in array:
        data[row['rlzi']] += row['loss']
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
    array = util.compose_arrays(numpy.array(rlzids), data, 'rlz_id')
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
    data = [('#assets', len(assetcol)),
            ('#taxonomies', len(taxonomies))]
    return rst_table(data) + '\n\n' + view_assets_by_site(token, dstore)


@view.add('ruptures_events')
def view_ruptures_events(token, dstore):
    num_ruptures = len(dstore['ruptures'])
    num_events = len(dstore['events'])
    events_by_rlz = countby(dstore['events'][()], 'rlz_id')
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
    taxo = dstore['assetcol/tagcol/taxonomy'][()]
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
    taxonomies = dstore['assetcol/tagcol/taxonomy'][()]
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
    full_lt = dstore['full_lt']
    tbl = []
    for grp_id, trt in sorted(full_lt.trt_by_grp.items()):
        gsims = full_lt.gsim_lt.get_gsims(trt)
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
    task_info = dstore['task_info']
    task_info.refresh()
    args = token.split(':')[1:]  # called as task_info:task_name
    if args:
        [task] = args
        array = get_array(task_info[()], taskname=task.encode('utf8'))
        rduration = array['duration'] / array['weight']
        data = util.compose_arrays(rduration, array, 'rduration')
        data.sort(order='duration')
        return rst_table(data)

    data = ['operation-duration mean stddev min max outputs'.split()]
    for task, arr in group_array(task_info[()], 'taskname').items():
        val = arr['duration']
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
    array = get_array(dstore['task_info'][()], taskname=task)['duration']
    return '\n'.join(map(str, array))


@view.add('task')
def view_task_hazard(token, dstore):
    """
    Display info about a given task. Here are a few examples of usage::

     $ oq show task:classical:0  # the fastest task
     $ oq show task:classical:-1  # the slowest task
    """
    _, name, index = token.split(':')
    if 'by_task' not in dstore:
        return 'Missing by_task'
    data = get_array(dstore['task_info'][()], taskname=encode(name))
    if len(data) == 0:
        raise RuntimeError('No task_info for %s' % name)
    data.sort(order='duration')
    rec = data[int(index)]
    taskno = rec['task_no']
    eff_ruptures = dstore['by_task/eff_ruptures'][taskno]
    eff_sites = dstore['by_task/eff_sites'][taskno]
    srcids = dstore['by_task/srcids'][taskno]
    res = ('taskno=%d, eff_ruptures=%d, eff_sites=%d, duration=%d s\n'
           'sources="%s"' % (taskno, eff_ruptures, eff_sites, rec['duration'],
                             srcids))
    return res


@view.add('task_ebrisk')
def view_task_ebrisk(token, dstore):
    """
    Display info about ebrisk tasks:

    $ oq show task_ebrisk:-1  # the slowest task
    """
    idx = int(token.split(':')[1])
    task_info = get_array(dstore['task_info'][()], taskname=b'ebrisk')
    task_info.sort(order='duration')
    info = task_info[idx]
    times = get_array(dstore['gmf_info'][()], task_no=info['task_no'])
    extra = times[['nsites', 'gmfbytes', 'dt']]
    ds = dstore.parent if dstore.parent else dstore
    rups = ds['ruptures']['id', 'code', 'n_occ', 'mag'][times['rup_id']]
    codeset = set('code_%d' % code for code in numpy.unique(rups['code']))
    tbl = rst_table(util.compose_arrays(rups, extra))
    codes = ['%s: %s' % it for it in ds.getitem('ruptures').attrs.items()
             if it[0] in codeset]
    msg = '%s\n%s\nHazard time for task %d: %d of %d s, ' % (
        tbl, '\n'.join(codes), info['task_no'], extra['dt'].sum(),
        info['duration'])
    msg += 'gmfbytes=%s, w=%d' % (
        humansize(extra['gmfbytes'].sum()),
        (rups['n_occ'] * extra['nsites']).sum())
    return msg


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
    rlzs = dstore['full_lt'].get_realizations()
    weights = [rlz.weight for rlz in rlzs]
    mean = getters.PmapGetter(dstore, weights).get_mean()
    array = calc.convert_to_array(mean, nsites, oq.imtls)
    res = numpy.zeros(1, array.dtype)
    for name in array.dtype.names:
        res[name] = array[name].mean()
    return rst_table(res)


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
    array = dstore['hmaps/mean'][()].view(dt)[:, 0]
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


@view.add('gmv_by_rup')
def view_gmv_by_rup(token, dstore):
    """
    Display a synthetic gmv per rupture serial for debugging purposes
    """
    rup_id = dstore['events']['rup_id']
    serial = dstore['ruptures']['serial']
    data = dstore['gmf_data/data'][()]
    gmv = fast_agg3(data, 'eid', ['gmv'])
    gmv['eid'] = serial[rup_id[gmv['eid']]]
    gm = fast_agg3(gmv, 'eid', ['gmv'])
    return rst_table(gm, header=['serial', 'gmv'])


@view.add('mean_disagg')
def view_mean_disagg(token, dstore):
    """
    Display mean quantities for the disaggregation. Useful for checking
    differences between two calculations.
    """
    N, M, P, Z = dstore['iml4'].shape
    tbl = []
    kd = {key: dset[:] for key, dset in sorted(dstore['disagg'].items())}
    oq = dstore['oqparam']
    for s in range(N):
        for m, imt in enumerate(oq.imtls):
            for p in range(P):
                row = ['%s-sid-%d-poe-%s' % (imt, s, p)]
                for k, d in kd.items():
                    row.append(d[s, m, p].mean())
                tbl.append(row)
    return rst_table(sorted(tbl), header=['key'] + list(kd))


@view.add('disagg_times')
def view_disagg_times(token, dstore):
    """
    Display slow tasks for disaggregation
    """
    data = dstore['disagg_task'][:]
    info = dstore.read_df('task_info', 'taskname').loc[b'compute_disagg']
    tbl = []
    for duration, task_no in zip(info['duration'], info['task_no']):
        tbl.append((duration, task_no) + tuple(data[task_no]))
    header = ('duration', 'task_no') + data.dtype.names
    return rst_table(sorted(tbl), header=header)


@view.add('elt')
def view_elt(token, dstore):
    """
    Display the event loss table averaged by event
    """
    oq = dstore['oqparam']
    R = len(dstore['full_lt'].rlzs)
    dic = group_array(dstore['losses_by_event'][()], 'rlzi')
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
    rlzs = dstore['full_lt'].get_realizations()
    weights = [rlz.weight for rlz in rlzs]
    pgetter = getters.PmapGetter(dstore, weights)
    pmap = pgetter.get_mean(grp)
    return str(pmap)


@view.add('act_ruptures_by_src')
def view_act_ruptures_by_src(token, dstore):
    """
    Display the actual number of ruptures by source in event based calculations
    """
    data = dstore['ruptures'][('source_id', 'grp_id', 'rup_id')]
    counts = sorted(countby(data, 'source_id').items(),
                    key=operator.itemgetter(1), reverse=True)
    table = [['src_id', 'grp_id', 'act_ruptures']]
    for source_id, act_ruptures in counts:
        table.append([source_id, src['grp_id'], act_ruptures])
    return rst_table(table)


@view.add('bad_ruptures')
def view_bad_ruptures(token, dstore):
    """
    Display the ruptures degenerating to a point
    """
    data = dstore['ruptures']['id', 'code', 'mag',
                              'minlon', 'maxlon', 'minlat', 'maxlat']
    bad = data[numpy.logical_and(data['minlon'] == data['maxlon'],
                                 data['minlat'] == data['maxlat'])]
    return rst_table(bad)


Source = collections.namedtuple(
    'Source', 'source_id code num_ruptures checksum')


@view.add('extreme_groups')
def view_extreme_groups(token, dstore):
    """
    Show the source groups contributing the most to the highest IML
    """
    data = dstore['disagg_by_grp'][()]
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
    assert rlz < dstore['full_lt'].get_num_rlzs()
    oq = dstore['oqparam']
    num_ses = oq.ses_per_logic_tree_path
    data = dstore['gmf_data/data'][()]
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


@view.add('gmvs')
def view_gmvs(token, dstore):
    """
    Show the GMVs on a given site ID
    """
    sid = int(token.split(':')[1])  # called as view_gmvs:sid
    assert sid in dstore['sitecol'].sids
    data = dstore['gmf_data/data'][()]
    gmvs = data[data['sid'] == sid]['gmv']
    return rst_table(gmvs)


@view.add('events_by_mag')
def view_events_by_mag(token, dstore):
    """
    Show how many events there are for each magnitude
    """
    rups = dstore['ruptures'][()]
    num_evs = fast_agg(dstore['events']['rup_id'])
    counts = {}
    for mag, grp in group_array(rups, 'mag').items():
        counts[mag] = sum(num_evs[rup_id] for rup_id in grp['id'])
    return rst_table(counts.items(), ['mag', 'num_events'])


@view.add('maximum_intensity')
def view_maximum_intensity(token, dstore):
    """
    Show intensities at minimum and maximum distance for the highest magnitude
    """
    effect = extract(dstore, 'effect')
    data = zip(dstore['full_lt'].trts, effect[-1, -1], effect[-1, 0])
    return rst_table(data, ['trt', 'intensity1', 'intensity2'])


@view.add('extreme_sites')
def view_extreme(token, dstore):
    """
    Show sites where the mean hazard map reaches maximum values
    """
    mean = dstore.sel('hmaps-stats', stat='mean')[:, 0, 0, -1]  # shape N1MP
    site_ids, = numpy.where(mean == mean.max())
    arr = dstore['sitecol'][site_ids]
    return write_csv(io.StringIO(), arr)
