# The Hazard Library
# Copyright (C) 2012-2025 GEM Foundation
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
Module :mod:`openquake.hazardlib.mgmp.nrcan15_site_term` implements
:class:`~openquake.hazardlib.mgmpe.NRCan15SiteTerm`
"""

import copy
import numpy as np
from openquake.hazardlib import const
from openquake.hazardlib.gsim.base import CoeffsTable
from openquake.hazardlib.gsim.base import GMPE, registry
from openquake.hazardlib.gsim.atkinson_boore_2006 import (
    _get_site_amplification_non_linear, _get_site_amplification_linear)
from openquake.baselib.general import CallableDict

BA08_AB06 = CallableDict()


@BA08_AB06.add("base")
def BA08_AB06_base(kind, C, C2, vs30, imt, pgar):
    """
    Computes amplification factor similarly to what is done in the 2015
    version of the Canada building code. An initial version of this code
    was kindly provided by Michal Kolaj - Geological Survey of Canada

    :param vs30:
        Can be either a scalar or a :class:`~numpy.ndarray` instance
    :param imt:
        The intensity measure type
    :param pgar:
        The value of hazard on rock (vs30=760). Can be either a scalar or
        a :class:`~numpy.ndarray` instance. Unit of measure is fractions
        of gravity acceleration.
    :return:
        A scalar or a :class:`~numpy.ndarray` instance with the
        amplification factor.
    """
    fa = np.ones_like(vs30)
    if np.isscalar(vs30):
        vs30 = np.array([vs30])
    if np.isscalar(pgar):
        pgar = np.array([pgar])
    #
    # Fixing vs30 for hard rock to 1999 m/s. Beyond this threshold the
    # motion will not be deamplified further
    vs = copy.copy(vs30)
    vs[vs >= 2000] = 1999.
    #
    # Computing motion on rock
    idx = np.where(vs30 > 760)
    if np.size(idx) > 0:
        """
        # This is the original implementation - Since this code is
        # experimental we keep it for possible further developments
        # For values of Vs30 greater than 760 a linear interpolation is
        # used between the gm factor at 2000 m/s and 760 m/s
        fa[idx] = 10**(np.interp(np.log10(vs[idx]),
                                 np.log10([760.0, 2000.0]),
                                 np.log10([1.0, C2['c']])))
        """
        nl = _get_site_amplification_non_linear(vs[idx], pgar[idx], C)
        lin = _get_site_amplification_linear(vs[idx], C)
        tmp = np.exp(nl+lin)
        fa[idx] = tmp
    #
    # For values of Vs30 lower than 760 the amplification is computed
    # using the site term of Boore and Atkinson (2008)
    idx = np.where(vs < 760.)
    if np.size(idx) > 0:
        nl = _get_site_amplification_non_linear(vs[idx], pgar[idx], C)
        lin = _get_site_amplification_linear(vs[idx], C)
        fa[idx] = np.exp(nl+lin)
    return fa


@BA08_AB06.add("linear")
def BA08_AB06_linear(kind, C, C2, vs30, imt, pgar):
    """
    Computes amplification factor using an approach similar to the one used
    for the 2015 Canada Buiding code. Michal Kolaj's help is acknoledged.

    :param vs30:
        an be either a scalar or a :class:`~numpy.ndarray` instance
    :param imt:
        The intensity measure type
    :param pgar:
        The value of hazard on rock (vs30=760). Can be either a scalar or
        a :class:`~numpy.ndarray` instance. Unit of measure is fractions
        of gravity acceleration.
    :return:
        A scalar or a :class:`~numpy.ndarray` instance with the
        amplification factor.
    """
    fa = np.ones_like(vs30)
    if np.isscalar(vs30):
        vs30 = np.array([vs30])
    if np.isscalar(pgar):
        pgar = np.array([pgar])
    #
    # Fixing vs30 for hard rock to 1999 m/s. Beyond this threshold the
    # motion will not be modified
    vs = copy.copy(vs30)
    vs[vs >= 2000] = 2000.
    #
    # Computing motion on rock
    idx = np.where(vs30 > 760)
    if np.size(idx) > 0:
        fa[idx] = 1. / 10**(np.interp(np.log10(vs[idx]),
                                      np.log10([760.0, 2000.0]),
                                      np.log10([1.0, C2['c']])))
    #
    # For values of Vs30 lower than 760 the amplification is computed
    # using the site term of Boore and Atkinson (2008)
    idx = np.where(vs < 760.)
    if np.size(idx) > 0:
        nl = _get_site_amplification_non_linear(vs[idx], pgar[idx], C)
        lin = _get_site_amplification_linear(vs[idx], C)
        fa[idx] = np.exp(nl+lin)
    return fa


class NRCan15SiteTerm(GMPE):
    """
    Implements a modified GMPE class that can be used to account for local
    soil conditions in the estimation of ground motion.

    :param gmpe_name:
        The name of a GMPE class
    """
    kind = "base"

    # Parameters
    REQUIRES_SITES_PARAMETERS = {'vs30'}
    #: Required distances are set on the underlying gmpe
    REQUIRES_DISTANCES = set()
    REQUIRES_RUPTURE_PARAMETERS = set()
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = ''
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set()
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}
    DEFINED_FOR_TECTONIC_REGION_TYPE = ''
    DEFINED_FOR_REFERENCE_VELOCITY = None

    def __init__(self, gmpe_name, **kwargs):
        self.gmpe = registry[gmpe_name](**kwargs)
        self.set_parameters()

        # Check if this GMPE has the necessary requirements
        if not (hasattr(self.gmpe, 'DEFINED_FOR_REFERENCE_VELOCITY') or
                'vs30' in self.gmpe.REQUIRES_SITES_PARAMETERS):
            msg = '{:s} does not use vs30 nor a defined reference velocity'
            raise AttributeError(msg.format(str(self.gmpe)))
        if 'vs30' not in self.gmpe.REQUIRES_SITES_PARAMETERS:
            self.REQUIRES_SITES_PARAMETERS = frozenset(
                self.gmpe.REQUIRES_SITES_PARAMETERS | {'vs30'})

        # Check compatibility of reference velocity
        if hasattr(self.gmpe, 'DEFINED_FOR_REFERENCE_VELOCITY'):
            ok = 760 <= self.gmpe.DEFINED_FOR_REFERENCE_VELOCITY <= 820
            if not ok:
                name = self.gmpe.__class__.__name__
                raise ValueError(f'{name}.DEFINED_FOR_REFERENCE_VELOCITY '
                                 'is not in the range 760..800')

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        # compute mean and standard deviations on rock
        ctx_rock = copy.copy(ctx)
        ctx_rock.vs30 = np.full_like(ctx.vs30, 760.)
        self.gmpe.compute(ctx_rock, imts, mean, sig, tau, phi)
        for m, imt in enumerate(imts):
            C = self.COEFFS_BA08[imt]
            C2 = self.COEFFS_AB06r[imt]
            fa = BA08_AB06(self.kind, C, C2, ctx.vs30, imt, np.exp(mean[m]))
            mean[m] = np.log(np.exp(mean[m]) * fa)

    COEFFS_AB06r = CoeffsTable(sa_damping=5, table="""\
    IMT  c
    pgv  1.230
    pga  0.891
    0.05 0.891
    0.10 1.072
    0.20 1.318
    0.30 1.380
    0.50 1.380
    1.00 1.288
    2.00 1.230
    5.00 1.148
    10.0 1.072
    """)

    COEFFS_BA08 = CoeffsTable(sa_damping=5, table="""\
    IMT     blin    b1      b2
    pgv    -0.60   -0.50   -0.06
    pga    -0.36   -0.64   -0.14
    0.010  -0.36   -0.64   -0.14
    0.020  -0.34   -0.63   -0.12
    0.030  -0.33   -0.62   -0.11
    0.040  -0.31   -0.61   -0.11
    0.050  -0.29   -0.64   -0.11
    0.060  -0.25   -0.64   -0.11
    0.075  -0.23   -0.64   -0.11
    0.090  -0.23   -0.64   -0.12
    0.100  -0.25   -0.60   -0.13
    0.120  -0.26   -0.56   -0.14
    0.150  -0.28   -0.53   -0.18
    0.170  -0.29   -0.53   -0.19
    0.200  -0.31   -0.52   -0.19
    0.240  -0.38   -0.52   -0.16
    0.250  -0.39   -0.52   -0.16
    0.300  -0.44   -0.52   -0.14
    0.360  -0.48   -0.51   -0.11
    0.400  -0.50   -0.51   -0.10
    0.460  -0.55   -0.50   -0.08
    0.500  -0.60   -0.50   -0.06
    0.600  -0.66   -0.49   -0.03
    0.750  -0.69   -0.47   -0.00
    0.850  -0.69   -0.46   -0.00
    1.000  -0.70   -0.44   -0.00
    1.500  -0.72   -0.40   -0.00
    2.000  -0.73   -0.38   -0.00
    3.000  -0.74   -0.34   -0.00
    4.000  -0.75   -0.31   -0.00
    5.000  -0.75   -0.291  -0.00
    7.500  -0.692  -0.247  -0.00
    10.00  -0.650  -0.215  -0.00
    """)


class NRCan15SiteTermLinear(NRCan15SiteTerm):
    """
    Implements a modified GMPE class that can be used to account for local
    soil conditions in the estimation of ground motion.

    This site term issimilar in structure to the
    :class:`openquake.hazardlib.gsim.mgmpe.NRCan15SiteTerm` in the OQengine
    but uses a different scaling of the motion for values of Vs30 greater
    than 760 m/s.

    This implementation follows what suggested in
    http://www.daveboore.com/pubs_online/ab06_gmpes_programs_and_tables.pdf.

    :param gmpe_name:
        The name of a GMPE class
    """
    kind = "linear"

    COEFFS_AB06r = CoeffsTable(sa_damping=5, table="""\
    IMT  c
    pgv  1.230
    pga  0.891
    0.05 0.891
    0.10 1.072
    0.20 1.318
    0.30 1.380
    0.50 1.380
    1.00 1.288
    2.00 1.230
    5.00 1.148
    10.0 1.072
    """)

    COEFFS_BA08 = CoeffsTable(sa_damping=5, table="""\
    IMT     blin    b1      b2
    pgv    -0.60   -0.50   -0.06
    pga    -0.36   -0.64   -0.14
    0.010  -0.36   -0.64   -0.14
    0.020  -0.34   -0.63   -0.12
    0.030  -0.33   -0.62   -0.11
    0.040  -0.31   -0.61   -0.11
    0.050  -0.29   -0.64   -0.11
    0.060  -0.25   -0.64   -0.11
    0.075  -0.23   -0.64   -0.11
    0.090  -0.23   -0.64   -0.12
    0.100  -0.25   -0.60   -0.13
    0.120  -0.26   -0.56   -0.14
    0.150  -0.28   -0.53   -0.18
    0.170  -0.29   -0.53   -0.19
    0.200  -0.31   -0.52   -0.19
    0.240  -0.38   -0.52   -0.16
    0.250  -0.39   -0.52   -0.16
    0.300  -0.44   -0.52   -0.14
    0.360  -0.48   -0.51   -0.11
    0.400  -0.50   -0.51   -0.10
    0.460  -0.55   -0.50   -0.08
    0.500  -0.60   -0.50   -0.06
    0.600  -0.66   -0.49   -0.03
    0.750  -0.69   -0.47   -0.00
    0.850  -0.69   -0.46   -0.00
    1.000  -0.70   -0.44   -0.00
    1.500  -0.72   -0.40   -0.00
    2.000  -0.73   -0.38   -0.00
    3.000  -0.74   -0.34   -0.00
    4.000  -0.75   -0.31   -0.00
    5.000  -0.75   -0.291  -0.00
    7.500  -0.692  -0.247  -0.00
    10.00  -0.650  -0.215  -0.00
    """)
