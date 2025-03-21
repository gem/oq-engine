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
Module exports :class:`LanzanoEtAl2016`.
"""
import numpy as np
from scipy.constants import g

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib.gsim import utils
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, PGV, SA
from openquake.baselib.general import CallableDict

_compute_distance = CallableDict()


@_compute_distance.add('rjb')
def _compute_distance_rjb(dist_type, ctx, C):
    """
    Compute the third term of the equation 1:
    FD(Mw,R) = [c1j + c2j(M-Mr)] * log10(R/Rh) con j=1,...4 (eq 4)
    c coeffs are in matrix C
    """
    Mr = 5.0
    Rh = 70

    LATref = -0.33 * ctx.lon + 48.3
    diff = ctx.lat - LATref
    R = np.sqrt(ctx.rjb**2 + C['h']**2)

    dist_term = (diff >= 0) * (C['c11'] + C['c21'] * (ctx.mag - Mr)) *\
                (R <= Rh) * np.log10(R/Rh) +\
                (diff >= 0) * (C['c12'] + C['c22'] * (ctx.mag - Mr)) *\
                (R > Rh) * np.log10(R/Rh) +\
                (diff < 0) * (C['c13'] + C['c23'] * (ctx.mag - Mr)) *\
                (R <= Rh) * np.log10(R/Rh) +\
                (diff < 0) * (C['c14'] + C['c24'] * (ctx.mag - Mr)) *\
                (R > Rh) * np.log10(R/Rh)
    return dist_term


@_compute_distance.add('rhypo')
def _compute_distance_rhypo(dist_type, ctx, C):
    """
    Compute the third term of the equation 1:
    FD(Mw,R) = [c1j + c2j(M-Mr)] * log10(R/Rh) con j=1,...4 (eq 4)
    c coeffs are in matrix C
    """
    Mr = 5.0
    Rh = 70

    LATref = -0.33 * ctx.lon + 48.3
    diff = ctx.lat - LATref
    R = ctx.rhypo

    dist_term = (diff >= 0) * (C['c11'] + C['c21'] * (ctx.mag - Mr)) *\
                (R <= Rh) * np.log10(R/Rh) +\
                (diff >= 0) * (C['c12'] + C['c22'] * (ctx.mag - Mr)) *\
                (R > Rh) * np.log10(R/Rh) +\
                (diff < 0) * (C['c13'] + C['c23'] * (ctx.mag - Mr)) *\
                (R <= Rh) * np.log10(R/Rh) +\
                (diff < 0) * (C['c14'] + C['c24'] * (ctx.mag - Mr)) *\
                (R > Rh) * np.log10(R/Rh)
    return dist_term


def _compute_magnitude(ctx, C):
    """
    Compute the second term of the equation 1:
    Fm(M) = b1(M-Mr) + b2(M-Mr)^2   Eq (5)
    """
    Mr = 5
    return C['a'] + C['b1'] * (ctx.mag - Mr) + C['b2'] * (ctx.mag - Mr)**2


def _get_basin_effect_term(ctx, C):
    """
    Get basin correction for ctx in the Po Plain.
    if ctx.bas == 0 the correction is not necessary,
    otherwise if ctx.bas == 1 the site is in the Po Plain
    and the correction is applied.
    """
    delta = np.zeros(len(ctx.vs30))
    delta[ctx.bas == 1] = 1.0

    return C['dbas'] * delta


def _get_mechanism(ctx, C):
    """
    Compute the part of the second term of the equation 1 (FM(SoF)):
    Get fault type dummy variables
    """
    UN, NF, TF = utils.get_fault_type_dummy_variables(ctx)
    return C['fNF'] * NF + C['fTF'] * TF + C['fUN'] * UN


def _get_site_amplification(ctx, C):
    """
    Compute the fourth term of the equation 1 described on paragraph :
    The functional form Fs in Eq. (1) represents the site amplification and
    it is given by FS = sj Cj , for j = 1,...,3, where sj are the
    coefficients to be determined through the regression analysis,
    while Cj are dummy variables used to denote the five different EC8
    site classes
    """
    ssa, ssb, ssc = _get_site_type_dummy_variables(ctx)
    return (C['sA'] * ssa) + (C['sB'] * ssb) + (C['sC'] * ssc)


def _get_site_type_dummy_variables(ctx):
    """
    Get site type dummy variables, five different EC8 site classes
    The recording ctx are classified into 3 classes,
    based on the shear wave velocity intervals in the uppermost 30 m, Vs30,
    according to the EC8 (CEN 2003):
    class A: Vs30 > 800 m/s
    class B: Vs30 = 360 - 800 m/s
    class C: Vs30 < 360 m/s
    """
    ssa = np.zeros(len(ctx.vs30))
    ssb = np.zeros(len(ctx.vs30))
    ssc = np.zeros(len(ctx.vs30))

    # Class C; 180 m/s <= Vs30 <= 360 m/s.
    idx = ctx.vs30 < 360.0
    ssc[idx] = 1.0
    # Class B; 360 m/s <= Vs30 <= 800 m/s.
    idx = (ctx.vs30 >= 360.0) & (ctx.vs30 < 800)
    ssb[idx] = 1.0
    # Class A; Vs30 > 800 m/s.
    idx = (ctx.vs30 >= 800.0)
    ssa[idx] = 1.0
    return ssa, ssb, ssc


class LanzanoEtAl2016_RJB(GMPE):
    """
    Implements GMPE developed by G.Lanzano, M. D'Amico, C.Felicetta, R.Puglia,
    L.Luzi, F.Pacor, D.Bindi and published as
    "Ground-Motion Prediction Equations
    for Region-Specific Probabilistic Seismic-Hazard Analysis",
    Bull Seismol. Soc. Am., DOI 10.1785/0120150096
    SA are given up to 4 s.
    The regressions are developed considering the geometrical mean of the
    as-recorded horizontal components
    """
    #: Supported tectonic region type is 'active shallow crust' because the
    #: equations have been derived from data from Italian database ITACA, as
    #: explained in the 'Introduction'.
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Set of :mod:`intensity measure types <openquake.hazardlib.imt>`
    #: this GSIM can calculate. A set should contain classes from module
    #: :mod:`openquake.hazardlib.imt`.
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, PGV, SA}

    #: Supported intensity measure component is the geometric mean of two
    #: horizontal components
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GEOMETRIC_MEAN

    #: Supported standard deviation types are inter-event, intra-event
    #: and total
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL, const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT}

    #: Required site parameter
    REQUIRES_SITES_PARAMETERS = {'vs30', 'lon', 'lat', 'bas'}

    #: Required rupture parameters are magnitude and rake (eq. 1).
    REQUIRES_RUPTURE_PARAMETERS = {'rake', 'mag'}

    #: Required distance measure is R Joyner-Boore distance (eq. 1).
    REQUIRES_DISTANCES = {'rjb'}

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            dist_type = 'rjb' if "RJB" in self.__class__.__name__ else 'rhypo'

            imean = (_compute_magnitude(ctx, C) +
                     _compute_distance(dist_type, ctx, C) +
                     _get_site_amplification(ctx, C) +
                     _get_basin_effect_term(ctx, C) +
                     _get_mechanism(ctx, C))

            # Convert units to g, but only for PGA and SA (not PGV):
            if imt.string.startswith(("SA", "PGA")):
                mean[m] = np.log((10.0 ** (imean - 2.0)) / g)
            else:
                # PGV
                mean[m] = np.log(10.0 ** imean)

            # Return stddevs in terms of natural log scaling
            sig[m] = np.log(10.0 ** C['SigmaTot'])
            tau[m] = np.log(10.0 ** C['tau'])
            phi[m] = np.log(10.0 ** C['phi'])

    #: Coefficients from SA PGA and PGV from Table S2

    COEFFS = CoeffsTable(sa_damping=5, table="""
    IMT     a       b1      b2      c11     c21     c12     c22     c13     c23     c14     c24     h       fNF     fTF     fUN     sA      sB      sC      dbas    tau     phi     SigmaTot
    0.040   0.122   0.565   -0.015  -1.967  0.305   -0.968  0.026   -1.872  0.567   -2.280  0.443   6.507   0.058   0.199   0.000   0.000   0.028   0.189   -0.094  0.108   0.324   0.342
    0.070   0.258   0.555   -0.017  -2.131  0.299   -0.885  0.087   -1.986  0.593   -2.501  0.486   7.296   0.042   0.182   0.000   0.000   -0.002  0.161   -0.099  0.113   0.340   0.359
    0.100   0.334   0.537   -0.011  -2.125  0.268   -0.742  0.123   -1.996  0.486   -2.573  0.451   7.463   0.032   0.193   0.000   0.000   0.018   0.180   -0.102  0.118   0.354   0.373
    0.150   0.431   0.561   -0.008  -1.979  0.235   -0.804  0.070   -1.890  0.452   -2.443  0.348   7.073   0.024   0.183   0.000   0.000   0.033   0.180   -0.081  0.118   0.353   0.372
    0.200   0.436   0.579   -0.014  -1.847  0.201   -0.810  0.066   -1.820  0.348   -2.321  0.364   6.698   0.022   0.191   0.000   0.000   0.058   0.209   -0.070  0.114   0.342   0.360
    0.250   0.436   0.610   -0.020  -1.790  0.196   -0.905  0.022   -1.683  0.357   -2.205  0.311   6.933   0.035   0.183   0.000   0.000   0.065   0.201   -0.029  0.110   0.331   0.349
    0.300   0.394   0.629   -0.015  -1.759  0.180   -0.963  0.009   -1.639  0.305   -2.065  0.343   7.016   0.038   0.177   0.000   0.000   0.075   0.219   -0.016  0.108   0.323   0.340
    0.350   0.335   0.644   -0.008  -1.724  0.165   -1.009  0.015   -1.631  0.243   -1.979  0.328   7.304   0.044   0.178   0.000   0.000   0.081   0.241   0.012   0.105   0.316   0.333
    0.400   0.284   0.662   -0.010  -1.662  0.155   -1.080  0.004   -1.641  0.182   -1.863  0.282   7.272   0.031   0.176   0.000   0.000   0.088   0.257   0.046   0.103   0.309   0.326
    0.450   0.240   0.683   -0.010  -1.646  0.146   -1.045  -0.017  -1.648  0.169   -1.737  0.266   7.500   0.025   0.169   0.000   0.000   0.078   0.255   0.073   0.102   0.305   0.322
    0.500   0.182   0.699   -0.009  -1.601  0.140   -1.027  -0.027  -1.638  0.166   -1.663  0.270   7.493   0.030   0.168   0.000   0.000   0.086   0.270   0.094   0.101   0.303   0.319
    0.600   0.084   0.727   -0.017  -1.549  0.107   -0.963  0.000   -1.584  0.170   -1.492  0.244   7.135   0.024   0.150   0.000   0.000   0.097   0.280   0.125   0.101   0.303   0.319
    0.700   0.010   0.751   -0.025  -1.509  0.091   -0.956  -0.001  -1.561  0.134   -1.373  0.209   7.044   0.006   0.131   0.000   0.000   0.108   0.292   0.123   0.100   0.301   0.317
    0.800   -0.051  0.771   -0.034  -1.460  0.100   -0.989  0.028   -1.520  0.149   -1.307  0.225   6.943   -0.004  0.122   0.000   0.000   0.104   0.292   0.123   0.101   0.302   0.318
    0.900   -0.114  0.799   -0.036  -1.417  0.114   -0.985  0.016   -1.463  0.180   -1.212  0.259   6.760   -0.004  0.108   0.000   0.000   0.100   0.293   0.131   0.100   0.300   0.316
    1.000   -0.158  0.827   -0.043  -1.373  0.130   -1.009  0.000   -1.411  0.206   -1.189  0.207   6.500   -0.003  0.098   0.000   0.000   0.091   0.289   0.136   0.100   0.300   0.316
    1.200   -0.260  0.879   -0.041  -1.316  0.166   -1.038  -0.020  -1.313  0.267   -1.173  0.121   6.026   0.004   0.091   0.000   0.000   0.087   0.289   0.131   0.100   0.299   0.315
    1.400   -0.323  0.909   -0.052  -1.264  0.157   -1.139  0.053   -1.208  0.260   -1.262  0.116   5.366   -0.004  0.075   0.000   0.000   0.082   0.293   0.119   0.099   0.298   0.314
    1.600   -0.409  0.946   -0.045  -1.238  0.150   -1.214  0.046   -1.128  0.323   -1.278  0.072   5.033   0.000   0.070   0.000   0.000   0.085   0.303   0.115   0.099   0.297   0.313
    1.800   -0.486  0.977   -0.039  -1.218  0.141   -1.239  0.066   -1.103  0.313   -1.315  0.014   4.737   -0.001  0.067   0.000   0.000   0.080   0.303   0.119   0.100   0.299   0.315
    2.000   -0.554  0.997   -0.037  -1.189  0.138   -1.263  0.069   -1.100  0.282   -1.345  0.057   4.241   -0.010  0.056   0.000   0.000   0.081   0.308   0.117   0.099   0.298   0.314
    2.500   -0.742  1.034   -0.027  -1.164  0.151   -1.326  0.045   -1.072  0.299   -1.385  0.060   4.126   0.040   0.054   0.000   0.000   0.085   0.327   0.115   0.100   0.301   0.317
    3.000   -0.881  1.057   -0.019  -1.152  0.165   -1.378  0.018   -1.020  0.339   -1.449  0.084   4.170   0.072   0.045   0.000   0.000   0.089   0.325   0.114   0.101   0.304   0.320
    4.000   -1.084  1.134   0.019   -1.101  0.244   -1.488  -0.153  -0.971  0.414   -1.619  -0.119  4.454   0.073   0.019   0.000   0.000   0.096   0.322   0.131   0.113   0.298   0.318
    pga     0.071   0.603   -0.019  -1.895  0.286   -0.926  0.035   -1.838  0.511   -2.256  0.455   6.701   0.035   0.181   0.000   0.000   0.050   0.203   -0.060  0.106   0.318   0.336
    pgv     -1.142  0.767   -0.005  -1.623  0.230   -1.037  -0.054  -1.596  0.379   -1.741  0.348   5.904   0.022   0.144   0.000   0.000   0.085   0.260   0.037   0.096   0.288   0.304
    """)


class LanzanoEtAl2016_Rhypo(LanzanoEtAl2016_RJB):
    """
    Implements GMPE developed by G.Lanzano, M. D'Amico, C.Felicetta, R.Puglia,
    L.Luzi, F.Pacor, D.Bindi and published as "Ground-Motion Prediction Equations
    for Region-Specific Probabilistic Seismic-Hazard Analysis",
    Bull Seismol. Soc. Am., DOI 10.1785/0120150096
    SA are given up to 4 s.
    The regressions are developed considering the geometrical mean of the
    as-recorded horizontal components
    """

    #: Required distance measure is R Hypocentral Distance.
    REQUIRES_DISTANCES = {'rhypo'}

    #: Coefficients from SA PGA and PGV from esupp Table S3
    COEFFS = CoeffsTable(sa_damping=5, table="""
    IMT     a       b1      b2      c11     c21     c12     c22     c13     c23     c14     c24     fNF     fTF     fUN     sA      sB      sC      dbas    tau     phi     SigmaTot
    0.040   0.096   0.586   0.036   -2.119  0.151   -0.970  -0.009  -2.191  0.438   -2.263  0.428   0.029   0.207   0.000   0.000   0.040   0.199   -0.084  0.111   0.333   0.351
    0.070   0.236   0.569   0.030   -2.242  0.137   -0.918  0.055   -2.270  0.437   -2.509  0.497   0.018   0.196   0.000   0.000   0.010   0.173   -0.094  0.116   0.348   0.367
    0.100   0.318   0.553   0.035   -2.221  0.110   -0.785  0.083   -2.281  0.305   -2.586  0.463   0.005   0.205   0.000   0.000   0.027   0.190   -0.097  0.120   0.361   0.380
    0.150   0.411   0.578   0.038   -2.106  0.086   -0.830  0.027   -2.181  0.300   -2.436  0.361   -0.001  0.195   0.000   0.000   0.043   0.189   -0.079  0.120   0.359   0.379
    0.200   0.416   0.594   0.030   -1.992  0.056   -0.833  0.028   -2.110  0.193   -2.312  0.380   0.000   0.203   0.000   0.000   0.067   0.219   -0.071  0.116   0.349   0.368
    0.250   0.421   0.628   0.022   -1.909  0.065   -0.938  -0.019  -1.918  0.238   -2.212  0.313   0.016   0.193   0.000   0.000   0.073   0.209   -0.028  0.113   0.338   0.356
    0.300   0.380   0.648   0.027   -1.868  0.054   -0.997  -0.034  -1.860  0.192   -2.079  0.335   0.020   0.187   0.000   0.000   0.082   0.227   -0.014  0.110   0.330   0.347
    0.350   0.325   0.664   0.032   -1.809  0.043   -1.051  -0.031  -1.831  0.142   -2.003  0.313   0.026   0.188   0.000   0.000   0.088   0.249   0.016   0.108   0.323   0.340
    0.400   0.274   0.682   0.030   -1.745  0.039   -1.119  -0.042  -1.845  0.077   -1.887  0.263   0.012   0.185   0.000   0.000   0.094   0.265   0.049   0.105   0.315   0.332
    0.450   0.232   0.702   0.028   -1.713  0.031   -1.089  -0.064  -1.843  0.063   -1.764  0.247   0.006   0.178   0.000   0.000   0.084   0.263   0.077   0.104   0.311   0.328
    0.500   0.173   0.718   0.028   -1.668  0.027   -1.068  -0.073  -1.835  0.062   -1.689  0.249   0.010   0.177   0.000   0.000   0.092   0.278   0.099   0.103   0.309   0.325
    0.600   0.073   0.746   0.019   -1.639  -0.009  -0.998  -0.052  -1.797  0.073   -1.513  0.215   0.004   0.159   0.000   0.000   0.103   0.287   0.128   0.103   0.308   0.325
    0.700   -0.001  0.771   0.012   -1.602  -0.022  -0.990  -0.060  -1.777  0.045   -1.395  0.169   -0.013  0.140   0.000   0.000   0.113   0.300   0.126   0.102   0.305   0.322
    0.800   -0.062  0.792   0.001   -1.554  -0.006  -1.022  -0.037  -1.736  0.073   -1.329  0.178   -0.024  0.131   0.000   0.000   0.110   0.299   0.126   0.102   0.306   0.323
    0.900   -0.126  0.818   -0.003  -1.521  0.008   -1.010  -0.041  -1.679  0.112   -1.228  0.217   -0.023  0.116   0.000   0.000   0.105   0.300   0.133   0.101   0.304   0.321
    1.000   -0.176  0.844   -0.009  -1.490  0.025   -1.028  -0.051  -1.622  0.140   -1.197  0.175   -0.017  0.109   0.000   0.000   0.097   0.297   0.136   0.101   0.304   0.320
    1.200   -0.278  0.896   -0.008  -1.444  0.073   -1.053  -0.071  -1.526  0.214   -1.175  0.092   -0.008  0.102   0.000   0.000   0.092   0.296   0.131   0.101   0.303   0.320
    1.400   -0.345  0.928   -0.016  -1.417  0.067   -1.141  0.001   -1.437  0.212   -1.255  0.082   -0.014  0.086   0.000   0.000   0.087   0.300   0.118   0.101   0.302   0.319
    1.600   -0.432  0.966   -0.008  -1.402  0.062   -1.211  -0.007  -1.357  0.290   -1.268  0.033   -0.011  0.082   0.000   0.000   0.090   0.309   0.114   0.101   0.302   0.318
    1.800   -0.510  0.999   0.000   -1.393  0.055   -1.235  0.005   -1.339  0.283   -1.300  -0.025  -0.011  0.078   0.000   0.000   0.085   0.309   0.117   0.101   0.304   0.320
    2.000   -0.581  1.020   0.003   -1.380  0.053   -1.255  0.000   -1.350  0.250   -1.324  0.010   -0.017  0.069   0.000   0.000   0.085   0.313   0.116   0.101   0.303   0.319
    2.500   -0.766  1.063   0.015   -1.340  0.079   -1.324  -0.043  -1.315  0.286   -1.365  -0.002  0.032   0.063   0.000   0.000   0.087   0.332   0.118   0.102   0.305   0.322
    3.000   -0.903  1.086   0.023   -1.322  0.096   -1.377  -0.070  -1.242  0.340   -1.430  0.025   0.065   0.053   0.000   0.000   0.091   0.329   0.117   0.102   0.307   0.324
    4.000   -1.105  1.161   0.062   -1.243  0.188   -1.475  -0.209  -1.169  0.418   -1.596  -0.153  0.065   0.027   0.000   0.000   0.098   0.324   0.136   0.101   0.302   0.318
    pga     0.053   0.619   0.023   -2.036  0.150   -0.949  -0.006  -2.129  0.383   -2.257  0.455   0.011   0.192   0.000   0.000   0.059   0.212   -0.059  0.109   0.327   0.344
    pgv     -1.160  0.788   0.033   -1.792  0.124   -1.050  -0.116  -1.868  0.318   -1.740  0.314   0.003   0.155   0.000   0.000   0.092   0.268   0.034   0.099   0.296   0.312
    """)
