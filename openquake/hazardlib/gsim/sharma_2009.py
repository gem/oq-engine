# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2019 GEM Foundation
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
:mod:`openquake.hazardlib.gsim.sharma_2009`
exports
:class:`SharmaEtAl2009`
"""
import warnings
import numpy as np
from scipy.constants import g

from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, SA
from openquake.hazardlib.gsim.base import GMPE, CoeffsTable


class SharmaEtAl2009(GMPE):
    # pylint: disable=no-init
    """
    Implements GMPE of Sharma et al. (2009). This GMPE is intended for the
    Indian Himalayas but is based on data from both Zagros in Iran and the
    Himalayas. The combination of these two regions is motivated by the
    sparsity of near field data. Seismotectonic similarity is supposed
    based on both regions being continental collision zones, and in spite
    of the lack of subduction in Zagros.

    Note that Figure 7-9 of Sharma et al. (2009) are in error (Sharma,
    personal communication). This implementation is verified against test
    vector obtained from lead author.

    Support for PGA has been added by assuming it to be equal to the spectral
    acceleration at 0.04 s. This is assumed by the authors in the captions for
    Figures 11-13 anyway.

    Reference:

    Sharma, M. L., Douglas, J., Bungum, H., and Kotadia, J. (2009).
    Ground-motion prediction equations based on data from the Himalayan and
    Zagros regions. *Journal of Earthquake Engineering*, 13(8):1191–1210.
    """

    #: Supported tectonic region type is 'active shallow crust'
    #: however as inndicated the introduction  the tectonics of the
    #: Himalayas have a "great range of focal depths" (Sharma et
    #: al., 2009, p. 1192).
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Set of :mod:`intensity measure types <openquake.hazardlib.imt>`
    #: this GSIM can calculate. A set should contain classes from module
    #: :mod:`openquake.hazardlib.imt`.
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([PGA, SA])

    #: Supported intensity measure component is the geometric mean of two
    #: horizontal components
    #: :attr:`~openquake.hazardlib.const.IMC.AVERAGE_HORIZONTAL`,
    #: see p. 1200.
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.AVERAGE_HORIZONTAL

    #: Only total standard deviation is supported, see Table 2, p. 1202.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([const.StdDev.TOTAL])

    #: Required site parameter Vs30 is used to set binary rock/soil
    #: classification dummy variable, see equation (1) on p. 1200.
    REQUIRES_SITES_PARAMETERS = set(('vs30',))

    #: Required rupture parameters are magnitude and rake, see
    #: equation (1) on p. 1200. Rake is used to distinguish between
    #: reverse and strike-slip faulting, and to detect mis-application
    #: of GMPE to normal faulting.
    REQUIRES_RUPTURE_PARAMETERS = set(('rake', 'mag'))

    #: Required distance measure is Joyner-Boore distance, see p. 1200
    REQUIRES_DISTANCES = set(('rjb',))

    ALREADY_WARNED = False  # warn the first time only

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        # pylint: disable=too-many-arguments
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for specification of input and result values.
        """

        # extract dictionary of coefficients specific to required
        # intensity measure type
        coeffs = self.COEFFS[imt]
        coeffs.update(self.CONSTS)

        # equation (1) is in terms of common logarithm
        log_mean = (self._compute_magnitude(rup, coeffs) +
                    self._compute_distance(dists, coeffs) +
                    self._get_site_amplification(sites, coeffs) +
                    self._get_mechanism(rup, coeffs))
        # so convert to g and thence to the natural logarithm
        mean = log_mean*np.log(10.0) - np.log(g)

        # convert standard deviations from common to natural logarithm
        log_stddevs = self._get_stddevs(coeffs, stddev_types, len(sites.vs30))
        stddevs = log_stddevs*np.log(10.0)

        return mean, stddevs

    def _get_stddevs(self, coeffs, stddev_types, num_sites):
        """
        Return total sigma as reported in Table 2, p. 1202.
        """
        stddevs = []
        for stddev_type in stddev_types:
            assert stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
            stddevs.append(coeffs['sigma'] + np.zeros(num_sites))
        return np.array(stddevs)

    @classmethod
    def _compute_magnitude(cls, rup, coeffs):
        """
        Compute first two terms of equation (1) on p. 1200:

        ``b1 + b2 * M``
        """
        return coeffs['b1'] + coeffs['b2']*rup.mag

    @classmethod
    def _compute_distance(cls, dists, coeffs):
        """
        Compute third term of equation (1) on p. 1200:

        ``b3 * log(sqrt(Rjb ** 2 + b4 ** 2))``
        """
        return coeffs['b3']*np.log10(np.sqrt(dists.rjb**2. + coeffs['b4']**2.))

    def _get_site_amplification(self, sites, coeffs):
        """
        Compute fourth term of equation (1) on p. 1200:

        ``b5 * S``
        """
        is_rock = self.get_site_type_dummy_variables(sites)
        return coeffs['b5']*is_rock

    def _get_mechanism(self, rup, coeffs):
        """
        Compute fifth term of equation (1) on p. 1200:

        ``b6 * H``
        """
        is_strike_slip = self.get_fault_type_dummy_variables(rup)
        return coeffs['b6']*is_strike_slip

    def get_site_type_dummy_variables(self, sites):
        """
        Binary rock/soil classification dummy variable based on sites.vs30.

        "``S`` is 1 for a rock site and 0 otherwise" (p. 1201).
        """
        is_rock = np.array(sites.vs30 > self.NEHRP_BC_BOUNDARY)
        return is_rock

    def get_fault_type_dummy_variables(self, rup):
        """
        Fault-type classification dummy variable based on rup.rake.

        "``H`` is 1 for a strike-slip mechanism and 0 for a reverse mechanism"
        (p. 1201).

        Note:
            UserWarning is raised if mechanism is determined to be normal
            faulting, since as summarized in Table 2 on p. 1197 the data used
            for regression included only reverse and stike-slip events.
        """

        # normal faulting
        is_normal = np.array(
            self.RAKE_THRESH < -rup.rake < (180. - self.RAKE_THRESH))

        # reverse raulting
        is_reverse = np.array(
            self.RAKE_THRESH < rup.rake < (180. - self.RAKE_THRESH))

        if not self.ALREADY_WARNED and is_normal.any():
            # make sure that the warning is printed only once to avoid
            # flooding the terminal
            msg = ('Normal faulting not supported by %s; '
                   'treating as strike-slip' % type(self).__name__)
            warnings.warn(msg, UserWarning)
            self.ALREADY_WARNED = True

        is_strike_slip = ~is_reverse | is_normal
        is_strike_slip = is_strike_slip.astype(float)

        return is_strike_slip

    #: Coefficients taken from Table 2, p. 1202. Note that "In
    #: this article, only the coefficients for a subset of these
    #: periods [between 0.04 and 2.5 s] are reported" and the damping
    #: is 5% (Sharma et al., 2009, p. 1200).
    COEFFS = CoeffsTable(sa_damping=5., table="""\
     IMT      b1      b2      b3      b5      b6   sigma
     pga  1.0170  0.1046 -1.0070 -0.0735 -0.3068  0.3227
    0.04  1.0170  0.1046 -1.0070 -0.0735 -0.3068  0.3227
    0.05  1.0280  0.1245 -1.0550 -0.0775 -0.3246  0.3350
    0.10  1.3820  0.1041 -1.0620 -0.1358 -0.3326  0.3427
    0.20  1.3820  0.1041 -1.0620 -0.1358 -0.3326  0.3596
    0.30  1.3680  0.0684 -0.9139 -0.0972 -0.3011  0.3651
    0.40  0.9747  0.1009 -0.8886 -0.0552 -0.2639  0.3613
    0.50  0.5295  0.1513 -0.8601 -0.0693 -0.2533  0.3654
    0.75 -0.5790  0.3147 -0.9064 -0.0111 -0.2394  0.3770
    1.00 -1.6120  0.4673 -0.9278 -0.0203 -0.2355  0.3949
    1.25 -1.7160  0.4763 -0.9482 -0.0200 -0.2921  0.4190
    1.50 -2.1380  0.5222 -0.9333  0.0284 -0.3197  0.4251
    2.00 -2.6900  0.5707 -0.9082  0.0400 -0.2770  0.4077
    2.50 -2.9420  0.5671 -0.8270  0.0054 -0.2710  0.3959
    """)

    #: "After trials with different values b4 was fixed to be 15km for
    #: all periods." (Sharma et al., 2009, p. 1201)
    CONSTS = {
        'b4': 15.0
    }

    #: Sharma et al. (2009) does not use VS30 so no threshhold is given.
    #: A value of 760 m/s was selected. This is consistent with
    #: :mod:`openquake.hazardlib.gsim.atkinson_boore_2003`,
    #: corresponds to NEHRP class A/B, and is close to the
    #: threshhold for Eurocode 8 Class 8 (800 m/s).
    NEHRP_BC_BOUNDARY = 760.

    #: Rake threshhold of 30 degrees was selected, same as
    #: :mod:`openquake.hazardlib.gsim.boore_atkinson_2008` and
    #: :mod:`openquake.hazardlib.gsim.campbell_bozorgnia_2008`.
    #: Contrast with 45 degree threshhold used by 30 degree
    #: threshhold used in :mod:`openquake.hazardlib.gsim.zhao_2006`.
    RAKE_THRESH = 30.
