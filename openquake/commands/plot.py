# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2025 GEM Foundation
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

import sys
import ast
import time
import gzip
import json
import logging
from urllib.parse import parse_qs
import shapely
import numpy
import pandas
from scipy.stats import linregress
from shapely.geometry import Polygon, LineString
from openquake.baselib import hdf5
from openquake.commonlib import readinput
from openquake.commonlib.util import unique_filename
from openquake.hazardlib.geo.utils import PolygonPlotter
from openquake.hazardlib.contexts import Effect, get_effect_by_mag
from openquake.hazardlib.source.rupture import build_planar_rupture_from_dict
from openquake.hazardlib.calc.filters import getdefault, IntegrationDistance
from openquake.calculators.getters import get_ebrupture
from openquake.calculators.extract import (
    Extractor, WebExtractor, clusterize)
from openquake.calculators.postproc.plots import (
    plot_avg_gmf, import_plt, add_borders, plot_rupture, plot_rupture_3d,
    adjust_limits, auto_limits)
from openquake.calculators.postproc.aelo_plots import (
    plot_mean_hcurves_rtgm, plot_disagg_by_src,
    plot_governing_mce_asce_7_16, plot_mce_spectra, plot_governing_mce,
    plot_sites)


def getparams(what):
    """
    >>> getparams('rupture?')
    ({}, False)
    >>> getparams('rupture?mag=6&lon=10&lat=45&dep=10')
    ({'mag': 6, 'lon': 10, 'lat': 45, 'dep': 10}, False)
    >>> getparams('rupture?mag=6&lon=10&lat=45&dep=10&with_borders=True')
    ({'mag': 6, 'lon': 10, 'lat': 45, 'dep': 10}, True)
    """
    assert '?' in what, what
    params = {}
    with_borders = False
    for namevalue in what.split('?')[1].split('&'):
        if not namevalue:
            continue
        name, value = namevalue.split('=')
        if name == 'with_borders':
            with_borders = ast.literal_eval(value)
        else:
            try:
                params[name] = ast.literal_eval(value)
            except ValueError:
                params[name] = value
    return params, with_borders


def make_figure_magdist(extractors, what):
    """
    $ oq plot "magdist?"
    """
    plt = import_plt()
    _fig, ax = plt.subplots()
    [ex] = extractors
    grp = ex.dstore['source_mags']
    ax.set_xlabel('magnitude')
    ax.set_ylabel('distance')
    ax.set_xlim(4, 10)
    ax.set_ylim(0, 600)
    for trt in grp:
        magdist = ex.oqparam.maximum_distance(trt)
        mags = numpy.float64(grp[trt][:])
        dsts = magdist(mags)
        ax.plot(mags, dsts, '-', label=trt)
        ax.grid(True)
        ax.legend()
    return plt


def make_figure_hcurves(extractors, what):
    """
    $ oq plot "hcurves?kind=mean&imt=PGA&site_id=0"
    """
    plt = import_plt()
    fig = plt.figure()
    got = {}  # (calc_id, kind) -> curves
    for i, ex in enumerate(extractors):
        hcurves = ex.get(what)
        for kind in hcurves.kind:
            arr = getattr(hcurves, kind)
            got[ex.calc_id, kind] = arr
    oq = ex.oqparam
    n_imts = len(hcurves.imt)
    [site] = hcurves.site_id
    for j, imt in enumerate(hcurves.imt):
        imls = oq.imtls[imt]
        ax = fig.add_subplot(n_imts, 1, j + 1)
        ax.set_xlabel('%s, site %s, inv_time=%dy' %
                      (imt, site, oq.investigation_time))
        ax.set_ylabel('PoE')
        ax.set_xlabel(f'{imt} (g units)')
        for ck, arr in got.items():
            if (arr == 0).all():
                logging.warning('There is a zero curve %s_%s', *ck)
            ax.loglog(imls, arr.flat, '-', label='%s_%s' % ck)
        for poe in oq.poes:
            ax.loglog(imls, [poe]*len(imls), label=f'{poe=}')
        ax.grid(True)
        ax.legend()
    return plt


def make_figure_uhs_cluster(extractors, what):
    """
    $ oq plot "uhs_cluster?k=12"
    """
    plt = import_plt()
    import matplotlib.cm as cm
    kstr = what.split('?')[1]
    k = int(kstr.split('=')[1])
    _fig, ax = plt.subplots()
    [ex] = extractors
    trts = ex.get('full_lt').trts
    hmaps = ex.get('hmaps?kind=rlzs')
    rlzs = ex.get('realizations').array
    labels = []
    for p, poe in enumerate(ex.oqparam.poes):
        for imt in ex.oqparam.imtls:
            labels.append('%s' % imt)
    xs = numpy.arange(len(labels))
    ax.set_xticks(xs)
    ax.set_xticklabels(labels)
    ax.set_ylabel('IML')
    obs = [getattr(hmaps, 'rlz-%03d' % rlz)[0] for rlz in range(len(rlzs))]
    arrK = clusterize(numpy.array(obs), rlzs, k)
    # arrK of size K <= k, label of size R
    colors = cm.rainbow(numpy.linspace(0, 1, len(arrK)))  # shape (K, 4)
    paths = [p.decode('utf-8') for p in arrK['branch_paths']]  # length K
    for trt in trts:
        print(trt)
    for c, curve in enumerate(arrK['centroid']):
        rlzs = arrK[c]['rlzs']
        lbl = '%s:%s' % (c + 1, paths[c])
        print(lbl, '(%d rlzs)' % len(rlzs))
        for rlz in rlzs:
            ys = getattr(hmaps, 'rlz-%03d' % rlz)[0].T.flatten()
            ax.plot(xs, ys, '-', color=colors[c])
        ax.plot(xs, curve, '--', color=colors[c], label=lbl)
    ax.grid(True)
    ax.legend()
    return plt


