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
Module exports :class:`ArtetaEtAl2021Inter`
               :class:`ArtetaEtAl2021Slab`
               :class:`ArtetaEtAl2021Inter_Vs30`
               :class:`ArtetaEtAl2021Slab_Vs30`
"""
import numpy as np
from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, SA

CONSTS = {"C1Slab": 6.5}


def _get_stddevs(C, rrup):
    """
    Return standard deviations as defined in Table 3
    """
    phi = np.zeros_like(rrup)
    tau = np.zeros_like(rrup)
    phi[rrup <= 150] = C["Phi1"]
    phi[rrup >= 200] = C["Phi2"]
    idx = (rrup > 150) & (rrup < 200)
    phi[idx] = C["Phi1"] + ((C["Phi2"] - C["Phi1"]) * (rrup[idx] - 150) * 0.02)
    tau = C['Tau']
    return [np.sqrt(tau**2 + phi**2), tau, phi]


def _compute_base_term(C):
    """
    Returns the base coefficient of the GMPE, which for interface events
    is just the coefficient a1 (adjusted regionally)
    """
    return C["Teta1"]


def _compute_magnitude_term(C, mag):
    """
    Returns the magnitude scaling term
    """
    f_mag = C["Teta3"] * ((10.0 - mag) ** 2.)
    idx = mag <= C["MC1"]
    f_mag[idx] = C["Teta2"] * (mag[idx] - C["MC1"]) + f_mag[idx]
    return f_mag


def _compute_distance_term(C, rrup, mag):
    """
    Returns the distance attenuation
    """
    scale = C["Teta4"] + 0.1 * (mag - 7)
    fdist = scale * np.log(rrup + 10 * np.exp(0.4 * (mag - 6.0)))
    return fdist + C["Teta5"] * rrup


def _compute_site_term(C_SITE, vs30):
    """
    Returns the site amplification from P and type list
    """
    f_sites = np.zeros_like(vs30)
    f_sites[vs30 >= 600] = C_SITE["s2"] * np.log(3.29)
    f_sites[(vs30 >= 370) & (vs30 < 600)] = C_SITE["s3"] * np.log(4.48)
    f_sites[(vs30 >= 230) & (vs30 < 370)] = C_SITE["s4"] * np.log(4.24)
    f_sites[(vs30 >= 0.0) & (vs30 < 230)] = C_SITE["s5"] * np.log(3.47)
    return f_sites


class ArtetaEtAl2021InterVs30(GMPE):
    """
    Implements the model of Arteta et al (2021) as described in "Ground-motion
    model for subduction earthquakes in northern South America" by Arteta et
    al. (2021) - Earthquake Spectra, https://doi.org/10.1177/87552930211027585

    Soil term is associated with Vs30 using the simplification given in terms
    of natural period of HVRSR and mean value of P*
    """

    #: Supported tectonic region type is subduction interface
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTERFACE

    #: Supported intensity measure types are spectral acceleration,
    #: and peak ground acceleration
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, SA}

    #: Supported intensity measure component is the geometric mean component
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.RotD50

    #: Supported standard deviation types are inter-event, intra-event
    #: and total, see section 4.5

    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL, const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT}

    #: Site amplification is dependent only upon Vs30
    REQUIRES_SITES_PARAMETERS = {'vs30'}

    #: Required rupture parameters are only magnitude for the interface model
    REQUIRES_RUPTURE_PARAMETERS = {'mag'}

    #: Required distance measure is closest distance to rupture, for
    #: interface events
    REQUIRES_DISTANCES = {'rrup'}

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
                       _compute_site_term(C_SITE, ctx.vs30))
            sig[m], tau[m], phi[m] = _get_stddevs(C, ctx.rrup)

    # Actualizado, los terminos de la incertidumbre se ajustaron paro T 0.03
    COEFFS = CoeffsTable(sa_damping=5, table="""\
        imt	Teta1	Teta2	Teta3	Teta4	Teta5	MC1	Tau	Phi1	Phi2	Sigma1	Sigma2	Phis2s	Phiss	Sigmass
        PGA	4.329	0.73	-0.021	-1.45	-0.006	8.2	0.452	0.726	0.817	0.855	0.934	0.729	0.522	0.69
        0.01	4.329	0.73	-0.021	-1.45	-0.006	8.2	0.452	0.726	0.817	0.855	0.934	0.729	0.522	0.69
        0.02	4.347	0.73	-0.021	-1.45	-0.006	8.2	0.448	0.739	0.832	0.864	0.945	0.729	0.522	0.688
        0.03	4.36	0.73	-0.021	-1.45	-0.006	8.2	0.439	0.777	0.841	0.893	0.949	0.746	0.574	0.723
        0.05	4.473	0.73	-0.021	-1.45	-0.006	8.2	0.439	0.798	0.854	0.911	0.96	0.763	0.659	0.792
        0.075	4.679	0.73	-0.021	-1.45	-0.007	8.2	0.446	0.836	0.892	0.948	0.997	0.796	0.674	0.808
        0.1	4.893	0.73	-0.021	-1.45	-0.008	8.2	0.444	0.753	0.965	0.874	1.062	0.738	0.63	0.771
        0.15	5.07	0.73	-0.023	-1.425	-0.008	8.2	0.459	0.708	0.982	0.844	1.084	0.628	0.65	0.796
        0.2	4.95	0.73	-0.025	-1.335	-0.008	8.2	0.519	0.73	0.962	0.896	1.093	0.588	0.647	0.83
        0.25	4.9	0.73	-0.029	-1.275	-0.008	8.2	0.559	0.83	0.916	1.001	1.073	0.597	0.668	0.871
        0.3	4.85	0.73	-0.038	-1.231	-0.008	8.2	0.535	0.806	0.944	0.967	1.085	0.584	0.63	0.826
        0.4	4.65	0.73	-0.057	-1.165	-0.008	8.2	0.508	0.704	0.85	0.868	0.99	0.591	0.592	0.78
        0.5	4.334	0.73	-0.072	-1.115	-0.007	8.2	0.509	0.715	0.867	0.877	1.005	0.604	0.585	0.775
        0.75	3.564	0.73	-0.099	-1.02	-0.007	8.15	0.536	0.627	0.821	0.824	0.981	0.551	0.499	0.732
        1	2.957	0.73	-0.118	-0.95	-0.006	8.1	0.598	0.658	0.822	0.889	1.016	0.565	0.445	0.745
        1.5	1.986	0.73	-0.145	-0.86	-0.006	8.05	0.631	0.675	0.804	0.924	1.022	0.588	0.404	0.749
        2	1.323	0.73	-0.164	-0.82	-0.005	8	0.592	0.716	0.807	0.929	1	0.6	0.478	0.761
        3	0.518	0.73	-0.191	-0.793	-0.005	7.9	0.57	0.696	0.759	0.899	0.949	0.602	0.543	0.787
        4	-0.022	0.73	-0.21	-0.793	-0.004	7.85	0.525	0.748	0.731	0.914	0.9	0.603	0.589	0.789
        5	-0.437	0.73	-0.22	-0.793	-0.003	7.8	0.494	0.747	0.775	0.895	0.919	0.629	0.51	0.71
        6	-0.784	0.73	-0.224	-0.793	-0.003	7.8	0.455	0.791	0.807	0.913	0.927	0.632	0.48	0.662
        7.5	-1.281	0.73	-0.224	-0.793	-0.002	7.8	0.44	0.746	0.831	0.866	0.94	0.636	0.444	0.625
        10	-1.883	0.73	-0.224	-0.793	-0.001	7.8	0.468	0.724	0.791	0.862	0.919	0.64	0.39	0.609
    """)

    # Se añade esta tabla para los coeficientes
    COEFFS_SITE = CoeffsTable(sa_damping=5, table="""\
        imt	s2	s3	s4	s5
        PGA	0.74	0.966	0.959	0.986
        0.01	0.74	0.966	0.959	0.986
        0.02	0.828	0.99	0.994	0.971
        0.03	0.896	0.964	0.989	0.959
        0.05	1.011	0.941	0.955	0.885
        0.075	1.196	0.948	0.899	0.783
        0.1	1.237	1.022	0.85	0.692
        0.15	1.18	1.182	0.772	0.582
        0.2	1.016	1.21	0.706	0.514
        0.25	0.85	1.221	0.693	0.509
        0.3	0.65	1.119	0.732	0.531
        0.4	0.227	0.628	0.934	0.601
        0.5	0.094	0.434	0.949	0.687
        0.75	-0.047	0.233	0.784	0.865
        1	-0.146	0.143	0.632	0.881
        1.5	-0.287	0.026	0.384	0.692
        2	-0.386	-0.011	0.225	0.386
        3	-0.438	-0.041	0.09	0.13
        4	-0.438	-0.041	0.042	0.052
        5	-0.438	-0.041	0.022	0.012
        6	-0.438	-0.041	0.022	0.012
        7.5	-0.438	-0.041	0.022	0.012
        10	-0.438	-0.041	0.022	0.012
    """)


def _compute_site_term_Period(C_SITE, periods, ampl):
    """
    Returns the site amplification from P and type list
    """
    f_sites = np.zeros_like(periods)
    f_sites[periods <= 0.2] = C_SITE["s2"] * np.log(ampl[periods <= 0.2])
    f_sites[(periods > 0.2) & (periods <= 0.4)] = \
        C_SITE["s3"] * np.log(ampl[(periods > 0.2) & (periods <= 0.4)])
    f_sites[(periods > 0.4) & (periods <= 0.8)] = \
        C_SITE["s4"] * np.log(ampl[(periods > 0.4) & (periods <= 0.8)])
    f_sites[periods > 0.8] = C_SITE["s5"] * np.log(ampl[periods > 0.8])
    f_sites[ampl < 2] = 0
    return f_sites


class ArtetaEtAl2021Inter(ArtetaEtAl2021InterVs30):

    """
    Implements the model of Arteta et al (2021) as described in "Ground-motion
    model for subduction earthquakes in northern South America" by Arteta et
    al. (2021) - Earthquake Spectra, https://doi.org/10.1177/87552930211027585

    Soil term depends of natural perod and pick value of HVRSR spectra
    """

    #: Supported tectonic region type is subduction interface
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTERFACE

    #: Supported intensity measure types are spectral acceleration,
    #: and peak ground acceleration
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, SA}

    #: Supported intensity measure component is the geometric mean component
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.RotD50

    #: Supported standard deviation types are inter-event, intra-event
    #: and total, see section 4.5

    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL, const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT}

    #: Amplification is dependent on the period and amplitude of HVRSR spectra
    REQUIRES_SITES_PARAMETERS = {'THV', 'PHV'}

    #: Required rupture parameters are only magnitude for the interface model
    REQUIRES_RUPTURE_PARAMETERS = {'mag'}

    #: Required distance measure is closest distance to rupture, for
    #: interface events
    REQUIRES_DISTANCES = {'rrup'}

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
                       _compute_site_term_Period(C_SITE, ctx.THV, ctx.PHV))
            sig[m], tau[m], phi[m] = _get_stddevs(C, ctx.rrup)


def _compute_magnitude_term_slab(C, mag):
    """
    Returns the magnitude scaling term
    """
    idx = mag <= CONSTS['C1Slab']
    fmag = C["Teta3"] * (10.0 - mag) ** 2.
    fmag[idx] = C["Teta2"] * (mag[idx] - CONSTS['C1Slab']) + fmag[idx]
    return fmag


def _compute_distance_term_slab(C, rhypo, mag):
    """
    Returns the distance attenuation
    """
    scale = C["Teta4"] + 0.1 * (mag - 7)
    fdist = scale * np.log(rhypo + 10 * np.exp(0.4 * (mag - 6.0)))
    return fdist + C["Teta5"] * rhypo


def _compute_forearc_backarc_term_slab(C, sites, dists):
    """
    Computes the forearc/backarc scaling term given by equation (4)
    """
    # Term only applies to backarc sites (F_FABA = 0. for forearc)
    f_faba = sites.backarc * C['Teta6']
    return f_faba


def _get_stddevs_slab(C, rhypo):
    """
    Return standard deviations as defined in Table 3
    """
    phi = np.zeros_like(rhypo)
    tau = np.zeros_like(rhypo)
    phi[rhypo <= 150] = C["Phi1"]
    phi[rhypo >= 200] = C["Phi2"]
    idx = (rhypo > 150) & (rhypo < 200)
    phi[idx] = C["Phi1"] + ((C["Phi2"] - C["Phi1"]) *
                            (rhypo[idx] - 150) * 0.02)
    tau = C['Tau']
    return [np.sqrt(tau**2 + phi**2), tau, phi]


class ArtetaEtAl2021SlabVs30(ArtetaEtAl2021InterVs30):

    """
    Implements the model of Arteta et al (2021) as described in "Ground-motion
    model for subduction earthquakes in northern South America" by Arteta et
    al. (2021) - Earthquake Spectra, https://doi.org/10.1177/87552930211027585

    Soil term is associated with Vs30 using the simplification given in terms
    of natural period of HVRSR and mean value of P*
    """
    #: Supported tectonic region type is subduction in-slab
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTRASLAB

    #: Required distance measure is hypocentral for in-slab events
    REQUIRES_DISTANCES = {'rhypo'}
    REQUIRES_SITES_PARAMETERS = {'backarc'}

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
                       _compute_magnitude_term_slab(C, ctx.mag) +
                       _compute_distance_term_slab(C, ctx.rhypo, ctx.mag) +
                       _compute_site_term(C_SITE, ctx.vs30) +
                       _compute_forearc_backarc_term_slab(C, ctx, ctx.rhypo))

            sig[m], tau[m], phi[m] = _get_stddevs_slab(C, ctx.rhypo)

    # Actualizado, los terminos de la incertidumbre se ajustaron paro T 0.03
    COEFFS = CoeffsTable(sa_damping=5, table="""\
        imt	Teta1	Teta2	Teta3	Teta4	Teta5	Teta6	Tau	Phi1	Phi2	Sigma1	Sigma2	Phis2s	Phiss	Sigmass
        PGA	4.639	1.07	-0.027	-1.45	-0.005	-0.653	0.364	0.707	0.834	0.795	0.909	0.556	0.569	0.676
        0.01	4.639	1.07	-0.027	-1.45	-0.005	-0.653	0.364	0.707	0.834	0.795	0.909	0.556	0.569	0.676
        0.02	4.714	1.07	-0.027	-1.45	-0.005	-0.653	0.356	0.699	0.848	0.784	0.92	0.566	0.576	0.678
        0.03	4.752	1.07	-0.027	-1.45	-0.005	-0.653	0.359	0.704	0.856	0.79	0.928	0.572	0.583	0.684
        0.05	4.951	1.07	-0.027	-1.45	-0.005	-0.653	0.34	0.725	0.873	0.801	0.937	0.587	0.586	0.678
        0.075	5.126	1.07	-0.027	-1.42	-0.006	-0.717	0.318	0.791	0.902	0.853	0.957	0.595	0.627	0.703
        0.1	5.153	1.07	-0.027	-1.364	-0.006	-0.807	0.308	0.855	0.977	0.909	1.024	0.604	0.706	0.77
        0.15	4.975	1.07	-0.027	-1.298	-0.006	-0.862	0.351	0.853	0.995	0.922	1.056	0.614	0.711	0.793
        0.2	4.65	1.07	-0.027	-1.258	-0.006	-0.857	0.358	0.793	0.983	0.87	1.046	0.628	0.667	0.757
        0.25	4.3	1.07	-0.027	-1.227	-0.005	-0.824	0.345	0.782	0.942	0.855	1.003	0.609	0.626	0.715
        0.3	4	1.07	-0.027	-1.201	-0.004	-0.766	0.358	0.731	0.972	0.814	1.035	0.641	0.635	0.729
        0.4	3.5	1.07	-0.03	-1.161	-0.003	-0.628	0.382	0.6	0.889	0.712	0.967	0.614	0.528	0.652
        0.5	3.118	1.07	-0.037	-1.13	-0.003	-0.521	0.416	0.656	0.913	0.777	1.003	0.619	0.56	0.698
        0.75	2.4	1.07	-0.056	-1.074	-0.003	-0.329	0.452	0.748	0.88	0.874	0.989	0.623	0.527	0.695
        1	1.821	1.07	-0.072	-1	-0.003	-0.192	0.466	0.694	0.85	0.836	0.969	0.63	0.494	0.679
        1.5	0.953	1.07	-0.085	-0.958	-0.002	-0.089	0.453	0.581	0.839	0.737	0.953	0.585	0.508	0.68
        2	0.34	1.07	-0.095	-0.938	-0.002	-0.036	0.422	0.552	0.841	0.695	0.941	0.576	0.512	0.664
        3	-0.458	1.07	-0.104	-0.933	-0.002	-0.018	0.398	0.573	0.809	0.697	0.901	0.57	0.47	0.616
        4	-1.033	1.07	-0.107	-0.933	-0.002	-0.018	0.405	0.549	0.757	0.682	0.859	0.57	0.412	0.578
        5	-1.468	1.07	-0.109	-0.933	-0.002	-0.018	0.415	0.578	0.781	0.711	0.885	0.588	0.462	0.621
        6	-1.825	1.07	-0.109	-0.933	-0.002	-0.018	0.427	0.627	0.813	0.758	0.918	0.607	0.501	0.658
        7.5	-2.265	1.07	-0.109	-0.933	-0.002	-0.018	0.446	0.68	0.825	0.813	0.938	0.635	0.519	0.684
        10	-2.755	1.07	-0.109	-0.933	-0.002	-0.018	0.486	0.691	0.761	0.845	0.903	0.598	0.544	0.73
    """)

    # Se añade esta tabla para los coeficientes
    COEFFS_SITE = CoeffsTable(sa_damping=5, table="""\
        imt	s2	s3	s4	s5
        PGA	0.745	0.892	0.933	0.886
        0.01	0.745	0.892	0.933	0.886
        0.02	0.723	0.879	0.932	0.862
        0.03	0.725	0.863	0.936	0.81
        0.05	0.752	0.806	0.889	0.747
        0.075	0.823	0.795	0.825	0.653
        0.1	0.929	0.82	0.785	0.561
        0.15	0.953	0.917	0.785	0.505
        0.2	0.849	1.018	0.95	0.553
        0.25	0.691	1.101	1.066	0.659
        0.3	0.556	1.113	1.153	0.744
        0.4	0.499	1.003	1.281	0.904
        0.5	0.442	0.829	1.283	1.082
        0.75	0.391	0.535	1.146	1.403
        1	0.355	0.409	0.98	1.35
        1.5	0.304	0.317	0.756	1.092
        2	0.278	0.282	0.666	0.909
        3	0.267	0.257	0.597	0.751
        4	0.267	0.247	0.577	0.724
        5	0.267	0.247	0.567	0.724
        6	0.267	0.247	0.567	0.724
        7.5	0.267	0.247	0.567	0.724
        10	0.267	0.247	0.567	0.724
    """)


class ArtetaEtAl2021Slab(ArtetaEtAl2021SlabVs30):
    """
    Implements the model of Arteta et al (2021) as described in "Ground-motion
    model for subduction earthquakes in northern South America" by Arteta et
    al. (2021) - Earthquake Spectra, https://doi.org/10.1177/87552930211027585

    Soil term depends of natural perod and pick value of HVRSR spectra
    """
    #: Site amplification is dependent on the period and amplitude of HVRSR
    #: spectra
    REQUIRES_SITES_PARAMETERS = {'THV', 'PHV', 'backarc'}

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GMPE.compute>` for spec of input and result values.
        """

        for m, imt in enumerate(imts):

            # extract dictionaries of coefficients specific to required
            # intensity measure type and for PGA
            C = self.COEFFS[imt]
            C_SITE = self.COEFFS_SITE[imt]

            # Get full model
            mean[m] = (_compute_base_term(C) +
                       _compute_magnitude_term_slab(C, ctx.mag) +
                       _compute_distance_term_slab(C, ctx.rhypo, ctx.mag) +
                       _compute_site_term_Period(C_SITE, ctx.THV, ctx.PHV) +
                       _compute_forearc_backarc_term_slab(C, ctx, ctx.rhypo))

            sig[m], tau[m], phi[m] = _get_stddevs_slab(C, ctx.rhypo)
