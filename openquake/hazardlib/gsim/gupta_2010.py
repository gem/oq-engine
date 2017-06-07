# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2017 GEM Foundation
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
Module
:mod:`openquake.hazardlib.gsim.gupta_2010`
exports
:class:`Gupta2010SSlab`
"""

from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, SA
from openquake.hazardlib.gsim.base import CoeffsTable
from openquake.hazardlib.gsim.atkinson_boore_2003 \
    import AtkinsonBoore2003SSlab


class Gupta2010SSlab(AtkinsonBoore2003SSlab):
    # pylint: disable=too-few-public-methods
    """
    Implements GMPE of Gupta (2010) for Indo-Burmese intraslab subduction.

    This model is closely related to the model of Atkinson & Boore (2003).
    In particular the functional form and coefficients ``C2``-``C7`` of
    Gupta (2010) are adopted from Atkinson & Boore (2003). The only
    substantive changes are a) the horizontal component modeled is different
    (as noted below) b) a coefficient ``C8`` and a dummy variable ``v``
    are added to model vertical motion and c) the coefficient ``C1`` is
    recalculated based on a database of "a total of 56 three-component
    accelerograms at 37 different sites from three in-slab earthquakes
    along the Indo-Burmese subduction zone" (p 370).

    Equation (2) p. 373 gives the form of the equation which was fitted:

    ``log Y - C2*M - C3*h - C4*R + g log R = C1 + C8*v + sigma``

    The left-hand side of this equation was computed using event parameters
    and the coefficients of Atkinson & Boore (2003).  The regression
    coefficients C1 and C8 on the right-hand side were slightly smoothed
    after fitting. Note that since "v=0 for horizontal and 1 for vertical
    motion", and since the current implementation only models horizontal
    motion, we can subclass directly from
    :class:`openquake.hazardlib.gsim.atkinson_boore_2003.AtkinsonBoore2003SSlab`,
    modifying only the metadata constants and regression coefficients.

    Page number citations in this documentation refer to Gupta (2010).

    **References**

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
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([PGA, SA])

    #: Unlike Atkinson & Boore (2003), "rather than the random horizontal
    #: component, the geometric mean of both the horizontal components has
    #: been used in the modified attenuation relations." (p. 376)
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.MEDIAN_HORIZONTAL

    #: Since the database is small only the total standard deviation is
    #: reported.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([const.StdDev.TOTAL])

    #: Coefficients taken from Table 3, p. 884. The row for 0.02 was
    #: relabeled PGA since the paper indicates this is what it actually is
    #: (see p. 371) and since these were the coefficients for PGA in
    #: Atkinson & Boore (2003).
    COEFFS_SSLAB = CoeffsTable(sa_damping=5., table="""\
      IMT      c1       c2       c3       c4    c5    c6    c7      c8  sigma
      pga  0.4598  0.69090  0.01130 -0.00202  0.19  0.24  0.29 -0.3312  0.347
     0.04  0.7382  0.63273  0.01275 -0.00234  0.15  0.20  0.20 -0.3090  0.343
     0.10  1.0081  0.66675  0.01080 -0.00219  0.15  0.23  0.20 -0.3005  0.341
     0.20  1.2227  0.69186  0.00572 -0.00192  0.15  0.27  0.25 -0.4001  0.340
     0.40  0.8798  0.77270  0.00173 -0.00178  0.13  0.37  0.38 -0.4408  0.341
     1.00 -0.3339  0.87890  0.00130 -0.00173  0.10  0.30  0.55 -0.3380  0.344
     2.00 -2.0677  0.99640  0.00364 -0.00118  0.10  0.25  0.40 -0.2674  0.347
     3.00 -3.4227  1.11690  0.00615 -0.00045  0.10  0.25  0.36 -0.3942  0.351
    """)

    #: Mean value data obtained from author matched well at 1 s and below but
    #: not at longer periods. As a temporary measure the reference test result
    #: has been generated from the current implementation.
    non_verified = True
