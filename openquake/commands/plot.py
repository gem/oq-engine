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
import os
import io
import gzip
import json
import logging
import shapely
import numpy
import pandas
import matplotlib as mpl
from scipy import interpolate
from scipy.stats import linregress
from openquake.hazardlib.geo.utils import PolygonPlotter, cross_idl
from openquake.hazardlib.contexts import Effect, get_effect_by_mag
from openquake.hazardlib.calc.filters import getdefault, IntegrationDistance
from openquake.hazardlib.calc.mean_rates import to_rates
from openquake.hazardlib.imt import from_string
from openquake.calculators.extract import (
    Extractor, WebExtractor, clusterize, get_info)

try:
    from PIL import Image
except ImportError:
    Image = None


def import_plt():
    if os.environ.get('TEXT'):
        import plotext as plt
    else:
        import matplotlib.pyplot as plt
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
        for ck, arr in got.items():
            if (arr == 0).all():
                logging.warning('There is a zero curve %s_%s', *ck)
            ax.loglog(imls, arr.flat, '-', label='%s_%s' % ck)
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
    fig, ax = plt.subplots()
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
    plt = import_plt()
    fig = plt.figure()
    imt = what.split('=')[1]
    ax = fig.add_subplot(1, 1, 1)
    ax.grid(True)
    ax.set_title('Avg GMF for %s' % imt)
    ax.set_xlabel('Lon')
    ax.set_ylabel('Lat')
    if len(extractors) == 2:  # compare two avg_gmf
        ex1, ex2 = extractors
        avg_gmf = ex1.get(what)
        avg_gmf2 = ex2.get(what)
        gmf = avg_gmf[imt] - avg_gmf2[imt]
    else:  # plot a single avg_gmf
        [ex] = extractors
        avg_gmf = ex.get(what)
        gmf = avg_gmf[imt]
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
    for i, ex in enumerate(extractors):
        uhs = ex.get(what)
        for kind in uhs.kind:
            got[ex.calc_id, kind] = uhs[kind][0]  # 1 site
    oq = ex.oqparam
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
            ax.plot(periods, curve, '-', label='%s_%s' % ck)
            ax.plot(periods, curve, '.')
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
    y = disagg.array[..., 0, 0]  # shape (..., M, P)
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
    [(task_name, task_info)] = dic.items()
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
    fig, ax = plt.subplots()
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
    fig, ax = plt.subplots()
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


def make_figure_sources(extractors, what):
    """
    $ oq plot "sources?limit=100"
    $ oq plot "sources?source_id=1&source_id=2"
    $ oq plot "sources?code=A&code=N"
    """
    # NB: matplotlib is imported inside since it is a costly import
    plt = import_plt()
    [ex] = extractors
    info = ex.get(what)
    wkts = gzip.decompress(info.wkt_gz).decode('utf8').split(';')
    srcs = gzip.decompress(info.src_gz).decode('utf8').split(';')
    fig, ax = plt.subplots()
    ax.grid(True)
    sitecol = ex.get('sitecol')
    pp = PolygonPlotter(ax)
    n = 0
    tot = 0
    psources = []
    for rec, srcid, wkt in zip(info, srcs, wkts):
        if not wkt:
            logging.warning('No geometries for source id %s', srcid)
            continue
        color = 'green'
        alpha = .3
        n += 1
        if wkt.startswith('POINT'):
            psources.append(shapely.wkt.loads(wkt))
        else:
            pp.add(shapely.wkt.loads(wkt), alpha=alpha, color=color)
        tot += 1
    lons = [p.x for p in psources]
    lats = [p.y for p in psources]
    ss_lons = lons + list(sitecol['lon'])  # sites + sources longitudes
    ss_lats = lats + list(sitecol['lat'])  # sites + sources latitudes
    if len(ss_lons) > 1 and cross_idl(*ss_lons):
        ss_lons = [lon % 360 for lon in ss_lons]
        lons = [lon % 360 for lon in lons]
        sitecol['lon'] = sitecol['lon'] % 360
    ax.plot(sitecol['lon'], sitecol['lat'], '.')
    ax.plot(lons, lats, 'o')
    pp.set_lim(ss_lons, ss_lats)
    ax.set_title('calc#%d, %d/%d sources' % (ex.calc_id, n, tot))
    return plt


