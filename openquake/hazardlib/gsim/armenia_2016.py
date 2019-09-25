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
Armenian modification to selected active shallow crustal GMPEs
Module exports :class:`AkkarEtAlRjb2014Armenia`,
:class:`BindiEtAl2014RjbArmenia`,
:class:`BooreEtAl2014LowQArmenia`,
:class:`CauzziEtAl2014Armenia`,
:class:`KaleEtAl2015Armenia`,
:class:`KothaEtAl2016Armenia`,
:class:`ChiouYoungs2014Armenia`
"""
import numpy as np
from openquake.hazardlib.gsim.base import CoeffsTable
from openquake.hazardlib.gsim.akkar_2014 import AkkarEtAlRjb2014
from openquake.hazardlib.gsim.bindi_2014 import BindiEtAl2014Rjb
from openquake.hazardlib.gsim.boore_2014 import BooreEtAl2014LowQ
from openquake.hazardlib.gsim.cauzzi_2014 import CauzziEtAl2014
from openquake.hazardlib.gsim.kale_2015 import KaleEtAl2015Turkey
from openquake.hazardlib.gsim.kotha_2016 import KothaEtAl2016Turkey
from openquake.hazardlib.gsim.chiou_youngs_2014 import ChiouYoungs2014
from openquake.hazardlib import const


class AkkarEtAlRjb2014Armenia(AkkarEtAlRjb2014):
    """
    A
    """
    ADJUST = CoeffsTable(sa_damping=5, table="""\
    IMT            a          b        tau_adj        sig_adj
    pga     -4.41108    0.67245    1.237606958    1.382804565
    0.01    -4.41108    0.67245    1.237606958    1.382804565
    0.1     -4.26857    0.63633    1.234234554    1.411711027
    0.15    -3.58023    0.53806    1.213586478    1.454392101
    0.2     -3.21751    0.47609    1.197379023    1.431701071
    0.25    -2.75984    0.39380    1.117471608    1.370689616
    0.3     -2.51856    0.35743    1.058800958    1.366881400
    0.4     -1.98910    0.27073    0.975805217    1.275963791
    0.5     -1.77380    0.24280    0.959430009    1.260264111
    0.75    -1.63645    0.23295    0.905920923    1.166368305
    1.0     -1.79853    0.26714    0.927536136    1.115748947
    2.0     -1.83168    0.26919    0.891918855    1.078281365
    3.0     -1.90646    0.28960    0.924211474    1.139651450
    4.0     -1.90646    0.28960    0.924211474    1.139651450
    """)

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        """
        C_ADJ = self.ADJUST[imt]
        mean, stddevs = super().get_mean_and_stddevs(
            sites, rup, dists, imt, [const.StdDev.INTER_EVENT,
                                     const.StdDev.INTRA_EVENT])
        # Offset factor is dependent on magnitude and inter-event residual
        adj_factor = (C_ADJ["a"] + C_ADJ["b"] * rup.mag) * stddevs[0]
        adj_tau = stddevs[0] * C_ADJ["tau_adj"]
        adj_sigma = stddevs[1] * C_ADJ["sig_adj"]
        stddevs = []
        for stddev in stddev_types:
            if stddev == const.StdDev.INTER_EVENT:
                stddevs.append(adj_tau)
            elif stddev == const.StdDev.INTRA_EVENT:
                stddevs.append(adj_sigma)
            elif stddev == const.StdDev.TOTAL:
                stddevs.append(np.sqrt(adj_tau ** 2. + adj_sigma ** 2.))

        return mean + adj_factor, stddevs


