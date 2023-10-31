# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2023 GEM Foundation
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
import html
import os.path
import numbers
import operator
import functools
import itertools
import collections
import logging
import numpy
import pandas

from openquake.baselib.general import (
    humansize, countby, AccumDict, CallableDict,
    get_array, group_array, fast_agg)
from openquake.baselib.hdf5 import FLOAT, INT, get_shape_descr
from openquake.baselib.performance import performance_view
from openquake.baselib.python3compat import encode, decode
from openquake.hazardlib import logictree, calc, source
from openquake.hazardlib.contexts import KNOWN_DISTANCES
from openquake.hazardlib.gsim.base import ContextMaker, Collapser
from openquake.commonlib import util
from openquake.risklib.scientific import (
    losses_by_period, return_periods, LOSSID)
from openquake.baselib.writers import build_header, scientificformat
from openquake.calculators.classical import get_pmaps_gb
from openquake.calculators.getters import get_ebrupture
from openquake.calculators.extract import extract

F32 = numpy.float32
F64 = numpy.float64
U32 = numpy.uint32
U8 = numpy.uint8

# a dictionary of views datastore -> array
view = CallableDict(keyfunc=lambda s: s.split(':', 1)[0])
code2cls = source.rupture.code2cls

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
    >>> form(103.41)
    '103.4'
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
            return str(round(value, 1))
    elif isinstance(value, bytes):
        return decode(value)
    elif isinstance(value, str):
        return value
    elif isinstance(value, numpy.object_):
        return str(value)
    elif hasattr(value, '__len__') and len(value) > 1:
        return ' '.join(map(form, value))
    return str(value)


def dt(names):
    """
    :param names: list or a string with space-separated names
    :returns: a numpy structured dtype
    """
    if isinstance(names, str):
        names = names.split()
    return numpy.dtype([(name, object) for name in names])


class HtmlTable(object):
    """
    Convert a sequence header+body into a HTML table.
    """
    css = """\
    tr.evenRow { background-color: lightgreen }
    tr.oddRow { }
    th { background-color: lightblue }
    """
    maxrows = 5000
    border = "1"
    summary = ""

    def __init__(self, header_plus_body, name='noname',
                 empty_table='Empty table'):
        header, body = header_plus_body[0], header_plus_body[1:]
        self.name = name
        self.empty_table = empty_table
        rows = []  # rows is a finite sequence of tuples
        for i, row in enumerate(body):
            if i == self.maxrows:
                rows.append(
                    ["Table truncated because too big: more than %s rows" % i])
                break
            rows.append(row)
        self.rows = rows
        self.header = tuple(header)  # horizontal header

    def render(self, dummy_ctxt=None):
        out = "\n%s\n" % "".join(list(self._gen_table()))
        if not self.rows:
            out += '<em>%s</em>' % html.escape(self.empty_table, quote=True)
        return out

    def _gen_table(self):
        yield '<table id="%s" border="%s" summary="%s" class="tablesorter">\n'\
              % (self.name, self.border, self.summary)
        yield '<thead>\n'
        yield '<tr>%s</tr>\n' % ''.join(
            '<th>%s</th>\n' % h for h in self.header)
        yield '</thead>\n'
        yield '<tbody\n>'
        for r, row in enumerate(self.rows):
            yield '<tr class="%s">\n' % ["even", "odd"][r % 2]
            for col in row:
                yield '<td>%s</td>\n' % col
            yield '</tr>\n'
        yield '</tbody>\n'
        yield '</table>\n'


def text_table(data, header=None, fmt=None, ext='rst'):
    """
    Build a .rst (or .org) table from a matrix or a DataFrame

    >>> tbl = [['a', 1], ['b', 2]]
    >>> print(text_table(tbl, header=['Name', 'Value']))
    +------+-------+
    | Name | Value |
    +------+-------+
    | a    | 1     |
    +------+-------+
    | b    | 2     |
    +------+-------+
    """
    assert ext in 'rst org html', ext
    if isinstance(data, pandas.DataFrame):
        if data.index.name:
            data = data.reset_index()
        header = header or list(data.columns)
        data = zip(*[data[col].to_numpy() for col in data.columns])
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
    if ext == 'html':
        return HtmlTable([header] + body).render()

    wrap = '+-%s-+' if ext == 'rst' else '|-%s-|'
    sepline = wrap % '-+-'.join('-' * size for size in col_sizes)
    templ = '| %s |' % ' | '.join('%-{}s'.format(size) for size in col_sizes)
    if header and ext == 'rst':
        lines = [sepline, templ % tuple(header), sepline]
    elif header and ext == 'org':
        lines = [templ % tuple(header), sepline]
    else:
        lines = [sepline]
    for row in body:
        lines.append(templ % row)
        if ext == 'rst':
            lines.append(sepline)
    return '\n'.join(lines)


@view.add('worst_sources')
def view_worst_sources(token, dstore):
    """
    Returns the sources with worst weights
    """
    if ':' in token:
        step = int(token.split(':')[1])
    else:
        step = 1
    data = dstore.read_df('source_data', 'src_id')
    del data['impact']
    ser = data.groupby('taskno').ctimes.sum().sort_values().tail(1)
    [[taskno, maxtime]] = ser.to_dict().items()
    data = data[data.taskno == taskno]
    print('Sources in the slowest task (%d seconds, weight=%d, taskno=%d)'
          % (maxtime, data['weight'].sum(), taskno))
    data['slow_rate'] = data.ctimes / data.weight
    del data['taskno']
    df = data.sort_values('ctimes', ascending=False)
    return df[slice(None, None, step)]


@view.add('slow_sources')
def view_slow_sources(token, dstore, maxrows=20):
    """
    Returns the slowest sources
    """
    info = dstore['source_info']['source_id', 'code',
                                 'calc_time', 'num_sites', 'num_ruptures']
    info.sort(order='calc_time')
    data = numpy.zeros(len(info), dt(info.dtype.names))
    for name in info.dtype.names:
        data[name] = info[name]
    return data[::-1][:maxrows]


