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
    """
    :param n_sites: the number of sites under analysis
    :param imtls: ordered dictionary with the IMTs and levels
    :param spec_curves: a dictionary of curves IMT -> array(n_sites, n_levels)
    :param curves: a dictionary of dictionaries IMT -> array
    :param label: the label associated to `spec_curves`
    """
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


def combined_curves(haz, hazard_pik):
    """
    :param haz: a dictionary with the hazard outputs
    :param hazard_pik: the pathname to a pickled file
    :returns: curves_by_rlz, mean_curves
    """
    no_curves = all(len(c) == 0 for c in haz['curves_by_trt_gsim'].values())
    if no_curves:
        raise Exception('Could not find hazard curves in %s' % hazard_pik)

    curves_by_rlz = haz['rlzs_assoc'].combine(haz['curves_by_trt_gsim'])
    rlzs = sorted(curves_by_rlz)
    weights = [rlz.weight for rlz in rlzs]
    return curves_by_rlz, scientific.mean_curve(
        [curves_by_rlz[rlz] for rlz in rlzs], weights)


def plot(hazard_pik, hazard_pik2=None):
    """
    Hazard curves plotter.

    :param hazard_pik: the pathname to a pickled file
    :param hazard_pik2: None or the pathname to another pickled file
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
    curves_by_rlz, mean_curves = combined_curves(haz, hazard_pik)
    if hazard_pik2 is None:
        single_curve = len(curves_by_rlz) == 1 or not getattr(
            oq, 'individual_curves', True)
        plt = make_figure(n_sites, oq.imtls, mean_curves,
                          {} if single_curve else curves_by_rlz, 'mean')
    else:
        _, mean1 = combined_curves(haz, hazard_pik)
        _, mean2 = combined_curves(
            cPickle.load(open(hazard_pik2)), hazard_pik2)
        plt = make_figure(n_sites, oq.imtls, mean1, {'mean2': mean2}, 'mean1')
    plt.show()


parser = sap.Parser(plot)
parser.arg('hazard_pik', '.pik file containing the result of a computation')
parser.arg('hazard_pik2', 'optional .pik file containing the result '
           'of another computation')
