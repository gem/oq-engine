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
Module exports : class:`ZafaraniEtAl2018`
                 class:`ZafaraniEtAl2018VHratio`
"""
import numpy as np
from scipy.constants import g

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib.gsim import utils
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, SA


def _compute_distance(C, ctx):
    """
    Compute the second term of the equation 1 which is presented in eq.3 and c2 is zero:

    ``c1 * log(sqrt(Rjb ** 2 + h ** 2)/Rref)``
    """
    rref = 1.0
    rval = np.sqrt(ctx.rjb ** 2 + C['h'] ** 2)
    return C['c1'] * np.log10(rval / rref)


def _compute_magnitude(C, ctx):
    """
    Compute the third term of the equation 1:

    e1 + b1 * (M-Mh) + b2 * (M-Mh)**2 for M<=Mh
    e1 + b3 * (M-Mh) otherwise
    """
    
    return np.where(
        ctx.mag <= C['mh'],
        C["e1"] + C['b1'] * (ctx.mag - C['mh']) + C['b2'] * (ctx.mag - C['mh']) ** 2,
        C["e1"] + C['b3'] * (ctx.mag - C['mh']))


def _get_mechanism(C, ctx):
    """
    Compute the fifth term of the equation 1 described on paragraph :
    Get fault type dummy variables, see Table 1
    """
    SS, U, TF = utils.get_fault_type_dummy_variables(ctx)
    fU = 0
    return C['fTF'] * TF + C['fSS'] * SS + fU * U

def _get_site_amplification(C, ctx):
    """
    Compute the fourth term of the equation 1 described on paragraph :
    The functional form Fs in Eq. (1) represents the site amplification and
    it is given by FS = sj Cj , for j = 1,...,5, where sj are the
    coefficients to be determined through the regression analysis,
    while Cj are dummy variables used to denote the five different EC8
    site classes
    """
    ssa, ssb, ssc, ssd = _get_site_type_dummy_variables(ctx)

    sA = 0
    return (sA * ssa + C['sB'] * ssb + C['sC'] * ssc +
            C['sD'] * ssd)


def _get_site_type_dummy_variables(ctx):
    """
    Get site type dummy variables, five different EC8 site classes
    The recording ctx are classified into 5 classes,
    based on the shear wave velocity intervals in the uppermost 30 m, Vs30,
    according to the EC8 (CEN 2003):
    class A: Vs30 > 800 m/s
    class B: Vs30 = 360 − 800 m/s
    class C: Vs30 = 180 - 360 m/s
    class D: Vs30 < 180 m/s
    """
    ssa = np.zeros(len(ctx.vs30))
    ssb = np.zeros(len(ctx.vs30))
    ssc = np.zeros(len(ctx.vs30))
    ssd = np.zeros(len(ctx.vs30))

    # Class D;  Vs30 < 180 m/s.
    idx = (ctx.vs30 >= 1E-10) & (ctx.vs30 < 180.0)
    ssd[idx] = 1.0
    # SClass C; 180 m/s <= Vs30 <= 360 m/s.
    idx = (ctx.vs30 >= 180.0) & (ctx.vs30 < 360.0)
    ssc[idx] = 1.0
    # Class B; 360 m/s <= Vs30 <= 800 m/s.
    idx = (ctx.vs30 >= 360.0) & (ctx.vs30 < 800)
    ssb[idx] = 1.0
    # Class A; Vs30 > 800 m/s.
    idx = (ctx.vs30 >= 800.0)
    ssa[idx] = 1.0
    return ssa, ssb, ssc, ssd


class ZafaraniEtAl2018(GMPE):
    """
    Implements GMPE developed by H.Zafarani, L.Luzi, G.Lanzano,
    M.R.Soghrat and published as "Empirical equations for the
    prediction of PGA and pseudo spectral accelerations using 
    Iranian strong-motion data",
    J Seismol, DOI 10.1007/s10950-017-9704-y.
    SA are given from 0.04 s to 4 s.
    The regressions are developed considering the geometrical mean of the
    horizontal components
    """
    #: Supported tectonic region type is 'active shallow crust' because the
    #: equations have been derived from data from Iran database, as
    #: explained in the 'Introduction'.
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Supported intensity measure types are PGA and SA
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, SA}

    #: Supported intensity measure component is the geometric mean of two
    #: horizontal components
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GEOMETRIC_MEAN

    #: Supported standard deviation types are inter-event, intra-event
    #: and total, page 1904
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL, const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT}

    #: Required site parameter is only Vs30
    REQUIRES_SITES_PARAMETERS = {'vs30'}

    #: Required rupture parameters are magnitude and rake (eq. 1).
    REQUIRES_RUPTURE_PARAMETERS = {'rake', 'mag'}

    #: Required distance measure is Rjb (eq. 1).
    REQUIRES_DISTANCES = {'rjb'}


    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            imean = (_compute_magnitude(C, ctx) +
                     _compute_distance(C, ctx) +
                     _get_site_amplification(C, ctx) +
                     _get_mechanism(C, ctx))


            mean[m] = np.log((10.0 ** (imean - 2.0)) / g)

            # Return stddevs in terms of natural log scaling
            sig[m] = np.log(10.0 ** C['SigmaTot'])
            tau[m] = np.log(10.0 ** C['SigmaB'])
            phi[m] = np.log(10.0 ** C['SigmaW'])

    #: Coefficients for PGA and SA from Table 1

    COEFFS = CoeffsTable(sa_damping=5, table="""
    IMT      mh       e1       b1       b2         b3        c1        h       fSS        fTF       sB       sC         sD    SigmaB   SigmaW  SigmaTot
    pga     5.0    2.880    0.554     0.103     0.244    -0.960     7.283     -0.030    -0.039    0.027    0.010    -0.017    0.094    0.283     0.298
    0.04    5.0    3.065    0.491     0.043     0.237    -1.027     6.835     -0.023    -0.045    0.010   -0.003    -0.039    0.098    0.294     0.310
    0.07    5.3    3.473    0.241    -0.153     0.204    -1.137     8.311     -0.014    -0.046   -0.006   -0.037    -0.055    0.113    0.298     0.319
    0.10    5.4    3.673    0.283    -0.116     0.180    -1.159     9.376     -0.024    -0.056    0.007   -0.052    -0.049    0.115    0.305     0.326
    0.15    5.6    3.623    0.249    -0.097     0.183    -1.090    10.228     -0.020    -0.028    0.061   -0.001    -0.029    0.105    0.315     0.332
    0.20    5.8    3.401    0.193    -0.124     0.207    -0.963     8.795      0.001     0.000    0.071    0.022     0.000    0.103    0.309     0.326
    0.25    5.9    3.429    0.227    -0.112     0.232    -0.986    11.315      0.006     0.013    0.080    0.073     0.031    0.102    0.306     0.323
    0.30    6.0    3.383    0.245    -0.118     0.227    -0.959    11.012     -0.008     0.010    0.073    0.104     0.048    0.103    0.308     0.325
    0.35    6.0    3.325    0.305    -0.104     0.241    -0.947    11.250     -0.012     0.008    0.073    0.113     0.065    0.103    0.310     0.326
    0.40    6.1    3.148    0.277    -0.128     0.254    -0.861     7.953     -0.016     0.010    0.076    0.114     0.077    0.104    0.313     0.330
    0.45    6.1    3.089    0.286    -0.140     0.262    -0.848     7.498     -0.022     0.011    0.074    0.112     0.097    0.104    0.312     0.329
    0.50    6.2    3.085    0.287    -0.139     0.263    -0.847     7.525     -0.013     0.020    0.060    0.095     0.100    0.104    0.313     0.330
    0.60    6.3    3.029    0.311    -0.139     0.277    -0.836     6.723     -0.002     0.021    0.056    0.086     0.115    0.106    0.318     0.335
    0.70    6.4    2.926    0.280    -0.157     0.302    -0.803     4.967      0.017     0.031    0.047    0.076     0.133    0.107    0.321     0.338
    0.80    6.4    2.873    0.317    -0.159     0.330    -0.798     4.966      0.017     0.032    0.047    0.065     0.144    0.108    0.323     0.341
    0.90    6.5    2.838    0.303    -0.164     0.373    -0.787     4.973      0.016     0.035    0.043    0.059     0.142    0.108    0.324     0.341
    1.00    6.5    2.791    0.341    -0.161     0.372    -0.782     4.975      0.022     0.041    0.034    0.056     0.146    0.108    0.325     0.342
    1.20    6.6    2.738    0.397    -0.145     0.388    -0.776     4.976      0.040     0.048    0.038    0.056     0.139    0.108    0.324     0.341
    1.40    6.7    2.691    0.442    -0.128     0.377    -0.769     4.980      0.062     0.059    0.039    0.054     0.135    0.109    0.327     0.345
    1.60    6.7    2.640    0.511    -0.110     0.410    -0.777     4.981      0.077     0.065    0.040    0.058     0.116    0.110    0.329     0.347
    1.80    6.8    2.642    0.558    -0.091     0.395    -0.778     4.994      0.078     0.068    0.047    0.062     0.114    0.109    0.327     0.344
    2.00    6.8    2.600    0.631    -0.072     0.397    -0.772     5.001      0.077     0.066    0.051    0.065     0.098    0.107    0.322     0.339
    2.50    6.9    2.665    0.789    -0.026     0.135    -0.795     6.960      0.086     0.054    0.053    0.056     0.078    0.104    0.311     0.328
    3.00    7.0    2.697    0.851    -0.008    -0.062    -0.809     8.447      0.099     0.048    0.047    0.041     0.043    0.101    0.303     0.319
    4.00    7.2    2.626    0.877     0.001    -0.455    -0.775     8.296      0.107     0.023    0.048    0.025     0.032    0.134    0.290     0.319
    """)

class ZafaraniEtAl2018VHratio(ZafaraniEtAl2018):
    """
    Calculates the V/H ratio.
    """

    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.VERTICAL_TO_HORIZONTAL_RATIO

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            imean = (_compute_magnitude(C, ctx) +
                     _compute_distance(C, ctx) +
                     _get_site_amplification(C, ctx) +
                     _get_mechanism(C, ctx))


            mean[m] = np.log(10.0 ** imean)

            # Return stddevs in terms of natural log scaling
            sig[m] = np.log(10.0 ** C['SigmaTot'])
            tau[m] = np.log(10.0 ** C['SigmaB'])
            phi[m] = np.log(10.0 ** C['SigmaW'])

    #: Coefficients for V/H from Table 2

    COEFFS = CoeffsTable(sa_damping=5, table="""
    IMT      mh       e1       b1       b2         b3        c1        h       fSS        fTF       sB       sC         sD    SigmaB   SigmaW  SigmaTot
    PGA	    5.0	  -0.058	0.054	 0.098	    0.021	 -0.140	    6.107	   0.005	 0.006	  0.009	   0.033	-0.019	  0.056	   0.169	 0.179
    0.04	5.0	   0.215	0.022	 0.037	    0.021	 -0.257	    6.679	   0.021	 0.000	  0.018	   0.016	-0.017	  0.059	   0.177	 0.186
    0.07	5.3	   0.153	0.116	 0.071	    0.032	 -0.195	    7.182	  -0.014	-0.023	  0.056	   0.03	     0.013	  0.062	   0.185	 0.195
    0.10	5.4	  -0.133   -0.023	-0.018	    0.041	 -0.093	    5.187  	   0.022	 0.020	  0.075	   0.097	-0.007	  0.064	   0.192	 0.203
    0.15	5.6	  -0.194	0.016	-0.001	    0.061	 -0.073	    7.047	   0.000	 0.007	  0.001	   0.087	 0.012	  0.070	   0.209	 0.221
    0.20	5.8	  -0.196	0.048	 0.014	    0.041	 -0.072	    5.152	   0.008	 0.012	 -0.051	   0.046	-0.021	  0.067	   0.200 	 0.210
    0.25	5.9	  -0.176	0.075	 0.032	    0.038	 -0.067	    5.136	  -0.022	-0.017	 -0.070	  -0.018	-0.034	  0.067	   0.201	 0.212
    0.30	6.0	  -0.118	0.058	 0.009	    0.040	 -0.082	    5.130	  -0.033	-0.031	 -0.082	  -0.093	-0.050	  0.067	   0.201	 0.212
    0.35	6.0	  -0.113	0.058	 0.012	    0.043	 -0.080	    5.136	  -0.027	-0.025	 -0.092	  -0.122	-0.049	  0.068	   0.204	 0.215
    0.40	6.1	  -0.096	0.070	 0.019	    0.018	 -0.082	    5.142	  -0.021	-0.019	 -0.093	  -0.139	-0.046	  0.068	   0.204	 0.216
    0.45	6.1	  -0.090	0.058	 0.010	    0.027	 -0.082	    6.776	  -0.029	-0.015	 -0.090	  -0.151	-0.068	  0.069	   0.207	 0.218
    0.50	6.2	  -0.083	0.048	 0.000	    0.017	 -0.079	    5.152	  -0.028	-0.021	 -0.083	  -0.143	-0.078	  0.069	   0.208	 0.219
    0.60	6.3	  -0.168   -0.017	-0.024	    0.015	 -0.046	    6.935	  -0.006	-0.006	 -0.073	  -0.131	-0.081	  0.071	   0.213	 0.225
    0.70	6.4	  -0.181   -0.016	-0.021	    0.025	 -0.030	    7.434	  -0.008	-0.005	 -0.078	  -0.126	-0.117	  0.074	   0.221	 0.233
    0.80	6.4	  -0.174   -0.014	-0.021	    0.005	 -0.024	    7.562	  -0.011	-0.003	 -0.078	  -0.125	-0.140	  0.075	   0.224	 0.236
    0.90	6.5	  -0.159	0.016	-0.006	   -0.027	 -0.019	    7.186	  -0.026	-0.009	 -0.073	  -0.111	-0.141	  0.075	   0.225	 0.237
    1.00	6.5	  -0.157	0.020	-0.001	   -0.022	 -0.022	    7.448	  -0.016	 0.001	 -0.073	  -0.112	-0.150	  0.075	   0.225	 0.237
    1.20	6.6	  -0.158	0.002	-0.004	   -0.020	 -0.029	    7.518	  -0.001	 0.034	 -0.083	  -0.102	-0.138	  0.074	   0.223	 0.235
    1.40	6.7	  -0.112   -0.001	-0.009	    0.001	 -0.044	    12.481	  -0.012	 0.034	 -0.085	  -0.101	-0.126	  0.073	   0.220	 0.232
    1.60	6.7	  -0.120   -0.004	-0.011	    0.016	 -0.041	    13.310	  -0.007	 0.044	 -0.073	  -0.087	-0.114	  0.073	   0.220	 0.232
    1.80	6.8	  -0.113   -0.005	-0.011	   -0.027	 -0.037	    12.995	  -0.011	 0.038	 -0.067	  -0.089	-0.125	  0.073	   0.220	 0.232
    2.00	6.8	  -0.117	0.006	-0.005	   -0.052	 -0.035	    13.411	  -0.002	 0.040	 -0.063	  -0.090	-0.098	  0.073	   0.220	 0.232
    2.50	6.9	  -0.184	0.011	 0.000     -0.004	  0.011	    12.964	   0.008	 0.050	 -0.065	  -0.089	-0.081	  0.070	   0.209	 0.220
    3.00	7.0	  -0.188	0.023	 0.005	   -0.052	  0.020	    11.714	   0.007	 0.055	 -0.057	  -0.084	-0.047	  0.069	   0.207	 0.218
    4.00	7.2	  -0.212	0.014	 0.005	   -0.232	  0.036	    12.426	   0.000	 0.047	 -0.064	  -0.082	-0.028	  0.074	   0.223	 0.235

    """)

