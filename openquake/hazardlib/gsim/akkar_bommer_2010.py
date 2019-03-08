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
Module exports :class:`AkkarBommer2010`,
class:`AkkarBommer2010SWISS01`,
class:`AkkarBommer2010SWISS04`,
class:`AkkarBommer2010SWISS08`,
"""
import numpy as np
from scipy.constants import g

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, PGV, SA
from openquake.hazardlib.gsim.akkar_bommer_2010_swiss_coeffs import (
    COEFFS_FS_ROCK_SWISS01,
    COEFFS_FS_ROCK_SWISS04,
    COEFFS_FS_ROCK_SWISS08
)
from openquake.hazardlib.gsim.utils_swiss_gmpe import _apply_adjustments


class AkkarBommer2010(GMPE):

    """
    Implements GMPE developed by Sinan Akkar and Julian J. Bommer
    and published as "Empirical Equations for the Prediction of PGA, PGV,
    and Spectral Accelerations in Europe, the Mediterranean Region, and
    the Middle East", Seismological Research Letters, 81(2), 195-206.
    SA at 4 s (not supported by the original equations) has been added in the
    context of the SHARE project and assumed to be equal to SA at 3 s but
    scaled with proper factor.
    Equation coefficients for PGA and SA periods up to 0.05 seconds have been
    taken from updated model as described in 'Extending ground-motion
    prediction equations for spectral accelerations to higher response
    frequencies',Julian J. Bommer, Sinan Akkar, Stephane Drouet,
    Bull. Earthquake Eng. (2012) volume 10, pages 379 - 399.
    Coefficients for PGV and SA above 0.05 seconds are taken from the
    original 2010 publication.
    """
    #: Supported tectonic region type is 'active shallow crust' because the
    #: equations have been derived from data from Southern Europe, North
    #: Africa, and active areas of the Middle East, as explained in the
    # 'Introduction', page 195.
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Set of :mod:`intensity measure types <openquake.hazardlib.imt>`
    #: this GSIM can calculate. A set should contain classes from module
    #: :mod:`openquake.hazardlib.imt`.
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([
        PGA,
        PGV,
        SA
    ])

    #: Supported intensity measure component is the geometric mean of two
    #: horizontal components
    #: :attr:`~openquake.hazardlib.const.IMC.AVERAGE_HORIZONTAL`, see page 196.
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.AVERAGE_HORIZONTAL

    #: Supported standard deviation types are inter-event, intra-event
    #: and total, see equation 2, page 199.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL,
        const.StdDev.INTER_EVENT,
        const.StdDev.INTRA_EVENT
    ])

    #: Required site parameter is only Vs30 (used to distinguish rock
    #: and stiff and soft soil).
    REQUIRES_SITES_PARAMETERS = set(('vs30', ))

    #: Required rupture parameters are magnitude and rake (eq. 1, page 199).
    REQUIRES_RUPTURE_PARAMETERS = set(('rake', 'mag'))

    #: Required distance measure is RRup (eq. 1, page 199).
    REQUIRES_DISTANCES = set(('rjb', ))

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
                 self._compute_distance(rup, dists, imt, C) +
                 self._get_site_amplification(sites, imt, C) +
                 self._get_mechanism(sites, rup, imt, C))

        # Convert units to g,
        # but only for PGA and SA (not PGV):
        if imt.name in 'PGA SA':
            mean = np.log((10.0 ** (imean - 2.0)) / g)
        else:
            # PGV:
            mean = np.log(10.0 ** imean)

        # apply scaling factor for SA at 4 s
        if imt.name == 'SA' and imt.period == 4.0:
            mean /= 0.8

        istddevs = self._get_stddevs(
            C, stddev_types, num_sites=len(sites.vs30)
        )

        stddevs = np.log(10 ** np.array(istddevs))

        return mean, stddevs

    def _get_stddevs(self, C, stddev_types, num_sites):
        """
        Return standard deviations as defined in table 1, p. 200.
        """
        stddevs = []
        for stddev_type in stddev_types:
            assert stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
            if stddev_type == const.StdDev.TOTAL:
                stddevs.append(C['SigmaTot'] + np.zeros(num_sites))
            elif stddev_type == const.StdDev.INTRA_EVENT:
                stddevs.append(C['Sigma1'] + np.zeros(num_sites))
            elif stddev_type == const.StdDev.INTER_EVENT:
                stddevs.append(C['tau'] + np.zeros(num_sites))
        return stddevs

    def _compute_magnitude(self, rup, C):
        """
        Compute the first term of the equation described on p. 199:

        ``b1 + b2 * M + b3 * M**2``
        """
        return C['b1'] + (C['b2'] * rup.mag) + (C['b3'] * (rup.mag ** 2))

    def _compute_distance(self, rup, dists, imt, C):
        """
        Compute the second term of the equation described on p. 199:

        ``(b4 + b5 * M) * log(sqrt(Rjb ** 2 + b6 ** 2))``
        """
        return (((C['b4'] + C['b5'] * rup.mag)
                 * np.log10((np.sqrt(dists.rjb ** 2.0 + C['b6'] ** 2.0)))))

    def _get_site_amplification(self, sites, imt, C):
        """
        Compute the third term of the equation described on p. 199:

        ``b7 * Ss + b8 * Sa``
        """
        Ss, Sa = self._get_site_type_dummy_variables(sites)
        return (C['b7'] * Ss) + (C['b8'] * Sa)

    def _get_site_type_dummy_variables(self, sites):
        """
        Get site type dummy variables, ``Ss`` (for soft and stiff soil sites)
        and ``Sa`` (for rock sites).
        """
        Ss = np.zeros((len(sites.vs30),))
        Sa = np.zeros((len(sites.vs30),))
        # Soft soil; Vs30 < 360 m/s. Page 199.
        idxSs = (sites.vs30 < 360.0)
        # Stiff soil Class A; 360 m/s <= Vs30 <= 750 m/s. Page 199.
        idxSa = (sites.vs30 >= 360.0) & (sites.vs30 <= 750.0)
        Ss[idxSs] = 1
        Sa[idxSa] = 1
        return Ss, Sa

    def _get_mechanism(self, sites, rup, imt, C):
        """
        Compute the fourth term of the equation described on p. 199:

        ``b9 * Fn + b10 * Fr``
        """
        Fn, Fr = self._get_fault_type_dummy_variables(sites, rup, imt)
        return (C['b9'] * Fn) + (C['b10'] * Fr)

    def _get_fault_type_dummy_variables(self, sites, rup, imt):
        """
        Same classification of SadighEtAl1997. Akkar and Bommer 2010 is based
        on Akkar and Bommer 2007b; read Strong-Motion Dataset and Record
        Processing on p. 514 (Akkar and Bommer 2007b).
        """

        Fn, Fr = 0, 0
        if rup.rake >= -135 and rup.rake <= -45:
            # normal
            Fn = 1
        elif rup.rake >= 45 and rup.rake <= 135:
            # reverse
            Fr = 1
        return Fn, Fr

    #: For PGA and SA up to 0.05 seconds, coefficients are taken from table 5,
    #: page 385 of 'Extending ground-motion prediction equations for spectral
    #: accelerations to higher response frequencies', while for PGV and SA with
    #: periods greater than 0.05 coefficients are taken from table 1, pages
    #: 200-201 of 'Empirical Equations for the Prediction of PGA, PGV,
    #: and Spectral Accelerations in Europe, the Mediterranean Region, and
    #: the Middle East'
    COEFFS = CoeffsTable(sa_damping=5, table="""\
    IMT      b1         b2          b3          b4         b5         b6         b7          b8          b9          b10        Sigma1    tau       SigmaTot
    pga      1.43525    0.74866    -0.06520    -2.72950    0.25139    7.74959    0.08320     0.00766    -0.05823     0.07087    0.2611    0.1056    0.281646179
    0.01     1.43153    0.75258    -0.06557    -2.73290    0.25170    7.73304    0.08105     0.00745    -0.05886     0.07169    0.2616    0.1051    0.281922986
    0.02     1.48690    0.75966    -0.06767    -2.82146    0.26510    7.20661    0.07825     0.00618    -0.06111     0.06756    0.2635    0.1114    0.286080775
    0.03     1.64821    0.73507    -0.06700    -2.89764    0.27607    6.87179    0.06376    -0.00528    -0.06189     0.06529    0.2675    0.1137    0.290661212
    0.04     2.08925    0.65032    -0.06218    -3.02618    0.28999    7.42328    0.05045    -0.02091    -0.06278     0.05935    0.2709    0.1152    0.294377054
    0.05     2.49228    0.58575    -0.06043    -3.20215    0.31485    7.75532    0.03798    -0.03143    -0.06708     0.06382    0.2728    0.1181    0.297266631
    0.10     2.11994    0.75179    -0.07448    -3.10538    0.30253    8.21405    0.02667    -0.00062    -0.04906     0.07910    0.2728    0.1167    0.296713212
    0.15     1.64489    0.83683    -0.07544    -2.75848    0.25490    8.31786    0.02578     0.01703    -0.04184     0.07840    0.2788    0.1192    0.303212928
    0.20     0.92065    0.96815    -0.07903    -2.49264    0.21790    8.21914    0.06557     0.02105    -0.02098     0.08438    0.2821    0.1081    0.302102665
    0.25     0.13978    1.13068    -0.08761    -2.33824    0.20089    7.20688    0.09810     0.03919    -0.04853     0.08577    0.2871    0.0990    0.303689661
    0.30    -0.84006    1.37439    -0.10349    -2.19123    0.18139    6.54299    0.12847     0.04340    -0.05554     0.09221    0.2902    0.0976    0.306172827
    0.35    -1.32207    1.47055    -0.10873    -2.12993    0.17485    6.24751    0.16213     0.06695    -0.04722     0.09003    0.2983    0.1054    0.316373276
    0.40    -1.70320    1.55930    -0.11388    -2.12718    0.17137    6.57173    0.21222     0.09201    -0.05145     0.09903    0.2998    0.1101    0.319377598
    0.45    -1.97201    1.61645    -0.11742    -2.16619    0.17700    6.78082    0.24121     0.11675    -0.05202     0.09943    0.3037    0.1123    0.323797746
    0.50    -2.76925    1.83268    -0.13202    -2.12969    0.16877    7.17423    0.25944     0.13562    -0.04283     0.08579    0.3078    0.1163    0.329038797
    0.55    -3.51672    2.02523    -0.14495    -2.04211    0.15617    6.76170    0.26498     0.14446    -0.04259     0.06945    0.3070    0.1274    0.332384958
    0.60    -3.92759    2.08471    -0.14648    -1.88144    0.13621    6.10103    0.27718     0.15156    -0.03853     0.05932    0.3007    0.1430    0.332970704
    0.65    -4.49490    2.21154    -0.15522    -1.79031    0.12916    5.19135    0.28574     0.15239    -0.03423     0.05111    0.3004    0.1546    0.337848072
    0.70    -4.62925    2.21764    -0.15491    -1.79800    0.13495    4.46323    0.30348     0.15652    -0.04146     0.04661    0.2978    0.1626    0.339298688
    0.75    -4.95053    2.29142    -0.15983    -1.81321    0.13920    4.27945    0.31516     0.16333    -0.04050     0.04253    0.2973    0.1602    0.337714865
    0.80    -5.32863    2.38389    -0.16571    -1.77273    0.13273    4.37011    0.32153     0.17366    -0.03946     0.03373    0.2927    0.1584    0.332812034
    0.85    -5.75799    2.50635    -0.17479    -1.77068    0.13096    4.62192    0.33520     0.18480    -0.03786     0.02867    0.2917    0.1543    0.32999603
    0.90    -5.82689    2.50287    -0.17367    -1.76295    0.13059    4.65393    0.34849     0.19061    -0.02884     0.02475    0.2915    0.1521    0.328795772
    0.95    -5.90592    2.51405    -0.17417    -1.79854    0.13535    4.84540    0.35919     0.19411    -0.02209     0.02502    0.2912    0.1484    0.326833291
    1.00    -6.17066    2.58558    -0.17938    -1.80717    0.13599    4.97596    0.36619     0.19519    -0.02269     0.02121    0.2895    0.1483    0.325273946
    1.05    -6.60337    2.69584    -0.18646    -1.73843    0.12485    5.04489    0.37278     0.19461    -0.02613     0.01115    0.2888    0.1465    0.323832812
    1.10    -6.90379    2.77044    -0.19171    -1.71109    0.12227    5.00975    0.37756     0.19423    -0.02655     0.00140    0.2896    0.1427    0.322848958
    1.15    -6.96180    2.75857    -0.18890    -1.66588    0.11447    5.08902    0.38149     0.19402    -0.02088     0.00148    0.2871    0.1435    0.320965201
    1.20    -6.99236    2.73427    -0.18491    -1.59120    0.10265    5.03274    0.38120     0.19309    -0.01623     0.00413    0.2878    0.1439    0.321770182
    1.25    -6.74613    2.62375    -0.17392    -1.52886    0.09129    5.08347    0.38782     0.19392    -0.01826     0.00413    0.2863    0.1453    0.321060399
    1.30    -6.51719    2.51869    -0.16330    -1.46527    0.08005    5.14423    0.38862     0.19273    -0.01902    -0.00369    0.2869    0.1427    0.320429243
    1.35    -6.55821    2.52238    -0.16307    -1.48223    0.08173    5.29006    0.38677     0.19082    -0.01842    -0.00897    0.2885    0.1428    0.321906959
    1.40    -6.61945    2.52611    -0.16274    -1.48257    0.08213    5.33490    0.38625     0.19285    -0.01607    -0.00876    0.2875    0.1458    0.322356774
    1.45    -6.62737    2.49858    -0.15910    -1.43310    0.07577    5.19412    0.38285     0.19161    -0.01288    -0.00564    0.2857    0.1477    0.321620553
    1.50    -6.71787    2.49486    -0.15689    -1.35301    0.06379    5.15750    0.37867     0.18812    -0.01208    -0.00215    0.2839    0.1468    0.319608276
    1.55    -6.80776    2.50291    -0.15629    -1.31227    0.05697    5.27441    0.37267     0.18568    -0.00845    -0.00047    0.2845    0.1450    0.319319981
    1.60    -6.83632    2.51009    -0.15676    -1.33260    0.05870    5.54539    0.36952     0.18149    -0.00533    -0.00006    0.2844    0.1457    0.319549448
    1.65    -6.88684    2.54048    -0.15995    -1.40931    0.06860    5.93828    0.36531     0.17617    -0.00852    -0.00301    0.2841    0.1503    0.321407685
    1.70    -6.94600    2.57151    -0.16294    -1.47676    0.07672    6.36599    0.35936     0.17301    -0.01204    -0.00744    0.2840    0.1537    0.32292366
    1.75    -7.09166    2.62938    -0.16794    -1.54037    0.08428    6.82292    0.35284     0.16945    -0.01386    -0.01387    0.2840    0.1558    0.323928449
    1.80    -7.22818    2.66824    -0.17057    -1.54273    0.08325    7.11603    0.34775     0.16743    -0.01402    -0.01492    0.2834    0.1582    0.324565556
    1.85    -7.29772    2.67565    -0.17004    -1.50936    0.07663    7.31928    0.34561     0.16730    -0.01526    -0.01192    0.2828    0.1592    0.32453117
    1.90    -7.35522    2.67749    -0.16934    -1.46988    0.07065    7.25988    0.34142     0.16325    -0.01563    -0.00703    0.2826    0.1611    0.325293667
    1.95    -7.40716    2.68206    -0.16906    -1.43816    0.06525    7.25344    0.33720     0.16171    -0.01848    -0.00351    0.2832    0.1642    0.327358947
    2.00    -7.50404    2.71004    -0.17130    -1.44395    0.06602    7.26059    0.33298     0.15839    -0.02258    -0.00486    0.2835    0.1657    0.328372867
    2.05    -7.55598    2.72737    -0.17291    -1.45794    0.06774    7.40320    0.33010     0.15496    -0.02626    -0.00731    0.2836    0.1665    0.328863513
    2.10    -7.53463    2.71709    -0.17221    -1.46662    0.06940    7.46168    0.32645     0.15337    -0.02920    -0.00871    0.2832    0.1663    0.328417311
    2.15    -7.50811    2.71035    -0.17212    -1.49679    0.07429    7.51273    0.32439     0.15264    -0.03484    -0.01225    0.2830    0.1661    0.328143581
    2.20    -8.09168    2.91159    -0.18920    -1.55644    0.08428    7.77062    0.31354     0.14430    -0.03985    -0.01927    0.2830    0.1627    0.326435736
    2.25    -8.11057    2.92087    -0.19044    -1.59537    0.09052    7.87702    0.30997     0.14430    -0.04155    -0.02322    0.2830    0.1627    0.326435736
    2.30    -8.16272    2.93325    -0.19155    -1.60461    0.09284    7.91753    0.30826     0.14412    -0.04238    -0.02626    0.2829    0.1633    0.326648588
    2.35    -7.94704    2.85328    -0.18539    -1.57428    0.09077    7.61956    0.32071     0.14321    -0.04963    -0.02342    0.2815    0.1632    0.325386678
    2.40    -7.96679    2.85363    -0.18561    -1.57833    0.09288    7.59643    0.31801     0.14301    -0.04910    -0.02570    0.2826    0.1645    0.326990841
    2.45    -7.97878    2.84900    -0.18527    -1.57728    0.09428    7.50338    0.31401     0.14324    -0.04812    -0.02643    0.2825    0.1665    0.327915385
    2.50    -7.88403    2.81817    -0.18320    -1.60381    0.09887    7.53947    0.31104     0.14332    -0.04710    -0.02769    0.2818    0.1681    0.328129319
    2.55    -7.68101    2.75720    -0.17905    -1.65212    0.10680    7.61893    0.30875     0.14343    -0.04607    -0.02819    0.2818    0.1688    0.328488478
    2.60    -7.72574    2.82043    -0.18717    -1.88782    0.14049    8.12248    0.31122     0.14255    -0.05106    -0.02966    0.2838    0.1741    0.332946317
    2.65    -7.53288    2.74824    -0.18142    -1.89525    0.14356    7.92236    0.30935     0.14223    -0.05024    -0.02930    0.2845    0.1759    0.334486263
    2.70    -7.41587    2.69012    -0.17632    -1.87041    0.14283    7.49999    0.30688     0.14074    -0.04887    -0.02963    0.2854    0.1772    0.335936006
    2.75    -7.34541    2.65352    -0.17313    -1.86079    0.14340    7.26668    0.30635     0.14052    -0.04743    -0.02919    0.2862    0.1783    0.337196278
    2.80    -7.24561    2.61028    -0.16951    -1.85612    0.14444    7.11861    0.30534     0.13923    -0.04731    -0.02751    0.2867    0.1794    0.338202972
    2.85    -7.07107    2.56123    -0.16616    -1.90422    0.15127    7.36277    0.30508     0.13933    -0.04522    -0.02776    0.2869    0.1788    0.338054803
    2.90    -6.99332    2.52699    -0.16303    -1.89704    0.15039    7.45038    0.30362     0.13776    -0.04203    -0.02615    0.2874    0.1784    0.338268119
    2.95    -6.95669    2.51006    -0.16142    -1.90132    0.15081    7.60234    0.29987     0.13584    -0.03863    -0.02487    0.2872    0.1783    0.338045456
    3.00    -6.92924    2.45899    -0.15513    -1.76801    0.13314    7.21950    0.29772     0.13198    -0.03855    -0.02469    0.2876    0.1785    0.338490783
    4.00    -6.92924    2.45899    -0.15513    -1.76801    0.13314    7.21950    0.29772     0.13198    -0.03855    -0.02469    0.2876    0.1785    0.338490783
    pgv     -2.12833    1.21448    -0.08137    -2.46942    0.22349    6.41443    0.20354     0.08484    -0.05856     0.01305    0.2562    0.1083    0.278149834
    """)


class AkkarBommer2010SWISS01(AkkarBommer2010):

    """
    This class extends :class:`AkkarBommer2010`
    adjusted to be used for the Swiss Hazard Model [2014].
    This GMPE is valid for a fixed value of vs30=600m/s

    # kappa value
    K-adjustments corresponding to model 01 - as prepared by Ben Edwards
    K-value for PGA were not provided but infered from SA[0.01s]
    the model considers a fixed value of vs30=600 to match the
    reference vs30=1100m/s

    # small-magnitude correction

    # single station sigma - inter-event magnitude/distance adjustment

    Disclaimer: these equations are modified to be used for the
    Swiss Seismic Hazard Model [2014].
    The use of these models is the soly responsability of the hazard modeler.

    Model implmented by laurentiu.danciu@gmail.com
    """
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL
    ])

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """

        sites.vs30 = 600 * np.ones(len(sites.vs30))

        mean, stddevs = super(AkkarBommer2010SWISS01, self).\
            get_mean_and_stddevs(sites, rup, dists, imt, stddev_types)

        tau_ss = 'tau'
        log_phi_ss = np.log(10)
        mean, stddevs = _apply_adjustments(
            AkkarBommer2010.COEFFS, self.COEFFS_FS_ROCK[imt], tau_ss,
            mean, stddevs, sites, rup, dists.rjb, imt, stddev_types,
            log_phi_ss)

        return mean,  np.log(10 ** np.array(stddevs))

    COEFFS_FS_ROCK = COEFFS_FS_ROCK_SWISS01


class AkkarBommer2010SWISS04(AkkarBommer2010SWISS01):
    """
    This class extends :class:`AkkarBommer2010` following same strategy
    as for :class:`AkkarBommer2010SWISS01`
    """
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL
    ])

    COEFFS_FS_ROCK = COEFFS_FS_ROCK_SWISS04


class AkkarBommer2010SWISS08(AkkarBommer2010SWISS01):
    """
    This class extends :class:`AkkarBommer2010` following same strategy
    as for :class:`AkkarBommer2010SWISS01` to be used for the
    Swiss Hazard Model [2014].
    """
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL
    ])

    COEFFS_FS_ROCK = COEFFS_FS_ROCK_SWISS08
