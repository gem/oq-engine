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
from openquake.baselib import sap, config
from openquake.hazardlib.imt import from_string
from openquake.calculators.extract import Extractor


def make_figure(lons, lats, imt, imls, poes, hmaps):
    """
    :param lons: site longitudes
    :param lats: site latitudes
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
        ax.set_xlabel('hmap for IMT=%s, poe=%s' % (imt, poe))
        ax.scatter(lons, lats, c=hmaps[:, j], cmap='rainbow')
    return plt


@sap.Script
def plot_hmaps(imt, calc_id, remote=False):
    """
    Mean hazard maps plotter.
    """
    w = config.webui
    extractor = Extractor(calc_id, w.server, w.username, w.password, remote)
    with extractor:
        oq = extractor.oqparam
        sitecol = extractor.get('sitecol').array
        hmaps = extractor.get('hmaps/%s' % str(imt)).array
    lons, lats = sitecol['lon'], sitecol['lat']
    plt = make_figure(lons, lats, imt, oq.imtls[str(imt)], oq.poes, hmaps)
    plt.show()


plot_hmaps.arg('imt', 'an intensity measure type', type=from_string)
plot_hmaps.arg('calc_id', 'a computation id', type=int)
plot_hmaps.flg('remote', 'use a remote server')
