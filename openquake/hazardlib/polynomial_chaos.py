# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2019 GEM Foundation
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
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import numpy
from scipy.stats import norm
from scipy.constants import pi


def get_hermite(sg):
    """
    :param vals:
    :param coeff:
    :param degree:
    :param partial:
    """
    deg = []
    deg.append(numpy.ones((len(sg))))
    deg.append(sg)
    deg.append(sg**2 - 1)
    deg.append(sg**3 - 3*sg)
    deg.append(sg**4 - 6*sg**2 + 3)
    deg.append(sg**5 - 10*sg**3 + 15*sg)
    deg.append(sg**6 - 15*sg**4 + 45*sg**2 - 15)
    return numpy.array(deg)


def get_coeff(m_mu, sigma, sigma_mu, imls):
    """
    Compute the PCE coefficients for a given 'scenario' as described in
    Lacour and Abrahanson (2019). The input parameters are the mean hazard
    computed using the combined epistemic and aleatory standard deviation,
    the aleatory std, the epistemic std and the intensity measure levels
    considered.

    :param gmvs:
        A :class:`numpy.ndarray` instance containing the ground motion values
    :param sigma:
        A :class:`numpy.ndarray` instance containing the aleatory std
    :param sigma_mu:
        A :class:`numpy.ndarray` instance containing the epistemic std
    :param imls:
        A :class:`numpy.ndarray` instance containing the intensity measure
        levels
    :return:
        A :class:`numpy.ndarray` instance containing the PC coefficients. The
        shape of this array is N x M x K:
            - N is the degree of the PC expansion (typically 6)
            - M is the
            - K is the number of IMLs
    """

    # sigma_mu is the epistemic std
    # sigma is the total aleatory std
    assert sigma.shape == sigma_mu.shape

    az = -1*sigma_mu**2/(2*sigma**2)-0.5
    bz = (numpy.log(imls) - m_mu) * sigma_mu / sigma**2
    cz = -1*(numpy.log(imls) - m_mu)**2 / (2*sigma**2)
    alpha = sigma_mu/(2*sigma*numpy.sqrt(pi))*numpy.exp(cz-bz**2/(4*az))
    #
    coeff = []
    # c1
    coeff.append(alpha / ((-az)**(0.5)))
    # c2
    coeff.append(alpha/2 * bz/(2*(-az)**1.5))
    # c3
    num = -2*az*(1+2*az)+bz**2
    den = 4*(-az)**2.5
    coeff.append(alpha/6 * num / den)
    # c4
    num = -bz * (6*az*(1+2*az) - bz**2)
    den = 8 * (-az)**3.5
    coeff.append(alpha/24 * num / den)
    # c5
    num = 12*az**2*(1 + 2*az)**2 - 12*az*(1 + 2*az)*bz**2 + bz**4
    den = 16*(-az)**4.5
    coeff.append(alpha/120 * num / den)
    # c6
    num = bz*(60*az**2*(1+2*az))**2-20*az*(1+2*az)*bz**2+bz**4
    den = 32*(-az)**5.5
    coeff.append(alpha/720 * num / den)

    return numpy.array(coeff)
