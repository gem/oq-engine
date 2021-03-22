# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2021 GEM Foundation
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
import gzip
import json
import logging
import shapely
import numpy
from openquake.hazardlib.geo.utils import cross_idl
from openquake.hazardlib.contexts import Effect, get_effect_by_mag
from openquake.hazardlib.calc.filters import getdefault, MagDepDistance
from openquake.calculators.extract import Extractor, WebExtractor


def make_figure_hcurves(extractors, what):
    """
    $ oq plot "hcurves?kind=mean&imt=PGA&site_id=0"
    """
    import matplotlib.pyplot as plt
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


def make_figure_avg_gmf(extractors, what):
    """
    $ oq plot "avg_gmf?imt=gmv_0"
    """
    import matplotlib.pyplot as plt
    fig = plt.figure()
    [ex] = extractors
    avg_gmf = ex.get(what)
    imt = what.split('=')[1]
    ax = fig.add_subplot(1, 1, 1)
    ax.grid(True)
    ax.set_title('Avg GMF for %s' % imt)
    ax.set_xlabel('Lon')
    ax.set_ylabel('Lat')
    coll = ax.scatter(avg_gmf['lons'], avg_gmf['lats'],
                      c=avg_gmf[imt], cmap='jet')
    plt.colorbar(coll)
    return plt


def make_figure_vs30(extractors, what):
    """
    $ oq plot "vs30?"
    """
    import matplotlib.pyplot as plt
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
    import matplotlib.pyplot as plt
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
    import matplotlib.pyplot as plt
    fig = plt.figure()
    got = {}  # (calc_id, kind) -> curves
    for i, ex in enumerate(extractors):
        uhs = ex.get(what)
        for kind in uhs.kind:
            got[ex.calc_id, kind] = uhs[kind]
    oq = ex.oqparam
    n_poes = len(oq.poes)
    periods = [imt.period for imt in oq.imt_periods()]
    [site] = uhs.site_id
    for j, poe in enumerate(oq.poes):
        ax = fig.add_subplot(n_poes, 1, j + 1)
        ax.set_xlabel('UHS on site %s, poe=%s, inv_time=%dy' %
                      (site, poe, oq.investigation_time))
        ax.set_ylabel('SA')
        for ck, arr in got.items():
            curve = list(arr[site][str(poe)])
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


def make_figure_disagg(extractors, what):
    """
    $ oq plot "disagg?kind=Mag&imt=PGA"
    """
    import matplotlib.pyplot as plt
    from matplotlib import cm
    fig = plt.figure()
    oq = extractors[0].oqparam
    disagg = extractors[0].get(what)
    [sid] = disagg.site_id
    [imt] = disagg.imt
    [poe_id] = disagg.poe_id
    y = disagg.array
    print(y)
    ndims = len(y.shape)
    axis = disagg.kind.split('_')
    bins = getattr(disagg, axis[0])
    ncalcs = len(extractors)
    width = (bins[1] - bins[0]) * 0.5
    x = middle(bins) if ncalcs == 1 else middle(bins) - width
    if ndims == 1:  # simple bar chart
        ax = fig.add_subplot(1, 1, 1)
        ax.set_xlabel('Disagg%s on site %s, imt=%s, poe_id=%d, inv_time=%dy' %
                      (disagg.kind, sid, imt, poe_id, oq.investigation_time))
        ax.set_xlabel(axis[0])
        ax.set_xticks(bins)
        ax.bar(x, y, width)
        for ex in extractors[1:]:
            ax.bar(x + width, ex.get(what).array, width)
        return plt
    if ncalcs > 1:
        raise NotImplementedError('Comparison for %s' % disagg.kind)
    # 2D images
    if ndims == 2:
        y = y.reshape(y.shape + (1,))
        zbins = ['']
    else:
        zbins = getattr(disagg, axis[2])
    Z = y.shape[-1]
    axes = []
    for z in range(Z):
        arr = y[:, :, z]
        ax = fig.add_subplot(Z, 1, z + 1)
        axes.append(ax)
        ax.set_ylabel(axis[1])
        ax.set_title(zbins[z])
        vbins = getattr(disagg, axis[1])  # vertical bins
        cmap = cm.get_cmap('jet', 100)
        extent = bins[0], bins[-1], vbins[0], vbins[-1]
        im = ax.imshow(arr, cmap=cmap, extent=extent,
                       aspect='auto', vmin=y.min(), vmax=y.max())
        # stacked bar chart
        # stacked_bar(ax, x, y.T, width)
        # ys = ['%.1f' % y for y in getattr(disagg, axis[1])]
        # ax.legend(ys)
    fig.colorbar(im, ax=axes)
    return plt