def make_figure_avg_gmf(extractors, what):
    """
    $ oq plot "avg_gmf?imt=PGA"
    """
    [ex] = extractors
    imt = what.split('=')[1]
    plt = plot_avg_gmf(ex, imt)
    return plt


def make_figure_compare_avg_gmf(extractors, what):
    """
    $ oq plot "compare_avg_gmf?imt=PGA"
    """
    assert len(extractors) == 2
    plt = import_plt()
    fig = plt.figure()
    imt = what.split('=')[1]
    ax = fig.add_subplot(1, 1, 1)
    ax.grid(True)
    ax.set_xlabel('Lon')
    ax.set_ylabel('Lat')
    ax.set_title('Delta GMF for %s' % imt)
    ex1, ex2 = extractors
    avg_gmf = ex1.get(what)
    avg_gmf2 = ex2.get(what)
    gmf = avg_gmf[imt] - avg_gmf2[imt]
    coll = ax.scatter(avg_gmf['lons'], avg_gmf['lats'], c=gmf, cmap='jet')
    plt.colorbar(coll)
    return plt


def make_figure_vs30(extractors, what):
    """
    $ oq plot "vs30?"
    """
    plt = import_plt()
    fig = plt.figure()
    [ex] = extractors
    sitecol = ex.get('sitecol')
    ax = fig.add_subplot(111)
    ax.grid(True)
    ax.set_xlabel('vs30 for calculation %d' % ex.calc_id)
    vs30 = sitecol['vs30']
    vs30[numpy.isnan(vs30)] = 0
    ax.scatter(sitecol['lon'], sitecol['lat'], c=vs30, cmap='jet')
    return plt


def make_figure_hmaps(extractors, what):
    """
    $ oq plot "hmaps?kind=mean&imt=PGA"
    """
    plt = import_plt()
    fig = plt.figure()
    ncalcs = len(extractors)
    if ncalcs > 2:
        raise RuntimeError('Could not plot more than two calculations at once')
    elif ncalcs == 2:  # plot the differences
        ex1, ex2 = extractors
        oq1 = ex1.oqparam
        oq2 = ex2.oqparam
        n_poes = len(oq1.poes)
        assert n_poes == len(oq2.poes)
        itime = oq1.investigation_time
        assert oq2.investigation_time == itime
        sitecol = ex1.get('sitecol')
        array2 = ex2.get('sitecol').array
        for name in ('lon', 'lat'):
            numpy.testing.assert_equal(array2[name], sitecol.array[name])
        hmaps1 = ex1.get(what)
        hmaps2 = ex2.get(what)
        [imt] = hmaps1.imt
        assert [imt] == hmaps2.imt
        [kind] = hmaps1.kind
        assert hmaps1.kind == [kind]
        for j, poe in enumerate(oq1.poes):
            diff = hmaps1[kind][:, 0, j] - hmaps2[kind][:, 0, j]
            maxdiff = numpy.abs(diff).max()
            ax = fig.add_subplot(1, n_poes, j + 1)
            ax.grid(True)
            ax.set_xlabel('IMT=%s, kind=%s, poe=%s\ncalcs %d-%d, '
                          'inv_time=%dy\nmaxdiff=%s' %
                          (imt, kind, poe, ex1.calc_id, ex2.calc_id,
                           itime, maxdiff))
            coll = ax.scatter(sitecol['lon'], sitecol['lat'],
                              c=diff, cmap='jet')
            plt.colorbar(coll)
    elif ncalcs == 1:  # plot the hmap
        [ex] = extractors
        oq = ex.oqparam
        n_poes = len(oq.poes)
        sitecol = ex.get('sitecol')
        hmaps = ex.get(what)
        [imt] = hmaps.imt
        [kind] = hmaps.kind
        for j, poe in enumerate(oq.poes):
            ax = fig.add_subplot(1, n_poes, j + 1)
            ax.grid(True)
            ax.set_xlabel('hmap for IMT=%s, kind=%s, poe=%s\ncalculation %d, '
                          'inv_time=%dy' %
                          (imt, kind, poe, ex.calc_id, oq.investigation_time))
            coll = ax.scatter(sitecol['lon'], sitecol['lat'],
                              c=hmaps[kind][:, 0, j], cmap='jet')
            plt.colorbar(coll)
    return plt


def make_figure_uhs(extractors, what):
    """
    $ oq plot "uhs?kind=mean&site_id=0"
    """
    plt = import_plt()
    fig = plt.figure()
    got = {}  # (calc_id, kind) -> curves
    spec = {}  # calc_id -> spectra
    for i, ex in enumerate(extractors):
        oq = ex.oqparam
        uhs = ex.get(what)
        for kind in uhs.kind:
            got[ex.calc_id, kind] = uhs[kind][0]  # 1 site
        if 'median_spectra' in ex.dstore:
            for j, poe in enumerate(oq.poes):
                arr = ex.get(f'median_spectra?site_id=0&poe_id={j}').array
                spec[ex.calc_id, j] = numpy.exp(arr[:, 0].sum(axis=0))
    n_poes = len(oq.poes)
    periods = [imt.period for imt in oq.imt_periods()]
    imts = [imt.string for imt in oq.imt_periods()]
    [site] = uhs.site_id
    for j, poe in enumerate(oq.poes):
        ax = fig.add_subplot(n_poes, 1, j + 1)
        ax.set_xlabel('UHS on site %s, poe=%s, inv_time=%dy' %
                      (site, poe, oq.investigation_time))
        ax.set_ylabel('g')
        for ck, arr in got.items():
            curve = list(arr['%.6f' % poe][imts])
            ax.plot(periods, curve, '-', label='%s_%s_spectrum' % ck)
            ax.plot(periods, curve, '.')
        for (calc_id, poe_id), spectrum in spec.items():
            ax.plot(periods, spectrum, '-', label=f'{calc_id}_median_spectrum')
        ax.grid(True)
        ax.legend()
    return plt


