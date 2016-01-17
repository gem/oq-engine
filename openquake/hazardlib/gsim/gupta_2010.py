# -*- coding: utf-8 -*-
# The Hazard Library
# Copyright (C) 2012-2014, GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Module
:mod:`openquake.hazardlib.gsim.gupta_2010`
exports
:class:`Gupta2010SSlab`
"""
# :class:`Gupta2010SSlabNortheastJapan`

from __future__ import division
import warnings
import numpy as np
from scipy.constants import g
from openquake.hazardlib import const, imt
from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib.gsim.atkinson_boore_2003 \
    import AtkinsonBoore2003SSlab

class Gupta2010SSlab(GMPE):
    # pylint: disable=too-few-public-methods
    """
    Implements GMPE of Gupta (2010) for Indo-Burmese intraslab subduction.

    This model is closely related to the model of Atkinson & Boore (2003).
    In particular the functional form and coefficients ``C2``-``C7`` of
    Gupta (2010) are the same as Atkinson & Boore (2003). The only
    substantive changes are a) the horizontal component modeled is different
    (as noted below) b) a coefficient ``C8`` and a dummy variable ``v``
    are added to model vertical motion and c) the coefficient ``C1`` is
    recalculated based on a database of "a total of 56 three-component
    accelerograms at 37 different sites from three in-slab earthquakes
    along the Indo-Burmese subduction zone" (p 370).

    Page number citations in this documentation refer to Gupta (2010).

    References
    ----------

    Gupta, I. (2010). Response spectral attenuation relations for in-slab
    earthquakes in Indo-Burmese subduction zone. *Soil Dyn. Earthq. Eng.*,
    30(5):368–377.

    Atkinson, G. M. and Boore, D. M. (2003). Empirical ground-motion relations
    for subduction-zone earthquakes and their application to Cascadia and other
    regions. *Bull. Seism. Soc. Am.*, 93(4):1703–1729.
    """

    #: As stated in the title.
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTRASLAB

    #: "The actual peak ground acceleration (PGA) from the corrected time
    #: histories are taken as the response spectral amplitudes at a period of
    #: 0.02 s (50 Hz frequency)." p. 371. Based on this comment, the
    #: coefficients labeled as being for 0.02 s have been relabeld as PGA.
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([imt.PGA, imt.SA])

    #: Unlike Atkinson & Boore (2003), "rather than the random horizontal
    #: component, the geometric mean of both the horizontal components has
    #: been used in the modified attenuation relations." (p. 376)
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.MEDIAN_HORIZONTAL

    #: Since the database is small only the total standard deviation is
    #: reported.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([const.StdDev.TOTAL])

    #: "Coefficients p and q were derived by regression analysis on the
    #: residuals averaged at intervals of every 100 m/sec in AVS30." (p. 884)
    REQUIRES_SITES_PARAMETERS = set(('vs30',))

    #: Sole required rupture parameter is magnitude; faulting style is not
    #: addressed.
    REQUIRES_RUPTURE_PARAMETERS = set(('mag',))

    #: "The source distance is the closest distance from a fault plane to the
    #: observation site and is the hypocentral distance in the case of
    #: earthquakes for which the fault model is not available." (p. 880)
    REQUIRES_DISTANCES = set(('rrup',))

    def get_mean_and_stddevs(self, sites, rup, dists, im_type, stddev_types):
        # pylint: disable=too-many-arguments
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for specification of input and result values.

        Implements the following equations:

        Equation (2) predicts spectral accelerations (slightly rearranged from
        p. 373):

        ``log Y  = C1 + C2*M + C3*h + C4*R + g log R + C8*v + sigma``

        "where Y is the predicted PGA (cm/sec^2), PGV (cm/sec), or 5%
        damped response spectral acceleration (cm/sec^2)" (p. 883) and a,
        b, c and d are tabulated regression coefficients. Note that
        subscripts on the regression coeffients have been dropped -
        subscript `1` denoted "shallow" while subscript `2` denoted "deep"
        - so that the "deep" model of equation (6) can be implemented trivally
        by changing coefficients and setting d = 0.

        Equation (8) on p. 883 gives the model used for site amplitfication:

        ``G = p*log(VS30) + q``

        Where p and q are tabulated regression coefficients.

        Equation (9) on p. 884 for the ground motion at a given site:

        ``log(pre_G) = log(pre) + G``

        No adjustment of epsilon is made as a function of VS30.

        Note finally that "log represents log_10 in the present study"
        (p. 880).

        """

        assert im_type.__class__ in self.DEFINED_FOR_INTENSITY_MEASURE_TYPES

        # obtain coefficients for required intensity measure type (IMT)
        coeffs = self.COEFFS_BASE[im_type].copy()
        coeffs.update(self.COEFFS_SITE[im_type])

        # obtain IMT-independent coefficients
        coeffs.update(self.CONSTS)

        # raise warning outside applicable range
        is_valid = ~((dists.rrup < coeffs['R_valid']) &
                     (rup.mag > coeffs['M_valid']))
        if not is_valid.all():
            warnings.warn('%s used outside applicable range for M=%g at %g km'
                          % (self.__class__.__name__,
                             rup.mag, dists.rrup[is_valid][0]))

        # compute bedrock motion, equation (5)
        log_mean = self._compute_mag_dist_terms(rup, dists, coeffs)

        # make site corrections, equation (9)
        log_mean += self._compute_site_amplification(sites, coeffs)

        # retrieve standard deviations
        log_stddevs = self._get_stddevs(coeffs, stddev_types)

        # convert from common to natural logarithm
        ln_mean = log_mean*np.log(10)
        ln_stddevs = log_stddevs*np.log(10)

        # convert accelerations from cm/s^2 to g
        if im_type.__class__.__name__ != 'PGV':
            ln_mean -= np.log(100*g)

        return ln_mean, [ln_stddevs]

    def _compute_mag_dist_terms(self, rup, dists, coeffs):
        # pylint: disable=no-self-use
        """
        Compute equation (5) and implcitly equation (6):

        ``log(pre) = c + a*M + b*X - log(X + d*10^(e*M)) + epsilon``
        """

        log_pre = coeffs['c'] + coeffs['a']*rup.mag + coeffs['b']*dists.rrup \
            - np.log10(dists.rrup + coeffs['d']*10**(coeffs['e']*rup.mag))

        return log_pre

    def _compute_site_amplification(self, sites, coeffs):
        # pylint: disable=no-self-use
        """
        Compute equation (8):

        ``G = p*log(VS30) + q``
        """

        return coeffs['p']*np.log10(sites.vs30) + coeffs['q']

    def _get_stddevs(self, coeffs, stddev_types):
        """
        Equation (11) on p. 207 for total standard error at a given site:

        ``σ{ln(ε_site)} = sqrt(σ{ln(ε_br)}**2 + σ{ln(δ_site)}**2)``
        """
        for stddev_type in stddev_types:
            assert stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES

        return coeffs['epsilon']

    COEFFS_SSLAB = CoeffsTable(sa_damping=5., table="""\
      IMT      C1       C2       C3       C4    C5    C6    C7      C8  sigma
     0.02  0.4598  0.69090  0.01130 -0.00202  0.19  0.24  0.29 -0.3312  0.347
     0.04  0.7382  0.63273  0.01275 -0.00234  0.15  0.20  0.20 -0.3090  0.343
     0.10  1.0081  0.66675  0.01080 -0.00219  0.15  0.23  0.20 -0.3005  0.341
     0.20  1.2227  0.69186  0.00572 -0.00192  0.15  0.27  0.25 -0.4001  0.340
     0.40  0.8798  0.77270  0.00173 -0.00178  0.13  0.37  0.38 -0.4408  0.341
     1.00 -0.3339  0.87890  0.00130 -0.00173  0.10  0.30  0.55 -0.3380  0.344
     2.00 -2.0677  0.99640  0.00364 -0.00118  0.10  0.25  0.40 -0.2674  0.347
     3.00 -3.4227  1.11690  0.00615 -0.00045  0.10  0.25  0.36 -0.3942  0.351
    """)

    #:
    CONSTS = {
    }
