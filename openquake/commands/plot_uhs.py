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

from openquake.baselib import sap
from openquake.calculators.extract import Extractor, WebExtractor


def make_figure(site, oq, uhs_dict):
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
            'UHS on site %d, poe=%s, period in seconds' % (site, poe))
        if j == 0:  # set Y label only on the leftmost graph
            ax.set_ylabel('SA')
        for kind, uhs in uhs_dict.items():
            ax.plot(periods, uhs[0, :, j], label=kind)
    plt.legend()
    return plt


@sap.Script
def plot_uhs(calc_id, site=0, webapi=False):
    """
    UHS plotter.
    """
    x = WebExtractor(calc_id) if webapi else Extractor(calc_id)
    oq = x.oqparam
    uhs = {stat: x.get('uhs/%s?site_id=%d' % (stat, site))
           for stat in oq.hazard_stats()}
    plt = make_figure(site, oq, uhs)
    plt.show()


plot_uhs.arg('calc_id', 'computation ID', type=int)
plot_uhs.opt('site', 'site ID', type=int)
plot_uhs.flg('webapi', 'if given, pass through the WebAPI')