def middle(x):
    # [1, 2, 3] => [1.5, 2.5]
    return (x[:-1] + x[1:]) / 2.


def stacked_bar(ax, x, ys, width):
    cumsum = ys.cumsum(axis=0)
    for i, y in enumerate(ys):
        if i > 0:
            ax.bar(x, y, width, bottom=cumsum[i-1])
        else:
            ax.bar(x, y, width)


# plot a single rlz or the mean
def make_figure_disagg(extractors, what):
    """
    $ oq plot "disagg?kind=Mag&imt=PGA&poe_id=0&spec=rlzs"
    """
    plt = import_plt()
    from matplotlib import cm
    fig = plt.figure()
    oq = extractors[0].oqparam
    disagg = extractors[0].get(what)
    kind = [k.lower() for k in disagg.kind[0].split('_')]  # ex. ('mag','dist')
    [sid] = disagg.site_id
    [imt] = disagg.imt
    [poe_id] = disagg.poe_id
    y = disagg.array[..., 0, 0, 0]  # shape (..., M, P, Z) => (...)
    ndims = len(kind)  # number of dimensions of the array
    assert ndims == len(y.shape), (ndims, len(y.shape))
    print(y)
    x = getattr(disagg, kind[0])
    ncalcs = len(extractors)
    width = (x[1] - x[0]) * 0.5
    if ncalcs == 1:
        x -= width
    if ndims == 1:  # simple bar chart
        ax = fig.add_subplot(1, 1, 1)
        ax.set_xlabel('Disagg%s on site %s, imt=%s, poe_id=%d, inv_time=%dy' %
                      (disagg.kind, sid, imt, poe_id, oq.investigation_time))
        ax.set_xlabel(kind[0])
        ax.set_xticks(x)
        ax.bar(x, y, width)
        for ex in extractors[1:]:
            ax.bar(x + width, ex.get(what).array, width)
        return plt
    if ncalcs > 1:
        raise NotImplementedError('Comparison for %s' % disagg.kind)
    if ndims == 3:
        Zs = range(y.shape[-1])
        zbin = getattr(disagg, kind[2])
    else:
        Zs = [None]
    axes = []
    for z in Zs:
        arr = y[:, :, z]
        ax = fig.add_subplot(len(Zs), 1, z or 0 + 1)
        axes.append(ax)
        ax.set_ylabel(kind[1])
        if ndims == 2:  # 2D
            ax.set_xlabel(kind[0])
        else:  # 3D
            ax.set_xlabel('%s [%s=%s]' % (kind[0], kind[2], zbin[z]))
        vbins = getattr(disagg, kind[1])  # vertical bins
        cmap = cm.get_cmap('jet', 100)
        extent = (x[0] - width, x[-1] + width,
                  vbins[0], vbins[-1])
        im = ax.imshow(arr, cmap=cmap, extent=extent,
                       aspect='auto', vmin=y.min(), vmax=y.max())
        # stacked bar chart
        # stacked_bar(ax, x, y.T, width)
        # ys = ['%.1f' % y for y in getattr(disagg, kind[1])]
        # ax.legend(ys)
    fig.tight_layout()
    fig.colorbar(im, ax=axes)
    return plt


def make_figure_event_based_mfd(extractors, what):
    """
    $ oq plot "event_based_mfd?" -1 -2
    """
    plt = import_plt()
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.set_xlabel("magnitude")
    ax.set_ylabel("annual frequency")
    ax.set_yscale('log')
    magdics = []
    for ex in extractors:
        aw = ex.get(what)
        magdics.append(dict(zip(numpy.round(aw.mag, 1), aw.freq)))
    min_mag = min(min(magdic) for magdic in magdics)
    max_mag = max(max(magdic) for magdic in magdics)
    mags = numpy.round(numpy.arange(min_mag, max_mag + .1, .1), 1)
    for ex, magdic in zip(extractors, magdics):
        edges = [min_mag - .05] + list(mags + .05)
        freqs = [magdic.get(mag, 0) for mag in mags]
        ax.stairs(freqs, edges, label='calc_%d' % ex.calc_id)
    ax.set_xticks(mags[::2])
    ax.legend()
    return plt


def make_figure_task_info(extractors, what):
    """
    $ oq plot "task_info?kind=classical"
    """
    plt = import_plt()
    [ex] = extractors
    dic = ex.get(what).to_dict()
    del dic['extra']
    [(_task_name, task_info)] = dic.items()
    x = task_info['duration']
    if plt.__name__ == 'plotext':
        mean, std, med = x.mean(), x.std(ddof=1), numpy.median(x)
        plt.hist(x, bins=50)
        plt.title("mean=%d+-%d seconds, median=%d" % (mean, std, med))
        return plt
    fig = plt.figure()
    ax = fig.add_subplot(2, 1, 1)
    mean, std = x.mean(), x.std(ddof=1)
    ax.hist(x, bins=50, rwidth=0.9)
    ax.set_title("mean=%d+-%d seconds" % (mean, std))
    ax.set_ylabel("tasks=%d" % len(x))

    ax = fig.add_subplot(2, 1, 2)
    arr = numpy.sort(task_info, order='duration')
    x, y = arr['duration'], arr['weight']
    reg = linregress(x, y)
    ax.plot(x, reg.intercept + reg.slope * x)
    ax.plot(x, y)
    ax.set_ylabel("weight")
    ax.set_xlabel("duration")
    return plt


def make_figure_source_data(extractors, what):
    """
    $ oq plot "source_data?taskno=XX"
    """
    plt = import_plt()
    _fig, ax = plt.subplots()
    [ex] = extractors
    aw = ex.get(what)
    x, y = aw.ctimes, aw.weight
    reg = linregress(x, y)
    ax.plot(x, reg.intercept + reg.slope * x)
    ax.plot(x, y)
    ax.set_xlabel("duration")
    ax.set_ylabel("weight")
    return plt


