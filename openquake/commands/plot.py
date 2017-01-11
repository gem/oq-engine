# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2017 GEM Foundation
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

from __future__ import print_function
from openquake.baselib import sap
from openquake.commonlib import datastore
from openquake.commands.show import get_hcurves_and_means


def make_figure(indices, imtls, spec_curves, curves=(), label=''):
    """
    :param indices: the indices of the sites under analysis
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
    n_sites = len(indices)
    for i, site in enumerate(indices):
        for j, imt in enumerate(imtls):
            ax = fig.add_subplot(n_sites, n_imts, i * n_imts + j + 1)
            ax.grid(True)
            ax.set_xlabel('Hazard curve on site %d, %s' % (site, imt))
            ax.set_ylim([0, 1])
            if j == 0:  # set Y label only on the leftmost graph
                ax.set_ylabel('PoE')
            if spec_curves is not None:
                ax.plot(imtls[imt], spec_curves[imt][site], '--', label=label)
            for rlz in sorted(curves):
                ax.plot(imtls[imt], curves[rlz][imt][site], label=str(rlz))
    plt.legend()
    return plt


@sap.Script
def plot(calc_id, other_id=None, sites='0'):
    """
    Hazard curves plotter.
    """
    # read the hazard data
    haz = datastore.read(calc_id)
    other = datastore.read(other_id) if other_id else None
    oq = haz['oqparam']
    indices = list(map(int, sites.split(',')))
    n_sites = len(haz['sitecol'])
    if not set(indices) <= set(range(n_sites)):
        invalid = sorted(set(indices) - set(range(n_sites)))
        print('The indices %s are invalid: no graph for them' % invalid)
    valid = sorted(set(range(n_sites)) & set(indices))
    print('Found %d site(s); plotting %d of them' % (n_sites, len(valid)))
    if other is None:
        curves_by_rlz, mean_curves = get_hcurves_and_means(haz)
        single_curve = len(curves_by_rlz) == 1 or not getattr(
            oq, 'individual_curves', True)
        plt = make_figure(valid, oq.imtls, mean_curves,
                          {} if single_curve else curves_by_rlz, 'mean')
    else:
        mean1 = haz['hcurves/mean']
        mean2 = other['hcurves/mean']
        plt = make_figure(valid, oq.imtls, mean1, {'mean': mean2}, 'reference')
    plt.show()

plot.arg('calc_id', 'a computation id', type=int)
plot.arg('other_id', 'optional id of another computation', type=int)
plot.opt('sites', 'comma-separated string with the site indices')
