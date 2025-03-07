# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2025 GEM Foundation
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
Module exports :class:`TavakoliPezeshk2005`,
:class:`TavakoliPezeshk2005MblgAB1987NSHMP2008`,
:class:`TavakoliPezeshk2005MblgJ1996NSHMP2008`,
:class:`TavakoliPezeshk2005MwNSHMP2008`
"""
import numpy as np

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, SA
from openquake.hazardlib.gsim.utils import (
    mblg_to_mw_atkinson_boore_87,
    mblg_to_mw_johnston_96,
    clip_mean)


def _compute_anelastic_attenuation_term(C, rrup, mag):
    """
    Compute magnitude-distance scaling term as defined in equation 21,
    page 2291 (Tavakoli and Pezeshk, 2005)
    """
    r = (rrup**2. + (C['c5'] * np.exp(C['c6'] * mag +
                                      C['c7'] * (8.5 - mag)**2.5))**2.)**.5
    f3 = ((C['c4'] + C['c13'] * mag) * np.log(r) +
          (C['c8'] + C['c12'] * mag) * r)
    return f3


def _compute_geometrical_spreading_term(C, rrup):
    """
    Compute magnitude scaling term as defined in equation 19, page 2291
    (Tavakoli and Pezeshk, 2005)
    """
    f2 = np.ones_like(rrup)
    idx1 = np.nonzero(rrup <= 70.)
    idx2 = np.nonzero((rrup > 70.) & (rrup <= 130.))
    idx3 = np.nonzero(rrup > 130.)

    f2[idx1] = (C['c9'] * np.log(rrup[idx1] + 4.5))
    f2[idx2] = (C['c10'] * np.log(rrup[idx2]/70.) +
                C['c9'] * np.log(rrup[idx2] + 4.5))
    f2[idx3] = (C['c11'] * np.log(rrup[idx3]/130.) +
                C['c10'] * np.log(rrup[idx3]/70.) +
                C['c9'] * np.log(rrup[idx3] + 4.5))
    return f2


def _compute_magnitude_scaling_term(C, mag):
    """
    Compute magnitude scaling term as defined in equation 19, page 2291
    (Tavakoli and Pezeshk, 2005)
    """
    if (mag > 8.5).any():
        raise ValueError('Magnitude %s > 8.5' % mag)
    return C['c1'] + C['c2'] * mag + C['c3'] * (8.5 - mag) ** 2.5


class TavakoliPezeshk2005(GMPE):
    """
    Implements the GMPE developed by B. Tavakoli and S. Pezeshk in 2005
    and published as "Empirical-Stochastic Ground-Motion Prediction for
    Eastern North America" (2005, Bull. Seism. Soc. Am., Volume 95, No. 6,
    pages 2283-2296).
    """
    #: Supported tectonic region type is stable continental crust
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.STABLE_CONTINENTAL

    #: Supported intensity measure types are peak ground acceleration
    #: and spectral acceleration, see abstract
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, SA}

    #: Supported intensity measure horizontal.
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.HORIZONTAL

    #: Supported standard deviation type is total, see equation 23, pag 2291.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}

    #: This GMPE doesn't require site parameters since it has been developed
    #: for hard rock ctx (see page 2290)
    REQUIRES_SITES_PARAMETERS = set()

    #: Required rupture parameters is magnitude
    #: See equation 18 page page 2291
    REQUIRES_RUPTURE_PARAMETERS = {'mag'}

    #: Required distance measure is Rrup.
    #: See equation 18 page page 2291
    REQUIRES_DISTANCES = {'rrup'}

    kind = 'base'

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]

            if self.kind == 'Mblg':
                mag = mblg_to_mw_johnston_96(ctx.mag)
            elif self.kind == 'Mblg2008':
                mag = mblg_to_mw_atkinson_boore_87(ctx.mag)
            else:
                mag = ctx.mag

            # computing the magnitude term. Equation 19, page 2291
            f1 = _compute_magnitude_scaling_term(C, mag)

            # computing the geometrical spreading term. Equation 20, page 2291
            f2 = _compute_geometrical_spreading_term(C, ctx.rrup)

            # computing the anelastic attenuation term. Equation 21, page 2291
            f3 = _compute_anelastic_attenuation_term(C, ctx.rrup, mag)

            # computing the mean ln(IMT) using equation 18 at page 2290
            mean[m] = f1 + f2 + f3

            if self.kind != 'base':  # in subclasses
                mean[m] = clip_mean(imt, mean[m])

            # computing the total standard deviation
            sig[m] = np.where(mag < 7.2, C['c14'] + C['c15'] * mag, C['c16'])

    #: Coefficient table is constructed from an excel spreadsheet available
    #: on Pezeshk's website http://www.ce.memphis.edu/pezeshk
    COEFFS = CoeffsTable(sa_damping=5, table="""\
    IMT    c1         c2         c3          c4          c5          c6          c7          c8          c9         c10        c11         c12        c13        c14         c15        c16
    pga    1.139E+00  6.228E-01  -4.834E-02  -1.807E+00  -6.516E-01  4.465E-01  -2.933E-05  -4.045E-03   9.456E-03  1.410E+00  -9.611E-01  4.315E-04  1.332E-04  1.205E+00  -1.109E-01  4.091E-01
    0.05   1.823E+00  5.333E-01  -4.748E-02  -1.631E+00  -5.672E-01  4.538E-01   7.771E-03  -4.907E-03  -3.139E-03  9.797E-01  -9.386E-01  5.121E-04  9.301E-04  1.216E+00  -1.080E-01  4.413E-01
    0.08   6.826E-01  7.428E-01  -2.928E-02  -1.715E+00  -7.562E-01  4.601E-01  -9.677E-04  -4.941E-03  -5.500E-03  1.135E+00  -9.156E-01  4.822E-04  7.331E-04  1.224E+00  -1.081E-01  4.494E-01
    0.10   8.692E-01  6.070E-01  -4.736E-02  -1.522E+00  -7.044E-01  4.491E-01  -6.188E-03  -4.702E-03  -4.239E-03  1.039E+00  -9.129E-01  4.108E-04  3.584E-04  1.232E+00  -1.081E-01  4.562E-01
    0.15   2.383E+00  5.009E-01  -6.422E-02  -1.732E+00  -9.763E-01  4.137E-01   6.598E-03  -4.805E-03   3.928E-03  1.506E+00  -8.650E-01  3.642E-04  6.841E-04  1.240E+00  -1.082E-01  4.643E-01
    0.20  -5.476E-01  8.570E-01  -2.622E-02  -1.684E+00  -8.607E-01  4.332E-01   2.786E-03  -3.655E-03  -2.025E-03  1.643E+00  -9.252E-01  1.615E-04  6.434E-04  1.240E+00  -1.082E-01  4.691E-01
    0.30  -5.130E-01  6.673E-01  -4.431E-02  -1.421E+00  -4.695E-01  4.681E-01   1.076E-02  -5.407E-03   6.436E-03  1.519E+00  -9.153E-01  4.324E-04  2.870E-04  1.260E+00  -1.088E-01  4.788E-01
    0.50   2.403E-01  6.106E-01  -7.889E-02  -1.548E+00  -8.438E-01  4.145E-01   7.889E-03  -3.648E-03  -2.654E-04  1.592E+00  -8.586E-01  2.770E-04  1.457E-04  1.275E+00  -1.073E-01  5.051E-01
    0.75  -6.789E-01  6.659E-01  -8.304E-02  -1.481E+00  -7.340E-01  4.347E-01   9.531E-03  -3.374E-03  -1.189E-03  1.546E+00  -7.839E-01  2.454E-04  5.470E-04  1.276E+00  -1.050E-01  5.222E-01
    1.00  -1.550E+00  7.644E-01  -8.585E-02  -1.491E+00  -9.409E-01  4.238E-01  -5.836E-03  -2.088E-03   3.298E-03  1.519E+00  -7.568E-01  1.166E-04  7.589E-04  1.275E+00  -1.029E-01  5.368E-01
    1.50  -2.296E+00  7.941E-01  -8.842E-02  -1.453E+00  -8.860E-01  4.122E-01   8.299E-03  -3.272E-03   2.506E-03  1.706E+00  -7.688E-01  2.329E-04  1.656E-04  1.268E+00  -9.990E-02  5.509E-01
    2.00  -2.704E+00  8.053E-01  -9.294E-02  -1.444E+00  -9.235E-01  4.077E-01   2.062E-02  -2.143E-03   2.301E-03  1.426E+00  -7.551E-01  2.138E-04  3.908E-04  1.264E+00  -9.780E-02  5.617E-01
    3.00  -2.421E+00  8.008E-01  -1.077E-01  -1.648E+00  -8.976E-01  4.368E-01   1.675E-02  -2.033E-03   3.576E-03  1.934E+00  -8.183E-01  1.158E-04  3.983E-04  1.257E+00  -9.520E-02  5.729E-01
    4.00  -3.685E+00  8.166E-01  -1.177E-01  -1.463E+00  -8.448E-01  4.249E-01   1.135E-02  -1.719E-03  -3.345E-03  1.689E+00  -7.374E-01  1.100E-04  3.592E-04  1.254E+00  -9.260E-02  5.893E-01
    """)


class TavakoliPezeshk2005MblgAB1987NSHMP2008(TavakoliPezeshk2005):
    """
    Extend :class:`TavakoliPezeshk2005` and implements equation as defined
    by the National Seismic Hazard Mapping Project (NSHMP) for the 2008
    US model.

    The class replicates the equation as coded in suroutine ``getTP05`` in
    ``hazgridXnga2.f`` Fortran code available at:
    http://earthquake.usgs.gov/hazards/products/conterminous/2008/software/

    The class assumes rupture magnitude to be in Mblg scale. Therefore Mblg
    is converted to Mw using the Atkinson & Boore 1987 conversion equation.

    Coefficients are given for the B/C site conditions.
    """
    kind = 'Mblg2008'

    #: Shear-wave velocity for reference soil conditions in [m s-1]
    DEFINED_FOR_REFERENCE_VELOCITY = 760.

    #: Coefficient table is constructed using the values included in
    #: hazgridXnga2.f
    COEFFS = CoeffsTable(sa_damping=5, table="""\
    IMT        c1         c2        c3         c4         c5         c6        c7         c8         c9         c10       c11        c12       c13       c14       c15        c16
    pga        1.56E+00  6.23E-01  -4.83E-02  -1.81E+00  -6.52E-01  4.46E-01  -2.93E-05  -4.05E-03   9.46E-03  1.41E+00  -9.61E-01  4.32E-04  1.33E-04  1.21E+00  -1.11E-01  4.09E-01
    5.00E-02   2.24E+00  5.33E-01  -4.75E-02  -1.63E+00  -5.67E-01  4.54E-01   7.77E-03  -4.91E-03  -3.14E-03  9.80E-01  -9.39E-01  5.12E-04  9.30E-04  1.22E+00  -1.08E-01  4.41E-01
    8.00E-02   1.10E+00  7.43E-01  -2.93E-02  -1.71E+00  -7.56E-01  4.60E-01  -9.68E-04  -4.94E-03  -5.50E-03  1.13E+00  -9.16E-01  4.82E-04  7.33E-04  1.22E+00  -1.08E-01  4.49E-01
    1.00E-01   1.4229    6.07E-01  -4.74E-02  -1.52E+00  -7.04E-01  4.49E-01  -6.19E-03  -4.70E-03  -4.24E-03  1.04E+00  -9.13E-01  4.11E-04  3.58E-04  1.23E+00  -1.08E-01  4.56E-01
    1.50E-01   2.87E+00  5.01E-01  -6.42E-02  -1.73E+00  -9.76E-01  4.14E-01   6.60E-03  -4.80E-03   3.93E-03  1.51E+00  -8.65E-01  3.64E-04  6.84E-04  1.24E+00  -1.08E-01  4.64E-01
    2.00E-01   1.70E-02  8.57E-01  -2.62E-02  -1.68E+00  -8.61E-01  4.33E-01   2.79E-03  -3.65E-03  -2.02E-03  1.64E+00  -9.25E-01  1.61E-04  6.43E-04  1.24E+00  -1.08E-01  4.69E-01
    3.00E-01   0.491     6.67E-01  -4.43E-02  -1.42E+00  -4.70E-01  4.68E-01   1.08E-02  -5.41E-03   6.44E-03  1.52E+00  -9.15E-01  4.32E-04  2.87E-04  1.26E+00  -1.09E-01  4.79E-01
    5.00E-01   6.97E-01  6.11E-01  -7.89E-02  -1.55E+00  -8.44E-01  4.14E-01   7.89E-03  -3.65E-03  -2.65E-04  1.59E+00  -8.59E-01  2.77E-04  1.46E-04  1.28E+00  -1.07E-01  5.05E-01
    7.50E-01  -3.23E-01  6.66E-01  -8.30E-02  -1.48E+00  -7.34E-01  4.35E-01   9.53E-03  -3.37E-03  -1.19E-03  1.55E+00  -7.84E-01  2.45E-04  5.47E-04  1.28E+00  -1.05E-01  5.22E-01
    1.00E+00  -1.26E+00  7.64E-01  -8.59E-02  -1.49E+00  -9.41E-01  4.24E-01  -5.84E-03  -2.09E-03   3.30E-03  1.52E+00  -7.57E-01  1.17E-04  7.59E-04  1.28E+00  -1.03E-01  5.37E-01
    1.50E+00  -1.94E+00  7.94E-01  -8.84E-02  -1.45E+00  -8.86E-01  4.12E-01   8.30E-03  -3.27E-03   2.51E-03  1.71E+00  -7.69E-01  2.33E-04  1.66E-04  1.27E+00  -9.99E-02  5.51E-01
    2.00E+00  -2.5177    8.05E-01  -9.29E-02  -1.44E+00  -9.23E-01  4.08E-01   2.06E-02  -2.14E-03   2.30E-03  1.43E+00  -7.55E-01  2.14E-04  3.91E-04  1.26E+00  -9.78E-02  5.62E-01
    3.00E+00  -2.28      8.01E-01  -1.08E-01  -1.65E+00  -8.98E-01  4.37E-01   1.67E-02  -2.03E-03   3.58E-03  1.93E+00  -8.18E-01  1.16E-04  3.98E-04  1.26E+00  -9.52E-02  5.73E-01
    4.00E+00  -2.28      8.17E-01  -1.18E-01  -1.46E+00  -8.45E-01  4.25E-01   1.13E-02  -1.72E-03  -3.34E-03  1.69E+00  -7.37E-01  1.10E-04  3.59E-04  1.25E+00  -9.26E-02  5.89E-01
    """)


class TavakoliPezeshk2005MblgJ1996NSHMP2008(
        TavakoliPezeshk2005MblgAB1987NSHMP2008):
    """
    Extend :class:`TavakoliPezeshk2005MblgAB1987NSHMP2008` but uses Johnston
    1996 equation to convert Mblg to Mw
    """
    kind = 'Mblg'


class TavakoliPezeshk2005MwNSHMP2008(TavakoliPezeshk2005MblgAB1987NSHMP2008):
    """
    Extend :class:`TavakoliPezeshk2005MblgAB1987NSHMP2008` but assumes
    magnitude to be in Mw scale, and therefore no conversion is applied
    """
    kind = '2008'
