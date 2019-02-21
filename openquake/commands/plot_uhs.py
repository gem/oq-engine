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
from openquake.calculators.extract import Extractor


def make_figure(indices, oq, uhs_dict):
    """
    :param indices: the indices of the sites under analysis
    :param oq: instance of OqParam
    :param uhs_dict: a dictionary of uniform hazard spectra
    """
    # NB: matplotlib is imported inside since it is a costly import
    import matplotlib.pyplot as plt

    fig = plt.figure()
    n_poes = len(oq.poes)
    periods = [imt.period for imt in oq.imt_periods()]
    for i, site in enumerate(indices):
        for j, poe in enumerate(oq.poes):
            ax = fig.add_subplot(len(indices), n_poes, i * n_poes + j + 1)
            ax.grid(True)
            ax.set_xlim([periods[0], periods[-1]])
            ax.set_xlabel(
                'UHS on site %d, poe=%s, period in seconds' % (site, poe))
            if j == 0:  # set Y label only on the leftmost graph
                ax.set_ylabel('SA')
            for kind, uhs in uhs_dict.items():
                ax.plot(periods, uhs[site, :, j], label=kind)
    plt.legend()
    return plt


@sap.Script
def plot_uhs(calc_id, sites='0'):
    """
    UHS plotter.
    """
    # read the hazard data
    indices = list(map(int, sites.split(',')))
    x = Extractor(calc_id)
    oq = x.oqparam
    uhs = {stat: x.get('uhs/' + stat) for stat, _ in oq.hazard_stats()}
    plt = make_figure(indices, oq, uhs)
    plt.show()


plot_uhs.arg('calc_id', 'a computation id', type=int)
plot_uhs.opt('sites', 'comma-separated string with the site indices')
