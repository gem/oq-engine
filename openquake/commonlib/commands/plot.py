#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2015, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import cPickle
import matplotlib.pyplot as plt
from openquake.commonlib import sap


def plot(hazard_pik):
    """
    Hazard curves plotter
    """
    with open(hazard_pik) as f:
        haz = cPickle.load(f)

    imtls = haz['oqparam'].imtls
    n_sites = len(haz['sitecol'])
    if n_sites > 5:
        print('There are %d sites; only the first 5 will be displayed'
              % n_sites)
        n_sites = 5
    n_imts = len(imtls)
    mean_curves = haz['mean_curves']
    curves_by_rlz = haz['rlzs_assoc'].combine(haz['curves_by_trt_gsim'])
    fig = plt.figure()
    axes = {}
    for i in range(1, n_sites + 1):
        for j, imt in enumerate(imtls, 1):
            ax = axes[i, imt] = fig.add_subplot(
                n_sites, n_imts, (i - 1) * n_imts + j)
            ax.grid(True)
            ax.set_xlabel('Hazard curve on site %d, %s' % (i, imt))
            if j == 1:  # set Y label only on the leftmost graph
                ax.set_ylabel('PoE')
            if mean_curves is not None and len(curves_by_rlz) > 1:
                ax.plot(imtls[imt], mean_curves[imt][i - 1],
                        '--', label='mean')
            for rlz in sorted(curves_by_rlz):
                ax.plot(imtls[imt], curves_by_rlz[rlz][imt][i - 1],
                        label=str(rlz))

    plt.legend()
    plt.show()

parser = sap.Parser(plot)
parser.arg('hazard_pik', '.pik file containing the result of a computation')
