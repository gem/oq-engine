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
import numpy
from openquake.baselib import sap, general
from openquake.calculators.extract import Extractor


def make_figure(indices, n, imtls, spec_curves, other_curves=(), label=''):
    """
    :param indices: the indices of the sites under analysis
    :param n: the total number of sites
    :param imtls: ordered dictionary with the IMTs and levels
    :param spec_curves: a dictionary of curves sid -> levels
    :param other_curves: dictionaries sid -> levels
    :param label: the label associated to `spec_curves`
    """
    # NB: matplotlib is imported inside since it is a costly import
    import matplotlib.pyplot as plt

    fig = plt.figure()
    n_imts = len(imtls)
    n_sites = len(indices)
    for i, site in enumerate(indices):
        for j, imt in enumerate(imtls):
            imls = imtls[imt]
            imt_slice = imtls(imt)
            ax = fig.add_subplot(n_sites, n_imts, i * n_imts + j + 1)
            ax.grid(True)
            ax.set_xlabel('site %d, %s' % (site, imt))
            if j == 0:  # set Y label only on the leftmost graph
                ax.set_ylabel('PoE')
            if spec_curves is not None:
                ax.loglog(imls, spec_curves[site][imt_slice], '--',
                          label=label)
            for r, curves in enumerate(other_curves):
                ax.loglog(imls, curves[site][imt_slice], label=str(r))
            ax.legend()
    return plt


def get_hcurves(dstore):
    hcurves = {name: dstore['hcurves/' + name] for name in dstore['hcurves']}
    return hcurves.pop('mean'), hcurves.values()


@sap.Script
def plot(imt, calc_id=-1, other_id=None, sites='0'):
    """
    Hazard curves plotter.
    """
    x1 = Extractor(calc_id)
    x2 = Extractor(other_id) if other_id else None
    oq = x1.oqparam
    stats = dict(oq.hazard_stats())
    sitecol = x1.get('sitecol').array
    imls = oq.imtls[imt]
    imtls = general.DictArray({imt: imls})
    indices = numpy.array(list(map(int, sites.split(','))))
    n_sites = len(sitecol)
    if not set(indices) <= set(range(n_sites)):
        invalid = sorted(set(indices) - set(range(n_sites)))
        print('The indices %s are invalid: no graph for them' % invalid)
    valid = sorted(set(range(n_sites)) & set(indices))
    print('Found %d site(s); plotting %d of them' % (n_sites, len(valid)))
    if x2 is None:
        stats.pop('mean')
        mean_curves = x1.get('hcurves/mean/' + imt)
        others = [x1.get('hcurves/mean/%s/%s' % (stat, imt)) for stat in stats]
        plt = make_figure(valid, n_sites, imtls, mean_curves, others, 'mean')
    else:
        mean1 = x1.get('hcurves/mean/' + imt)
        mean2 = x2.get('hcurves/mean/' + imt)
        plt = make_figure(valid, n_sites, imtls, mean1,
                          [mean2], 'reference')
    plt.show()


plot.arg('imt', 'intensity measure type')
plot.arg('calc_id', 'computation ID', type=int)
plot.arg('other_id', 'ID of another computation', type=int)
plot.opt('sites', 'comma-separated string with the site indices')