def make_figure_memory(extractors, what):
    """
    $ oq plot "memory?"
    """
    # NB: matplotlib is imported inside since it is a costly import
    plt = import_plt()

    [ex] = extractors
    task_info = ex.get('task_info').to_dict()
    del task_info['extra']
    _fig, ax = plt.subplots()
    ax.grid(True)
    ax.set_xlabel('tasks')
    ax.set_ylabel('GB')
    start = 0
    for task_name in task_info:
        mem = task_info[task_name]['mem_gb']
        ax.plot(range(start, start + len(mem)), mem, label=task_name)
        start += len(mem)
    ax.legend()
    return plt


def make_figure_gridded_sources(extractors, what):
    """
    $ oq plot "gridded_sources?task_no=0"
    """
    # NB: matplotlib is imported inside since it is a costly import
    plt = import_plt()
    [ex] = extractors
    dic = json.loads(ex.get(what).json)  # id -> lonlats
    _fig, ax = plt.subplots()
    ax.grid(True)
    sitecol = ex.get('sitecol')
    tot = 0
    for lonlats in dic.values():
        if len(lonlats) == 2:  # not collapsed
            tot += 1
        else:  # collapsed
            tot += len(lonlats) / 2 - 1
        ax.plot([lonlats[0]], [lonlats[1]], '*')
        lons = lonlats[2::2]
        lats = lonlats[3::2]
        ax.scatter(lons, lats)
    ax.plot(sitecol['lon'], sitecol['lat'], '.')
    ax.set_title('Reduced %d->%d sources' % (tot, len(dic)))
    # TODO: fix plot around the IDL
    return plt


def make_figure_rupture_info(extractors, what):
    """
    $ oq plot "rupture_info?min_mag=6"
    """
    # NB: matplotlib is imported inside since it is a costly import
    plt = import_plt()
    [ex] = extractors
    info = ex.get(what)
    _fig, ax = plt.subplots()
    ax.grid(True)
    n = 0
    tot = 0
    pp = PolygonPlotter(ax)
    geoms = gzip.decompress(info['boundaries']).decode('utf8').split('\n')
    for rec, wkt in zip(info, geoms):
        poly = shapely.wkt.loads(wkt)
        if poly.is_valid:
            pp.add(poly)
            n += 1
        else:
            print('Invalid %s' % wkt)
        tot += 1
    pp.set_lim()
    ax.set_title('%d/%d valid ruptures' % (n, tot))
    if tot == 1:
        # print the full geometry
        print(ex.get('rupture/%d' % rec['rupid']).toml())
    return plt


def make_figure_ebruptures(extractors, what):
    """
    $ oq plot "ebruptures?min_mag=6"
    """
    # NB: matplotlib is imported inside since it is a costly import
    plt = import_plt()
    [ex] = extractors
    hypo = ex.get(what)['hypo']
    _fig, ax = plt.subplots()
    add_borders(ax, readinput.read_mosaic_df, buffer=0.)
    ax.grid(True)
    ax.scatter(hypo[:, 0], hypo[:, 1])
    ax.set_title('%d ruptures' % len(hypo))
    return plt


def make_figure_effect(extractors, what):
    """
    $ oq plot "effect?"
    """
    # NB: matplotlib is imported inside since it is a costly import
    plt = import_plt()
    from matplotlib import cm
    [ex] = extractors
    effect = ex.get(what)
    trts = ex.get('full_lt').trts
    mag_ticks = effect.mags[::-5]
    fig = plt.figure()
    cmap = cm.get_cmap('jet', 100)
    axes = []
    vmin = numpy.log10(effect.array.min())
    vmax = numpy.log10(effect.array.max())
    for trti, trt in enumerate(trts):
        ax = fig.add_subplot(len(trts), 1, trti + 1)
        axes.append(ax)
        ax.set_xticks(mag_ticks)
        ax.set_xlabel('Mag')
        dist_ticks = effect.dist_bins[trt][::10]
        ax.set_yticks(dist_ticks)
        ax.set_ylabel(trt)
        extent = mag_ticks[0], mag_ticks[-1], dist_ticks[0], dist_ticks[-1]
        im = ax.imshow(numpy.log10(effect[:, :, trti]), cmap=cmap,
                       extent=extent, aspect='auto', vmin=vmin, vmax=vmax)
    fig.colorbar(im, ax=axes)
    return plt


def make_figure_rups_by_mag_dist(extractors, what):
    """
    $ oq plot "rups_by_mag_dist?"
    """
    # NB: matplotlib is imported inside since it is a costly import
    plt = import_plt()
    from matplotlib import cm
    [ex] = extractors
    counts = ex.get(what)
    counts.array = numpy.log10(counts.array + 1)
    trts = ex.get('full_lt').trts
    mag_ticks = counts.mags[::-5]
    fig = plt.figure()
    cmap = cm.get_cmap('jet', 100)
    axes = []
    vmax = counts.array.max()
    for trti, trt in enumerate(trts):
        ax = fig.add_subplot(len(trts), 1, trti + 1)
        axes.append(ax)
        ax.set_xticks(mag_ticks)
        ax.set_xlabel('Mag')
        dist_ticks = counts.dist_bins[trt][::10]
        ax.set_yticks(dist_ticks)
        ax.set_ylabel(trt)
        extent = mag_ticks[0], mag_ticks[-1], dist_ticks[0], dist_ticks[-1]
        im = ax.imshow(counts[:, :, trti], cmap=cmap,
                       extent=extent, aspect='auto', vmin=0, vmax=vmax)
    fig.colorbar(im, ax=axes)
    return plt


