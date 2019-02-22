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
from openquake.calculators.extract import Extractor, WebExtractor


def make_figure(site, inv_time, imtls, spec_curves, other_curves=(), label=''):
    """
    :param site: ID of the site to plot
    :param inv_time: investigation time
    :param imtls: ordered dictionary with the IMTs and levels
    :param spec_curves: a dictionary of curves sid -> levels
    :param other_curves: dictionaries sid -> levels
    :param label: the label associated to `spec_curves`
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
        ax.set_xlabel('site %d, %s, inv_time=%dy' % (site, imt, inv_time))
        if j == 0:  # set Y label only on the leftmost graph
            ax.set_ylabel('PoE')
        if spec_curves is not None:
            ax.loglog(imls, spec_curves[0, imt_slice], '--', label=label)
        for key, curves in other_curves.items():
            ax.loglog(imls, curves[0, imt_slice], label=key)
        ax.legend()
    return plt


@sap.Script
def plot(imt, calc_id=-1, other_id=None, site=0, webapi=False):
    """
    Hazard curves plotter.
    """
    if webapi:
        x1 = WebExtractor(calc_id)
        x2 = WebExtractor(other_id) if other_id else None
    else:
        x1 = Extractor(calc_id)
        x2 = Extractor(other_id) if other_id else None
    oq = x1.oqparam
    stats = dict(oq.hazard_stats())
    imls = oq.imtls[imt]
    imtls = general.DictArray({imt: imls})
    itime = oq.investigation_time

    if x2 is None:
        stats.pop('mean')
        mean_curves = x1.get('hcurves/mean?imt=%s&site_id=%d' % (imt, site))
        others = {
            stat: x1.get('hcurves/%s?imt=%s&site_id=%d' % (stat, imt, site))
            for stat in stats}
        plt = make_figure(site, itime, imtls, mean_curves, others, 'mean')
    else:
        mean1 = x1.get('hcurves/mean?imt=%s?site_id=%d' % (imt, site))
        mean2 = x2.get('hcurves/mean?imt=%s?site_id=%d' % (imt, site))
        plt = make_figure(site, itime, imtls, mean1, [mean2], 'reference')
    plt.show()


plot.arg('imt', 'intensity measure type')
plot.arg('calc_id', 'computation ID', type=int)
plot.arg('other_id', 'ID of another computation', type=int)
plot.opt('site', 'ID of the site to plot', type=int)
plot.flg('webapi', 'if given, pass through the WebAPI')