@view.add('rup_info')
def view_rup_info(token, dstore, maxrows=25):
    """
    Show the slowest ruptures
    """
    if not code2cls:
        code2cls.update(source.rupture.BaseRupture.init())
    fields = ['code', 'n_occ', 'nsites', 'mag']
    rups = dstore.read_df('ruptures', 'id')[fields]
    info = dstore.read_df('gmf_data/rup_info', 'rup_id')
    df = rups.join(info).sort_values('time', ascending=False)
    df['surface'] = [code2cls[code][1].__name__ for code in df.code]
    del df['task_no']
    del df['code']
    return df[:maxrows]


@view.add('contents')
def view_contents(token, dstore):
    """
    Returns the size of the contents of the datastore and its total size
    """
    tot = (dstore.filename, humansize(os.path.getsize(dstore.filename)))
    data = sorted((dstore.getsize(key), key) for key in dstore)
    rows = [(key, humansize(nbytes)) for nbytes, key in data] + [tot]
    return numpy.array(rows, dt('dataset size'))


def short_repr(lst):
    if len(lst) <= 10:
        return ' '.join(map(str, lst))
    return '[%d rlzs]' % len(lst)


@view.add('full_lt')
def view_full_lt(token, dstore):
    full_lt = dstore['full_lt'].init()
    num_paths = full_lt.get_num_potential_paths()
    if not full_lt.num_samples and num_paths > 15000:
        return '<%d realizations>' % num_paths
    full_lt.get_trt_rlzs(dstore['trt_smrs'][:])  # set _rlzs_by
    header = ['trt_smr', 'gsim', 'rlzs']
    rows = []
    for trt_smr, rbg in full_lt._rlzs_by.items():
        for gsim, rlzs in rbg.items():
            rows.append((trt_smr, repr(str(gsim)), short_repr(rlzs)))
    return numpy.array(rows, dt(header))


@view.add('weight_by_src')
def view_eff_ruptures(token, dstore):
    info = dstore.read_df('source_info', 'source_id')
    df = info.groupby('code').sum()
    df['slow_factor'] = df.calc_time / df.weight
    del df['grp_id'], df['trti'], df['mutex_weight']
    return df


@view.add('short_source_info')
def view_short_source_info(token, dstore, maxrows=20):
    return dstore['source_info'][:maxrows]


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
    return numpy.array([(param, repr(getattr(oq, param, None)))
                        for param in params], dt('parameter value'))


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
    return numpy.array(build_links(inputs), dt('Name File'))


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
    data = []
    task_info = dstore['task_info'][()]
    task_sent = ast.literal_eval(decode(dstore['task_sent'][()]))
    for task, dic in task_sent.items():
        sent = sorted(dic.items(), key=operator.itemgetter(1), reverse=True)
        sent = ['%s=%s' % (k, humansize(v)) for k, v in sent[:3]]
        recv = get_array(task_info, taskname=encode(task))['received']
        data.append((task, ' '.join(sent),
                     humansize(recv.sum()), humansize(recv.mean())))
    return numpy.array(data, dt('task sent received mean_recv'))


@view.add('avglosses_data_transfer')
def avglosses_data_transfer(token, dstore):
    """
    Determine the amount of average losses transferred from the workers to the
    controller node in a risk calculation.
    """
    oq = dstore['oqparam']
    N = len(dstore['assetcol'])
    R = dstore['full_lt'].get_num_paths()
    L = len(dstore.get_attr('crm', 'loss_types'))
    ct = oq.concurrent_tasks
    size_bytes = N * R * L * 8 * ct  # 8 byte floats
    return (
        '%d asset(s) x %d realization(s) x %d loss type(s) losses x '
        '8 bytes x %d tasks = %s' % (N, R, L, ct, humansize(size_bytes)))


# for scenario_risk and classical_risk
@view.add('totlosses')
def view_totlosses(token, dstore):
    """
    This is a debugging view. You can use it to check that the total
    losses, i.e. the losses obtained by summing the average losses on
    all assets are indeed equal to the aggregate losses. This is a
    sanity check for the correctness of the implementation.
    """
    oq = dstore['oqparam']
    tot_losses = 0
    for ltype in oq.loss_types:
        name = 'avg_losses-stats/' + ltype
        try:
            tot = dstore[name][()].sum(axis=0)
        except KeyError:
            name = 'avg_losses-rlzs/' + ltype
            tot = dstore[name][()].sum(axis=0)
        tot_losses += tot
    return text_table(tot_losses.view(oq.loss_dt(F32)), fmt='%.6E')


def alt_to_many_columns(alt, loss_types):
    # convert an risk_by_event in the format
    # (event_id, agg_id, loss_id, loss) =>
    # (event_id, agg_id, structural, nonstructural, ...)
    dic = dict(event_id=[])
    for ln in loss_types:
        dic[ln] = []
    for (eid, kid), df in alt.groupby(['event_id', 'agg_id']):
        dic['event_id'].append(eid)
        for ln in loss_types:
            arr = df[df.loss_id == LOSSID[ln]].loss.to_numpy()
            loss = 0 if len(arr) == 0 else arr[0]  # arr has size 0 or 1
            dic[ln].append(loss)
    return pandas.DataFrame(dic)


def _portfolio_loss(dstore):
    oq = dstore['oqparam']
    R = dstore['full_lt'].get_num_paths()
    K = dstore['risk_by_event'].attrs.get('K', 0)
    alt = dstore.read_df('risk_by_event', 'agg_id', dict(agg_id=K))
    df = alt_to_many_columns(alt, oq.loss_types)
    eids = df.pop('event_id').to_numpy()
    loss = df.to_numpy()
    rlzs = dstore['events']['rlz_id'][eids]
    L = loss.shape[1]
    data = numpy.zeros((R, L))
    for row, rlz in zip(loss, rlzs):
        data[rlz] += row
    return data


@view.add('portfolio_losses')
def view_portfolio_losses(token, dstore):
    """
    The losses for the full portfolio, for each realization and loss type,
    extracted from the event loss table.
    """
    oq = dstore['oqparam']
    loss_dt = oq.loss_dt()
    data = _portfolio_loss(dstore).view(loss_dt)[:, 0]  # shape R
    rlzids = [str(r) for r in range(len(data))]
    array = util.compose_arrays(numpy.array(rlzids), data, 'rlz_id')
    # this is very sensitive to rounding errors, so I am using a low precision
    return text_table(array, fmt='%.5E')