def make_figure_dist_by_mag(extractors, what):
    """
    $ oq plot "dist_by_mag?"
    """
    # NB: matplotlib is imported inside since it is a costly import
    plt = import_plt()
    [ex] = extractors
    effect = ex.get('effect')
    mags = ['%.2f' % mag for mag in effect.mags]
    _fig, ax = plt.subplots()
    trti = 0
    for trt, dists in effect.dist_bins.items():
        dic = dict(zip(mags, effect[:, :, trti]))
        if ex.oqparam.pointsource_distance:
            pdist = getdefault(ex.oqparam.pointsource_distance, trt)
        else:
            pdist = None
        eff = Effect(dic, dists, pdist)
        dist_by_mag = eff.dist_by_mag()
        ax.plot(effect.mags, list(dist_by_mag.values()), label=trt,
                color='red')
        if pdist:
            dist_by_mag = eff.dist_by_mag(eff.collapse_value)
            ax.plot(effect.mags, list(dist_by_mag.values()), label=trt,
                    color='green')
        ax.set_xlabel('Mag')
        ax.set_ylabel('Dist')
        ax.set_title('Integration Distance at intensity=%s' % eff.zero_value)
        trti += 1
    ax.legend()
    return plt


def make_figure_effect_by_mag(extractors, what):
    """
    $ oq plot "effect_by_mag?"
    """
    # NB: matplotlib is imported inside since it is a costly import
    plt = import_plt()
    [ex] = extractors
    gsims_by_trt = ex.get('gsims_by_trt', asdict=True)
    mags = ex.get('source_mags').array
    try:
        effect = ex.get('effect')
    except KeyError:
        onesite = ex.get('sitecol').one()
        maximum_distance = IntegrationDistance(ex.oqparam.maximum_distance)
        imtls = ex.oqparam.imtls
        ebm = get_effect_by_mag(
            mags, onesite, gsims_by_trt, maximum_distance, imtls)
        effect = numpy.array(list(ebm.values()))
    _fig, ax = plt.subplots()
    trti = 0
    for trt in gsims_by_trt:
        ax.plot(mags, effect[:, -1, trti], label=trt)
        ax.set_xlabel('Mag')
        ax.set_ylabel('Intensity')
        ax.set_title('Effect at maximum distance')
        trti += 1
    ax.legend()
    return plt


def make_figure_agg_curves(extractors, what):
    """
    $ oq plot "agg_curves?kind=mean&loss_type=structural" -1
    """
    plt = import_plt()
    fig = plt.figure()
    got = {}  # (calc_id, kind) -> curves
    for i, ex in enumerate(extractors):
        aw = ex.get(what + '&absolute=1')
        if isinstance(aw.json, numpy.ndarray):  # from webui
            js = bytes(aw.json).decode('utf8')
        else:
            js = aw.json
        vars(aw).update(json.loads(js))
        agg_curve = aw.array.squeeze()
        got[ex.calc_id, aw.kind[0]] = agg_curve
    oq = ex.oqparam
    periods = aw.return_period
    ax = fig.add_subplot(1, 1, 1)
    ax.set_xlabel('risk_inv_time=%dy' % oq.risk_investigation_time)
    ax.set_ylabel('loss')
    for ck, arr in got.items():
        ax.loglog(periods, agg_curve, '-', label='%s_%s' % ck)
        ax.loglog(periods, agg_curve, '.')
    ax.grid(True)
    ax.legend()
    return plt


def make_figure_csq_curves(extractors, what):
    """
    $ oq plot "csq_curves?agg_id=0&loss_type=structural&consequence=losses" -1
    """
    plt = import_plt()
    fig = plt.figure()
    got = {}  # (calc_id, limit_state) -> curve
    for i, ex in enumerate(extractors):
        aw = ex.get(what)
        P, _C = aw.shape
        if P < 2:
            raise RuntimeError('Not enough return periods: %d' % P)
        for c, csq in enumerate(aw.consequences):
            if csq in what:
                got[ex.calc_id, csq] = aw[:, c]
    oq = ex.oqparam
    periods = aw.return_period
    ax = fig.add_subplot(1, 1, 1)
    ax.set_xlabel('risk_inv_time=%dy' % oq.risk_investigation_time)
    ax.set_ylabel(csq)
    for ck, arr in got.items():
        ax.loglog(periods, arr, '-', label=ck[0])
        ax.loglog(periods, arr, '.')
    ax.grid(True)
    ax.legend()
    return plt


def make_figure_tot_curves(extractors, what):
    """
    $ oq plot "tot_curves?loss_type=structural&kind=rlz-000&absolute=1"
    """
    return make_figure_agg_curves(extractors, what)


def make_figure_mean_hcurves_rtgm(extractors, what):
    """
    $ oq plot "mean_hcurves_rtgm?sid=0"
    """
    [ex] = extractors
    dstore = ex.dstore
    kwargs = parse_qs(what.split('?')[1])
    [sid] = kwargs.get('sid', ['0'])
    plt = plot_mean_hcurves_rtgm(dstore, sid=int(sid))
    return plt


def make_figure_governing_mce_asce_7_16(extractors, what):
    """
    $ oq plot "governing_mce_asce_7_16?"
    """
    [ex] = extractors
    dstore = ex.dstore
    plt = plot_governing_mce_asce_7_16(dstore)
    return plt


def make_figure_mce_spectra(extractors, what):
    """
    $ oq plot "mce_spectra?"
    """
    [ex] = extractors
    dstore = ex.dstore
    plt = plot_mce_spectra(dstore)
    return plt


def make_figure_governing_mce(extractors, what):
    """
    $ oq plot "governing_mce?"
    """
    [ex] = extractors
    dstore = ex.dstore
    plt = plot_governing_mce(dstore)
    return plt


def make_figure_disagg_by_src(extractors, what):
    """
    $ oq plot "disagg_by_src?sid=0"
    """
    [ex] = extractors
    dstore = ex.dstore
    kwargs = parse_qs(what.split('?')[1])
    [sid] = kwargs.get('sid', ['0'])
    plt = plot_disagg_by_src(dstore, sid=int(sid))
    return plt