def make_figure_gridded_sources(extractors, what):
    """
    $ oq plot "gridded_sources?task_no=0"
    """
    # NB: matplotlib is imported inside since it is a costly import
    plt = import_plt()
    [ex] = extractors
    dic = json.loads(ex.get(what).json)  # id -> lonlats
    fig, ax = plt.subplots()
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
    fig, ax = plt.subplots()
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
    fig, ax = plt.subplots()
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
    fig, ax = plt.subplots()
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
        P, C = aw.shape
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


def _find_fact_maxC(T, code):
    # find the factor to convert to maximum component based on
    # ASCE7-16 and ASCE7-22

    f1 = interpolate.interp1d([0.2, 1], [1.1, 1.3])
    f2 = interpolate.interp1d([1, 5], [1.3, 1.5])
    f3 = interpolate.interp1d([0.2, 1], [1.2, 1.25])
    f4 = interpolate.interp1d([0.2, 1], [1.1, 1.3])

    if code == 'ASCE7-16':
        if T == 0:
            fact_maxC = 1.
        elif T <= 0.2:
            fact_maxC = 1.1
        elif T <= 1:
            fact_maxC = f1(T)
        elif T <= 5:
            fact_maxC = f2(T)
        else:
            fact_maxC = 1.5
    elif code == 'ASCE7-22':
        if T == 0:
            fact_maxC = 1.
        elif T <= 0.2:
            fact_maxC = 1.2
        elif T <= 1:
            fact_maxC = f3(T)
        elif T <= 10:
            fact_maxC = f4(T)
        else:
            fact_maxC = 1.5
    return fact_maxC


def _find_afe_target(imls, afe, sa_target):
    # find the target afe (or poe) for a given acceleration
    if len(imls) != len(afe):
        afe.extend([1E-15] * (len(imls) - len(afe)))
    f = interpolate.interp1d(numpy.log(imls), numpy.log(afe))
    afe_target = numpy.exp(f(numpy.log(sa_target)))
    return afe_target


def _get_label(imt):
    imtlab = imt if imt == 'PGA' else imt.replace(')', 's)')
    comp = 'Geom. mean' if imt == 'PGA' else 'Max. comp.'
    return imtlab + ' - ' + comp


def plot_mean_hcurves_afe_rtgm(dstore, update_dstore=False):
    """
    :param dstore: the datastore
    :returns: figure of hazard curves
    """
    dinfo = get_info(dstore)
    # get imls and imts, make arrays
    imtls = dinfo['imtls']
    # separate imts and imls
    AFE, afe_RTGM, imls = [], [], []
    imts = ['PGA', 'SA(0.2)', 'SA(1.0)']
    for imt in imts:
        # get periods and factors for converting btw geom mean and
        # maximum component
        T = from_string(imt).period
        f = 0 if imt == 0.0 else _find_fact_maxC(T, 'ASCE7-16')
        imls.append([im*f for im in imtls[imt]])
    # get rtgm ouptut from the datastore
    rtgm_df = dstore.read_df('rtgm')
    # get the IML for the 2475 RP
    rtgm_probmce = rtgm_df['ProbMCE']
    # get investigation time
    window = dinfo['investigation_time']
    # get hazard curves, put into rates
    mean_hcurve = dstore['hcurves-stats'][0, 0]  # shape(M, L1)
    for m, hcurve in enumerate(mean_hcurve):
        AFE.append(to_rates(hcurve, window, minrate=1E-12))
        # get the AFE of the iml that will be disaggregated for each IMT
        afe_RTGM.append(_find_afe_target(
            imls[m], AFE[m], rtgm_probmce[m]))

    plt = import_plt()
    plt.figure(figsize=(12, 9))
    plt.rcParams.update({'font.size': 16})
    colors = mpl.colormaps['viridis'].reversed()._resample(3)
    patterns = ['-', '--', ':']
    for i, imt in enumerate(imts):
        lab = _get_label(imt)
        plt.loglog(imls[i], AFE[i], color=colors(i), linestyle=patterns[i],
                   label=lab, linewidth=3, zorder=1)
        # plot the label only once but it must be at the end of the legend
        if imt == imts[-1]:
            plt.loglog([rtgm_probmce[i]], [afe_RTGM[i]], 'ko',
                       label='Probabilistic MCE',  linewidth=2,
                       markersize=10, zorder=3)
        else:
            plt.loglog([rtgm_probmce[i]], [afe_RTGM[i]], 'ko',
                       linewidth=2, markersize=10, zorder=3)
        plt.loglog([numpy.min(imls[i]), rtgm_probmce[i]],
                   [afe_RTGM[i], afe_RTGM[i]],
                   'darkgray', linestyle='--', linewidth=1)
        plt.loglog([rtgm_probmce[i], rtgm_probmce[i]],
                   [0, afe_RTGM[i]], 'darkgray',
                   linestyle='--', linewidth=1)
    plt.grid('both')
    plt.legend(fontsize=13)
    plt.xlabel('Acceleration (g)', fontsize=20)
    plt.ylabel('Annual frequency of exceedance', fontsize=20)
    plt.legend(loc="best", fontsize='16')
    plt.ylim([10E-6, 1.1])
    plt.xlim([0.01, 4])
    if update_dstore:
        if Image is not None:
            bio = io.BytesIO()
            plt.savefig(bio, format='png', bbox_inches='tight')
            logging.info('Storing png/hcurves.png')
            dstore['png/hcurves.png'] = Image.open(bio)
        else:
            logging.warning(
                'Missing module PIL: skipping storing png/hcurves.png')
    return plt