@view.add('portfolio_loss')
def view_portfolio_loss(token, dstore):
    """
    The mean portfolio loss for each loss type,
    extracted from the event loss table.
    """
    oq = dstore['oqparam']
    R = dstore['full_lt'].get_num_paths()
    K = dstore['risk_by_event'].attrs.get('K', 0)
    alt_df = dstore.read_df('risk_by_event', 'agg_id', dict(agg_id=K))
    weights = dstore['weights'][:]
    rlzs = dstore['events']['rlz_id']
    E = len(rlzs)
    ws = weights[rlzs]
    avgs = []
    if oq.investigation_time:
        factor = oq.time_ratio * E / R
    else:
        factor = 1 / R
    for ln in oq.loss_types:
        df = alt_df[alt_df.loss_id == LOSSID[ln]]
        eids = df.pop('event_id').to_numpy()
        avgs.append(ws[eids] @ df.loss.to_numpy() / ws.sum() * factor)
    return text_table([['avg'] + avgs], ['loss'] + oq.loss_types)


@view.add('portfolio_dmgdist')
def portfolio_dmgdist(token, dstore):
    """
    The portfolio damages extracted from the first realization of damages-rlzs
    """
    oq = dstore['oqparam']
    dstates = ['no_damage'] + oq.limit_states
    D = len(dstates)
    arr = dstore['damages-rlzs'][:, 0, :, :D].sum(axis=0)  # shape (L, D)
    tbl = numpy.zeros(len(arr), dt(['loss_type', 'total'] + dstates))
    tbl['loss_type'] = oq.loss_types
    tbl['total'] = arr.sum(axis=1)
    for dsi, ds in enumerate(dstates):
        tbl[ds] = arr[:, dsi]
    return tbl


@view.add('portfolio_damage')
def view_portfolio_damage(token, dstore):
    """
    The mean full portfolio damage for each loss type,
    extracted from the average damages
    """
    if 'aggcurves' in dstore:  # event_based_damage
        K = dstore.get_attr('risk_by_event', 'K')
        df = dstore.read_df('aggcurves', sel=dict(agg_id=K, return_period=0))
        lnames = numpy.array(dstore['oqparam'].loss_types)
        df['loss_type'] = lnames[df.loss_id.to_numpy()]
        del df['loss_id']
        del df['agg_id']
        del df['return_period']
        return df.set_index('loss_type')
    # dimensions assets, stat, loss_types, dmg_state
    if 'damages-stats' in dstore:
        attrs = get_shape_descr(dstore['damages-stats'].attrs['json'])
        arr = dstore.sel('damages-stats', stat='mean').sum(axis=(0, 1))
    else:
        attrs = get_shape_descr(dstore['damages-rlzs'].attrs['json'])
        arr = dstore.sel('damages-rlzs', rlz=0).sum(axis=(0, 1))
    rows = [(lt,) + tuple(row) for lt, row in zip(attrs['loss_type'], arr)]
    return numpy.array(rows, dt(['loss_type'] + list(attrs['dmg_state'])))


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
    return text_table(data) + '\n\n' + view_assets_by_site(token, dstore)


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
    return text_table(lst)


@view.add('fullreport')
def view_fullreport(token, dstore):
    """
    Display an .rst report about the computation
    """
    # avoid circular imports
    from openquake.calculators.reportwriter import ReportWriter
    return ReportWriter(dstore).make_report(show_inputs=False)


@view.add('performance')
def view_performance(token, dstore):
    """
    Display performance information
    """
    return performance_view(dstore)


def stats(name, array, *extras):
    """
    Returns statistics from an array of numbers.

    :param name: a descriptive string
    :returns: (name, mean, rel_std, min, max, len) + extras
    """
    avg = numpy.mean(array)
    std = 'nan' if len(array) == 1 else '%d%%' % (numpy.std(array) / avg * 100)
    max_ = numpy.max(array)
    return (name, len(array), avg, std, numpy.min(array), max_) + extras


@view.add('num_units')
def view_num_units(token, dstore):
    """
    Display the number of units by taxonomy
    """
    taxo = dstore['assetcol/tagcol/taxonomy'][()]
    counts = collections.Counter()
    for asset in dstore['assetcol']:
        counts[taxo[asset['taxonomy']]] += asset['value-number']
    data = sorted(counts.items())
    data.append(('*ALL*', sum(d[1] for d in data)))
    return numpy.array(data, dt('taxonomy num_units'))


@view.add('assets_by_site')
def view_assets_by_site(token, dstore):
    """
    Display statistical information about the distribution of the assets
    """
    taxonomies = dstore['assetcol/tagcol/taxonomy'][()]
    assets_by = group_array(dstore['assetcol'].array, 'site_id')
    data = ['taxonomy num_sites mean stddev min max num_assets'.split()]
    num_assets = AccumDict()
    for assets in assets_by.values():
        num_assets += {k: [len(v)] for k, v in group_array(
            assets, 'taxonomy').items()}
    for taxo in sorted(num_assets):
        val = numpy.array(num_assets[taxo])
        data.append(stats(taxonomies[taxo], val, val.sum()))
    if len(num_assets) > 1:  # more than one taxonomy, add a summary
        n_assets = numpy.array([len(assets) for assets in assets_by.values()])
        data.append(stats('*ALL*', n_assets, n_assets.sum()))
    return text_table(data)


