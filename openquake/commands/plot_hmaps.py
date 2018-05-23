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
from openquake.baselib import sap, datastore
from openquake.calculators import getters
from openquake.commonlib import calc


def make_figure(sitecol, imtls, poes, hmaps):
    """
    :param sitecol: site collection
    :param imtls: DictArray with the IMTs and levels
    :param poes: PoEs used to compute the hazard maps
    :param hmaps: mean hazard maps as an array of shape (N, M, P)
    """
    # NB: matplotlib is imported inside since it is a costly import
    import matplotlib.pyplot as plt
    fig = plt.figure()
    n_poes = len(poes)
    num_imts = len(imtls)
    for i, imt in enumerate(imtls):
        for j, poe in enumerate(poes):
            ax = fig.add_subplot(num_imts, n_poes, i * n_poes + j + 1)
            ax.grid(True)
            ax.set_xlabel('hmap for IMT=%s, poe=%s' % (imt, poe))
            ax.scatter(sitecol.lons, sitecol.lats, c=hmaps[:, i, j],
                       cmap='rainbow')
    return plt


@sap.Script
def plot_hmaps(calc_id):
    """
    Mean hazard maps plotter.
    """
    dstore = datastore.read(calc_id)
    oq = dstore['oqparam']
    rlzs_assoc = dstore['csm_info'].get_rlzs_assoc()
    mean = getters.PmapGetter(dstore, rlzs_assoc).get_mean()
    hmaps = calc.make_hmap(mean, oq.imtls, oq.poes)
    M, P = len(oq.imtls), len(oq.poes)
    array = hmaps.array.reshape(len(hmaps.array), M, P)
    plt = make_figure(dstore['sitecol'], oq.imtls, oq.poes, array)
    plt.show()

plot_hmaps.arg('calc_id', 'a computation id', type=int)