class BindiEtAl2014RjbArmenia(BindiEtAl2014Rjb):
    """
    Adjustment of Bindi et al based on Armenian data
    """
    ADJUST = CoeffsTable(sa_damping=5, table="""\
    IMT              a          b      tau_adj       sig_adj
    pga       -3.53175    0.51121  1.148988194   1.339231170
    0.01      -3.53175    0.51121  1.148988194   1.339231170
    0.10      -4.01062    0.58731  1.186227974   1.369630629
    0.15      -3.60795    0.53588  1.184067775   1.449236792
    0.20      -3.38293    0.49443  1.170257166   1.438171195
    0.25      -2.60904    0.35474  1.073720674   1.375382159
    0.30      -2.21182    0.28479  1.021028896   1.382389947
    0.40      -1.44091    0.15445  0.957455011   1.310175818
    0.50      -0.97126    0.08268  0.908470546   1.243316094
    0.75      -0.59226    0.03920  0.865291003   1.168719929
    1.00      -0.66675    0.08514  0.842739543   1.070340828
    2.00      -0.78984    0.09427  0.804244641   1.021916357
    3.00      -0.91307    0.09874  0.873047313   1.096061687
    4.00      -0.91307    0.09874  0.873047313   1.096061687
    """)

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        """
        C_ADJ = self.ADJUST[imt]
        mean, stddevs = super().get_mean_and_stddevs(
            sites, rup, dists, imt, [const.StdDev.INTER_EVENT,
                                     const.StdDev.INTRA_EVENT])
        # Offset factor is dependent on magnitude and inter-event residual
        adj_factor = (C_ADJ["a"] + C_ADJ["b"] * rup.mag) * stddevs[0]
        adj_tau = stddevs[0] * C_ADJ["tau_adj"]
        adj_sigma = stddevs[1] * C_ADJ["sig_adj"]
        stddevs = []
        for stddev in stddev_types:
            if stddev == const.StdDev.INTER_EVENT:
                stddevs.append(adj_tau)
            elif stddev == const.StdDev.INTRA_EVENT:
                stddevs.append(adj_sigma)
            elif stddev == const.StdDev.TOTAL:
                stddevs.append(np.sqrt(adj_tau ** 2. + adj_sigma ** 2.))
        return mean + adj_factor, stddevs


class BooreEtAl2014LowQArmenia(BooreEtAl2014LowQ):
    """
    Adjustment of Boore et al for Low Q regions - adjusted for Armenian data
    """
    ADJUST = CoeffsTable(sa_damping=5, table="""\
    IMT             a          b        tau_adj        sig_adj
    pga      -5.45458    0.84260    1.633057382    1.315998086
    0.01     -5.45458    0.84260    1.633057382    1.315998086
    0.10     -5.45010    0.78926    1.531996667    1.326562840
    0.15     -4.64516    0.65549    1.575356285    1.421007734
    0.20     -3.98702    0.55509    1.585970506    1.411586591
    0.25     -3.11883    0.42217    1.524902361    1.368089701
    0.30     -2.80831    0.39356    1.472224512    1.388970102
    0.40     -2.63587    0.38977    1.418578519    1.362769784
    0.50     -2.66857    0.41789    1.349996281    1.333836045
    0.75     -2.76879    0.48144    1.283089899    1.290967084
    1.00     -2.42320    0.43353    1.199592804    1.258813632
    2.00     -2.67819    0.50808    1.137460426    1.303954815
    3.00     -2.58421    0.48516    1.121100923    1.357550507
    4.00     -2.58421    0.48516    1.121100923    1.357550507
    """)

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        """
        C_ADJ = self.ADJUST[imt]
        mean, stddevs = super().get_mean_and_stddevs(
            sites, rup, dists, imt, [const.StdDev.INTER_EVENT,
                                     const.StdDev.INTRA_EVENT])
        # Offset factor is dependent on magnitude and inter-event residual
        adj_factor = (C_ADJ["a"] + C_ADJ["b"] * rup.mag) * stddevs[0]
        adj_tau = stddevs[0] * C_ADJ["tau_adj"]
        adj_sigma = stddevs[1] * C_ADJ["sig_adj"]
        stddevs = []
        for stddev in stddev_types:
            if stddev == const.StdDev.INTER_EVENT:
                stddevs.append(adj_tau)
            elif stddev == const.StdDev.INTRA_EVENT:
                stddevs.append(adj_sigma)
            elif stddev == const.StdDev.TOTAL:
                stddevs.append(np.sqrt(adj_tau ** 2. + adj_sigma ** 2.))
        return mean + adj_factor, stddevs


