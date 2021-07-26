# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2021 GEM Foundation
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
Module exports :class:`BergeThierryEtAl2003SIGMA`.
"""
import copy
import numpy as np
from scipy.constants import g

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, SA


# TODO: Check whether lower validity bound is 4 or 7 km
def _compute(self, ctx, imts, mean, sig, tau, phi, mag_conversion_sigma=0.):
    for m, imt in enumerate(imts):
        C = self.COEFFS[imt]

        # clip distance at 4 km, minimum distance for which the equation is
        # valid (see section 2.2.4, page 201). This also avoids singularity
        # in the equation
        rhypo = np.array(ctx.rhypo)  # make a copy
        rhypo[rhypo < 4.] = 4.

        mean[m] = C['a'] * ctx.mag + C['b'] * rhypo - np.log10(rhypo)

        mean[m, ctx.vs30 >= 800] += C['c1']
        mean[m, ctx.vs30 < 800] += C['c2']

        # convert from log10 to ln, and from cm/s2 to g
        mean[m] = mean[m] * np.log(10) - 2 * np.log(10) - np.log(g)

        sigma = C['sigma'] * np.log(10)
        sig[m] = np.sqrt(sigma**2 + C['a']**2 * mag_conversion_sigma**2)


class BergeThierryEtAl2003Ms(GMPE):
    """
    Implements GMPE developed by Catherine Berge-Thierry, Fabrice Cotton,
    Oona Scoti, Daphne-Anne Griot-Pommera, and Yoshimitsu Fukushima and
    published as "New Empirical Response Spectral Attenuation Laws For Moderate
    European Earthquakes" (2003, Journal of Earthquake Engineering, 193-222)
    This class corresponds to the original formulation, usable with Ms.
    """
    #: Supported tectonic region type is active shallow crust, see
    #: `Introduction`, page 194.
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Supported intensity measure types are spectral acceleration, and peak
    #: ground acceleration. The original manuscript provide coefficients only
    #: SA. For PGA, coefficients are assumed equal to the ones of SA for the
    #: smallest period (0.03 s)
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, SA}

    #: Supported intensity measure component is horizontal, see page 196.
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.HORIZONTAL

    #: Supported standard deviation type is total, see table 3, page 203
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}

    #: Required site parameters is Vs30, used to distinguish between rock sites
    #: (Vs30 >= 800) m/s and alluvium sites (300 < Vs < 800), see section 2.2.3
    #: page 201
    REQUIRES_SITES_PARAMETERS = {'vs30'}

    #: Required rupture parameters is magnitude, see equation 1 page 201
    REQUIRES_RUPTURE_PARAMETERS = {'mag'}

    #: Required distance measure is hypocentral distance, see equation 1 page
    #: 201
    REQUIRES_DISTANCES = {'rhypo'}

    mag_conversion_sigma = 0.0

    compute = _compute

    #: Coefficient tables are constructed from the electronic suplements of
    #: the original paper. Original coefficients in function of frequency.
    COEFFS = CoeffsTable(sa_damping=5, table="""\
    IMT         a             b             c1           c2         sigma
    pga         0.3118000    -0.0009303     1.537000     1.57300    0.2923
    0.029412    0.3118000    -0.0009303     1.537000     1.57300    0.2923
    0.030000    0.3114000    -0.0009334     1.541000     1.57600    0.2924
    0.032258    0.3097000    -0.0009422     1.558000     1.58900    0.2928
    0.034000    0.3083000    -0.0009547     1.573000     1.60200    0.2935
    0.035714    0.3068000    -0.0009822     1.593000     1.61800    0.2947
    0.040000    0.3033000    -0.0011190     1.653000     1.66500    0.2982
    0.045455    0.3016000    -0.0012820     1.701000     1.70000    0.3015
    0.050000    0.2992000    -0.0013410     1.740000     1.72900    0.3009
    0.053000    0.2981000    -0.0014290     1.766000     1.74900    0.3022
    0.055556    0.2969000    -0.0014320     1.785000     1.76500    0.3027
    0.058824    0.2960000    -0.0014600     1.809000     1.78400    0.3040
    0.059999    0.2960000    -0.0014720     1.814000     1.78800    0.3041
    0.062500    0.2965000    -0.0015070     1.826000     1.79600    0.3047
    0.064998    0.2944000    -0.0015150     1.851000     1.81700    0.3059
    0.066667    0.2933000    -0.0015130     1.865000     1.82900    0.3059
    0.068966    0.2924000    -0.0015460     1.881000     1.84200    0.3048
    0.069999    0.2920000    -0.0015700     1.888000     1.84900    0.3046
    0.071429    0.2909000    -0.0015830     1.901000     1.86100    0.3047
    0.074074    0.2879000    -0.0015550     1.926000     1.88700    0.3059
    0.075002    0.2871000    -0.0015400     1.933000     1.89300    0.3066
    0.076923    0.2857000    -0.0015200     1.947000     1.90600    0.3072
    0.080000    0.2866000    -0.0015310     1.954000     1.91100    0.3061
    0.083333    0.2858000    -0.0015520     1.968000     1.92700    0.3058
    0.084998    0.2856000    -0.0015830     1.976000     1.93500    0.3053
    0.086957    0.2848000    -0.0015710     1.987000     1.94600    0.3042
    0.090001    0.2819000    -0.0015360     2.011000     1.97300    0.3020
    0.090909    0.2809000    -0.0015280     2.020000     1.98100    0.3016
    0.095238    0.2781000    -0.0015430     2.054000     2.01000    0.3017
    0.100000    0.2786000    -0.0014740     2.059000     2.01600    0.3019
    0.105260    0.2776000    -0.0014220     2.072000     2.03400    0.3043
    0.110000    0.2783000    -0.0014420     2.075000     2.04500    0.3073
    0.111110    0.2783000    -0.0014380     2.077000     2.04700    0.3079
    0.117650    0.2793000    -0.0014380     2.081000     2.05600    0.3103
    0.120000    0.2806000    -0.0014360     2.076000     2.05400    0.3106
    0.125000    0.2831000    -0.0014150     2.066000     2.05100    0.3121
    0.129030    0.2863000    -0.0014400     2.052000     2.04200    0.3137
    0.130010    0.2867000    -0.0014250     2.050000     2.04000    0.3142
    0.133330    0.2887000    -0.0013970     2.040000     2.03300    0.3156
    0.137930    0.2903000    -0.0013380     2.032000     2.02800    0.3161
    0.140000    0.2915000    -0.0013220     2.027000     2.02200    0.3166
    0.142860    0.2933000    -0.0013070     2.018000     2.01400    0.3173
    0.148150    0.2950000    -0.0012560     2.009000     2.01000    0.3191
    0.149990    0.2955000    -0.0012180     2.004000     2.00900    0.3196
    0.153850    0.2955000    -0.0010520     1.997000     2.00700    0.3201
    0.160000    0.2939000    -0.0008056     1.996000     2.01300    0.3200
    0.166670    0.2952000    -0.0007097     1.989000     2.00600    0.3215
    0.170010    0.2974000    -0.0006986     1.978000     1.99400    0.3230
    0.173910    0.3016000    -0.0007341     1.957000     1.97000    0.3247
    0.179990    0.3089000    -0.0007793     1.915000     1.93000    0.3267
    0.181820    0.3109000    -0.0007826     1.901000     1.91900    0.3271
    0.190010    0.3147000    -0.0007369     1.868000     1.89400    0.3262
    0.190480    0.3149000    -0.0007337     1.867000     1.89300    0.3262
    0.200000    0.3167000    -0.0006889     1.843000     1.88100    0.3250
    0.208330    0.3196000    -0.0006719     1.814000     1.86100    0.3261
    0.217390    0.3254000    -0.0006750     1.770000     1.82500    0.3281
    0.219780    0.3271000    -0.0006918     1.758000     1.81500    0.3292
    0.227270    0.3303000    -0.0006678     1.726000     1.79200    0.3320
    0.238100    0.3340000    -0.0006171     1.683000     1.76200    0.3367
    0.239980    0.3344000    -0.0005988     1.677000     1.75800    0.3371
    0.250000    0.3365000    -0.0005750     1.651000     1.73600    0.3394
    0.259740    0.3430000    -0.0007075     1.609000     1.69700    0.3422
    0.263160    0.3442000    -0.0007200     1.599000     1.68800    0.3429
    0.277780    0.3501000    -0.0007520     1.550000     1.64500    0.3444
    0.280030    0.3511000    -0.0007530     1.542000     1.63800    0.3447
    0.290020    0.3555000    -0.0007836     1.506000     1.60500    0.3458
    0.300030    0.3590000    -0.0008520     1.477000     1.58100    0.3477
    0.303030    0.3602000    -0.0008737     1.466000     1.57300    0.3483
    0.316960    0.3671000    -0.0009272     1.412000     1.52500    0.3491
    0.320000    0.3690000    -0.0009468     1.397000     1.51200    0.3487
    0.333330    0.3742000    -0.0010100     1.352000     1.47200    0.3474
    0.340020    0.3752000    -0.0010060     1.337000     1.46100    0.3469
    0.344830    0.3760000    -0.0009698     1.326000     1.45200    0.3471
    0.357140    0.3807000    -0.0009114     1.286000     1.41500    0.3481
    0.359970    0.3822000    -0.0009039     1.275000     1.40500    0.3484
    0.370370    0.3867000    -0.0008635     1.237000     1.37200    0.3492
    0.379940    0.3909000    -0.0008074     1.199000     1.33900    0.3500
    0.384620    0.3931000    -0.0007955     1.179000     1.32100    0.3507
    0.400000    0.3997000    -0.0007078     1.119000     1.26700    0.3517
    0.416670    0.4028000    -0.0006613     1.078000     1.23200    0.3512
    0.419990    0.4034000    -0.0006513     1.070000     1.22600    0.3513
    0.434780    0.4070000    -0.0006167     1.029000     1.19100    0.3521
    0.439950    0.4089000    -0.0006118     1.011000     1.17400    0.3527
    0.454550    0.4148000    -0.0005931     0.960100     1.12500    0.3547
    0.459980    0.4165000    -0.0005816     0.944000     1.10900    0.3549
    0.476190    0.4222000    -0.0005404     0.893100     1.05800    0.3555
    0.480080    0.4239000    -0.0005484     0.879500     1.04500    0.3556
    0.500000    0.4323000    -0.0005680     0.815000     0.97970    0.3555
    0.520020    0.4372000    -0.0005396     0.764200     0.93240    0.3568
    0.526320    0.4379000    -0.0005050     0.752200     0.92080    0.3570
    0.539960    0.4394000    -0.0004330     0.727100     0.89590    0.3574
    0.555560    0.4418000    -0.0003601     0.694100     0.86610    0.3587
    0.559910    0.4425000    -0.0003380     0.684400     0.85710    0.3592
    0.580050    0.4472000    -0.0002702     0.635700     0.81170    0.3610
    0.588240    0.4492000    -0.0002522     0.615700     0.79260    0.3609
    0.599880    0.4516000    -0.0002175     0.589500     0.76820    0.3603
    0.619960    0.4559000    -0.0001953     0.547800     0.72820    0.3604
    0.625000    0.4569000    -0.0001995     0.538300     0.71870    0.3609
    0.640200    0.4596000    -0.0001666     0.510600     0.69100    0.3625
    0.660070    0.4637000    -0.0001549     0.472500     0.65200    0.3647
    0.666670    0.4655000    -0.0001550     0.457300     0.63630    0.3649
    0.679810    0.4688000    -0.0001668     0.428400     0.60810    0.3655
    0.699790    0.4732000    -0.0001700     0.385700     0.56760    0.3667
    0.714290    0.4771000    -0.0002019     0.354800     0.53540    0.3680
    0.750190    0.4847000    -0.0003009     0.287100     0.46810    0.3700
    0.769230    0.4875000    -0.0003122     0.254500     0.43800    0.3703
    0.800000    0.4940000    -0.0002568     0.190600     0.37820    0.3714
    0.833330    0.5010000    -0.0001932     0.126400     0.31450    0.3746
    0.850340    0.5040000    -0.0001433     0.096150     0.28420    0.3758
    0.900090    0.5098000     3.28E-05      0.020060     0.21300    0.3747
    0.909090    0.5104000     8.39E-05      0.008195     0.20220    0.3744
    1.000000    0.5199000     0.0002516    -0.116200     0.08290    0.3737
    1.100100    0.5273000     0.0003908    -0.212300    -0.02900    0.3794
    1.111100    0.5278000     0.0004074    -0.220700    -0.03875    0.3804
    1.200500    0.5361000     0.0004479    -0.313300    -0.13380    0.3838
    1.250000    0.5409000     0.0004860    -0.367900    -0.18910    0.3877
    1.300400    0.5444000     0.0005329    -0.411300    -0.23770    0.3920
    1.400600    0.5481000     0.0007676    -0.487000    -0.31550    0.3935
    1.428600    0.5494000     0.0008272    -0.509500    -0.33850    0.3941
    1.499300    0.5527000     0.0009124    -0.560400    -0.39350    0.3932
    1.600000    0.5557000     0.0009844    -0.618600    -0.45830    0.3919
    1.666700    0.5580000     0.0010850    -0.656400    -0.50260    0.3919
    1.798600    0.5620000     0.0012450    -0.725800    -0.58340    0.3942
    2.000000    0.5622000     0.0013750    -0.796300    -0.66600    0.4030
    2.197800    0.5617000     0.0016520    -0.865600    -0.73950    0.4055
    2.398100    0.5641000     0.0018290    -0.940600    -0.81580    0.4093
    2.500000    0.5654000     0.0019210    -0.978700    -0.85420    0.4110
    2.597400    0.5677000     0.0020060    -1.019000    -0.89800    0.4130
    2.801100    0.5666000     0.0022770    -1.071000    -0.94950    0.4202
    3.003000    0.5683000     0.0024490    -1.130000    -1.01400    0.4255
    3.205100    0.5686000     0.0025360    -1.179000    -1.06900    0.4301
    3.333300    0.5705000     0.0025330    -1.220000    -1.11100    0.4329
    3.401400    0.5715000     0.0025410    -1.243000    -1.13500    0.4340
    3.597100    0.5727000     0.0025730    -1.300000    -1.19400    0.4359
    3.802300    0.5712000     0.0026620    -1.350000    -1.24200    0.4365
    4.000000    0.5722000     0.0027110    -1.417000    -1.30300    0.4344
    4.504500    0.5856000     0.0024490    -1.662000    -1.52000    0.4278
    5.000000    0.5990000     0.0021050    -1.886000    -1.72900    0.4233
    5.494500    0.6106000     0.0019410    -2.072000    -1.90400    0.4260
    5.988000    0.6160000     0.0018800    -2.201000    -2.02800    0.4284
    6.993000    0.6175000     0.0017660    -2.373000    -2.19200    0.4299
    8.000000    0.6145000     0.0017210    -2.491000    -2.30800    0.4284
    9.009000    0.6122000     0.0016370    -2.592000    -2.40800    0.4236
    10.00000    0.6086000     0.0015630    -2.668000    -2.48500    0.4183
    """)


class BergeThierryEtAl2003SIGMA(BergeThierryEtAl2003Ms):
    """
    Implements GMPE developed by Catherine Berge-Thierry, Fabrice Cotton,
    Oona Scoti, Daphne-Anne Griot-Pommera, and Yoshimitsu Fukushima and
    published as "New Empirical Response Spectral Attenuation Laws For Moderate
    European Earthquakes" (2003, Journal of Earthquake Engineering, 193-222)
    The class implements also adjustment of the sigma value as required by
    the SIGMA project to make standard deviations compatible with Mw
    (the GMPE was originally developed for Ms).
    Additional reference:
    Carbon, D. et al., 2012, Final preliminary Probabilistic Hazard map for
    France's southeast 1/4, Deliverable D4-18, p.31, SIGMA project.
    """
    def compute(self, ctx, imts, mean, sig, tau, phi):
        _compute(self, ctx, imts, mean, sig, tau, phi,
                 mag_conversion_sigma=0.2)


class BergeThierryEtAl2003MwW(BergeThierryEtAl2003Ms):
    """
    Mw version of the Berge-Thierry et al. (2003) GMPE. For this conversion
    we use the Weatherill et al. (2016) conversion equation between Ms and Mw
    Bilinear magnitude conversion relation.
    """
    def compute(self, ctx, imts, mean, sig, tau, phi):
        newctx = copy.copy(ctx)
        if ctx.mag <= 6.064:
            newctx.mag = (ctx.mag - 2.369) / 0.616
            _compute(self, newctx, imts, mean, sig, tau, phi,
                     mag_conversion_sigma=0.147/0.616)
        else:
            newctx.mag = (ctx.mag - 0.100) / 0.994
            _compute(self, newctx, imts, mean, sig, tau, phi,
                     mag_conversion_sigma=0.174/0.994)


class BergeThierryEtAl2003MwL_MED(BergeThierryEtAl2003Ms):
    """
    Mw version of the Berge-Thierry et al. (2003) GMPE. For this conversion
    we use the Lolli et al. (2014) conversion equation between Ms and Mw for
    the Euro-Mediterranean region.
    Exponential model: Mw = exp(a+b*Ms)+c  with slope=b*exp(a+b*Ms)
    Parameters: (a,b,c) = (2.133,0.063,-6.205)
    """
    def compute(self, ctx, imts, mean, sig, tau, phi):
        newctx = copy.copy(ctx)
        newctx.mag = (np.log(ctx.mag + 6.205) - 2.133) / 0.063
        slope = 0.063 * np.exp(2.133 + 0.063 * newctx.mag)
        _compute(self, newctx, imts, mean, sig, tau, phi,
                 mag_conversion_sigma=0.1703/slope)


class BergeThierryEtAl2003MwL_ITA(BergeThierryEtAl2003Ms):
    """
    Mw version of the Berge-Thierry et al. (2003) GMPE. For this conversion
    we use the Lolli et al. (2014) conversion equation between Ms and Mw for
    the ITA region.
    Exponential model: Mw = exp(a+b*Ms)+c  with slope=b*exp(a+b*Ms)
    Parameters: (a,b,c) = (1.421,0.108,-1.863)
    """
    def compute(self, ctx, imts, mean, sig, tau, phi):
        newctx = copy.copy(ctx)
        newctx.mag = (np.log(ctx.mag + 1.863) - 1.421) / 0.108
        slope = 0.108 * np.exp(1.421 + 0.108 * newctx.mag)
        _compute(self, newctx, imts, mean, sig, tau, phi,
                 mag_conversion_sigma=0.1685/slope)


class BergeThierryEtAl2003MwL_GBL(BergeThierryEtAl2003Ms):
    """
    Mw version of the Berge-Thierry et al. (2003) GMPE. For this conversion
    we use the Lolli et al. (2014) conversion equation between Ms and Mw for
    the GBL region (i.e. Global Scale).
    Exponential model:
    Mw = exp(a+b*Ms)+c  with slope=b*exp(a+b*Ms)
    Parameters:
    for Ms<=5.5: (a,b,c) = (2.133,0.063,-6.205)
    for Ms>5.5: (a,b,c) = (-0.109,0.229,2.586)
    """
    def compute(self, ctx, imts, mean, sig, tau, phi):
        newctx = copy.copy(ctx)
        if ctx.mag < 5.75:
            newctx.mag = (np.log(ctx.mag + 6.205) - 2.133) / 0.063
            slope = 0.063 * np.exp(2.133 + 0.063 * newctx.mag)
            _compute(self, newctx, imts, mean, sig, tau, phi,
                     mag_conversion_sigma=0.1703/slope)
        else:
            newctx.mag = (np.log(ctx.mag - 2.586) + 0.109) / 0.229
            slope = 0.229 * np.exp(-0.109 + 0.229 * newctx.mag)
            _compute(self, newctx, imts, mean, sig, tau, phi,
                     mag_conversion_sigma=0.1462/slope)
