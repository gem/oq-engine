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
Module exports :class:'PezeshkEtAl2011',
               :class:'PezeshkEtAl2011NEHRPBC'.
"""
import numpy as np

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, SA


class PezeshkEtAl2011(GMPE):
    """
    Implements GMPE developed by Shahram Pezeshk, Arash Zandieh
    and Behrooz Tavakoli. Published as "Hybrid Empirical Ground-Motion
    Prediction Equations for Eastern North America Using NGA Models and
    Updated Seismological Parameters", 2011, Bulletin of the Seismological
    Society of America, vol. 101, no. 4, 1859 - 1870.
    """
    #: Supported tectonic region type is 'stable continental region'
    #: equation has been derived from data from Eastern North America (ENA)
    # 'Instroduction', page 1859.
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.STABLE_CONTINENTAL

    #: Supported intensity measure types are spectral acceleration,
    #: and peak ground acceleration. See Table 2 in page 1865
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([
        PGA,
        SA
    ])

    #: Geometric mean determined from the fiftieth percentile values of the
    #: geometric means computed for all nonredundant rotation angles and all
    #: periods less than the maximum useable period, independent of
    #: sensor orientation. See page 1864.
    #: :attr:'~openquake.hazardlib.const.IMC.GMRotI50'.
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GMRotI50

    #: Supported standard deviation types is total.
    #: See equation 6 and 7, page 1866.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL
    ])

    #: No site parameters are needed. The GMPE was developed for hard-rock site
    # with Vs30 >= 2000 m/s (NEHRP site class A) only. Page 1864.
    REQUIRES_SITES_PARAMETERS = set()

    #: Required rupture parameters are magnitude (eq. 4, page 1866).
    REQUIRES_RUPTURE_PARAMETERS = set(('mag', ))

    #: Required distance measure is RRup, explained in page 1864 (eq. 2 page
    #: 1861, eq. 5 page 1866).
    REQUIRES_DISTANCES = set(('rrup', ))

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """

        # Extracting dictionary of coefficients specific to required
        # intensity measure type.
        C = self.COEFFS[imt]

        imean = (self._compute_magnitude(rup, C) +
                 self._compute_attenuation(rup, dists, imt, C) +
                 self._compute_distance(rup, dists, imt, C))

        mean = np.log(10.0 ** (imean))

        istddevs = self._get_stddevs(C, stddev_types, rup, imt,
                                     num_sites=len(dists.rrup))

        stddevs = np.log(10.0 ** np.array(istddevs))

        return mean, stddevs

    def _get_stddevs(self, C, stddev_types, rup, imt, num_sites):
        """
        Return standard deviations as defined in eq. 6 and 7, pag. 1866,
        based on table 2, p. 1865.
        """
        stddevs = []
        for stddev_type in stddev_types:
            sigma_mean = self._compute_standard_dev(rup, imt, C)
            sigma_tot = np.sqrt((sigma_mean ** 2) + (C['SigmaReg'] ** 2))
            stddevs.append(sigma_tot + np.zeros(num_sites))
        return stddevs

    def _compute_magnitude(self, rup, C):
        """
        Compute the first term of the equation described on p. 1866:

        "c1 + (c2 * M) + (c3 * M**2) "
        """
        return C['c1'] + (C['c2'] * rup.mag) + (C['c3'] * (rup.mag ** 2))

    def _compute_attenuation(self, rup, dists, imt, C):
        """
        Compute the second term of the equation described on p. 1866:

        " [(c4 + c5 * M) * min{ log10(R), log10(70.) }] +
        [(c4 + c5 * M) * max{ min{ log10(R/70.), log10(140./70.) }, 0.}] +
        [(c8 + c9 * M) * max{ log10(R/140.), 0}] "
        """

        vec = np.ones(len(dists.rrup))

        a1 = (np.log10(np.sqrt(dists.rrup ** 2.0 + C['c11'] ** 2.0)),
              np.log10(70. * vec))

        a = np.column_stack([a1[0], a1[1]])

        b3 = (np.log10(np.sqrt(dists.rrup ** 2.0 + C['c11'] ** 2.0) /
                      (70. * vec)),
              np.log10((140. / 70.) * vec))

        b2 = np.column_stack([b3[0], b3[1]])
        b1 = ([np.min(b2, axis=1), 0. * vec])
        b = np.column_stack([b1[0], b1[1]])

        c1 = (np.log10(np.sqrt(dists.rrup ** 2.0 + C['c11'] ** 2.0) /
              (140.) * vec), 0. * vec)
        c = np.column_stack([c1[0], c1[1]])

        return (((C['c4'] + C['c5'] * rup.mag) * np.min(a, axis=1)) +
                ((C['c6'] + C['c7'] * rup.mag) * np.max(b, axis=1)) +
                ((C['c8'] + C['c9'] * rup.mag) * np.max(c, axis=1)))

    def _compute_distance(self, rup, dists, imt, C):
        """
        Compute the third term of the equation described on p. 1866:

        " c10 * R "
        """
        return (C['c10'] * np.sqrt(dists.rrup ** 2.0 + C['c11'] ** 2.0))

    def _compute_standard_dev(self, rup, imt, C):
        """
        Compute the the standard deviation in terms of magnitude
        described on p. 1866, eq. 6
        """
        sigma_mean = 0.
        if rup.mag <= 7.0:
            sigma_mean = (C['c12'] * rup.mag) + C['c13']
        elif rup.mag > 7.0:
            sigma_mean = (-0.00695 * rup.mag) + C['c14']
        return sigma_mean

    #: Equation coefficients, described in Table 2 on pp. 1865
    COEFFS = CoeffsTable(sa_damping=5, table="""\
    IMT       c1             c2              c3              c4            c5             c6             c7              c8              c9              c10             c11            c12             c13            c14            SigmaReg
    pga       1.58278500     0.22980485     -0.038467279    -3.8325245     0.35351790     0.332086450   -0.091649259    -2.55169890      0.183070910    -0.000422375     6.6520975     -0.021050254     0.37776584     0.27905505     0.020605025
    0.010     2.04335530     0.19869692     -0.038373068    -4.0520987     0.36880267     0.199480560   -0.089184795    -2.59482830      0.184720410    -0.000396518     7.0644860     -0.019743027     0.36878898     0.27922877     0.021612537
    0.020     2.30502180     0.18772175     -0.036967652    -4.0442826     0.36162763    -0.122224550   -0.091565623    -2.99982330      0.194066370    -0.000170722     7.3313536     -0.019743461     0.36914553     0.27958228     0.022866162
    0.030     1.98482400     0.22034946     -0.036162832    -3.8031855     0.33840184     0.078141783   -0.112603350    -3.31249830      0.201652180    -5.32179E-05     7.1182747     -0.020937771     0.38173747     0.28381405     0.022372523
    0.040     1.68540590     0.24043926     -0.035776383    -3.6128750     0.32469480     0.295613210   -0.118021140    -3.33203870      0.197668130    -0.000111254     6.8113199     -0.021802452     0.39139487     0.28741869     0.023605119
    0.050     1.45173560     0.24141515     -0.034675707    -3.4682843     0.31767228     0.522379110   -0.129556390    -3.21086740      0.195626560    -0.000266881     6.3705068     -0.022441733     0.39897679     0.29052564     0.025051344
    0.075     1.06977950     0.29887294     -0.038974596    -3.3769847     0.31798753     0.742235930   -0.121484440    -2.68887410      0.172335850    -0.000665924     6.0817334     -0.023123141     0.41078656     0.29756555     0.025095256
    0.100     0.93139390     0.30877617     -0.038436152    -3.2926201     0.30631958     0.706381220   -0.095214253    -2.20903630      0.147206520    -0.000925354     6.1620694     -0.022592868     0.41023283     0.30072374     0.022233811
    0.150     0.39643437     0.43169606     -0.045775593    -3.2111790     0.29369212     0.608391200   -0.067269233    -1.61208100      0.107162070    -0.001076688     6.2666878     -0.021848921     0.40660604     0.30230457     0.015582655
    0.200    -0.48833625     0.62775027     -0.056541133    -3.0304035     0.26733511     0.542189400   -0.053474958    -1.35161460      0.087841291    -0.001045251     6.1904808     -0.020458744     0.39785283     0.30328260     0.014475725
    0.250    -1.00980480     0.74012641     -0.063085510    -2.9959199     0.26228068     0.442112110   -0.036248505    -1.23093190      0.077330183    -0.000964827     6.0635084     -0.019334356     0.39083594     0.30413643     0.014820287
    0.300    -1.68000460     0.88602986     -0.071623704    -2.8893864     0.24814951     0.486938120   -0.043237709    -1.14899390      0.070555429    -0.000904897     5.9890843     -0.018365879     0.38669103     0.30677086     0.014961957
    0.400    -2.31061360     1.02152740     -0.079650976    -2.9265220     0.25151054     0.471589720   -0.040392223    -1.09230140      0.065542242    -0.000785255     6.0262775     -0.016832386     0.37737845     0.30819274     0.017221468
    0.500    -3.13650760     1.20145830     -0.090369654    -2.8822916     0.24557786     0.333343350   -0.021047931    -1.00224290      0.055192621    -0.000706937     5.9116595     -0.015559903     0.37216518     0.31188685     0.016787106
    0.750    -4.54936770     1.50802900     -0.108711700    -2.8613890     0.24235022     0.402313090   -0.030918512    -0.97503715      0.055361787    -0.000568498     5.9835259     -0.013391470     0.36543753     0.32033822     0.020791085
    1.000    -5.41133340     1.69017010     -0.119600830    -2.8998486     0.24646305     0.376637070   -0.029283940    -0.94703476      0.052492510    -0.000456318     6.1234329     -0.011795872     0.35880759     0.32487746     0.022183642
    1.500    -6.48064580     1.86695490     -0.128177110    -2.9338076     0.25251393     0.263262110   -0.014416940    -0.90065097      0.049739355    -0.000353991     5.9874702     -0.010403524     0.35692188     0.33273819     0.018625013
    2.000    -6.93399290     1.90680910     -0.128724930    -3.0128154     0.26392116     0.317152250   -0.021502488    -0.87493043      0.047742343    -0.000302477     6.1355097     -0.009442865     0.35611062     0.33865155     0.020962228
    3.000    -7.42641010     1.88127470     -0.120486060    -2.9742397     0.25760353     0.258510050   -0.015195139    -0.88213320      0.053758057    -0.000264063     6.0597555     -0.008508698     0.35402644     0.34310654     0.02428989
    4.000    -7.80636730     1.89546280     -0.118292150    -3.0049879     0.25879498     0.306906560   -0.025450016    -0.88079876      0.057030983    -0.000242251     6.2536484     -0.007859427     0.35270488     0.34632987     0.029899076
    5.000    -8.27036650     1.93795990     -0.117965260    -2.9501142     0.25032167     0.329567930   -0.030227728    -1.01253690      0.073323916    -0.000200169     6.3422591     -0.006899636     0.35767668     0.35802021     0.031592909
    7.500    -8.33763300     1.80623080     -0.104248570    -2.9838785     0.25418641     0.287880220   -0.022521612    -1.18165170      0.095976523    -0.000162413     6.5180975     -0.007239689     0.37304593     0.37100909     0.029567069
    10.00    -9.10461860     1.89872240     -0.107604830    -2.8611231     0.23953867     0.286847230   -0.022896491    -1.37862210      0.122158550    -0.000126810     6.5383616     -0.007485065     0.38476363     0.38100915     0.024448978
    """)


