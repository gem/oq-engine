# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2018 GEM Foundation
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
Module exports :class:`ArtetaEtAl2023_Vs30`
               :class:`ArtetaEtAl2023`
"""
import numpy as np
from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, SA


CONSTS = {"C1Slab": 6.5}


def _get_stddevs(C):
    """
    Return standard deviations as defined in Table 3
    """
    Sigma = C['Sigma']
    phi = C['Phi']
    tau = C['Tau']
    return [Sigma, tau, phi]


def _compute_base_term(C):
    """
    Returns the base coefficient of the GMPE, which for interface events
    is just the coefficient a1 (adjusted regionally)
    """
    return C["Tetha1"]


def _compute_magnitude_term(C, mag):
    """
    Returns the magnitude scaling term adding the equations for global and regional terms (eq 5. and 6.)
    """
    f_mag = C["Tetha3"] * ((8.5 - mag) ** 2.)
    idx = mag <= C["M1"]
    f_mag[idx] = C["Tetha2"] * (mag[idx] - C["M1"]) + f_mag[idx]
    return f_mag


def _compute_distance_term(C, rhypo, mag):
    """
    Returns the distance attenuation adding the equations for global and regional terms (eq 7. and 8.)
    """
    scale = C["Tetha4"] + 0.275 * (mag - C["M1"])
    fdist = scale * np.log((rhypo**2 + 4.5**2)**0.5)
    return fdist + C["Tetha5"] * rhypo


def _compute_RVolc_term(C, rvolc):
    """
    Computes the term of attenuation by the path portion crossing the volcanic region
    """
    f_RVolc = C["Tetha6"]*rvolc
    return f_RVolc


def _compute_site_term(C_SITE, vs30):
    """
    Returns the site amplification from P and type list (Eq. 10)
    """
    f_sites = np.zeros_like(vs30)
    f_sites[vs30 >= 600] = C_SITE["s2"] * np.log(3.29)
    f_sites[(vs30 >= 370) & (vs30 < 600)] = C_SITE["s3"] * np.log(4.48)
    f_sites[(vs30 >= 230) & (vs30 < 370)] = C_SITE["s4"] * np.log(4.24)
    f_sites[(vs30 >= 0.0) & (vs30 < 230)] = C_SITE["s5"] * np.log(3.47)
    return f_sites


def _compute_Depth_term(C, hypo_depth):
    """
    Returns the depth term
    """
    return C["Tetha7"]*hypo_depth


class ArtetaEtAl2023_Vs30(GMPE):
    """
    Implements the model of Arteta et al (2021) as described in "Ground‐Motion
    Model (GMM) for Crustal Earthquakes in Northern South America (NoSAm
    Crustal GMM)" published on the Bulletin of the Seismological Society of
    America 2023 ( doi: https://doi.org/10.1785/0120220168) by Carlos A.
    Arteta, Cesar A. Pajaro, Vicente Mercado, Julián Montejo, Mónica Arcila,
    Norman A. Abrahamson;
    Soil term is associated with Vs30 using the simplification given in terms
    of natural period of HVRSR and mean value of P*
    """

    #: Supported tectonic region type is subduction interface
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Supported intensity measure types are spectral acceleration,
    #: and peak ground acceleration
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, SA}

    #: Supported intensity measure component is the geometric mean component
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.RotD50

    #: Supported standard deviation types are inter-event, intra-event
    #: and total, see section 4.5

    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL,
        const.StdDev.INTER_EVENT,
        const.StdDev.INTRA_EVENT
    ])

    #: Site amplification is dependent only upon Vs30
    REQUIRES_SITES_PARAMETERS = {'vs30'}

    #: Required rupture parameters are only magnitude for the interface model
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'hypo_depth'}

    #: Required distance measure is closest distance to rupture, for
    #: interface events
    REQUIRES_DISTANCES = {'rhypo', 'rvolc'}

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method <.base.GMPE.compute>`
        for spec of input and result values.
        """

        for m, imt in enumerate(imts):

            # extract dictionaries of coefficients specific to required
            # intensity measure type and for PGA
            C = self.COEFFS[imt]
            C_SITE = self.COEFFS_SITE[imt]

            # Get full model
            mean[m] = (_compute_base_term(C) +
                       _compute_magnitude_term(C, ctx.mag) +
                       _compute_distance_term(C, ctx.rhypo, ctx.mag) +
                       _compute_site_term(C_SITE, ctx.vs30) +
                       _compute_RVolc_term(C, ctx.rvolc) +
                       _compute_Depth_term(C, ctx.hypo_depth))

            sig[m], tau[m], phi[m] = _get_stddevs(C)

    COEFFS = CoeffsTable(sa_damping=5, table="""\
        imt	Tetha1	Tetha2	Tetha3	Tetha4	Tetha5	Tetha6	Tetha7	M1	Tau	Phi	Sigma
        PGA	-0.09036413715035	-0.10000000000000	0.00000000000000	-0.79000000000000	-0.00352290539285	-0.00546561424069	0.00827518138215	6.75	0.4300	0.7627169	0.8762061
        0.01	-0.09036413715035	-0.10000000000000	0.00000000000000	-0.79000000000000	-0.00352290539285	-0.00546561424069	0.00827518138215	6.75	0.4300	0.7627169	0.8762061
        0.02	-0.03163476464902	-0.10000000000000	0.00000000000000	-0.79000000000000	-0.00352290539285	-0.00531971750513	0.00827518138215	6.75	0.4000	0.7829162	0.8814521
        0.03	0.03803983153989	-0.10000000000000	0.00000000000000	-0.79000000000000	-0.00363290539285	-0.00523437338585	0.00827518138215	6.75	0.4100	0.7882987	0.8901769
        0.05	0.27268932473005	-0.10000000000000	0.00000000000000	-0.79000000000000	-0.00400640052793	-0.00512685251144	0.00827518138215	6.75	0.4400	0.7999928	0.9148708
        0.075	0.60357889389202	-0.10000000000000	0.00000000000000	-0.79000000000000	-0.00452272444232	-0.00504150839215	0.00827518138215	6.75	0.4600	0.8577381	0.9724786
        0.1	0.77250543153093	-0.10000000000000	0.00000000000000	-0.79000000000000	-0.00467558252445	-0.00498095577587	0.00827518138215	6.75	0.4900	0.8649259	0.9950361
        0.15	0.83031569129887	-0.10000000000000	0.00000000000000	-0.79000000000000	-0.00458263222610	-0.00489561165659	0.00827518138215	6.75	0.5500	0.8403353	1.0045713
        0.2	0.77177417567009	-0.10000000000000	0.00000000000000	-0.79000000000000	-0.00429041999020	-0.00483505904031	0.00827518138215	6.75	0.5500	0.8106246	0.9803633
        0.25	0.74406108525515	-0.10000000000000	-0.00200000000000	-0.79000000000000	-0.00391775471640	-0.00478809078218	0.00827518138215	6.75	0.5300	0.7754905	0.9404177
        0.3	0.69821259132840	-0.10000000000000	-0.00500000000000	-0.79000000000000	-0.00364935753065	-0.00474971492103	0.00827518138215	6.75	0.5300	0.7569856	0.9219692
        0.4	0.62586903534097	-0.10000000000000	-0.01960009546283	-0.79000000000000	-0.00301800756134	-0.00468916230475	0.00827518138215	6.75	0.5000	0.7611154	0.9095585
        0.5	0.56975501384440	-0.10000000000000	-0.04500000000000	-0.79000000000000	-0.00247688301109	-0.00464219404662	0.00827518138215	6.75	0.4900	0.7528100	0.8987341
        0.75	0.46779249842109	-0.10000000000000	-0.07811801033876	-0.79000000000000	-0.00171622454136	-0.00455684992733	0.00621850662809	6.75	0.4500	0.6891470	0.8230575
        1	0.39544894243366	-0.10000000000000	-0.10599108292670	-0.79000000000000	-0.00140926057664	-0.00439629731105	0.00475927266745	6.75	0.4300	0.6810577	0.8054437
        1.5	0.17664061846303	-0.10000000000000	-0.14687417215278	-0.79000000000000	-0.00116926057664	-0.00392977071920	0.00270259791339	6.75	0.3900	0.6951417	0.7970708
        2	-0.08174802136771	-0.10000000000000	-0.16775903473555	-0.79000000000000	-0.00105926057664	-0.00309952154089	0.00124336395275	6.75	0.3700	0.6892992	0.7823257
        3	-0.57719785948713	-0.10000000000000	-0.18504181640978	-0.79000000000000	-0.00095926057664	-0.00120000000000	-0.00081331080131	6.82	0.3700	0.6201469	0.7195882
        4	-0.87759786746456	-0.10000000000000	-0.19730414515362	-0.79000000000000	-0.00095926057664	-0.00035000000000	-0.00227254476196	6.92	0.3600	0.5703935	0.6744989
        5	-1.21369061239075	-0.10000000000000	-0.20681554626374	-0.76500000000000	-0.00095926057664	-0.00010000000000	-0.00340441455628	7	0.3600	0.5734581	0.6744473
        6	-1.64721216988727	-0.10000000000000	-0.21458692682785	-0.71100000000000	-0.00095926057664	0.00000000000000	-0.00432921951601	7.06	0.3500	0.5634325	0.6632919
        7.5	-2.25547443621606	-0.10000000000000	-0.22409832793798	-0.63400000000000	-0.00095926057664	0.00000000000000	-0.00546108931034	7.15	0.3500	0.5439533	0.6457470
        10	-3.04183101928269	-0.10000000000000	-0.23636065668181	-0.52900000000000	-0.00095926057664	0.00000000000000	-0.00692032327098	7.25	0.3500	0.5869896	0.6808684
    """)

    # Se añade esta tabla para los coeficientes
    COEFFS_SITE = CoeffsTable(sa_damping=5, table="""\
        imt	s2	s3	s4	s5
        PGA	0.337	0.692	0.679	0.609
        0.01	0.337	0.692	0.679	0.609
        0.02	0.337	0.683	0.672	0.609
        0.03	0.337	0.672	0.658	0.578
        0.05	0.337	0.643	0.58	0.505
        0.075	0.337	0.617	0.5	0.418
        0.1	0.363	0.649	0.477	0.366
        0.15	0.551	0.75	0.546	0.379
        0.2	0.527	0.832	0.62	0.457
        0.25	0.345	0.857	0.68	0.518
        0.3	0.186	0.83	0.769	0.582
        0.4	0.021	0.728	0.913	0.741
        0.5	-0.040	0.529	1	0.849
        0.75	-0.178	0.281	0.953	1.087
        1	-0.261	0.156	0.69	1.279
        1.5	-0.320	0.113	0.488	1.065
        2	-0.318	0.071	0.35	0.849
        3	-0.248	0.029	0.264	0.705
        4	-0.212	0.028	0.225	0.642
        5	-0.210	0.028	0.203	0.597
        6	-0.210	0.028	0.203	0.597
        7.5	-0.210	0.028	0.203	0.597
        10	-0.210	0.028	0.203	0.597
    """)


def _compute_site_term_Period(C_SITE, Periods, Amplitudes):
    """
    Returns the site amplification from periods and P* list
    """
    f_sites = np.zeros_like(Periods)
    f_sites[Periods <= 0.2] = C_SITE["s2"] * np.log(Amplitudes[Periods <= 0.2])
    f_sites[(Periods > 0.2) & (Periods <= 0.4)] = C_SITE["s3"] * np.log(Amplitudes[(Periods > 0.2) & (Periods <= 0.4)])
    f_sites[(Periods > 0.4) & (Periods <= 0.8)] = C_SITE["s4"] * np.log(Amplitudes[(Periods > 0.4) & (Periods <= 0.8)])
    f_sites[Periods > 0.8] = C_SITE["s5"] * np.log(Amplitudes[Periods > 0.8])
    f_sites[Amplitudes < 2] = 0
    return f_sites


class ArtetaEtAl2023(ArtetaEtAl2023_Vs30):
    """
    Implements the model of Arteta et al (2021) as described in "Ground‐Motion
    Model (GMM) for Crustal Earthquakes in Northern South America (NoSAm
    Crustal GMM)" published on the Bulletin of the Seismological Society of
    America 2023 ( doi: https://doi.org/10.1785/0120220168) by Carlos A.
    Arteta, Cesar A. Pajaro, Vicente Mercado, Julián Montejo, Mónica Arcila,
    Norman A. Abrahamson;
    Soil term depends of natural perod and peak value of HVRSR spectra
    """

    #: Supported tectonic region type is subduction interface
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Supported intensity measure types are spectral acceleration,
    #: and peak ground acceleration
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, SA}

    #: Supported intensity measure component is the geometric mean component
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.RotD50

    #: Supported standard deviation types are inter-event, intra-event
    #: and total, see section 4.5

    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL,
        const.StdDev.INTER_EVENT,
        const.StdDev.INTRA_EVENT
    ])

    #: Site amplification is dependent on the period and amplitude of HVRSR spectra
    REQUIRES_SITES_PARAMETERS = {'THV', 'PHV'}

    #: Required rupture parameters are only magnitude for the interface model
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'hypo_depth'}

    #: Required distance measure is closest distance to rupture, for
    #: interface events
    REQUIRES_DISTANCES = {'rhypo', 'rvolc'}

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method <.base.GMPE.compute>`
        for spec of input and result values.
        """

        for m, imt in enumerate(imts):

            # extract dictionaries of coefficients specific to required
            # intensity measure type and for PGA
            C = self.COEFFS[imt]
            C_SITE = self.COEFFS_SITE[imt]

            # Get full model
            mean[m] = (_compute_base_term(C) +
                       _compute_magnitude_term(C, ctx.mag) +
                       _compute_distance_term(C, ctx.rrup, ctx.mag) +
                       _compute_site_term_Period(C_SITE, ctx.THV, ctx.PHV) +
                       _compute_RVolc_term(C, ctx.rvolc) +
                       _compute_Depth_term(C, ctx.hypo_depth))

            sig[m], tau[m], phi[m] = _get_stddevs(C)