def plot_governing_mce(dstore, update_dstore=False):
    """
    :param dstore: the datastore
    :returns: image of governing MCE
    """
    dinfo = get_info(dstore)
    # get imls and imts, make arrays
    imtls = dinfo['imtls']
    plt = import_plt()
    js = dstore['asce7'][()].decode('utf8')
    dic = json.loads(js)
    MCEr = [dic['PGA'], dic['SS'], dic['S1']]
    T = [from_string(imt).period for imt in imtls]

    limit_det = [0.5, 1.5, 0.6]
    # presenting as maximum component -> do not need conversion facts
    RTGM = dstore.read_df('rtgm')['ProbMCE']
    plt.figure(figsize=(8, 6))
    plt.rcParams.update({'font.size': 15})
    plt.plot(T, limit_det, 'kx', markersize=15, label='DLL', linewidth=1)
    plt.plot(T[0], RTGM[0], 'bX', markersize=12, label='$PGA_{GM}$',
             linewidth=3)
    plt.plot(T[1:], RTGM[1:], 'bs', markersize=12,
             label='$S_{S,RT}$ and $S_{1,RT}$', linewidth=3)
    MCEr_det = [dic['PGA_84th'], dic['SS_84th'], dic['S1_84th']]
    if any([val == 'n.a.' for val in MCEr_det]):  # hazard is lower than DLLs
        plt.ylim([0, numpy.max([RTGM, MCEr, limit_det]) + 0.2])
    else:
        plt.plot(T[0], MCEr_det[0], 'c^', markersize=10, label='$PGA_{84th}$',
                 linewidth=3)
        plt.plot(T[1:], MCEr_det[1:], 'cd', markersize=10,
                 label='$S_{S,84th}$ and $S_{1,84th}$', linewidth=3)
        plt.ylim([0, numpy.max([RTGM,  MCEr, MCEr_det, limit_det]) + 0.2])
    plt.scatter(T[0], MCEr[0], s=200, label='Governing $MCE_G$',
                linewidth=2, facecolors='none', edgecolors='r')
    plt.scatter(T[1:], MCEr[1:], s=200, marker='s',
                label='Governing $MCE_R$', linewidth=2,
                facecolors='none', edgecolors='r')
    plt.grid('both')
    plt.ylabel('Spectral Acceleration (g)', fontsize=20)
    plt.xlabel('Period (s)', fontsize=20)
    plt.legend(loc="upper right", fontsize='13')
    plt.xlim([-0.02, 1.2])
    if update_dstore:
        if Image is not None:
            bio = io.BytesIO()
            plt.savefig(bio, format='png', bbox_inches='tight')
            logging.info('Storing png/governing_mce.png')
            dstore['png/governing_mce.png'] = Image.open(bio)
        else:
            logging.warning(
                'Missing module PIL: skipping storing png/governing_mce.png')
    return plt


