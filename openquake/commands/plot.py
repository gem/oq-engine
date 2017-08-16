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
import numpy
from openquake.baselib import sap
from openquake.hazardlib.stats import mean_curve, compute_pmap_stats
from openquake.commonlib import datastore, calc


def make_figure(indices, n, imtls, spec_curves, curves=(), label=''):
    """
    :param indices: the indices of the sites under analysis
    :param n: the total number of sites
    :param imtls: ordered dictionary with the IMTs and levels
    :param spec_curves: a dictionary of curves IMT -> array(n_sites, n_levels)
    :param curves: a dictionary of dictionaries IMT -> array
    :param label: the label associated to `spec_curves`
    """
    # NB: matplotlib is imported inside since it is a costly import
    import matplotlib.pyplot as plt

    fig = plt.figure()
    n_imts = len(imtls)
    n_sites = len(indices)
    spec_curves = spec_curves.convert(imtls, n)
    all_curves = [c.convert(imtls, n) for c in curves]
    for i, site in enumerate(indices):
        for j, imt in enumerate(imtls):
            ax = fig.add_subplot(n_sites, n_imts, i * n_imts + j + 1)
            ax.grid(True)
            ax.set_xlabel('site %d, %s' % (site, imt))
            ax.set_ylim([0, 1])
            if j == 0:  # set Y label only on the leftmost graph
                ax.set_ylabel('PoE')
            if spec_curves is not None:
                ax.plot(imtls[imt], spec_curves[imt][site], '--', label=label)
            for r, curves in enumerate(all_curves):
                ax.plot(imtls[imt], curves[imt][site], label=str(r))
    plt.legend()
    return plt


def get_pmaps(dstore, indices):
    getter = calc.PmapGetter(dstore)
    pmaps = getter.get_pmaps(indices)
    weights = dstore['realizations']['weight']
    mean = compute_pmap_stats(pmaps, [mean_curve], weights)
    return mean, pmaps


@sap.Script
def plot(calc_id, other_id=None, sites='0'):
    """
    Hazard curves plotter.
    """
    # read the hazard data
    haz = datastore.read(calc_id)
    other = datastore.read(other_id) if other_id else None
    oq = haz['oqparam']
    indices = numpy.array(list(map(int, sites.split(','))))
    n_sites = len(haz['sitecol'])
    if not set(indices) <= set(range(n_sites)):
        invalid = sorted(set(indices) - set(range(n_sites)))
        print('The indices %s are invalid: no graph for them' % invalid)
    valid = sorted(set(range(n_sites)) & set(indices))
    print('Found %d site(s); plotting %d of them' % (n_sites, len(valid)))
    if other is None:
        mean_curves, pmaps = get_pmaps(haz, indices)
        single_curve = len(pmaps) == 1
        plt = make_figure(valid, n_sites, oq.imtls, mean_curves,
                          [] if single_curve else pmaps, 'mean')
    else:
        mean1, _ = get_pmaps(haz, indices)
        mean2, _ = get_pmaps(other, indices)
        plt = make_figure(valid, n_sites, oq.imtls, mean1,
                          [mean2], 'reference')
    plt.show()

plot.arg('calc_id', 'a computation id', type=int)
plot.arg('other_id', 'optional id of another computation', type=int)
plot.opt('sites', 'comma-separated string with the site indices')