class CauzziEtAl2014Armenia(CauzziEtAl2014):
    """
    Adjustment of Cauzzi et al. (2014) for Armenia
    """
    ADJUST = CoeffsTable(sa_damping=5, table="""\
    IMT               a          b       tau_adj        sig_adj
    pga        -4.01091    0.54155   1.182557898    1.336230261
    0.01       -4.01091    0.54155   1.182557898    1.336230261
    0.10       -3.34721    0.36510   1.186559348    1.373721566
    0.15       -2.82428    0.30847   1.201945278    1.442548031
    0.20       -2.74625    0.33423   1.173609107    1.394245091
    0.25       -2.39827    0.29678   1.099842199    1.340558908
    0.30       -2.44472    0.32730   1.035868990    1.325016391
    0.40       -2.16876    0.32372   0.933214946    1.222426552
    0.50       -2.26622    0.36475   0.889392952    1.170935874
    0.75       -2.51359    0.44715   0.861511598    1.120853806
    1.00       -2.88180    0.52997   0.888264702    1.069753666
    2.00       -3.39240    0.63148   0.945492439    1.109182279
    3.00       -3.61081    0.65005   0.992899354    1.186719473
    4.00       -3.61081    0.65005   0.992899354    1.186719473
    """)

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        """
        C_ADJ = self.ADJUST[imt]
        mean, stddevs = super().get_mean_and_stddevs(
            sites, rup, dists, imt, [const.StdDev.INTER_EVENT,
                                     const.StdDev.INTRA_EVENT])
        # Offset factor is dependent on magnitude and inter-event residual
        adj_factor = (C_ADJ["a"] + C_ADJ["b"] * rup.mag) * stddevs[0]
        adj_tau = stddevs[0] * C_ADJ["tau_adj"]
        adj_sigma = stddevs[1] * C_ADJ["sig_adj"]
        stddevs = []
        for stddev in stddev_types:
            if stddev == const.StdDev.INTER_EVENT:
                stddevs.append(adj_tau)
            elif stddev == const.StdDev.INTRA_EVENT:
                stddevs.append(adj_sigma)
            elif stddev == const.StdDev.TOTAL:
                stddevs.append(np.sqrt(adj_tau ** 2. + adj_sigma ** 2.))
        return mean + adj_factor, stddevs


class KaleEtAl2015Armenia(KaleEtAl2015Turkey):
    """
    Adjustment of Kale et al (2015) - Turkish version, for use in Armenia
    """
    ADJUST = CoeffsTable(sa_damping=5, table="""\
    IMT             a          b       tau_adj        sig_adj
    pga       -3.81210   0.60842   1.211930412    1.380035424
    0.01      -3.81210   0.60842   1.211930412    1.380035424
    0.10      -3.92511   0.63176   1.233919574    1.414621711
    0.15      -3.44729   0.55878   1.254042916    1.474569346
    0.20      -3.10217   0.48826   1.212810598    1.423997907
    0.25      -2.55005   0.38159   1.124262327    1.359629083
    0.30      -2.37729   0.35305   1.067422117    1.368689600
    0.40      -1.88576   0.27297   0.972445035    1.277120209
    0.50      -1.53914   0.20799   0.959303094    1.278495040
    0.75      -1.39011   0.18682   0.933638443    1.214393206
    1.00      -1.42400   0.19305   0.958971104    1.165427891
    2.00      -1.34283   0.18456   0.893004825    1.103623015
    3.00      -1.27746   0.17166   0.899017934    1.125281264
    4.00      -1.27746   0.17166   0.899017934    1.125281264
    """)

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        """
        C_ADJ = self.ADJUST[imt]
        mean, stddevs = super().get_mean_and_stddevs(
            sites, rup, dists, imt, [const.StdDev.INTER_EVENT,
                                     const.StdDev.INTRA_EVENT])
        # Offset factor is dependent on magnitude and inter-event residual
        adj_factor = (C_ADJ["a"] + C_ADJ["b"] * rup.mag) * stddevs[0]
        adj_tau = stddevs[0] * C_ADJ["tau_adj"]
        adj_sigma = stddevs[1] * C_ADJ["sig_adj"]
        stddevs = []
        for stddev in stddev_types:
            if stddev == const.StdDev.INTER_EVENT:
                stddevs.append(adj_tau)
            elif stddev == const.StdDev.INTRA_EVENT:
                stddevs.append(adj_sigma)
            elif stddev == const.StdDev.TOTAL:
                stddevs.append(np.sqrt(adj_tau ** 2. + adj_sigma ** 2.))
        return mean + adj_factor, stddevs