# TODO: this is horrible code to be removed
def _disaggr_by_src(dstore):

    # get info : specific to disagg by src
    df = dstore['mean_rates_by_src'].to_dframe().set_index('src_id')
    grouped_m = df.groupby(['src_id', 'site_id', 'imt']).agg(
        {"value": list}).reset_index()
    # remove the sources that aren't contributing at all to the hazard
    mask = grouped_m.value.apply(lambda x: sum(x) > 0)
    gm = grouped_m[mask].reset_index()
    grouped_2 = gm.groupby(['imt', 'src_id']).agg(
        {"value": numpy.array}).reset_index()
    total_poe = []
    for wp in grouped_2.value.values:
        wsp = []
        if isinstance(wp, list):
            total_poe.append(wp)
        else:
            for wp_i in wp:
                wsp.append(wp_i)
            total_poe.append([sum(t) for t in numpy.array(wsp).T])
    grouped_2['poes'] = total_poe
    return grouped_2


def plot_disagg_by_src(dstore, update_dstore=False):
    df = _disaggr_by_src(dstore)
    dinfo = get_info(dstore)
    # get imls and imts, make arrays
    imtls = dinfo['imtls']
    imts = ['PGA', 'SA(0.2)', 'SA(1.0)']
    # get rtgm ouptut from the datastore
    rtgm_df = dstore.read_df('rtgm')
    # get the IML for the 2475 RP
    rtgm_probmce = rtgm_df['ProbMCE']
    # get hazard curves, put into rates
    mean_hcurve = dstore['hcurves-stats'][0, 0]  # shape(M, L1)
    plt = import_plt()
    fig, ax = plt.subplots(3, figsize=(8, 15))

    # identify the sources that have a contribution > than fact (here 10%) of
    # the largest contributor;
    fact = 0.1

    for m, imt in enumerate(imts):
        out_contr_all = []
        fig1, ax1 = plt.subplots()

        dms = df[(df['imt'] == imt)]
        # annual frequency of exceedance:
        T = from_string(imt).period
        f = 0 if imt == 0.0 else _find_fact_maxC(T, 'ASCE7-16')
        imls_o = imtls[imt]
        imls = [iml*f for iml in imls_o]
        # have to compute everything for max comp. and for geom. mean
        RTGM = rtgm_probmce[m]
        RTGM_o = rtgm_probmce[m]/f
        afe_target = _find_afe_target(imls, mean_hcurve[m], RTGM)
        afe_target_o = _find_afe_target(imls_o, mean_hcurve[m], RTGM_o)

        # populate 3-panel plot
        ax[m].loglog(imls, mean_hcurve[m], 'k', label=_get_label(imt),
                     linewidth=2, zorder=3)
        ax[m].loglog([numpy.min(imls), RTGM], [afe_target, afe_target], 'k--',
                     linewidth=2, zorder=3)
        ax[m].loglog([RTGM, RTGM], [0, afe_target], 'k--', linewidth=2,
                     zorder=3)
        ax[m].loglog([RTGM], [afe_target], 'ko', label='Probabilistic MCE',
                     linewidth=2, zorder=3)
        # populate individual plots
        ax1.loglog(imls_o, mean_hcurve[m], 'k', label=imt + ' - Geom. mean',
                   linewidth=2, zorder=3)
        ax1.loglog([numpy.min(imls_o), RTGM_o], [afe_target_o, afe_target_o],
                   'k--', linewidth=2, zorder=3)
        ax1.loglog([RTGM_o, RTGM_o], [0, afe_target_o], 'k--', linewidth=2,
                   zorder=3)
        ax1.loglog([RTGM_o], [afe_target_o], 'ko', label='Probabilistic MCE',
                   linewidth=2, zorder=3)

        # poes from dms are now rates
        for ind, (afes, src) in enumerate(zip(dms.poes, dms.src_id)):
            # get contribution at target level for that source
            afe_uhgm = _find_afe_target(imls, afes, rtgm_probmce[m])
            # get % contribution of that source
            contr_source = afe_uhgm/afe_target
            out_contr_all.append(contr_source * 100)

        # identify contribution of largest contributor, make color scale
        largest_contr = numpy.max(out_contr_all)
        sample = sum(out_contr_all > fact*largest_contr)
        viridis = mpl.colormaps['viridis'].reversed()._resample(sample)

        # find and plot the sources, highlighting the ones that contribute more
        # than 10% of largest contributor
        # use j to only add the "other sources" label once
        # use i to cycle through the colors for the major source contributors
        i = j = 0
        for ind, (afes, src) in enumerate(zip(dms.poes, dms.src_id)):
            # pad to have the same length of imls and afes
            afe_pad = afes + [0] * (len(imls) - len(afes))
            # if it's not a big contributor, plot in silver
            if out_contr_all[ind] <= fact*largest_contr:
                if j == 0:
                    ax[m].loglog(imls, afe_pad, 'silver', linewidth=0.7,
                                 label='other sources')
                    ax1.loglog(imls_o, afe_pad, 'silver', linewidth=0.7,
                               label='other source')
                    j += 1
                else:
                    ax[m].loglog(imls, afe_pad, 'silver', linewidth=0.7)
                    ax1.loglog(imls_o, afe_pad, 'silver', linewidth=0.7)
            # if it is, plot in color
            else:
                ax[m].loglog(imls, afe_pad, c=viridis(i), label=str(src))
                ax1.loglog(imls_o, afe_pad, c=viridis(i), label=str(src))
                i += 1
        # populate subplot - maximum component
        ax[m].grid('both')
        ax[m].set_xlabel(imt+' (g)', fontsize=16)
        ax[m].set_ylabel('Annual Freq. Exceedance', fontsize=16)
        ax[m].legend(loc='center left', bbox_to_anchor=(1, 0.5), fontsize='13')
        ax[m].set_ylim([10E-6, 1.1])
        ax[m].set_xlim([0.01, 4])

        # populate single imt plots - geometric mean
        ax1.grid('both')
        ax1.set_xlabel(imt+' (g)', fontsize=16)
        ax1.set_ylabel('Annual Freq. Exceedance', fontsize=16)
        ax1.legend(loc='center left', bbox_to_anchor=(1, 0.5), fontsize='13')
        ax1.set_ylim([10E-6, 1.1])
        ax1.set_xlim([0.01, 4])

        if update_dstore:
            if Image is not None:
                # save single imt plot
                bio1 = io.BytesIO()
                fig1.savefig(bio1, format='png', bbox_inches='tight')
                # keep these in webui until we finish checks and have a command
                # line exporter, then we can change the name to _{imt} and they
                # will not appear in the webui
                dstore[f'png/disagg_by_src-{imt}.png'] = Image.open(bio1)
            else:
                logging.warning(
                    f'Missing module PIL: skipping storing'
                    f' png/disagg_by_src-{imt}.png')

    if update_dstore:
        if Image is not None:
            # save triple plot
            bio = io.BytesIO()
            fig.savefig(bio, format='png', bbox_inches='tight')
            logging.info('Storing png/disagg_by_src.png')
            dstore['png/disagg_by_src-All-IMTs.png'] = Image.open(bio)
        else:
            logging.warning(
                'Missing module PIL: skipping storing'
                ' png/disagg_by_src-All-IMTs.png')
    return plt