def make_figure_gmf_scenario(extractors, what):
    """
    $ oq plot "gmf_scenario?imt=PGA&kind=rlz-0"
    """
    # NB: matplotlib is imported inside since it is a costly import
    plt = import_plt()
    [ex] = extractors
    arr = ex.get(what).array
    E, N = arr.shape
    sids = range(N)
    for eid in range(E):
        plt.plot(sids,
                 arr[eid],
                 marker='',
                 linestyle='-',
                 label=eid,
                 linewidth=0.5)

    # max_gmv / min_gmv ratio per site
    min_values = arr.min(axis=0)
    max_values = arr.max(axis=0)

    # NB: maximum rates are interesting, but only if the max_gmv
    # is large enough (>.1)
    ok = (min_values > 0) & (max_values > .1)
    if ok.any():
        rates = max_values[ok] / min_values[ok]
        idx = rates.argmax()
        info = f'max_rate={rates.max():.1f} at site ID={idx} over {E} GMFs'
    else:
        info = ''
    plt.xlabel('Site ID')
    plt.ylabel('Ground motion value')
    if info:
        plt.title(info)
    plt.grid(True)
    return plt


def plot_geom(geom, ax, color, label):
    if geom.geom_type == 'Polygon':
        x, y = geom.exterior.xy
        ax.plot(x, y, color=color, label=label)
    elif geom.geom_type == 'MultiPolygon':
        for polygon in geom:
            x, y = polygon.exterior.xy
            ax.plot(x, y, color=color, label=label)
    elif geom.geom_type == 'LineString':
        x, y = geom.xy
        ax.plot(x, y, color=color, label=label)
    else:
        raise NotImplementedError(
            f'Unable to plot geometry type {geom.geom_type}')


def get_boundary_2d(smsh):
    """ Returns a polygon """
    coo = []
    lons = smsh.mesh.lons
    lats = smsh.mesh.lats
    # Upper boundary + trace
    idx = numpy.where(numpy.isfinite(lons[0, :]))[0]
    tmp = [(lons[0, i], lats[0, i]) for i in idx]
    trace = LineString(tmp)
    coo.extend(tmp)
    # Right boundary
    idx = numpy.where(numpy.isfinite(lons[:, -1]))[0]
    tmp = [(lons[i, -1], lats[i, -1]) for i in idx]
    coo.extend(tmp)
    # Lower boundary
    idx = numpy.where(numpy.isfinite(lons[-1, :]))[0]
    tmp = [(lons[-1, i], lats[-1, i]) for i in numpy.flip(idx)]
    coo.extend(tmp)
    # Left boundary
    idx = idx = numpy.where(numpy.isfinite(lons[:, 0]))[0]
    tmp = [(lons[i, 0], lats[i, 0]) for i in numpy.flip(idx)]
    coo.extend(tmp)
    return trace, Polygon(coo)


def filter_sources(csm, src_ids, codes, excluded_codes):
    if src_ids:
        if codes:
            srcs = [src for src in csm.get_sources()
                    if src.source_id in src_ids and src.code in codes
                    and src.code not in excluded_codes]
        else:
            srcs = [src for src in csm.get_sources()
                    if src.source_id in src_ids
                    and src.code not in excluded_codes]
    else:
        if codes:
            srcs = [src for src in csm.get_sources()
                    if src.code in codes and src.code not in excluded_codes]
        else:
            srcs = [src for src in csm.get_sources()
                    if src.code not in excluded_codes]
    if not src_ids:
        print('The following sources will be plotted:')
        print([(src.source_id, src.code) for src in srcs])
    return srcs


def plot_multi_fault_sources(mfs, src_ids, ax):
    print('Plotting multi-fault sources...')
    t0 = time.time()
    src = mfs[0]
    sections = src.get_sections()
    if src_ids:
        secs = set()
        for src in mfs:
            if src.source_id in src_ids:
                for rup in src.iter_ruptures():
                    secs.update(
                        sections[surf.idx] for surf in rup.surface.surfaces)
    else:
        secs = sections
        print([mf.source_id for mf in mfs])
    print(f'Found {len(secs)} sections')
    for sec in secs:
        trace, poly = get_boundary_2d(sec)
        plot_geom(poly, ax, 'blue', 'Multi-fault sections')
        plot_geom(trace, ax, 'red', 'Multi-fault traces')
    print(f'...took {time.time() - t0} seconds')


def plot_polygon_sources(srcs, ax, kind):
    print(f'Plotting {kind} sources...')
    if kind == 'Non-parametric':
        color = 'orange'
    elif kind == 'Multi-point':
        color = 'purple'
    elif kind == 'Characteristic fault':
        color = 'olive'
    elif kind == 'Simple fault':
        color = 'magenta'
    elif kind == 'Complex fault':
        color = 'pink'
    elif kind == 'Area':
        color = 'yellow'
    elif kind == 'Kite fault':
        color = 'navy'
    else:
        color = 'teal'
    t0 = time.time()
    for src in srcs:
        poly = src.polygon
        min_x_, min_y_, max_x_, max_y_ = poly.get_bbox()
        ax.fill(poly.lons, poly.lats, alpha=0.3, color=color, label=kind)
    print(f'...took {time.time() - t0} seconds')


def plot_point_sources(srcs, ax):
    print('Plotting point sources...')
    t0 = time.time()
    for point in srcs:
        min_x_, min_y_, max_x_, max_y_ = point.get_bounding_box(0)
        if point.code == b'p':  # CollapsedPointSource
            color = 'brown'
            label = 'Collapsed point'
            lon = point.lon
            lat = point.lat
        elif point.code == b'P':  # PointSource
            color = 'cyan'
            label = 'Point'
            lon = point.location.longitude
            lat = point.location.latitude
        else:
            raise NotImplementedError(f'Unexpected code {point.code}')
        ax.plot(lon, lat, 'o', alpha=0.7, color=color,
                markersize=2, label=label)
    print(f'...took {time.time() - t0} seconds')


