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
from openquake.baselib import sap, general
from openquake.calculators.extract import Extractor, WebExtractor, parse


def basemap(projection, lons, lats):
    from mpl_toolkits.basemap import Basemap  # costly import
    bmap = Basemap(projection=projection,
                   llcrnrlon=lons.min() - 1, llcrnrlat=lats.min() - 1,
                   urcrnrlon=lons.max() + 1, urcrnrlat=lats.max() + 1,
                   lat_0=lats.mean(), lon_0=lons.mean())
    bmap.drawcoastlines()
    return bmap


def make_figure_hcurves(site, inv_time, imtls, curves):
    """
    :param site: ID of the site to plot
    :param inv_time: investigation time
    :param imtls: ordered dictionary with the IMTs and levels
    :param curves: a dictionary of curves sid -> levels
    """
    # NB: matplotlib is imported inside since it is a costly import
    import matplotlib.pyplot as plt
    fig = plt.figure()
    n_imts = len(imtls)
    for j, imt in enumerate(imtls):
        imls = imtls[imt]
        imt_slice = imtls(imt)
        ax = fig.add_subplot(1, n_imts, j + 1)
        ax.grid(True)
        ax.set_xlabel('site %s, %s, inv_time=%dy' % (site, imt, inv_time))
        if j == 0:  # set Y label only on the leftmost graph
            ax.set_ylabel('PoE')
        for key, curve in curves.items():
            ax.loglog(imls, curve[0, imt_slice], label=key)
        ax.legend()
    return plt


def make_figure_uhs(site, oq, uhs_dict):
    """
    :param site: ID of the site under analysis
    :param oq: instance of OqParam
    :param uhs_dict: a dictionary of uniform hazard spectra
    """
    # NB: matplotlib is imported inside since it is a costly import
    import matplotlib.pyplot as plt

    fig = plt.figure()
    n_poes = len(oq.poes)
    periods = [imt.period for imt in oq.imt_periods()]
    for j, poe in enumerate(oq.poes):
        ax = fig.add_subplot(1, n_poes, j + 1)
        ax.grid(True)
        ax.set_xlim([periods[0], periods[-1]])
        ax.set_xlabel(
            'UHS on site %s, poe=%s\nperiod in seconds, inv_time=%dy' %
            (site, poe, oq.investigation_time))
        if j == 0:  # set Y label only on the leftmost graph
            ax.set_ylabel('SA')
        for kind, uhs in uhs_dict.items():
            ax.plot(periods, uhs[0, :, j], label=kind)
    plt.legend()
    return plt


def make_figure_hmaps(lons, lats, itime, imt, imls, poes, hmaps):
    """
    :param lons: site longitudes
    :param lats: site latitudes
    :param itime: investigation time
    :param imt: intensity measure type
    :param imls: intensity measure levels
    :param poes: PoEs used to compute the hazard maps
    :param hmaps: mean hazard maps as an array of shape (N, M, P)
    """
    # NB: matplotlib is imported inside since it is a costly import
    import matplotlib.pyplot as plt
    fig = plt.figure()
    n_poes = len(poes)
    i = 0
    for j, poe in enumerate(poes):
        ax = fig.add_subplot(1, n_poes, i * n_poes + j + 1)
        ax.grid(True)
        ax.set_xlabel('hmap for IMT=%s, poe=%s\ninv_time=%dy' %
                      (imt, poe, itime))
        bmap = basemap('cyl', lons, lats)
        bmap.scatter(lons, lats, c=hmaps[:, 0, j], cmap='jet')
    return plt


@sap.Script
def plot(what, calc_id=-1, other_id=None, webapi=False):
    """
    Hazard curves plotter. Here is an example of use:

    $ oq plot 'hcurves?kind=mean&imt=PGA&site_id=0' -1 -2
    """
    if '?' not in what:
        raise SystemExit('Missing ? in %r' % what)
    prefix, rest = what.split('?', 1)
    assert prefix in 'hcurves hmaps uhs', prefix
    if prefix in 'hcurves hmaps' and 'imt=' not in rest:
        raise SystemExit('Missing imt= in %r' % what)
    if prefix in 'hcurves uhs' and 'site_id=' not in rest:
        rest += '&site_id=0'
    if prefix == 'hmaps' and 'kind=' not in rest:
        rest += '&kind=mean'
    if prefix == 'uhs' and 'imt=' in rest:
        raise SystemExit('Invalid IMT in %r' % what)
    if webapi:
        x1 = WebExtractor(calc_id)
        x2 = WebExtractor(other_id) if other_id else None
    else:
        x1 = Extractor(calc_id)
        x2 = Extractor(other_id) if other_id else None
    oq = x1.oqparam
    itime = oq.investigation_time
    stats = dict(oq.hazard_stats())
    suffix, index, qdict = parse(rest, stats)
    if prefix == 'hcurves':
        [site] = qdict['site_id']
        imtls = general.DictArray({imt: oq.imtls[imt] for imt in qdict['imt']})
        curves = {
            stat: x1.get('hcurves?%s&kind=%s' % (rest, stat))
            for stat in stats}
        if x2 is not None:
            for stat in stats:
                curves['%s-%d' % (stat, other_id)] = x2.get(
                    'hcurves?kind=%s&imt=%s&site_id=%d' % stat)
        plt = make_figure_hcurves(site, itime, imtls, curves)
    if prefix == 'hmaps':
        [imt] = qdict['imt']
        sitecol = x1.get('sitecol')
        lons, lats = sitecol['lon'], sitecol['lat']
        plt = make_figure_hmaps(lons, lats, oq.investigation_time,
                                imt, oq.imtls[imt], oq.poes,
                                x1.get('hmaps?' + rest))
    elif prefix == 'uhs':
        [site] = qdict['site_id']
        uhs_dict = {stat: x1.get('uhs?kind=%s&site_id=%s' % (stat, site))
                    for stat in stats}
        if x2 is not None:
            for stat in stats:
                uhs_dict['%s-%d' % (stat, other_id)] = x2.get(
                    'uhs?kind=%s&site_id=%s' % (stat, site))
        plt = make_figure_uhs(site, oq, uhs_dict)
    plt.show()


plot.arg('what', 'what to extract')
plot.arg('calc_id', 'computation ID', type=int)
plot.arg('other_id', 'ID of another computation', type=int)
plot.flg('webapi', 'if given, pass through the WebAPI')