class  PezeshkEtAl2011NEHRPBC(PezeshkEtAl2011):
    """
    Adaptation of Pezeshk et al. (2011) to amplify the ground motions from
    the original hard rock (Vs30 > 2000 m/s) sites to the NEHRP B/C site class
    using the factors of Atkinson and Adams (2013) (Table 2)
    Note:
    1) Correction at PGA is distance dependent in the original paper. Here
    we use a fixed distance of 20km (factor -0.10)
    2) All periods between 0.05s and PGA are kept constant at -0.10
    3) All periods above 5s are kept constant at 0.00 (no correction)
    """

    #: Shear-wave velocity for reference soil conditions in [m s-1]
    DEFINED_FOR_REFERENCE_VELOCITY = 760.

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        C_AMP = self.SITE_COEFFS[imt]
        # Get method from superclass
        mean, stddevs = super().get_mean_and_stddevs(
            sites, rup, dists, imt, stddev_types)
        return mean + C_AMP["F"]*np.log(10.), stddevs

    SITE_COEFFS = CoeffsTable(sa_damping=5, table="""
    IMT         F
    pga         -0.10
    0.010       -0.10
    0.050       -0.10
    0.100       0.03
    0.200       0.12
    0.330       0.14
    0.500       0.14
    1.000       0.11
    2.000       0.09
    5.000       0.06
    10.00       0.00
    """)