def plot_sources(srcs, ax):
    PLOTTABLE_CODES = (
        b'N', b'M', b'X', b'S', b'C', b'P', b'p', b'P', b'F', b'A', b'K')
    ax.set_aspect('equal')
    ax.grid(True)
    print(f'Plotting {len(srcs)} sources...')
    any_sources_were_plotted = False
    # NonParametricSource
    np_sources = [src for src in srcs if src.code == b'N']
    if np_sources:
        plot_polygon_sources(np_sources, ax, 'Non-parametric')
        any_sources_were_plotted = True
    # MultiPointSource
    mp_sources = [src for src in srcs if src.code == b'M']
    if mp_sources:
        # NOTE: perhaps plotting the polygon gives not enough detail?
        plot_polygon_sources(mp_sources, ax, 'Multi-point')
        any_sources_were_plotted = True
    # CharacteristicFaultSource
    ch_sources = [src for src in srcs if src.code == b'X']
    if ch_sources:
        plot_polygon_sources(ch_sources, ax, 'Characteristic fault')
        any_sources_were_plotted = True
    # SimpleFaultSource
    s_sources = [src for src in srcs if src.code == b'S']
    if s_sources:
        plot_polygon_sources(s_sources, ax, 'Simple fault')
        any_sources_were_plotted = True
    # ComplexFaultSource
    comp_sources = [src for src in srcs if src.code == b'C']
    if comp_sources:
        plot_polygon_sources(comp_sources, ax, 'Complex fault')
        any_sources_were_plotted = True
    # AreaSource
    a_sources = [src for src in srcs if src.code == b'A']
    if a_sources:
        plot_polygon_sources(a_sources, ax, 'Area')
        any_sources_were_plotted = True
    # KiteFaultSource
    k_sources = [src for src in srcs if src.code == b'K']
    if k_sources:
        plot_polygon_sources(k_sources, ax, 'Kite fault')
        any_sources_were_plotted = True
    # PointSource or CollapsedPointSource
    p_sources = [src for src in srcs if src.code in (b'p', b'P')]
    if p_sources:
        plot_point_sources(p_sources, ax)
        any_sources_were_plotted = True
    # MultiFaultSource
    mf_sources = [src for src in srcs if src.code == b'F']
    if mf_sources:
        src_ids = [src.source_id for src in srcs]
        plot_multi_fault_sources(mf_sources, src_ids, ax)
        any_sources_were_plotted = True
    unplottable = [(src.source_id, src.code)
                   for src in srcs if src.code not in PLOTTABLE_CODES]
    if unplottable:
        print(f'Plotting the following sources is not'
              f'implemented yet: {unplottable}')
    assert any_sources_were_plotted, 'No sources were plotted'


def make_figure_sources(extractors, what):
    """
    $ oq plot "sources?source_id=xxx"
    $ oq plot "sources?code=N&code=F"
    $ oq plot "sources?exclude=A"
    """
    # NB: matplotlib is imported inside since it is a costly import
    plt = import_plt()
    [ex] = extractors
    dstore = ex.dstore
    kwargs = what.split('?')[1]
    if kwargs and 'exclude' in kwargs:
        excluded_codes = [code.encode('utf8')
                          for code in parse_qs(kwargs)['exclude']]
    else:
        excluded_codes = []
    if kwargs and 'source_id' in kwargs:
        src_ids = list(parse_qs(kwargs)['source_id'])
    else:
        src_ids = []
    if kwargs and 'code' in kwargs:
        codes = [code.encode('utf8') for code in parse_qs(kwargs)['code']
                 if code.encode('utf8') not in excluded_codes]
    else:
        codes = []
    print('Reading sources...')
    csm = dstore['_csm']
    srcs = filter_sources(csm, src_ids, codes, excluded_codes)
    assert srcs, ('All sources were filtered out')
    _fig, ax = plt.subplots()
    plot_sources(srcs, ax)
    print('Plotting mosaic borders...')
    xlim, ylim = auto_limits(ax)
    add_borders(ax, readinput.read_mosaic_df, buffer=0.)
    adjust_limits(ax, xlim, ylim, padding=8)
    ax.set_title('Sources')
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys())
    return plt


def make_figure_rupture(extractors, what):
    """
    There are two ways of using this command:

    $ oq plot "rupture?"

    plots the first rupture from an already performed scenario calculation

    $ oq plot "rupture?rup_id=1"

    plots the rupture with the given id;

    $ oq plot "rupture?with_borders=True"

    also plots country borders
    """
    [ex] = extractors
    dstore = ex.dstore
    params, with_borders = getparams(what)
    rup_id = params['rup_id'] if 'rup_id' in params else 0
    rup = get_ebrupture(dstore, rup_id=rup_id).rupture
    return plot_rupture(rup, with_borders=with_borders)


def make_figure_build_rupture(extractors, what):
    """
    $ oq plot "build_rupture?mag=7&lon=10&lat=45&dep=10&rake=45&dip=30&strike=45&msr=WC1994"

    builds a new planar rupture.

    $ oq plot "build_rupture?mag=7&lon=10&lat=45&dep=10&rake=45&dip=30&strike=45&msr=WC1994&with_borders=True"

    also plots country borders.
    """
    params, with_borders = getparams(what)
    rup = build_planar_rupture_from_dict(params)
    return plot_rupture(rup, with_borders=with_borders)


def make_figure_rupture_3d(extractors, what):
    """
    $ oq plot "rupture_3d?"
    """
    [ex] = extractors
    dstore = ex.dstore
    params, _ = getparams(what)
    rup_id = params['rup_id'] if 'rup_id' in params else 0
    ebr = get_ebrupture(dstore, rup_id=rup_id)
    return plot_rupture_3d(ebr.rupture)