def make_figure_task_info(extractors, what):
    """
    $ oq plot "task_info?kind=classical"
    """
    import matplotlib.pyplot as plt
    fig = plt.figure()
    [ex] = extractors
    [(task_name, task_info)] = ex.get(what).to_dict().items()
    x = task_info['duration']
    ax = fig.add_subplot(1, 1, 1)
    mean, std = x.mean(), x.std(ddof=1)
    ax.hist(x, bins=50, rwidth=0.9)
    ax.set_xlabel("mean=%d+-%d seconds" % (mean, std))
    ax.set_ylabel("tasks=%d" % len(x))
    #from scipy.stats import linregress
    #ax = fig.add_subplot(2, 1, 2)
    #arr = numpy.sort(task_info, order='duration')
    #x, y = arr['duration'], arr['weight']
    #reg = linregress(x, y)
    #ax.plot(x, reg.intercept + reg.slope * x)
    #ax.plot(x, y)
    #ax.set_ylabel("weight")
    #ax.set_xlabel("duration")
    return plt


def make_figure_memory(extractors, what):
    """
    $ oq plot "memory?"
    """
    # NB: matplotlib is imported inside since it is a costly import
    import matplotlib.pyplot as plt

    [ex] = extractors
    task_info = ex.get('task_info').to_dict()
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


class PolygonPlotter():
    """
    Add polygons to a given axis object
    """
    def __init__(self, ax):
        self.ax = ax
        self.minxs = []
        self.maxxs = []
        self.minys = []
        self.maxys = []

    def add(self, poly, **kw):
        from openquake.hmtk.plotting.patch import PolygonPatch
        minx, miny, maxx, maxy = poly.bounds
        self.minxs.append(minx)
        self.maxxs.append(maxx)
        self.minys.append(miny)
        self.maxys.append(maxy)
        try:
            self.ax.add_patch(PolygonPatch(poly, **kw))
        except ValueError:  # LINESTRING, not POLYGON
            pass

    def set_lim(self, xs=(), ys=()):
        if len(xs):
            self.minxs.append(min(xs))
            self.maxxs.append(max(xs))
        if len(ys):
            self.minys.append(min(ys))
            self.maxys.append(max(ys))
        if self.minxs and self.maxxs:
            self.ax.set_xlim(min(self.minxs), max(self.maxxs))
        if self.minys and self.maxys:
            self.ax.set_ylim(min(self.minys), max(self.maxys))


def make_figure_sources(extractors, what):
    """
    $ oq plot "sources?limit=100"
    $ oq plot "sources?source_id=1&source_id=2"
    $ oq plot "sources?code=A&code=N"
    """
    # NB: matplotlib is imported inside since it is a costly import
    import matplotlib.pyplot as plt
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
        if rec['eff_ruptures']:  # not filtered out
            color = 'green'
            alpha = .3
            n += 1
        else:
            color = 'yellow'
            alpha = .1
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
    ax.set_title('%d/%d sources' % (n, tot))
    return plt


def make_figure_gridded_sources(extractors, what):
    """
    $ oq plot "gridded_sources?task_no=0"
    """
    # NB: matplotlib is imported inside since it is a costly import
    import matplotlib.pyplot as plt
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
    import matplotlib.pyplot as plt
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
    import matplotlib.pyplot as plt
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
    import matplotlib.pyplot as plt
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
    import matplotlib.pyplot as plt
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
    import matplotlib.pyplot as plt
    [ex] = extractors
    gsims_by_trt = ex.get('gsims_by_trt', asdict=True)
    mags = ex.get('source_mags').array
    try:
        effect = ex.get('effect')
    except KeyError:
        onesite = ex.get('sitecol').one()
        maximum_distance = MagDepDistance(ex.oqparam.maximum_distance)
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
    import matplotlib.pyplot as plt
    fig = plt.figure()
    got = {}  # (calc_id, kind) -> curves
    for i, ex in enumerate(extractors):
        aw = ex.get(what + '&absolute=1')
        agg_curve = aw.array.squeeze()
        got[ex.calc_id, aw.kind[0]] = agg_curve
    oq = ex.oqparam
    periods = aw.return_period
    ax = fig.add_subplot(1, 1, 1)
    ax.set_xlabel('risk_inv_time=%dy' % oq.risk_investigation_time)
    ax.set_ylabel('PoE')
    for ck, arr in got.items():
        ax.loglog(periods, agg_curve, '-', label='%s_%s' % ck)
        ax.loglog(periods, agg_curve, '.')
    ax.grid(True)
    ax.legend()
    return plt


def make_figure_tot_curves(extractors, what):
    """
    $ oq plot "tot_curves?loss_type=structural&kind=rlz-000&absolute=1"
    """
    import matplotlib.pyplot as plt
    fig = plt.figure()
    [ex] = extractors
    tot = ex.get(what)
    ax = fig.add_subplot(1, 1, 1)
    ax.set_xlabel('return periods')
    ax.set_ylabel('PoE')
    ax.loglog(tot.return_period, tot[:, 0], '-', label='tot_curves')
    ax.grid(True)
    ax.legend()
    return plt


def plot_wkt(wkt_string):
    """
    Plot a WKT string describing a polygon
    """
    from shapely import wkt
    import matplotlib.pyplot as plt
    poly = wkt.loads(wkt_string)
    coo = numpy.array(poly.exterior.coords)
    plt.plot(coo[:, 0], coo[:, 1], '-')
    return plt


def main(what,
         calc_id: int = -1,
         others: int = [],
         webapi=False,
         local=False):
    """
    Generic plotter for local and remote calculations.
    """
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