@view.add('required_params_per_trt')
def view_required_params_per_trt(token, dstore):
    """
    Display the parameters needed by each tectonic region type
    """
    full_lt = dstore['full_lt']
    tbl = []
    for trt in full_lt.trts:
        gsims = full_lt.gsim_lt.values[trt]
        # adding fake mags to the ContextMaker, needed for table-based GMPEs
        cmaker = ContextMaker(trt, gsims, {'imtls': {}, 'mags': ['7.00']})
        req = set()
        for gsim in cmaker.gsims:
            req.update(gsim.requires())
        req_params = sorted(req - {'mag'})
        gsim_str = ' '.join(map(repr, gsims)).replace('\n', '\\n')
        if len(gsim_str) > 160:
            gsim_str = ', '.join(repr(gsim).split('\n')[0] for gsim in gsims)
        tbl.append((trt, gsim_str, req_params))
    return text_table(tbl, header='trt gsims req_params'.split(),
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
        return data

    data = []
    for task, arr in group_array(task_info[()], 'taskname').items():
        val = arr['duration']
        if len(val):
            data.append(stats(task, val, val.max() / val.mean()))
    if not data:
        return 'Not available'
    return numpy.array(
        data, dt('operation-duration counts mean stddev min max slowfac'))


def reduce_srcids(srcids):
    s = set()
    for srcid in srcids:
        s.add(srcid.split(':')[0])
    return ' '.join(sorted(s))


@view.add('task_durations')
def view_task_durations(token, dstore):
    """
    Display the raw task durations. Here is an example of usage::

      $ oq show task_durations
    """
    df = dstore.read_df('source_data')
    out = []
    for taskno, rows in df.groupby('taskno'):
        srcids = reduce_srcids(rows.src_id.to_numpy())
        out.append((taskno, rows.ctimes.sum(), rows.weight.sum(), srcids))
    arr = numpy.array(out, dt('taskno duration weight srcids'))
    arr.sort(order='duration')
    return arr


@view.add('task')
def view_task_hazard(token, dstore):
    """
    Display info about a given task. Here are a few examples of usage::

     $ oq show task:classical:0  # the fastest task
     $ oq show task:classical:-1  # the slowest task
    """
    _, name, index = token.split(':')
    if 'source_data' not in dstore:
        return 'Missing source_data'
    data = get_array(dstore['task_info'][()], taskname=encode(name))
    if len(data) == 0:
        raise RuntimeError('No task_info for %s' % name)
    data.sort(order='duration')
    rec = data[int(index)]
    taskno = rec['task_no']
    sdata = dstore.read_df('source_data', 'taskno').loc[taskno]
    num_ruptures = sdata.nrupts.sum()
    eff_sites = sdata.nsites.sum()
    msg = ('taskno={:_d}, fragments={:_d}, num_ruptures={:_d}, '
           'eff_sites={:_d}, weight={:.1f}, duration={:.1f}s').format(
                 taskno, len(sdata), num_ruptures, eff_sites,
                 rec['weight'], rec['duration'])
    return msg


@view.add('source_data')
def view_source_data(token, dstore):
    """
    Display info about a given task. Here is an example::

     $ oq show source_data:42
    """
    if ':' not in token:
        return dstore.read_df(token, 'src_id')
    _, taskno = token.split(':')
    taskno = int(taskno)
    if 'source_data' not in dstore:
        return 'Missing source_data'
    df = dstore.read_df('source_data', 'src_id', sel={'taskno': taskno})
    del df['taskno']
    df['slowrate'] = df['ctimes'] / df['weight']
    return df.sort_values('ctimes')


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
    tbl = text_table(util.compose_arrays(rups, extra))
    codes = ['%s: %s' % it for it in ds.getitem('ruptures').attrs.items()
             if it[0] in codeset]
    msg = '%s\n%s\nHazard time for task %d: %d of %d s, ' % (
        tbl, '\n'.join(codes), info['task_no'], extra['dt'].sum(),
        info['duration'])
    msg += 'gmfbytes=%s, w=%d' % (
        humansize(extra['gmfbytes'].sum()),
        (rups['n_occ'] * extra['nsites']).sum())
    return msg


@view.add('global_hazard')
def view_global_hazard(token, dstore):
    """
    Display the global hazard for the calculation. This is used for
    debugging purposes when comparing the results of two
    calculations.
    """
    imtls = dstore['oqparam'].imtls
    arr = dstore.sel('hcurves-stats', stat='mean')  # shape N, S, M, L
    res = tuple(arr.mean(axis=(0, 1, 3)))  # length M
    return numpy.array([res], dt(imtls))


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
    hmaps = dstore.sel('hmaps-stats', stat='mean')
    means = hmaps.mean(axis=(0, 1))  # shape M, P
    return numpy.array([tuple(means.flatten())], dt)


@view.add('global_gmfs')
def view_global_gmfs(token, dstore):
    """
    Display GMFs on the first IMT averaged on everything for debugging purposes
    """
    imtls = dstore['oqparam'].imtls
    row = [dstore[f'gmf_data/gmv_{m}'][:].mean(axis=0)
           for m in range(len(imtls))]
    return text_table([row], header=imtls)


@view.add('gmf')
def view_gmf(token, dstore):
    """
    Display a mean gmf for debugging purposes
    """
    df = dstore.read_df('gmf_data', 'sid')
    gmf = df.groupby(df.index).mean()
    return str(gmf)


def binning_error(values, eids, nbins=10):
    """
    :param values: E values
    :param eids: E integer event indices
    :returns: std/mean for the sums of the values

    Group the values in nbins depending on the eids and returns the
    variability of the sums relative to the mean.
    """
    df = pandas.DataFrame({'val': values}, eids)
    res = df.groupby(eids % nbins).val.sum()
    return res.std() / res.mean()


class GmpeExtractor(object):
    def __init__(self, dstore):
        full_lt = dstore['full_lt']
        self.trt_by = full_lt.trt_by
        self.gsim_by_trt = full_lt.gsim_by_trt
        self.rlzs = full_lt.get_realizations()

    def extract(self, trt_smrs, rlz_ids):
        out = []
        for trt_smr, rlz_id in zip(trt_smrs, rlz_ids):
            trt = self.trt_by(trt_smr)
            out.append(self.gsim_by_trt(self.rlzs[rlz_id])[trt])
        return out


@view.add('extreme_gmvs')
def view_extreme_gmvs(token, dstore):
    """
    Display table of extreme GMVs with fields (eid, gmv_0, sid, rlz. rup)
    """
    if ':' in token:
        maxgmv = float(token.split(':')[1])
    else:
        maxgmv = 5  # PGA=5g is default value defining extreme GMVs
    imt0 = list(dstore['oqparam'].imtls)[0]

    eids = dstore['gmf_data/eid'][:]
    gmvs = dstore['gmf_data/gmv_0'][:]
    sids = dstore['gmf_data/sid'][:]
    msg = ''
    err = binning_error(gmvs, eids)
    if err > .05:
        msg += ('Your results are expected to have a large dependency '
                'from the rupture seed: %d%%' % (err * 100))
    if imt0 == 'PGA':
        rups = dstore['ruptures'][:]
        rupdict = dict(zip(rups['id'], rups))
        gmpe = GmpeExtractor(dstore)
        df = pandas.DataFrame({'gmv_0': gmvs, 'sid': sids}, eids)
        extreme_df = df[df.gmv_0 > maxgmv].rename(columns={'gmv_0': imt0})
        if len(extreme_df) == 0:
            return 'No PGAs over %s g found' % maxgmv
        ev = dstore['events'][()][extreme_df.index]
        # extreme_df['rlz'] = ev['rlz_id']
        extreme_df['rup'] = ev['rup_id']
        extreme_df['mag'] = [rupdict[rupid]['mag'] for rupid in ev['rup_id']]
        hypos = numpy.array([rupdict[rupid]['hypo'] for rupid in ev['rup_id']])
        # extreme_df['lon'] = numpy.round(hypos[:, 0])
        # extreme_df['lat'] = numpy.round(hypos[:, 1])
        extreme_df['dep'] = numpy.round(hypos[:, 2])
        trt_smrs = [rupdict[rupid]['trt_smr'] for rupid in ev['rup_id']]
        extreme_df['gmpe'] = gmpe.extract(trt_smrs, ev['rlz_id'])
        exdf = extreme_df.sort_values(imt0).groupby('sid').head(1)
        if len(exdf):
            msg += ('\nThere are extreme GMVs, run `oq show extreme_gmvs:%s`'
                    'to see them' % maxgmv)
            if ':' in token:
                msg = str(exdf.set_index('rup'))
        return msg
    return msg + '\nCould not extract extreme GMVs for ' + imt0


@view.add('mean_rates')
def view_mean_rates(token, dstore):
    """
    Display mean hazard rates for the first site
    """
    oq = dstore['oqparam']
    assert oq.use_rates
    poes = dstore.sel('hcurves-stats', site_id=0, stat='mean')[0, 0]  # NRML1
    rates = numpy.zeros(poes.shape[1], dt(oq.imtls))
    for m, imt in enumerate(oq.imtls):
        rates[imt] = calc.disagg.to_rates(poes[m])
    return rates


@view.add('mean_disagg')
def view_mean_disagg(token, dstore):
    """
    Display mean quantities for the disaggregation. Useful for checking
    differences between two calculations.
    """
    N, M, P = dstore['hmap3'].shape
    tbl = []
    kd = {key: dset[:] for key, dset in sorted(dstore['disagg-rlzs'].items())}
    oq = dstore['oqparam']
    for s in range(N):
        for m, imt in enumerate(oq.imtls):
            for p in range(P):
                row = ['%s-sid-%d-poe-%s' % (imt, s, p)]
                for k, d in kd.items():
                    row.append(d[s, ..., m, p, :].mean())
                tbl.append(tuple(row))
    return numpy.array(sorted(tbl), dt(['key'] + list(kd)))


@view.add('disagg')
def view_disagg(token, dstore):
    """
    Example: $ oq show disagg Mag
    Returns a table poe, imt, mag, contribution for the first site
    """
    kind = token.split(':')[1]
    assert kind in ('Mag', 'Dist', 'TRT'), kind
    site_id = 0
    if 'disagg-stats' in dstore:
        data = dstore['disagg-stats/' + kind][site_id, ..., 0]  # (:, M, P)
    else:
        data = dstore['disagg-rlzs/' + kind][site_id, ..., 0]  # (:, M, P)
    Ma, M, P = data.shape
    oq = dstore['oqparam']
    imts = list(oq.imtls)
    dtlist = [('poe', float), ('imt', (numpy.string_, 10)),
              (kind.lower() + 'bin', int), ('prob', float)]
    lst = []
    for p, m, ma in itertools.product(range(P), range(M), range(Ma)):
        lst.append((oq.poes[p], imts[m], ma, data[ma, m, p]))
    return numpy.array(lst, dtlist)


@view.add('bad_ruptures')
def view_bad_ruptures(token, dstore):
    """
    Display the ruptures degenerating to a point
    """
    data = dstore['ruptures']['id', 'code', 'mag',
                              'minlon', 'maxlon', 'minlat', 'maxlat']
    bad = data[numpy.logical_and(data['minlon'] == data['maxlon'],
                                 data['minlat'] == data['maxlat'])]
    return bad


Source = collections.namedtuple(
    'Source', 'source_id code num_ruptures checksum')


@view.add('gmvs_to_hazard')
def view_gmvs_to_hazard(token, dstore):
    """
    Show the number of GMFs over the highest IML
    """
    args = token.split(':')[1:]  # called as view_gmvs_to_hazard:sid
    if not args:
        sid = 0
    elif len(args) == 1:  # only sid specified
        sid = int(args[0])
    assert sid in dstore['sitecol'].sids
    oq = dstore['oqparam']
    num_ses = oq.ses_per_logic_tree_path
    data = dstore.read_df('gmf_data', 'sid').loc[sid]
    tbl = []
    for imti, (imt, imls) in enumerate(oq.imtls.items()):
        gmv = data['gmv_%d' % imti].to_numpy()
        for iml in imls:
            # same algorithm as in _gmvs_to_haz_curve
            exceeding = numpy.sum(gmv >= iml)
            poe = 1 - numpy.exp(- exceeding / num_ses)
            tbl.append((sid, imt, iml, exceeding, poe))
    return numpy.array(tbl, dt('sid imt iml num_exceeding poe'))


@view.add('gmvs')
def view_gmvs(token, dstore):
    """
    Show the GMVs on a given site ID
    """
    sid = int(token.split(':')[1])  # called as view_gmvs:sid
    assert sid in dstore['sitecol'].sids
    data = dstore.read_df('gmf_data', 'sid')
    return data.loc[sid]


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
    return numpy.array(list(counts.items()), dt('mag num_events'))


@view.add('ebrups_by_mag')
def view_ebrups_by_mag(token, dstore):
    """
    Show how many event based ruptures there are for each magnitude
    """
    mags = dstore['ruptures']['mag']
    uniq, counts = numpy.unique(mags, return_counts=True)
    return text_table(zip(uniq, counts), ['mag', 'num_ruptures'])


@view.add('maximum_intensity')
def view_maximum_intensity(token, dstore):
    """
    Show intensities at minimum and maximum distance for the highest magnitude
    """
    effect = extract(dstore, 'effect')
    data = zip(dstore['full_lt'].trts, effect[-1, -1], effect[-1, 0])
    return text_table(data, ['trt', 'intensity1', 'intensity2'])


@view.add('extreme_sites')
def view_extreme(token, dstore):
    """
    Show sites where the mean hazard map reaches maximum values
    """
    mean = dstore.sel('hmaps-stats', stat='mean')[:, 0, 0, -1]  # shape N1MP
    site_ids, = numpy.where(mean == mean.max())
    return dstore['sitecol'][site_ids]


@view.add('zero_losses')
def view_zero_losses(token, dstore):
    """
    Sanity check on avg_losses and avg_gmf
    """
    R = len(dstore['weights'])
    oq = dstore['oqparam']
    avg_gmf = dstore['avg_gmf'][0]
    asset_df = dstore.read_df('assetcol/array', 'site_id')
    for col in asset_df.columns:
        if not col.startswith('value-'):
            del asset_df[col]
    values_df = asset_df.groupby(asset_df.index).sum()
    avglosses = dstore['avg_losses-rlzs'][:].sum(axis=1) / R  # shape (A, L)
    dic = dict(site_id=dstore['assetcol']['site_id'])
    for lti, lname in enumerate(oq.loss_types):
        dic[lname] = avglosses[:, lti]
    losses_df = pandas.DataFrame(dic).groupby('site_id').sum()
    sids = losses_df.index.to_numpy()
    avg_gmf = avg_gmf[sids]
    nonzero_gmf = (avg_gmf > oq.min_iml).any(axis=1)
    nonzero_losses = (losses_df > 0).to_numpy().any(axis=1)
    bad, = numpy.where(nonzero_gmf != nonzero_losses)
    # this happens in scenario_risk/case_shakemap and case_3
    msg = 'Site #%d is suspicious:\navg_gmf=%s\navg_loss=%s\nvalues=%s'
    for idx in bad:
        sid = sids[idx]
        logging.warning(msg, sid, dict(zip(oq.all_imts(), avg_gmf[sid])),
                        _get(losses_df, sid), _get(values_df, sid))
    return bad


def _get(df, sid):
    return df.loc[sid].to_dict()


@view.add('gsim_for_event')
def view_gsim_for_event(token, dstore):
    """
    Display the GSIM used when computing the GMF for the given event:

    $ oq show gsim_for_event:123 -1
    [BooreAtkinson2008]
    """
    eid = int(token.split(':')[1])
    full_lt = dstore['full_lt']
    rup_id, rlz_id = dstore['events'][eid][['rup_id', 'rlz_id']]
    trt_smr = dict(dstore['ruptures'][:][['id', 'trt_smr']])
    trti = trt_smr[rup_id] // 2**24
    gsim = full_lt.get_realizations()[rlz_id].gsim_rlz.value[trti]
    return gsim


@view.add('event_loss_table')
def view_event_loss_table(token, dstore):
    """
    Display the top 20 losses of the event loss table for the first loss type

    $ oq show event_loss_table
    """
    K = dstore['risk_by_event'].attrs.get('K', 0)
    df = dstore.read_df('risk_by_event', 'event_id',
                        dict(agg_id=K, loss_id=0))
    df['std'] = numpy.sqrt(df.variance)
    df.sort_values('loss', ascending=False, inplace=True)
    del df['agg_id']
    del df['loss_id']
    del df['variance']
    return df[:20]


@view.add('risk_by_event')
def view_risk_by_event(token, dstore):
    """
    Display the top 30 losses of the aggregate loss table as a TSV.
    If aggregate_by was missing in the calculation, returns nothing.

    $ oq show risk_by_event:<loss_type>
    """
    _, ltype = token.split(':')
    loss_id = LOSSID[ltype]
    df = dstore.read_df('risk_by_event', sel=dict(loss_id=loss_id))
    del df['loss_id']
    del df['variance']
    df = df[df.agg_id == df.agg_id.max()].sort_values('loss', ascending=False)
    del df['agg_id']
    out = io.StringIO()
    df[:30].to_csv(out, sep='\t', index=False, float_format='%.1f',
                   lineterminator='\r\n')
    return out.getvalue()


@view.add('risk_by_rup')
def view_risk_by_rup(token, dstore):
    """
    Display the top 30 aggregate losses by rupture ID. Usage:

    $ oq show risk_by_rup
    """
    rbr = dstore.read_df('loss_by_rupture', 'rup_id')
    info = dstore.read_df('gmf_data/rup_info', 'rup_id')
    rdf = dstore.read_df('ruptures', 'id')
    df = rbr.join(rdf).join(info)[
        ['loss', 'mag', 'n_occ',  'hypo_0', 'hypo_1', 'hypo_2', 'rrup']]
    for field in df.columns:
        if field not in ('mag', 'n_occ'):
            df[field] = numpy.round(F64(df[field]), 1)
    return df[:30]


@view.add('delta_loss')
def view_delta_loss(token, dstore):
    """
    Estimate the stocastic error on the loss curve by splitting the events
    in odd and even. Example:

    $ oq show delta_loss  # consider the first loss type
    """
    if ':' in token:
        _, li = token.split(':')
        li = int(li)
    else:
        li = 0
    oq = dstore['oqparam']
    efftime = oq.investigation_time * oq.ses_per_logic_tree_path * len(
        dstore['weights'])
    num_events = len(dstore['events'])
    num_events0 = num_events // 2 + (num_events % 2)
    num_events1 = num_events // 2
    periods = return_periods(efftime, num_events)[1:-1]

    K = dstore['risk_by_event'].attrs.get('K', 0)
    df = dstore.read_df('risk_by_event', 'event_id',
                        dict(agg_id=K, loss_id=li))
    if len(df) == 0:  # for instance no fatalities
        return {'delta': numpy.zeros(1)}
    mod2 = df.index % 2
    losses0 = df['loss'][mod2 == 0]
    losses1 = df['loss'][mod2 == 1]
    c0 = losses_by_period(losses0, periods, num_events0, efftime / 2)
    c1 = losses_by_period(losses1, periods, num_events1, efftime / 2)
    ok = (c0 != 0) & (c1 != 0)
    c0 = c0[ok]
    c1 = c1[ok]
    losses = losses_by_period(df['loss'], periods, num_events, efftime)[ok]
    dic = dict(loss=losses, even=c0, odd=c1,
               delta=numpy.abs(c0 - c1) / (c0 + c1))
    return pandas.DataFrame(dic, periods[ok])


def to_str(arr):
    return ' '.join(map(str, numpy.unique(arr)))


@view.add('composite_source_model')
def view_composite_source_model(token, dstore):
    """
    Show the structure of the CompositeSourceModel in terms of grp_id
    """
    lst = []
    full_lt = dstore['full_lt'].init()
    for grp_id, df in dstore.read_df('source_info').groupby('grp_id'):
        lst.append((str(grp_id), full_lt.trts[df.trti.unique()[0]], len(df)))
    return numpy.array(lst, dt('grp_id trt num_sources'))


@view.add('branches')
def view_branches(token, dstore):
    """
    Show info about the branches in the logic tree
    """
    full_lt = dstore['full_lt']
    smlt = full_lt.source_model_lt
    gslt = full_lt.gsim_lt
    tbl = []
    for k, v in full_lt.source_model_lt.shortener.items():
        tbl.append((k, v, smlt.branches[k].value))
    gsims = sum(gslt.values.values(), [])
    if len(gslt.shortener) < len(gsims):  # possible for engine < 3.13
        raise ValueError(
            'There were duplicated branch IDs in the gsim logic tree %s'
            % gslt.filename)
    for g, (k, v) in enumerate(gslt.shortener.items()):
        tbl.append((k, v, str(gsims[g]).replace('\n', r'\n')))
    return numpy.array(tbl, dt('branch_id abbrev uvalue'))


@view.add('rlz')
def view_rlz(token, dstore):
    """
    Show info about a given realization in the logic tree
    Example:

    $ oq show rlz:0 -1
    """
    _, rlz_id = token.split(':')
    full_lt = dstore['full_lt']
    rlz = full_lt.get_realizations()[int(rlz_id)]
    smlt = full_lt.source_model_lt
    gslt = full_lt.gsim_lt
    tbl = []
    for bset, brid in zip(smlt.branchsets, rlz.sm_lt_path):
        tbl.append((bset.uncertainty_type, smlt.branches[brid].value))
    for trt, value in zip(sorted(gslt.bsetdict), rlz.gsim_rlz.value):
        tbl.append((trt, value))
    return numpy.array(tbl, dt('uncertainty_type uvalue'))


@view.add('branchsets')
def view_branchsets(token, dstore):
    """
    Show the branchsets in the logic tree
    """
    flt = dstore['full_lt']
    clt = logictree.compose(flt.source_model_lt, flt.gsim_lt)
    return text_table(enumerate(map(repr, clt.branchsets)),
                      header=['bsno', 'bset'], ext='org')


@view.add('rupture')
def view_rupture(token, dstore):
    """
    Show a rupture with its geometry
    """
    rup_id = int(token.split(':')[1])
    return get_ebrupture(dstore, rup_id)


@view.add('event_rates')
def view_event_rates(token, dstore):
    """
    Show the number of events per realization multiplied by risk_time/eff_time
    """
    oq = dstore['oqparam']
    R = dstore['full_lt'].get_num_paths()
    if oq.calculation_mode != 'event_based_damage':
        return numpy.ones(R)
    time_ratio = (oq.risk_investigation_time or oq.investigation_time) / (
        oq.ses_per_logic_tree_path * oq.investigation_time)
    if oq.collect_rlzs:
        return numpy.array([len(dstore['events']) * time_ratio / R])
    else:
        rlzs = dstore['events']['rlz_id']
        return numpy.bincount(rlzs, minlength=R) * time_ratio


def tup2str(tups):
    return ['_'.join(map(str, t)) for t in tups]


@view.add('sum')
def view_sum(token, dstore):
    """
    Show the sum of an array of shape (A, R, L, ...) on the first axis
    """
    _, arrayname = token.split(':')  # called as sum:damages-rlzs
    dset = dstore[arrayname]
    A, R, L, *D = dset.shape
    cols = ['RL'] + tup2str(itertools.product(*[range(d) for d in D]))
    arr = dset[:].sum(axis=0)  # shape R, L, *D
    z = numpy.zeros(R * L, dt(cols))
    for r, ar in enumerate(arr):
        for li, a in enumerate(ar):
            a = a.flatten()
            for c, col in enumerate(cols):
                z[r * L + li][col] = a[c-1] if c > 0 else (r, li)
    return z


@view.add('agg_id')
def view_agg_id(token, dstore):
    """
    Show the available aggregations
    """
    [aggby] = dstore['oqparam'].aggregate_by
    keys = [key.decode('utf8').split(',') for key in dstore['agg_keys'][:]]
    keys = numpy.array(keys)  # shape (N, A)
    dic = {aggkey: keys[:, a] for a, aggkey in enumerate(aggby)}
    df = pandas.DataFrame(dic)
    df.index.name = 'agg_id'
    return df


@view.add('mean_perils')
def view_mean_perils(token, dstore):
    """
    For instance `oq show mean_perils`
    """
    oq = dstore['oqparam']
    pdcols = dstore.get_attr('gmf_data', '__pdcolumns__').split()
    perils = [col for col in pdcols[2:] if not col.startswith('gmv_')]
    N = len(dstore['sitecol/sids'])
    sid = dstore['gmf_data/sid'][:]
    out = numpy.zeros(N, [(per, float) for per in perils])
    if oq.number_of_logic_tree_samples:
        E = len(dstore['events'])
        for peril in perils:
            out[peril] = fast_agg(sid, dstore['gmf_data/' + peril][:]) / E
    else:
        rlz_weights = dstore['weights'][:]
        ev_weights = rlz_weights[dstore['events']['rlz_id']]
        totw = ev_weights.sum()  # num_gmfs
        for peril in perils:
            data = dstore['gmf_data/' + peril][:]
            weights = ev_weights[dstore['gmf_data/eid'][:]]
            out[peril] = fast_agg(sid, data * weights) / totw
    return out


@view.add('pmaps_size')
def view_pmaps_size(token, dstore):
    return humansize(get_pmaps_gb(dstore)[0])


@view.add('rup_stats')
def view_rup_stats(token, dstore):
    """
    Show the statistics of event based ruptures
    """
    rups = dstore['ruptures'][:]
    out = [stats(f, rups[f]) for f in 'mag n_occ'.split()]
    return numpy.array(out, dt('kind counts mean stddev min max'))


@view.add('collapsible')
def view_collapsible(token, dstore):
    """
    Show how much the ruptures are collapsed for each site
    """
    if ':' in token:
        collapse_level = int(token.split(':')[1])
    else:
        collapse_level = 0
    dist_types = [dt for dt in dstore['rup'] if dt in KNOWN_DISTANCES]
    vs30 = dstore['sitecol'].vs30
    ctx_df = dstore.read_df('rup')
    ctx_df['vs30'] = vs30[ctx_df.sids]
    has_vs30 = len(numpy.unique(vs30)) > 1
    c = Collapser(collapse_level, dist_types, has_vs30)
    ctx_df['mdbin'] = c.calc_mdbin(ctx_df)
    print('cfactor = %d/%d' % (len(ctx_df), len(ctx_df['mdbin'].unique())))
    out = []
    for sid, df in ctx_df.groupby('sids'):
        n, u = len(df), len(df.mdbin.unique())
        out.append((sid, u, n, n / u))
    return numpy.array(out, dt('site_id eff_rups num_rups cfactor'))


# tested in oq-risk-tests etna
@view.add('event_based_mfd')
def view_event_based_mfd(token, dstore):
    """
    Compare n_occ/eff_time with occurrence_rate
    """
    dic = extract(dstore, 'event_based_mfd?').to_dict()
    del dic['extra']
    return pandas.DataFrame(dic).set_index('mag')


# used in the AELO project
@view.add('relevant_sources')
def view_relevant_sources(token, dstore):
    """
    Returns a table with the sources contributing more than 10%
    of the highest source.
    """
    imt = token.split(':')[1]
    kw = dstore['oqparam'].postproc_args
    iml = dict(zip(kw['imts'], kw['imls']))[imt]
    aw = extract(dstore, f'mean_rates_by_src?imt={imt}&iml={iml}')
    rates = aw.array['rate']  # for each source in decreasing order
    return aw.array[rates > .1 * rates[0]]


def shorten(lst):
    """
    Shorten a list of strings
    """
    if len(lst) <= 7:
        return lst
    return lst[:3] + ['...'] + lst[-3:]


@view.add('sources_branches')
def view_sources_branches(token, dstore):
    """
    Returns a table with the sources in the logic tree by branches
    """
    sd = dstore['full_lt/source_data'][:]
    acc = AccumDict(accum=[])
    for src, trt in numpy.unique(sd[['source', 'trt']]):
        brs = b' '.join(sorted(sd[sd['source'] == src]['branch']))
        acc[brs, trt].append(src.decode('utf8'))
    out = [(t, ' '.join(shorten(s)), b)
           for ((b, t), s) in sorted(acc.items())]
    return numpy.array(sorted(out), dt('trt sources branches'))


@view.add('MPL')
def view_MPL(token, dstore):
    """
    Maximum Probable Loss at a given return period
    """
    rp = int(token.split(':')[1])
    K = dstore['risk_by_event'].attrs['K']
    ltypes = list(dstore['agg_curves-stats'])
    out = numpy.zeros(1, [(lt, float) for lt in ltypes])
    for ltype in ltypes:
        # shape (K+1, S, P)
        arr = dstore.sel(f'agg_curves-stats/{ltype}',
                         stat='mean', agg_id=K, return_period=rp)
        out[ltype] = arr
    return out


def _drate(df, imt, src):
    return df[(df.imt == imt) & (df.source_id == src)].value.sum()


def _irate(df, imt, src, iml, imls):
    subdf = df[(df.imt == imt) & (df.src_id == src)]
    interp = numpy.interp(numpy.log(iml), numpy.log(imls[subdf.lvl]),
                       numpy.log(subdf.value))
    return numpy.exp(interp)


# used only in AELO calculations
@view.add('compare_disagg_rates')
def compare_disagg_rates(token, dstore):
    oq = dstore['oqparam']
    aw = dstore['mean_disagg_by_src']
    iml_disagg = dict(zip(aw.imt, aw.iml))
    mean_disagg_df = aw.to_dframe()
    mean_rates_df = dstore['mean_rates_by_src'].to_dframe()
    imts_out, srcs_out, drates, irates = [], [], [], []
    for imt, iml in iml_disagg.items():
        imls = oq.imtls[imt]
        srcs = mean_disagg_df[mean_disagg_df.imt == imt].source_id
        for src in set(srcs):
            imts_out.append(imt)
            srcs_out.append(src)    
            drates.append(_drate(mean_disagg_df, imt, src))
            irates.append(_irate(mean_rates_df, imt, src, iml, imls))
    return pandas.DataFrame({'imt': imts_out, 'src': srcs_out, 
                             'disagg_rate': drates, 
                             'interp_rate': irates}
                            ).sort_values(['imt', 'src'])
