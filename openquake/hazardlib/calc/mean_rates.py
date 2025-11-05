# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2025 GEM Foundation
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
from openquake.hazardlib.contexts import get_cmakers

F32 = numpy.float32
CUTOFF = 1E-12


def to_rates(probs, itime=1, minrate=0.):
    """
    Convert an array of probabilities into an array of rates

    >>> numpy.round(to_rates(numpy.array([.8])), 6)
    array([1.609438])
    """
    pnes = 1. - probs
    pnes[pnes == 0] = 1E-45  # minimum 32 bit float
    # NB: the test most sensitive to 1E-45 and 1E-12 is case_78
    rates = - numpy.log(pnes) / itime
    rates[rates < CUTOFF] = minrate
    rates[rates > 100.] = 100.
    return rates


def to_probs(rates, itime=1):
    """
    Convert an array of rates into an array of probabilities

    >>> numpy.round(to_probs(numpy.array([1.609438])), 6)
    array([0.8])
    """
    return 1. - numpy.exp(- rates * itime)


def get_rmap(src_groups, full_lt, sitecol, oq):
    """
    :returns: a MapArray of rates with shape (N, L, Gt)
    """
    oq.use_rates = True
    oq.disagg_by_src = False
    all_trt_smrs = [sg[0].trt_smrs for sg in src_groups]
    cmakers = get_cmakers(all_trt_smrs, full_lt, oq)
    rmap = cmakers.get_rmap(src_groups, sitecol)
    return rmap, cmakers


def calc_mean_rates(rmap, gweights, wget, imtls):
    """
    :returns: mean hazard rates as an array of shape (N, M, L1)
    """
    L1 = imtls.size // len(imtls)
    N = len(rmap.array)
    M = len(imtls)
    if len(gweights.shape) == 1:  # fast_mean
        return (rmap.array @ gweights).reshape(N, M, L1)
    rates = numpy.zeros((N, M, L1))
    for m, imt in enumerate(imtls):
        rates[:, m, :] = rmap.array[:, imtls(imt), :] @ wget(gweights, imt)
    return rates


# useful for debugging
def calc_mcurves(src_groups, sitecol, full_lt, oq):
    """
    Compute the mean hazard curves with use_rates. This is less
    efficient than the algorithm used in the engine and can run out
    of memory. It is meant to generate the expected results in small tests.

    :param src_groups: a list of source groups
    :param sitecol: a SiteCollection instance
    :param full_lt: a FullLogicTree instance
    :param oq: an OqParam instance
    :returns: an array of shape (N, M, L1)
    """
    assert oq.use_rates
    rmap, cmakers = get_rmap(src_groups, full_lt, sitecol, oq)
    gweights = numpy.concatenate([cm.wei for cm in cmakers])
    rates = (rmap.array @ gweights).reshape(len(sitecol), len(oq.imtls), -1)
    return to_probs(rates)


# tested in run-demos.sh
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
    rmap, cmakers = get_rmap(csm.src_groups, csm.full_lt, sitecol, oq)
    gws = numpy.concatenate([cm.wei for cm in cmakers])
    rates = calc_mean_rates(rmap, gws, csm.full_lt.gsim_lt.wget, oq.imtls)
    N, _M, L1 = rates.shape
    mrates = numpy.zeros((N, L1), oq.imt_dt())
    for m, imt in enumerate(oq.imtls):
        mrates[imt] = rates[:, m]
    print('Mean hazard rates for the first site')
    print(text_table(mrates[0], ext='org'))


main.job_ini = 'path to a job.ini file'


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    sap.run(main)
