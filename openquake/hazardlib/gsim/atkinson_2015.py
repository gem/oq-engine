# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2025 GEM Foundation
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

"""
Module exports :class:'Atkinson2015'
               :class:`Atkinson2015AltDistSat`
"""
import numpy as np
from scipy.constants import g

from openquake.baselib.general import CallableDict
from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, PGV, SA


def _get_magnitude_term(C, mag):
    """
    Returns the magnitude scaling term
    """
    return C["c0"] + C["c1"] * mag + C["c2"] * mag ** 2.0


def _get_distance_term(C, rhypo, mag, rsat):
    """
    Returns the distance scaling term including the apparent anelastic
    attenuation term (C4 * R)
    """
    h_eff = get_effective_depth(rsat, mag)
    r_val = np.sqrt(rhypo ** 2.0 + h_eff ** 2.0)
    return C["c3"] * np.log10(r_val) + C["c4"] * r_val


get_effective_depth = CallableDict()


@get_effective_depth.add('default')
def _get_effective_depth(rsat, mag):
    """
    Returns the effective distance term in equation 3. This may be
    overwritten in sub-classes
    """
    h_eff = 10.0 ** (-1.72 + 0.43 * mag)
    return np.where(h_eff > 1.0, h_eff, 1.0)


@get_effective_depth.add('alternative')
def _get_effective_depth_alt(rsat, mag):
    """
    Alternative effective distance term provided in Atkinson (2015) (page 986)
    for use of stronger distance-saturation effects than within default model
    """
    h_eff = 10.0 ** (-0.28 + 0.19 * mag)
    return np.where(h_eff > 1.0, h_eff, 1.0)


def _get_stddevs(C):
    """
    Return standard deviations, converting from log10 to log
    """
    return [np.log(10.0 ** C["sigma"]),
            np.log(10.0 ** C["tau"]),
            np.log(10.0 ** C["phi"])]


class Atkinson2015(GMPE):
    """
    Implements the Induced Seismicity GMPE of Atkinson (2015)
    Atkinson, G. A. (2015) Ground-Motion Prediction Equation for Small-to-
    Moderate Events at Short Hypocentral Distances, with Application to
    Induced-Seismicity Hazards. Bulletin of the Seismological Society of
    America. 105(2).
    """
    #: The GMPE is derived from induced earthquakes
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.INDUCED

    #: Supported intensity measure types are peak ground acceleration
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, PGV, SA}

    #: Supported intensity measure component is the larger of two components
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.RotD50

    #: Supported standard deviation types is total.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL, const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT}

    #: No required site parameters, the GMPE is derived for B/C site
    #: amplification factors
    REQUIRES_SITES_PARAMETERS = set()

    #: Required rupture parameters are magnitude
    REQUIRES_RUPTURE_PARAMETERS = {'mag'}

    #: Required distance measure is hypocentral distance
    REQUIRES_DISTANCES = {'rhypo'}

    # Default distance-saturation scaling
    rsat = 'default'    

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        rsat = self.rsat
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            imean = (_get_magnitude_term(C, ctx.mag) +
                     _get_distance_term(C, ctx.rhypo, ctx.mag, rsat))
            # Convert mean from cm/s and cm/s/s
            if imt.string.startswith(('PGA', 'SA')):
                mean[m] = np.log((10.0 ** (imean - 2.0)) / g)
            else:
                mean[m] = np.log(10.0 ** imean)
            sig[m], tau[m], phi[m] = _get_stddevs(C)

    COEFFS = CoeffsTable(sa_damping=5, table="""
    IMT         c0      c1         c2      c3         c4    phi    tau    sigma
    pgv     -4.151   1.762  -0.09509   -1.669   -0.00060   0.27   0.19     0.33
    pga     -2.376   1.818  -0.1153    -1.752   -0.00200   0.28   0.24     0.37
    0.0300  -2.283   1.842  -0.1189    -1.785   -0.00200   0.28   0.27     0.39
    0.0500  -2.018   1.826  -0.1192    -1.831   -0.00200   0.28   0.30     0.41
    0.1000  -1.954   1.830  -0.1185    -1.774   -0.00200   0.29   0.25     0.39
    0.2000  -2.266   1.785  -0.1061    -1.657   -0.00140   0.30   0.21     0.37
    0.3000  -2.794   1.852  -0.1078    -1.608   -0.00100   0.30   0.19     0.36
    0.5000  -3.873   2.060  -0.1212    -1.544   -0.00060   0.29   0.20     0.35
    1.0000  -4.081   1.742  -0.07381   -1.481    0.00000   0.26   0.22     0.34
    2.0000  -4.462   1.485  -0.03815   -1.361    0.00000   0.24   0.23     0.33
    3.0000  -3.827   1.060   0.009086  -1.398    0.00000   0.24   0.22     0.32
    5.0000  -4.321   1.080   0.009376  -1.378    0.00000   0.25   0.18     0.31
    """)


class Atkinson2015AltDistSat(Atkinson2015):
    """
    This class implements the alternative effective depth term provided on
    page 986 of Atkinson (2015) for the use of stronger distance-saturation
    effects than implemented within the default model.
    
    It should be noted that this class uses the coefficients obtained using the
    Yenier and Atkinson (2014) effective depth term i.e. those used within the
    base gsim class too, with modification only to the effective depth term
    """
    # Alternative (stronger) distance-saturation scaling
    rsat = 'alternative'