def make_figure_sites(extractors, what):
    """
    $ oq plot "sites?"
    """
    [ex] = extractors
    dstore = ex.dstore
    plt = plot_sites(dstore)
    return plt


def make_figure_show_png(extractors, what):
    """
    oq plot "show_png?site.png"

    shows an image stored in 'png/IMAGE_NAME'
    """
    plt = import_plt()
    [ex] = extractors
    dstore = ex.dstore
    name = what.split('?')[1]
    img = dstore['png'][name]
    plt.imshow(img)
    plt.axis('off')
    return plt


def plot_wkt(wkt_string):
    """
    Plot a WKT string describing a polygon
    """
    from shapely import wkt
    plt = import_plt()
    poly = wkt.loads(wkt_string)
    if hasattr(poly, 'exterior'):
        coo = numpy.array(poly.exterior.coords)
    else:  # POINT or LINESTRING
        coo = numpy.array(poly.coords)
    _fig, ax = plt.subplots()
    ax.plot(coo[:, 0], coo[:, 1], 'o')
    add_borders(ax, readinput.read_mosaic_df, buffer=0.)
    return plt


def plot_h3(hexes):
    """
    $ oq plot "H3 811ebffffff 81387fffff"

    plots H3 hexagons given a list of hexes
    """
    import h3
    import shapely
    plt = import_plt()
    # normalize the hexes to 15 characters
    for i, hex in enumerate(hexes):
        lenh = len(hex)
        if lenh < 15:
            hexes[i] = hex + 'f' * (15-lenh)
        elif lenh > 15:
            raise ValueError('%s must have <= 15 characters, got %d' %
                             (hex, lenh))
    _fig, ax = plt.subplots()
    for hex in hexes:
        mp = shapely.MultiPolygon(h3.h3_set_to_multi_polygon([hex]))
        lat, lon = mp.geoms[0].exterior.xy
        ax.fill(lon, lat, alpha=0.5, fc="lightblue", ec="blue")
    add_borders(ax, readinput.read_countries_df, buffer=0.)
    ax.set_aspect('equal')
    return plt


def plot_csv(fname):
    """
    Plot a CSV with columns (title, time1, time2, ...)
    """
    df = pandas.read_csv(fname)
    title, *cols = df.columns
    plt = import_plt()

    vals = [df[col].to_numpy() for col in cols]

    x = numpy.arange(len(df))  # the label locations
    width = 0.3  # the width of the bars

    fig, ax = plt.subplots()
    delta = -width
    for col, val in zip(cols, vals):
        rect = ax.bar(x + delta, val, width, label=col)
        ax.bar_label(rect)
        delta += width

    ax.set_title(title)
    ax.set_xticks(x, df[title])
    ax.legend()

    fig.tight_layout()
    plt.show()


def main(what,
         calc_id: int = -1,
         others: int = [],
         *,
         save_to: str = None,
         webapi=False,
         local=False,
         ):
    """
    Generic plotter for local and remote calculations.
    """
    if what.endswith('.csv'):
        plot_csv(what)
        return
    if save_to:
        save_to = unique_filename(save_to)
    if what.startswith(('POINT', 'POLYGON', 'LINESTRING')):
        plt = plot_wkt(what)
        if save_to:
            plt.savefig(save_to, dpi=300)
            logging.info(f'Plot saved to {save_to}')
        else:
            plt.show()
        return
    if what.startswith('H3'):
        hexes = what[2:].split()
        if what.endswith('.hdf5'):
            with hdf5.File(hexes[0]) as h5:
                hexes = [h.decode('ascii') for h in numpy.unique(
                    h5['assets/slice_by_hex6']['hex6'])]
        plt = plot_h3(hexes)
        if save_to:
            plt.savefig(save_to, dpi=300)
            logging.info(f'Plot saved to {save_to}')
        else:
            plt.show()
        return
    if what == 'examples':
        help_msg = ['Examples of possible plots:']
        for k, v in globals().items():
            if k.startswith('make_figure_'):
                help_msg.append(v.__doc__)
        print(''.join(help_msg), file=sys.stderr)
        return
    if '?' not in what:
        raise SystemExit('Missing ? in %r' % what)
    prefix, rest = what.split('?', 1)
    if prefix in 'hcurves hmaps' and 'imt=' not in rest:
        raise SystemExit('Missing imt= in %r' % what)
    elif prefix == 'uhs' and 'imt=' in rest:
        raise SystemExit('Invalid IMT in %r' % what)
    elif prefix in 'hcurves uhs disagg' and 'site_id=' not in rest:
        what += '&site_id=0'
    if prefix == 'disagg' and 'poe_id=' not in rest:
        what += '&poe_id=0'
    if local:
        xs = [WebExtractor(calc_id, 'http://localhost:8800', '')]
        for other_id in others:
            xs.append(WebExtractor(other_id), 'http://localhost:8800', '')
    elif webapi:
        xs = [WebExtractor(calc_id)]
        for other_id in others:
            xs.append(WebExtractor(other_id))
    else:
        xs = [Extractor(calc_id)]
        for other_id in others:
            xs.append(Extractor(other_id))
    make_figure = globals()['make_figure_' + prefix]
    plt = make_figure(xs, what)
    if save_to:
        plt.savefig(save_to, dpi=300)
        logging.info(f'Plot saved to {save_to}')
    else:
        plt.show()


main.what = 'what to extract (try examples)'
main.calc_id = 'computation ID'
main.others = dict(help='IDs of other computations', nargs='*')
main.save_to = 'if passed, save the plot to file instead of showing it'
main.webapi = 'if given, pass through the WebAPI'
main.local = 'if passed, use the local WebAPI'