class KothaEtAl2016Armenia(KothaEtAl2016Turkey):
    """
    Adaptation of Kotha et al. (2016) - Turkey Regionalisation - for use in
    Armenia
    """
    ADJUST = CoeffsTable(sa_damping=5, table="""\
    IMT             a          b       tau_adj       sig_adj
    pga      -4.69043    0.75333   1.309083043   1.468617949
    0.01     -4.69043    0.75333   1.309083043   1.468617949
    0.10     -4.72868    0.74971   1.336985424   1.497481448
    0.15     -4.51782    0.71800   1.353741045   1.580257565
    0.20     -4.46285    0.70487   1.352808356   1.572527267
    0.25     -3.92145    0.60281   1.257121957   1.510959250
    0.30     -3.62217    0.55451   1.181996812   1.505253214
    0.40     -2.99273    0.45143   1.067481785   1.380782474
    0.50     -2.51620    0.37752   1.000819031   1.304662398
    0.75     -2.23067    0.35049   0.922194178   1.190464263
    1.00     -2.30317    0.37384   0.935864813   1.140699579
    2.00     -1.95774    0.31052   0.884893920   1.097828852
    3.00     -2.55008    0.39507   0.965496258   1.178953103
    4.00     -2.55008    0.39507   0.965496258   1.178953103
    """)

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        """
        C_ADJ = self.ADJUST[imt]
        mean, stddevs = super().get_mean_and_stddevs(
            sites, rup, dists, imt, [const.StdDev.INTER_EVENT,
                                     const.StdDev.INTRA_EVENT])
        # Offset factor is dependent on magnitude and inter-event residual
        adj_factor = (C_ADJ["a"] + C_ADJ["b"] * rup.mag) * stddevs[0]
        adj_tau = stddevs[0] * C_ADJ["tau_adj"]
        adj_sigma = stddevs[1] * C_ADJ["sig_adj"]
        stddevs = []
        for stddev in stddev_types:
            if stddev == const.StdDev.INTER_EVENT:
                stddevs.append(adj_tau)
            elif stddev == const.StdDev.INTRA_EVENT:
                stddevs.append(adj_sigma)
            elif stddev == const.StdDev.TOTAL:
                stddevs.append(np.sqrt(adj_tau ** 2. + adj_sigma ** 2.))
        return mean + adj_factor, stddevs


class ChiouYoungs2014Armenia(ChiouYoungs2014):
    """
    Adaptation of Chiou & Youngs (2014) for use in Armenia
    """
    ADJUST = CoeffsTable(sa_damping=5, table="""\
    IMT             a          b       tau_adj        sig_adj
    pga      -4.51489    0.57803   1.647935626    1.331572905
    0.01     -4.51489    0.57803   1.647935626    1.331572905
    0.10     -4.81330    0.60673   1.727544316    1.399648152
    0.15     -4.42289    0.57473   1.647848885    1.418029342
    0.20     -4.03866    0.51074   1.541820226    1.351192764
    0.25     -3.35194    0.39041   1.413327547    1.283876978
    0.30     -2.99454    0.33887   1.345459122    1.274993187
    0.40     -2.32174    0.22834   1.247508543    1.211456466
    0.50     -1.92942    0.17754   1.171085981    1.169131822
    0.75     -1.72756    0.17691   1.126882382    1.137432224
    1.00     -1.67691    0.18544   1.130029032    1.125152033
    2.00     -1.83778    0.23912   1.175741677    1.242777814
    3.00     -1.94949    0.28219   1.223141696    1.318344654
    4.00     -1.94949    0.28219   1.223141696    1.318344654
    """)

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        """
        C_ADJ = self.ADJUST[imt]
        mean, stddevs = super().get_mean_and_stddevs(
            sites, rup, dists, imt, [const.StdDev.INTER_EVENT,
                                     const.StdDev.INTRA_EVENT])
        # Offset factor is dependent on magnitude and inter-event residual
        adj_factor = (C_ADJ["a"] + C_ADJ["b"] * rup.mag) * stddevs[0]
        adj_tau = stddevs[0] * C_ADJ["tau_adj"]
        adj_sigma = stddevs[1] * C_ADJ["sig_adj"]
        stddevs = []
        for stddev in stddev_types:
            if stddev == const.StdDev.INTER_EVENT:
                stddevs.append(adj_tau)
            elif stddev == const.StdDev.INTRA_EVENT:
                stddevs.append(adj_sigma)
            elif stddev == const.StdDev.TOTAL:
                stddevs.append(np.sqrt(adj_tau ** 2. + adj_sigma ** 2.))
        return mean + adj_factor, stddevs