def make_figure_mean_hcurves_afe_rtgm(extractors, what):
    """
    $ oq plot "mean_hcurves_afe_rtgm?"
    """
    [ex] = extractors
    dstore = ex.dstore
    plt = plot_mean_hcurves_afe_rtgm(dstore)
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
    $ oq plot "disagg_by_src?"
    """
    [ex] = extractors
    dstore = ex.dstore
    plt = plot_disagg_by_src(dstore)
    return plt


def plot_wkt(wkt_string):
    """
    Plot a WKT string describing a polygon
    """
    from shapely import wkt
    plt = import_plt()
    poly = wkt.loads(wkt_string)
    coo = numpy.array(poly.exterior.coords)
    plt.plot(coo[:, 0], coo[:, 1], '-')
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
         webapi=False,
         local=False):
    """
    Generic plotter for local and remote calculations.
    """
    if what.endswith('.csv'):
        plot_csv(what)
        return
    if what.startswith('POLYGON'):
        plt = plot_wkt(what)
        plt.show()
        return
    if what == 'examples':
        help_msg = ['Examples of possible plots:']
        for k, v in globals().items():
            if k.startswith('make_figure_'):
                help_msg.append(v.__doc__)
        raise SystemExit(''.join(help_msg))
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
    plt.show()


main.what = 'what to extract (try examples)'
main.calc_id = 'computation ID'
main.others = dict(help='IDs of other computations', nargs='*')
main.webapi = 'if given, pass through the WebAPI'
main.local = 'if passed, use the local WebAPI'
