# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2023 GEM Foundation
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

import logging
import numpy
from openquake.baselib import sap
from openquake.hazardlib.calc.hazard_curve import classical
from openquake.hazardlib.probability_map import ProbabilityMap
from openquake.hazardlib.contexts import get_cmakers


def to_rates(probs):
    """
    Convert an array of probabilities into an array of rates

    >>> numpy.round(to_rates(numpy.array([.8])), 6)
    array([1.609438])
    """
    pnes = 1. - probs
    pnes[pnes == 0] = 1E-45  # minimum float32
    return - numpy.log(pnes)


def to_probs(rates):
    """
    Convert an array of rates into an array of probabilities

    >>> numpy.round(to_probs(numpy.array([1.609438])), 6)
    array([0.8])
    """
    return 1. - numpy.exp(- rates)


def calc_rmap(src_groups, full_lt, sitecol, oq):
    """
    :returns: a ProbabilityMap of shape (N, L, Gt)
    """
    oq.use_rates = True
    oq.disagg_by_src = False
    L = oq.imtls.size
    rmap = ProbabilityMap(sitecol.sids, L, full_lt.Gt).fill(0)
    cmakers = get_cmakers(src_groups, full_lt, oq)
    ctxs = []
    for group, cmaker in zip(src_groups, cmakers):
        G = len(cmaker.gsims)
        dic = classical(group, sitecol, cmaker)
        if len(dic['rup_data']) == 0:  # the group was filtered away
            continue
        rates = to_rates(dic['pmap'].array)
        ctxs.append(numpy.concatenate(dic['rup_data']).view(numpy.recarray))
        for i, g in enumerate(cmaker.gidx):
            # += tested in logictree/case_05
            rmap.array[:, :, g] += rates[:, :, i % G]
    return rmap, ctxs, cmakers


def calc_mean_rates(rmap, gweights, imtls):
    """
    :returns: mean hazard rates as an array of shape (N, M, L1)
    """
    M = len(imtls)
    L1 = imtls.size // M
    N = len(rmap.array)
    rates = numpy.zeros((N, M, L1))
    for m, imt in enumerate(imtls):
        rates[:, m, :] = rmap.array[:, imtls(imt), :] @ [
            gw[imt] for gw in gweights]
    return rates


def main(job_ini):
    """
    Compute the mean rates from scratch without source splitting and without
    parallelization, pretty useful when debugging single site calculations
    """
    from openquake.commonlib import readinput
    from openquake.calculators.views import text_table
    oq = readinput.get_oqparam(job_ini)
    csm = readinput.get_composite_source_model(oq)
    sitecol = readinput.get_site_collection(oq)
    assert len(sitecol) <= oq.max_sites_disagg, sitecol
    if 'site_model' in oq.inputs:
        # TODO: see if it can be done in get_site_collection
        assoc_dist = (oq.region_grid_spacing * 1.414
                      if oq.region_grid_spacing else 5)  # Graeme's 5km
        sitecol.assoc(readinput.get_site_model(oq), assoc_dist)
    logging.info('Computing rate map with N=%d, L=%d, Gt=%d',
                 len(sitecol), oq.imtls.size, csm.full_lt.Gt)
    rmap, ctxs, cmakers = calc_rmap(csm.src_groups, csm.full_lt, sitecol, oq)
    rates = calc_mean_rates(rmap, csm.full_lt.g_weights, oq.imtls)
    N, M, L1 = rates.shape
    mrates = numpy.zeros((N, L1), oq.imt_dt())
    for m, imt in enumerate(oq.imtls):
        mrates[imt] = rates[:, m]
    print('Mean hazard rates for the first site')
    print(text_table(mrates[0], ext='org'))

main.job_ini = 'path to a job.ini file'


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    sap.run(main)
