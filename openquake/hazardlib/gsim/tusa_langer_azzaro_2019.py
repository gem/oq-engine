# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2025 GEM Foundation
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
Module exports :class:`TusaLangerAzzaro2019_100b`,
               :class:`TusaLangerAzzaro2019_60b`
"""
import numpy as np
from scipy.constants import g

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, SA


def _compute_distance(ctx, C):
    """
    Compute the distance function, equation (9):
    """
    mref = 3.6
    rref = 1.0
    const_h = 10**((ctx.mag-3.391)/2.076)
    rval = np.sqrt(ctx.rhypo ** 2 + const_h ** 2)
    return (C['c1'] + C['c2'] * (ctx.mag - mref)) *\
        np.log10(rval / rref) + C['c3'] * (rval - rref)


def _compute_magnitude(ctx, C):
    """
    Compute the magnitude function, equation (9):
    """
    return C['a'] + (C['b1'] * (ctx.mag)) + (C['b2'] * (ctx.mag) ** 2)


def _get_site_amplification(ctx, C):
    """
    Compute the site amplification function given by FS = eiSi, for
    i = 1,2,3 where Si are the coefficients determined through regression
    analysis, and ei are dummy variables (0 or 1) used to denote the
    different EC8 site classes.
    """
    ssa, ssb, sscd = _get_site_type_dummy_variables(ctx)

    return C['sA'] * ssa + C['sB'] * ssb + C['sCD'] * sscd


def _get_site_type_dummy_variables(ctx):
    """
    Get site type dummy variables, which classified the ctx into
    different site classes based on the shear wave velocity in the
    upper 30 m (Vs30) according to the EC8 (CEN 2003):
    class A: Vs30 > 800 m/s
    class B: Vs30 = 360 - 800 m/s
    class C&D: Vs30 < 360 m/s Class C and D togheter
    """
    ssa = np.zeros(len(ctx.vs30))
    ssb = np.zeros(len(ctx.vs30))
    sscd = np.zeros(len(ctx.vs30))
    # Class C&D; Vs30 < 360 m/s.
    idx = (ctx.vs30 < 360.0)
    sscd[idx] = 1.0
    # Class B; 360 m/s <= Vs30 <= 800 m/s.
    idx = (ctx.vs30 >= 360.0) & (ctx.vs30 < 800.0)
    ssb[idx] = 1.0
    # Class A; Vs30 > 800 m/s.
    idx = (ctx.vs30 >= 800.0)
    ssa[idx] = 1.0

    return ssa, ssb, sscd


class TusaLangerAzzaro2019_100b(GMPE):
    """
    Implements GMPE developed by Giuseppina Tusa, Horst Langer
    and Raffaele Azzaro (2020) and published as
    "Localizing ground motion models in volcanic terranes: Shallow events
    at Mt. Etna, Italy, revisited." BSSA, DOI: 10.1785/0120190325.

    GMPEs derive from shallow earthquakes (focal depth <= 6 km)
    in the volcanic area of Mt. Etna in the magnitude range 3<ML<4.8,
    and for hypocentral distances up to 100 km, and for soil classes A, B, C,
    and D. For soil classes C and D, the authors derived just one coefficient
    due to limited data belonging to these two soil classes.

    The functional form considered by the authors is a simplified version of
    Boore and Atkinson, 2008. Two GMPEs has been estimated taking into
    account two hypocentral distance ranges: (1) up to 100 km (TLA19-100) and
    (2) up to 60 km (TLA19-60).

    With a slightly modified approach, the authors considered a regression
    model using a pseudodepth (h) depending on magnitude according
    to the scaling law by Azzaro et al. (2017).

    Test tables are generated from a spreadsheet provided by the authors, and
    modified according to OQ format (e.g. conversion from cm/s2 to m/s2).

    """
    kind = "100b"

    #: Supported tectonic region type is 'volcanic' because the
    #: equations have been derived from data from Etna (Sicily, Italy)
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.VOLCANIC

    #: Supported intensity measure types are PGA and SA
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, SA}

    #: Supported intensity measure component is the maximum of two horizontal
    #: components
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = \
        const.IMC.GREATER_OF_TWO_HORIZONTAL

    #: Supported standard deviation type is total
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}

    #: Required site parameter is Vs30
    REQUIRES_SITES_PARAMETERS = {'vs30'}

    #: Required rupture parameter is magnitude.
    REQUIRES_RUPTURE_PARAMETERS = {'mag'}

    #: Required distance measure is Rhypo
    REQUIRES_DISTANCES = {'rhypo'}

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]

            imean = (_compute_magnitude(ctx, C) +
                     _compute_distance(ctx, C) +
                     _get_site_amplification(ctx, C))

            # convert from log10 to ln and from cm/s**2 to g
            mean[m] = np.log((10.0 ** (imean - 2.0)) / g)
            # Return stddevs in terms of natural log scaling
            sig[m] = np.log(10.0 ** C['SigmaTot'])

    # Coefficients from Table S2; sigma values in log

    COEFFS = CoeffsTable(sa_damping=5, table="""
    IMT a b1 b2 c1 c2 c3 sA sB sCD SigmaIE SigmaIS SigmaTot
    pga 5.9784 -2.9655 0.5414 -2.3472 -0.0064 0.0039 0 0.0616 0.0472 0.2215 0.3050 0.377
    0.05 5.03312916 -2.371134786 0.487782902 -2.644725857 -0.27160382 0.008859521 0 0.016207909 -0.028289107 0.1814 0.3646 0.4072
    0.07 5.80071276 -2.585765949 0.500144135 -2.756328588 -0.183080516 0.009150764 0 0.009462791 -0.027603963 0.2158 0.3507 0.4118
    0.10 5.755649351 -2.387920428 0.454945148 -2.75480015 -0.08350795 0.008117172 0 -0.005055584 -0.010595706 0.245 0.328 0.4094
    0.15 6.229986456 -2.484048684 0.447644508 -2.647078903 -0.005328263 0.004708701 0 -0.04104648 0.016330574 0.2393 0.3192 0.3989
    0.20 5.322463704 -2.121353683 0.40212508 -2.432324515 0.002903901 0.003018385 0 0.017083763 0.038095841 0.2041 0.3193 0.379
    0.25 5.370456651 -2.326933747 0.442659011 -2.291014032 -0.054707151 0.0020254 0 0.057348124 0.037184577 0.1906 0.3152 0.3684
    0.30 4.84306099 -2.148772986 0.421220858 -2.116716299 -0.061712069 0.000546632 0 0.063279457 0.046767903 0.1709 0.306 0.3505
    0.35 4.122014508 -1.845358545 0.383139905 -2.00064326 -0.077450354 -0.000292136 0 0.074067439 0.056067964 0.1529 0.3063 0.3423
    0.40 3.523063124 -1.55613006 0.342020029 -1.928693006 -0.0337765 -0.000771347 0 0.085750776 0.07079893 0.1407 0.3128 0.343
    0.45 3.306025013 -1.449626412 0.326246997 -1.904415375 -0.032777616 -0.000951386 0 0.08202187 0.069802678 0.1361 0.3116 0.34
    0.50 3.149878335 -1.414990784 0.32153886 -1.842153364 -0.011067473 -0.001266051 0 0.084897382 0.082929969 0.1283 0.3203 0.345
    0.60 1.839180668 -0.762614936 0.232486041 -1.759649051 0.031684753 -0.00167122 0 0.086822381 0.078478727 0.11 0.3302 0.3481
    0.70 2.954423259 -1.460822406 0.326280587 -1.670103371 0.011216384 -0.002554637 0 0.096759615 0.068548609 0.1073 0.3342 0.351
    0.80 1.74591192 -0.857869521 0.248470389 -1.647524752 0.061379382 -0.002611269 0 0.097899968 0.087265994 0.0998 0.3356 0.3501
    0.90 1.465338183 -0.758420699 0.236219765 -1.602888688 0.076468972 -0.003177039 0 0.098154243 0.073335296 0.1002 0.3404 0.3548
    1.00 0.960216541 -0.55691247 0.214633835 -1.588026538 0.063759198 -0.003177975 0 0.108785488 0.073554064 0.1045 0.3438 0.3593
    1.50 -1.641067892 0.41479094 0.112442313 -1.421211394 -0.02966249 -0.004308894 0 0.16870875 0.120855005 0.1442 0.3185 0.3496
    2.00 -1.137266465 -0.223917859 0.212622843 -1.149889034 -0.0540946 -0.006888255 0 0.148784989 0.127581245 0.1647 0.3188 0.3588
    2.50 -1.728930381 -0.166838889 0.22693676 -1.185098916 -0.137311748 -0.005261833 0 0.153919922 0.144729166 0.1552 0.3283 0.3631
    3.00 -1.406186089 -0.426719968 0.260881235 -1.211453158 -0.127134138 -0.003745407 0 0.130802552 0.097627145 0.1641 0.3333 0.3715
    4.00 1.885617556 -2.36620239 0.529529019 -1.348747493 -0.192179052 -0.000443602 0 0.131001754 0.065061426 0.1901 0.3394 0.389

    """)


class TusaLangerAzzaro2019_60b(TusaLangerAzzaro2019_100b):
    """
    Implements Tusa, Langer and Azzaro (2020) for shallow events and
    hypocentral distance less than 60 km.

    Extends
    :class:`openquake.hazardlib.gsim.tusa_langer_azzaro_2019.TusaLanger2019_60b`
    because the same functional form is used, only the coefficients differ.
    """
    # Coefficients from Table 3 (PGA) and Table S4 (SA); sigma values in log
    kind = "60b"

    COEFFS = CoeffsTable(sa_damping=5, table="""
    IMT a b1 b2 c1 c2 c3 sA sB sCD SigmaIE SigmaIS SigmaTot
    pga 4.3726000 -2.2482000 0.4431000 -1.8893000 -0.0104000 -0.0089000 0.0000000 0.0645000 0.0482000 0.2184000 0.2987000 0.3703000
    0.05 5.2436728 -2.5421764 0.4993491 -2.2998363 -0.1913852 -0.0011152 0.0000000 0.0393249 -0.0140838 0.2008000 0.3520000 0.4053000
    0.07 5.9139254 -2.7183646 0.5081123 -2.3998733 -0.1128104 -0.0009687 0.0000000 0.0291773 -0.0170058 0.2346000 0.3438000 0.4162000
    0.10 5.9421817 -2.5738913 0.4719028 -2.3597930 -0.0292817 -0.0030964 0.0000000 -0.0151451 -0.0327489 0.2552000 0.3281000 0.4157000
    0.15 5.1698924 -2.0759693 0.3887085 -2.0883064 0.0433321 -0.0100797 0.0000000 -0.0585306 0.0104927 0.2417000 0.3180000 0.3995000
    0.20 5.2680160 -2.3318910 0.4268689 -1.7403782 0.0295260 -0.0147125 0.0000000 0.0005907 0.0553342 0.1989000 0.3149000 0.3724000
    0.25 3.2976354 -1.4086831 0.3109890 -1.5452436 -0.0050946 -0.0173780 0.0000000 0.0267661 0.0263528 0.1819000 0.3062000 0.3560000
    0.30 3.7651689 -1.7540079 0.3597134 -1.4192212 -0.0092944 -0.0176496 0.0000000 0.0350723 0.0309209 0.1493000 0.3034000 0.3381000
    0.35 3.3540615 -1.6147791 0.3451980 -1.3576826 -0.0243821 -0.0172644 0.0000000 0.0598968 0.0492058 0.1316000 0.3048000 0.3320000
    0.40 2.7809547 -1.3627520 0.3128373 -1.2932124 -0.0221485 -0.0180948 0.0000000 0.0745132 0.0697572 0.1184000 0.3054000 0.3275000
    0.45 2.4197979 -1.1583205 0.2809283 -1.2544112 0.0158995 -0.0185904 0.0000000 0.0632829 0.0471988 0.1118000 0.3038000 0.3237000
    0.50 2.2233206 -1.0868276 0.2704889 -1.2202437 0.0450508 -0.0182200 0.0000000 0.0689673 0.0583819 0.0990000 0.3122000 0.3276000
    0.60 1.1849271 -0.5771243 0.2016261 -1.1560649 0.0692729 -0.0182035 0.0000000 0.0528332 0.0271682 0.0866000 0.3165000 0.3281000
    0.70 1.2931345 -0.6963938 0.2161315 -1.0862475 0.0992088 -0.0185661 0.0000000 0.0552103 -0.0056295 0.0780000 0.3157000 0.3252000
    0.80 1.5070611 -0.8827783 0.2453770 -1.0542005 0.1079944 -0.0189870 0.0000000 0.0534916 -0.0036760 0.0785000 0.3214000 0.3308000
    0.90 0.2738011 -0.2677009 0.1638896 -1.0026991 0.1147770 -0.0199745 0.0000000 0.0586503 -0.0074555 0.0879000 0.3250000 0.3367000
    1.00 0.6635555 -0.5687878 0.2121066 -1.0098256 0.0970782 -0.0194619 0.0000000 0.0827267 0.0209570 0.0976000 0.3310000 0.3450000
    1.50 -0.8443739 -0.1623523 0.1850412 -0.9067077 0.0323007 -0.0184072 0.0000000 0.1382940 0.0772604 0.1429000 0.3119000 0.3431000
    2.00 -2.9912398 0.7179408 0.0758292 -0.7338773 0.0313157 -0.0184330 0.0000000 0.1303062 0.0949040 0.1576000 0.3149000 0.3521000
    2.50 -3.7243800 0.9726243 0.0451616 -0.7755205 -0.0064767 -0.0156130 0.0000000 0.1369619 0.1178943 0.1618000 0.3095000 0.3493000
    3.00 -2.3935960 0.1580834 0.1551687 -0.8317885 0.0409512 -0.0131034 0.0000000 0.1233762 0.0874872 0.1686000 0.3135000 0.3560000
    4.00 -0.6953882 -0.9205602 0.3079770 -0.9680341 -0.0141747 -0.0101682 0.0000000 0.1330756 0.0636314 0.1899000 0.3170000 0.3960000


    """)
