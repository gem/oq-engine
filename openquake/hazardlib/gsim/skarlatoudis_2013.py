# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2019 GEM Foundation
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
Module exports :class:`SkarlatoudisEtAlSSlab2013`.
"""
import numpy as np
from scipy.constants import g

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, PGV, SA


class SkarlatoudisEtAlSSlab2013(GMPE):
    """
    Implements GMPEs developed by A.A.Skarlatoudis, C.B.Papazachos,
    B.N.Margaris, C.Ventouzi, I.Kalogeras and EGELADOS group published as
    "Ground-Motion Prediction Equations of Intermediate-Depth Earthquakes in
    the Hellenic Arc, Southern Aegean Subduction Area“,
    Bull Seism Soc Am, DOI 10.1785/0120120265
    SA are given up to 4 s.
    The regressions are developed considering the RotD50 (Boore, 2010) of the
    as-recorded horizontal components
    """
    #: Supported tectonic region type is ‘subduction intraslab’ because the
    #: equations have been derived from data from Hellenic Arc events, as
    #: explained in the 'Introduction'.
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTRASLAB

    #: Set of :mod:`intensity measure types <openquake.hazardlib.imt>`
    #: this GSIM can calculate. A set should contain classes from module
    #: :mod:`openquake.hazardlib.imt`.
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([
        PGA,
        PGV,
        SA
    ])

    #: Supported intensity measure component is the RotD50 of two
    #: horizontal components
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.RotD50

    #: Supported standard deviation types are inter-event, intra-event
    #: and total, page 1961
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL,
        const.StdDev.INTER_EVENT,
        const.StdDev.INTRA_EVENT
    ])

    #: Required site parameter is Vs30 and  backarc flag
    REQUIRES_SITES_PARAMETERS = set(('vs30', 'backarc'))

    #: Required rupture parameters are magnitude and hypocentral depth
    REQUIRES_RUPTURE_PARAMETERS = set(('mag', 'hypo_depth'))

    #: Required distance measure is Rhypo.
    REQUIRES_DISTANCES = set(('rhypo', ))

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        # extracting dictionary of coefficients specific to required
        # intensity measure type.

        C = self.COEFFS[imt]
        imean = (self._compute_magnitude(rup, C) +
                 self._compute_distance(rup, dists, C) +
                 self._get_site_amplification(sites, C) +
                 self._compute_forearc_backarc_term(C, sites, dists, rup))

        istddevs = self._get_stddevs(C,
                                     stddev_types,
                                     num_sites=len(sites.vs30))

        # Convert units to g,
        # but only for PGA and SA (not PGV):
        if imt.name in "SA PGA":
            mean = np.log((10.0 ** (imean - 2.0)) / g)
        else:
            # PGV:
            mean = np.log(10.0 ** imean)
        # Return stddevs in terms of natural log scaling
        stddevs = np.log(10.0 ** np.array(istddevs))
        # mean_LogNaturale = np.log((10 ** mean) * 1e-2 / g)
        return mean, stddevs

    def _get_stddevs(self, C, stddev_types, num_sites):
        """
        Return standard deviations as defined in table 1.
        """
        stddevs = []
        for stddev_type in stddev_types:
            assert stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
            if stddev_type == const.StdDev.TOTAL:
                stddevs.append(C['epsilon'] + np.zeros(num_sites))
            elif stddev_type == const.StdDev.INTRA_EVENT:
                stddevs.append(C['sigma'] + np.zeros(num_sites))
            elif stddev_type == const.StdDev.INTER_EVENT:
                stddevs.append(C['tau'] + np.zeros(num_sites))
        return stddevs

    def _compute_distance(self, rup, dists, C):
        """
        equation 3 pag 1960:

        ``c31 * logR + c32 * (R-Rref)``
        """
        rref = 1.0
        c31 = -1.7
        return (c31 * np.log10(dists.rhypo) + C['c32'] * (dists.rhypo - rref))

    def _compute_magnitude(self, rup, C):
        """
        equation 3 pag 1960:

        c1 + c2(M-5.5)
        """
        m_h = 5.5
        return C['c1'] + (C['c2'] * (rup.mag - m_h))

    def _get_site_amplification(self, sites, C):
        """
        Compute the fourth term of the equation 3:
        The functional form Fs in Eq. (1) represents the site amplification and
        it is given by FS = c61*S + c62*SS , where c61 and c62 are the
        coefficients to be determined through the regression analysis,
        while S and SS are dummy variables used to denote NEHRP site category
        C and D respectively
        Coefficents for categories A and B are set to zero
        """
        S, SS = self._get_site_type_dummy_variables(sites)

        return (C['c61'] * S) + (C['c62'] * SS)

    def _get_site_type_dummy_variables(self, sites):
        """
        Get site type dummy variables, three different site classes,
        based on the shear wave velocity intervals in the uppermost 30 m, Vs30,
        according to the NEHRP:
        class A-B: Vs30 > 760 m/s
        class C: Vs30 = 360 − 760 m/s
        class D: Vs30 < 360 m/s

        """
        S = np.zeros(len(sites.vs30))
        SS = np.zeros(len(sites.vs30))

        # Class C; 180 m/s <= Vs30 <= 360 m/s.
        idx = (sites.vs30 < 360.0)
        SS[idx] = 1.0
        # Class B; 360 m/s <= Vs30 <= 760 m/s. (NEHRP)
        idx = (sites.vs30 >= 360.0) & (sites.vs30 < 760)
        S[idx] = 1.0

        return S, SS

    def _compute_forearc_backarc_term(self, C, sites, dists, rup):
        """
        Compute back-arc term of Equation 3

        """
        # flag 1 (R < 335 & R >= 205)
        flag1 = np.zeros(len(dists.rhypo))
        ind1 = np.logical_and((dists.rhypo < 335), (dists.rhypo >= 205))
        flag1[ind1] = 1.0
        # flag 2 (R >= 335)
        flag2 = np.zeros(len(dists.rhypo))
        ind2 = (dists.rhypo >= 335)
        flag2[ind2] = 1.0
        # flag 3 (R < 240 & R >= 140)
        flag3 = np.zeros(len(dists.rhypo))
        ind3 = np.logical_and((dists.rhypo < 240), (dists.rhypo >= 140))
        flag3[ind3] = 1.0
        # flag 4 (R >= 240)
        flag4 = np.zeros(len(dists.rhypo))
        ind4 = (dists.rhypo >= 240)
        flag4[ind4] = 1.0

        A = flag1 * ((205 - dists.rhypo)/150) + flag2
        B = flag3 * ((140 - dists.rhypo)/100) + flag4
        if (rup.hypo_depth < 80):
            FHR = A
        else:
            FHR = B

        H0 = 100
        # Heaviside function
        if (rup.hypo_depth >= H0):
            H = 1
        else:
            H = 0

        # ARC = 0 for back-arc - ARC = 1 for forearc
        ARC = np.zeros(len(sites.backarc))
        idxarc = (sites.backarc == 1)
        ARC[idxarc] = 1.0

        return ((C['c41'] * (1 - ARC) * H) + (C['c42'] * (1 - ARC) * H * FHR) +
                (C['c51'] * ARC * H) + (C['c52'] * ARC * H * FHR))

    #: Coefficients from SA from Table 1
    #: Coefficients from PGA e PGV from Table 5

    COEFFS = CoeffsTable(sa_damping=5, table="""
    IMT         c1       c2         c32       c41       c42      c51      c52      c61      c62    sigma      tau  epsilon   
    pga      4.229    0.877    -0.00206    -0.481    -0.152    0.425    0.303    0.267    0.491    0.352    0.112    0.369
    pgv      2.965    1.069    -0.00178    -0.264     0.018    0.390    0.333    0.408    0.599    0.315    0.144    0.346
    0.010    4.235    0.876    -0.00206    -0.482    -0.153    0.425    0.304    0.265    0.488    0.353    0.111    0.370
    0.025    4.119    0.877    -0.00202    -0.490    -0.140    0.415    0.326    0.301    0.511    0.352    0.103    0.367
    0.050    4.320    0.863    -0.00212    -0.483    -0.178    0.410    0.286    0.245    0.475    0.376    0.095    0.388
    0.100    4.565    0.867    -0.00244    -0.515    -0.185    0.452    0.371    0.234    0.442    0.404    0.066    0.410
    0.200    4.613    0.842    -0.00199    -0.596    -0.221    0.396    0.291    0.289    0.469    0.379    0.154    0.409
    0.400    4.463    0.926    -0.00190    -0.427    -0.110    0.459    0.295    0.298    0.516    0.322    0.141    0.351
    1.000    3.952    1.102    -0.00178    -0.199     0.112    0.316    0.442    0.371    0.512    0.305    0.201    0.365
    2.000    3.281    1.260    -0.00106    -0.136     0.055    0.196    0.352    0.408    0.578    0.277    0.203    0.343
    4.000    2.588    1.384    -0.00039    -0.179    -0.046    0.113    0.189    0.264    0.475    0.278    0.176    0.329
    """)
