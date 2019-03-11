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
import logging
from openquake.baselib import sap
from openquake.hazardlib.geo.utils import get_bounding_box
from openquake.calculators.extract import Extractor, WebExtractor


def basemap(projection, sitecol):
    from mpl_toolkits.basemap import Basemap  # costly import
    minlon, minlat, maxlon, maxlat = get_bounding_box(sitecol, maxdist=10)
    bmap = Basemap(projection=projection,
                   llcrnrlon=minlon, llcrnrlat=minlat,
                   urcrnrlon=maxlon, urcrnrlat=maxlat,
                   lat_0=sitecol['lat'].mean(), lon_0=sitecol['lon'].mean())
    bmap.drawcoastlines()
    return bmap


def make_figure_hcurves(extractors, what):
    """
    $ oq plot 'hcurves?kind=mean&imt=PGA&site_id=0'
    """
    import matplotlib.pyplot as plt
    fig = plt.figure()
    got = {}  # (calc_id, kind) -> curves
    for i, ex in enumerate(extractors):
        hcurves = ex.get(what)
        for kind in hcurves.kind:
            got[ex.calc_id, kind] = hcurves[kind]
    oq = ex.oqparam
    n_imts = len(hcurves.imt)
    [site] = hcurves.site_id
    for j, imt in enumerate(hcurves.imt):
        imls = oq.imtls[imt]
        imt_slice = oq.imtls(imt)
        ax = fig.add_subplot(n_imts, 1, j + 1)
        ax.set_xlabel('%s, site %s, inv_time=%dy' %
                      (imt, site, oq.investigation_time))
        ax.set_ylabel('PoE')
        for ck, arr in got.items():
            if (arr == 0).all():
                logging.warning('There is a zero curve %s_%s', *ck)
            ax.loglog(imls, arr[0, imt_slice], '-', label='%s_%s' % ck)
            ax.loglog(imls, arr[0, imt_slice], '.')
        ax.grid(True)
        ax.legend()
    return plt


def make_figure_hmaps(extractors, what):
    """
    $ oq plot 'hmaps?kind=mean&imt=PGA'
    """
    import matplotlib.pyplot as plt
    fig = plt.figure()
    ncalcs = len(extractors)
    for i, ex in enumerate(extractors):
        oq = ex.oqparam
        n_poes = len(oq.poes)
        sitecol = ex.get('sitecol')
        hmaps = ex.get(what)
        [imt] = hmaps.imt
        [kind] = hmaps.kind
        for j, poe in enumerate(oq.poes):
            ax = fig.add_subplot(n_poes, ncalcs, j * ncalcs + i + 1)
            ax.grid(True)
            ax.set_xlabel('hmap for IMT=%s, kind=%s, poe=%s\ncalculation %d, '
                          'inv_time=%dy' %
                          (imt, kind, poe, ex.calc_id, oq.investigation_time))
            bmap = basemap('cyl', sitecol)
            bmap.scatter(sitecol['lon'], sitecol['lat'],
                         c=hmaps[kind][:, 0, j], cmap='jet')
    return plt


def make_figure_uhs(extractors, what):
    """
    $ oq plot 'uhs?kind=mean&site_id=0'
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
            ax.plot(periods, arr[0, :, j], '-', label='%s_%s' % ck)
            ax.plot(periods, arr[0, :, j], '.')
        ax.grid(True)
        ax.legend()
    return plt


def make_figure_source_geom(extractors, what):
    """
    Extract the geometry of a given sources
    Example:
    http://127.0.0.1:8800/v1/calc/30/extract/source_geom/1,2,3
    """
    import matplotlib.pyplot as plt
    fig = plt.figure()
    [ex] = extractors
    sitecol = ex.get('sitecol')
    geom_by_src = vars(ex.get(what))
    ax = fig.add_subplot(1, 1, 1)
    ax.grid(True)
    ax.set_xlabel('Source')
    bmap = basemap('cyl', sitecol)
    for src, geom in geom_by_src.items():
        if src != 'array':
            bmap.plot(geom['lon'], geom['lat'], label=src)
    bmap.plot(sitecol['lon'], sitecol['lat'], 'x')
    ax.legend()
    return plt


@sap.script
def plot(what, calc_id=-1, other_id=None, webapi=False):
    """
    Generic plotter for local and remote calculations.
    """
    if '?' not in what:
        raise SystemExit('Missing ? in %r' % what)
    prefix, rest = what.split('?', 1)
    assert prefix in 'source_geom hcurves hmaps uhs', prefix
    if prefix in 'hcurves hmaps' and 'imt=' not in rest:
        raise SystemExit('Missing imt= in %r' % what)
    elif prefix == 'uhs' and 'imt=' in rest:
        raise SystemExit('Invalid IMT in %r' % what)
    elif prefix in 'hcurves uhs' and 'site_id=' not in rest:
        what += '&site_id=0'
    if webapi:
        xs = [WebExtractor(calc_id)]
        if other_id:
            xs.append(WebExtractor(other_id))
    else:
        xs = [Extractor(calc_id)]
        if other_id:
            xs.append(Extractor(other_id))
    make_figure = globals()['make_figure_' + prefix]
    plt = make_figure(xs, what)
    plt.show()


plot.arg('what', 'what to extract')
plot.arg('calc_id', 'computation ID', type=int)
plot.arg('other_id', 'ID of another computation', type=int)
plot.flg('webapi', 'if given, pass through the WebAPI')
