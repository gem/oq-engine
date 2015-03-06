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
from openquake.commonlib import sap
from openquake.risklib import scientific


def make_figure(n_sites, imtls, spec_curves, curves=(), label=''):
    # NB: matplotlib is imported inside, otherwise nosetest would fail in an
    # installation without matplotlib
    import matplotlib.pyplot as plt

    fig = plt.figure()
    n_imts = len(imtls)
    for i in range(n_sites):
        for j, imt in enumerate(imtls):
            ax = fig.add_subplot(n_sites, n_imts, i * n_imts + j + 1)
            ax.grid(True)
            ax.set_xlabel('Hazard curve on site %d, %s' % (i + 1, imt))
            ax.set_ylim([0, 1])
            if j == 0:  # set Y label only on the leftmost graph
                ax.set_ylabel('PoE')
            if spec_curves is not None:
                ax.plot(imtls[imt], spec_curves[imt][i], '--', label=label)
            for rlz in sorted(curves):
                ax.plot(imtls[imt], curves[rlz][imt][i], label=str(rlz))
    plt.legend()
    return plt


def plot(hazard_pik):
    """
    Hazard curves plotter
    """
    # read the hazard data
    with open(hazard_pik) as f:
        haz = cPickle.load(f)
    oq = haz['oqparam']
    n_sites = len(haz['sitecol'])
    if n_sites > 5:
        print('There are %d sites; only the first 5 will be displayed'
              % n_sites)
        n_sites = 5
    no_curves = all(len(c) == 0 for c in haz['curves_by_trt_gsim'].values())
    if no_curves:
        raise Exception('Could not find hazard curves in %s' % hazard_pik)

    curves_by_rlz = haz['rlzs_assoc'].combine(haz['curves_by_trt_gsim'])
    rlzs = sorted(curves_by_rlz)
    weights = [rlz.weight for rlz in rlzs]
    mean_curves = scientific.mean_curve(
        [curves_by_rlz[rlz] for rlz in rlzs], weights)
    single_curve = len(rlzs) == 1 or not getattr(oq, 'individual_curves', True)
    plt = make_figure(n_sites, oq.imtls, mean_curves,
                      {} if single_curve else curves_by_rlz, 'mean')
    plt.show()

parser = sap.Parser(plot)
parser.arg('hazard_pik', '.pik file containing the result of a computation')
