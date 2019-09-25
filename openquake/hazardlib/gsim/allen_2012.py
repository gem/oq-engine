# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2013-2019 GEM Foundation
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
Module exports :class:`Allen2012`
"""
import numpy as np
from scipy.constants import g

from openquake.hazardlib.gsim.base import CoeffsTable, GMPE
from openquake.hazardlib import const
from openquake.hazardlib.imt import SA, PGA


class Allen2012(GMPE):
    """
    Implements GMPE developed by T. Allen and published as "Stochastic ground-
    motion prediction equations for southeastern Australian earthquakes using
    updated source and attenuation parameters", 2012, Geoscience Australia
    Record 2012/69. Document available at:
    https://www.ga.gov.au/products/servlet/controller?event=GEOCAT_DETAILS&catno=74133
    """

    #: Supported tectonic region type is stable continental crust
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.STABLE_CONTINENTAL

    #: Supported intensity measure types is spectral acceleration, see table 7,
    #: page 35, and PGA (coefficients assumed to be the same of SA(0.01))
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([
        PGA,
        SA
    ])

    #: Supported intensity measure component is the median horizontal component
    #: see table 7, page 35
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.MEDIAN_HORIZONTAL

    #: Supported standard deviation type is only total, see table 7, page 35
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL
    ])

    #: No site parameters are needed, the GMPE is calibrated for average South
    #: East Australia site conditions (assumed consistent to Vs30 = 820 m/s)
    #: see paragraph 'Executive Summary', page VII. (provisionally set to 800
    #: for compatibility with SiteTerm class)
    REQUIRES_SITES_PARAMETERS = set()
    DEFINED_FOR_REFERENCE_VELOCITY = 800.

    #: Required rupture parameters are magnitude and hypocentral depth, see
    #: paragraph 'Regression of Model Coefficients', page 32 and tables 7 and
    #: 8, pages 35, 36
    REQUIRES_RUPTURE_PARAMETERS = set(('mag', 'hypo_depth'))

    #: Required distance measure is closest distance to rupture, see paragraph
    #: 'Regression of Model Coefficients', page 32
    REQUIRES_DISTANCES = set(('rrup', ))

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        assert all(stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
                   for stddev_type in stddev_types)

        if rup.hypo_depth < 10:
            C = self.COEFFS_SHALLOW[imt]
        else:
            C = self.COEFFS_DEEP[imt]

        mean = self._compute_mean(C, rup.mag, dists.rrup)
        stddevs = self._get_stddevs(C, stddev_types, dists.rrup.shape[0])

        return mean, stddevs

    def _compute_mean(self, C, mag, rrup):
        """
        Compute mean value according to equation 18, page 32.
        """
        # see table 3, page 14
        R1 = 90.
        R2 = 150.
        # see equation 19, page 32
        m_ref = mag - 4
        r1 = R1 + C['c8'] * m_ref
        r2 = R2 + C['c11'] * m_ref
        assert r1 > 0
        assert r2 > 0
        g0 = np.log10(
            np.sqrt(np.minimum(rrup, r1) ** 2 + (1 + C['c5'] * m_ref) ** 2)
        )
        g1 = np.maximum(np.log10(rrup / r1), 0)
        g2 = np.maximum(np.log10(rrup / r2), 0)

        mean = (C['c0'] + C['c1'] * m_ref + C['c2'] * m_ref ** 2 +
                (C['c3'] + C['c4'] * m_ref) * g0 +
                (C['c6'] + C['c7'] * m_ref) * g1 +
                (C['c9'] + C['c10'] * m_ref) * g2)

        # convert from log10 to ln and units from cm/s2 to g
        mean = np.log((10 ** mean) * 1e-2 / g)

        return mean

    def _get_stddevs(self, C, stddev_types, num_sites):
        """
        Return total standard deviation.
        """
        # standard deviation is converted from log10 to ln
        std_total = np.log(10 ** C['sigma'])
        stddevs = []
        for _ in stddev_types:
            stddevs.append(np.zeros(num_sites) + std_total)

        return stddevs

    #: Coefficients for shallow events taken from Excel file produced by Trevor
    #: Allen and provided by Geoscience Australia (20120821.GMPE_coeffs.xls)
    #: (coefficients in the original report are not correct)
    COEFFS_SHALLOW = CoeffsTable(sa_damping=5, table="""\
    IMT     c0        c1         c2         c3        c4        c5         c6         c7         c8         c9        c10        c11       sigma
    pga     3.258600  0.505400  -0.069300  -1.838600  0.158000  1.246600  -0.204500  -0.044100  -5.108100  -2.861200  0.252000  -0.691100  0.412000
    0.0100  3.258600  0.505400  -0.069300  -1.838600  0.158000  1.246600  -0.204500  -0.044100  -5.108100  -2.861200  0.252000  -0.691100  0.412000
    0.0200  3.368300  0.496200  -0.062000  -1.807800  0.136300  1.247500  -0.486200   0.016300  -4.701900  -2.863100  0.248200  -0.939300  0.438300
    0.0300  3.510700  0.470500  -0.059900  -1.852300  0.142300  1.433600  -0.544500   0.014800  -4.977800  -2.849200  0.249500  -1.070600  0.431000
    0.0500  3.545000  0.476800  -0.062800  -1.836800  0.140300  1.459500  -0.488900  -0.010600  -5.116200  -3.072400  0.302500  -1.229400  0.399400
    0.0750  3.516000  0.491900  -0.067900  -1.806300  0.142400  1.418400  -0.340700  -0.042800  -4.987400  -3.251800  0.305900  -0.760200  0.380500
    0.1000  3.458400  0.514700  -0.072800  -1.773900  0.142300  1.374600  -0.215200  -0.061100  -4.836000  -3.286000  0.267700  -0.189000  0.372000
    0.1500  3.295600  0.580400  -0.081900  -1.700200  0.131400  1.285500  -0.062700  -0.067200  -4.664000  -3.122100  0.156200   0.632700  0.363700
    0.2000  3.136200  0.641600  -0.091600  -1.647500  0.127200  1.214000   0.071500  -0.080400  -4.682900  -2.934700  0.107400   1.033900  0.359400
    0.2500  2.998000  0.692000  -0.101400  -1.614900  0.130400  1.159500   0.207800  -0.104600  -4.805400  -2.789000  0.113000   1.191100  0.357500
    0.3000  2.872100  0.735800  -0.110100  -1.593400  0.135100  1.120600   0.318800  -0.124400  -4.854500  -2.680300  0.130700   1.166500  0.355800
    0.4000  2.623100  0.817700  -0.123900  -1.565400  0.139800  1.082300   0.433000  -0.127100  -4.466500  -2.539500  0.135800   0.651700  0.354400
    0.5000  2.398100  0.888800  -0.133900  -1.547600  0.139900  1.070500   0.465800  -0.105600  -3.820000  -2.457700  0.115600  -0.063200  0.352200
    0.7500  1.943700  1.010800  -0.147100  -1.526700  0.140400  1.050100   0.475600  -0.092400  -3.422000  -2.406200  0.124500  -1.012700  0.349500
    1.0000  1.616000  1.078400  -0.151400  -1.521700  0.144500  1.025200   0.481200  -0.123500  -4.045000  -2.438100  0.188700  -1.099200  0.348700
    1.4999  1.192500  1.102000  -0.142300  -1.539500  0.160400  1.008700   0.503600  -0.159200  -4.247400  -2.498400  0.255800  -0.692900  0.349200
    2.0000  0.928600  1.073700  -0.126300  -1.563900  0.175100  1.016400   0.521900  -0.163800  -3.754600  -2.526600  0.266400  -0.295300  0.348400
    3.0003  0.573800  1.010900  -0.095300  -1.587900  0.184800  1.047900   0.513700  -0.157400  -3.782600  -2.535600  0.268200  -0.057000  0.346700
    4.0000  0.339500  0.953600  -0.071200  -1.603600  0.188400  1.070600   0.509100  -0.158000  -4.200800  -2.564400  0.286000  -0.106100  0.345700
    """)

    #: Coefficients for deep events taken from Excel file produced by Trevor
    #: Allen and provided by Geoscience Australia (20120821.GMPE_coeffs.xls)
    #: (coefficients in the original report are not correct)
    COEFFS_DEEP = CoeffsTable(sa_damping=5, table="""\
    IMT     c0        c1         c2         c3        c4        c5         c6         c7         c8         c9        c10        c11       sigma
    pga     3.383000  0.603400  -0.090500  -1.928900  0.175400  1.114000  -0.182200  -0.012600  -4.697400  -3.149000  0.315200  -0.724200  0.365300
    0.0100  3.383000  0.603400  -0.090500  -1.928900  0.175400  1.114000  -0.182200  -0.012600  -4.697400  -3.149000  0.315200  -0.724200  0.365300
    0.0200  3.556500  0.590400  -0.085600  -1.939400  0.162100  1.195400  -0.456100   0.033800  -4.858800  -3.091900  0.301200  -1.151800  0.389700
    0.0300  3.706900  0.528100  -0.084300  -1.972900  0.185500  1.165300  -0.454800   0.001600  -4.683500  -3.284900  0.393800  -1.287100  0.384000
    0.0500  3.738800  0.546200  -0.083500  -1.936900  0.165000  1.428100  -0.439900   0.001200  -4.335200  -3.477700  0.416800  -1.086700  0.355800
    0.0750  3.671800  0.584400  -0.089300  -1.887900  0.157800  1.501000  -0.298600  -0.033500  -4.189500  -3.552900  0.399000  -1.230800  0.339200
    0.1000  3.578800  0.626600  -0.097200  -1.847800  0.157300  1.512500  -0.162900  -0.057900  -4.055200  -3.517900  0.347100  -1.158900  0.332300
    0.1500  3.377900  0.727600  -0.112800  -1.779600  0.147600  1.627700  -0.009000  -0.045100  -3.627400  -3.285000  0.182100  -0.189600  0.327100
    0.2000  3.182600  0.820500  -0.128300  -1.732500  0.144300  1.648100   0.122900  -0.043000  -3.485400  -3.059000  0.103500   0.163500  0.324700
    0.2500  3.004000  0.898700  -0.143200  -1.701000  0.148300  1.572900   0.259800  -0.063200  -3.597500  -2.883800  0.104700  -0.138500  0.324600
    0.3000  2.842900  0.963400  -0.155600  -1.679100  0.153700  1.490100   0.368900  -0.084300  -3.750900  -2.749300  0.126100  -0.592800  0.324500
    0.4000  2.550100  1.064800  -0.171800  -1.652100  0.159400  1.436400   0.460800  -0.095500  -3.856300  -2.559700  0.134600  -1.180600  0.324800
    0.5000  2.303500  1.139300  -0.180700  -1.636700  0.160300  1.472500   0.462600  -0.083300  -3.790200  -2.436500  0.111300  -1.410700  0.322500
    0.7500  1.821900  1.248000  -0.186000  -1.614500  0.157900  1.602600   0.453000  -0.076500  -3.630900  -2.380700  0.115500  -1.495100  0.318800
    1.0000  1.478900  1.296500  -0.181800  -1.603100  0.156700  1.682600   0.486800  -0.101400  -3.612200  -2.471300  0.182000  -1.424700  0.318000
    1.4999  1.070600  1.274400  -0.161100  -1.625600  0.172500  1.700600   0.526100  -0.134900  -3.722900  -2.564400  0.248000  -0.994700  0.316100
    2.0000  0.840700  1.205900  -0.139000  -1.663900  0.193800  1.657500   0.538500  -0.147500  -3.764200  -2.581400  0.259700  -0.585400  0.314200
    3.0003  0.534400  1.095900  -0.105400  -1.707400  0.217800  1.598000   0.597500  -0.167000  -3.159600  -2.706200  0.311300  -0.575300  0.311300
    4.0000  0.320200  1.025000  -0.084500  -1.730700  0.229100  1.570300   0.640300  -0.176500  -2.737500  -2.811400  0.352600  -0.854700  0.309700
    """)
