# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2018 GEM Foundation
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
Module exports :class:`FarajpourEtAl2019`.
"""
import numpy as np
from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, SA


class FarajpourEtAl2019(GMPE):
    """
    Farajpour Z, Pezeshk S, Zare M (2019) A New Empirical Ground Motion
    Model for Iran Bulletin of the Seismological Society of America
    109:732-744 doi:10.1785/0120180139
    """
    #: Supported tectonic region type is active shallow crust
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Supported intensity measure types are spectral acceleration,
    #: and peak ground acceleration
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([
        PGA,
        SA
    ])

    #: Supported intensity measure component is the geometric mean of two
    #: horizontal components (see last paragraph  page 734)
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.AVERAGE_HORIZONTAL

    #: Supported standard deviation types are inter-event, intra-event
    #: and total, see equation 2, pag 106.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
       const.StdDev.TOTAL,
    ])

    #: Required site parameters is Vs30
    REQUIRES_SITES_PARAMETERS = {'vs30'}

    #: Required rupture parameters are magnitude, and rake.
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'rake', 'dip', 'ztor', 'width', 'hypo_depth'}

    #: Required distance measure is rrup
    REQUIRES_DISTANCES = {'rrup'}

    def get_mean_and_stddevs(self, sites, rup, dists, imt):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        # extracting dictionary of coefficients specific to required
        # intensity measure type.
        C = self.COEFFS[imt]
        pga_rock = self.get_pga_rock_values(self, rup, dists)
        return pga_rock
        def get_pga_rock_values(self, rup, dists):
            return (self._get_magnitudescaling_term(rup) +
                    self._get_styleoffaulting_term(rup) +
                    self._get_faultdip_term(rup) +
                    self._get_hypocentraldepth_term(rup) +
                    self._get_geometricattenuation_term(rup.mag, dists.rrup) +
    def _get_magnitudescaling_term(self, rup):
        """
        Returns the magnitude scling term defined in equation (4)
        """
        dmag = rup.mag - self.CONSTS["Mh"]
        if rup.mag <= self.CONSTS["Mh"]:
            mag_term = (1.3532 + 0.5437 * dmag) + (-0.1489 * (dmag ** 2.0))
        else:
            mag_term = (1.3532 + 1.147 * dmag) + (-0.1489 * (dmag ** 2.0))
        return  mag_term
    def _get_styleoffaulting_term(self, rup):
        """
        Returns the style-of-faulting scaling term defined in equations  6
        """
        if (rup.rake > -150.0) and (rup.rake < -30.0):
            fnm = 1.0
            frv = 0.0
        else:
            fnm = 0.0
            frv = 1.0

        fflt_f = (0.0965 * frv) + (0.0136 * fnm)
        return fflt_f 
    def _get_faultdip_term(self, rup):
        """
        Returns the fault dip term, defined in equation 8
        """
        if rup.mag <= 4.0:
            return -0.0031 * rup.dip
        elif rup.mag > 5.5:
            return 0.0
        else:
            return -0.0031 * (5.5 - rup.mag) * rup.dip
    def _get_hypocentraldepth_term(self, rup):
        """
        Returns the hypocentral depth scaling term defined in equations 7
        """
        if rup.hypo_depth <= 7.0:
            fhyp_h = 0.0
        elif rup.hypo_depth > 20.0:
            fhyp_h = 13.0
        else:
            fhyp_h = rup.hypo_depth - 7.0

        if rup.mag > 6.5:
            fhyp_m = -0.0676
        else:
            fhyp_m = -0.0355 + ((-0.0676 + 0.0355) * (rup.mag - 6.5))
        return fhyp_h * fhyp_m
            
    def _get_geometricattenuation_term(self, mag, rrup):
        """
        Returns the geometric attenuation term defined in equation 5
        """
        return (-0.739 + -0.0582 * mag) * np.log(np.sqrt((rrup ** 2.0) +
               (11.8246 ** 2.0)))
        mean = self.get_mean_values(C, sites, rup, dists, pga_rock)
        stddevs = self._get_stddevs(C)
        return mean, stddevs
        def get_mean_values(self, C, sites, rup, dists, pga_rock):
            return (self._get_magnitude_scaling_term(C, rup) +
                    self._get_style_of_faulting_term(C, rup) +
                    self._get_fault_dip_term(C, rup) +
                    self._get_hypocentral_depth_term(C, rup) +
                    self._get_geometric_attenuation_term(C, rup.mag, dists.rrup) +
                    self._get_anelastic_attenuation_term(C, dists.rrup)+
                    self._get_site_scaling(C, pga_rock, sites))
    def _get_magnitude_scaling_term(self, C, rup):
        """
        Returns the magnitude scling term defined in equation (4)
        """
        dmag = rup.mag - self.CONSTS["Mh"]
        if rup.mag <= self.CONSTS["Mh"]:
            mag_term = (C["z1"] + C["z2"] * dmag) + (C["z3"] * (dmag ** 2.0))
        else:
            mag_term = (C["z1"] + C["z4"] * dmag) + (C["z3"] * (dmag ** 2.0))
        return  mag_term
    def _get_style_of_faulting_term(self, C, rup):
        """
        Returns the style-of-faulting scaling term defined in equations  6
        """
        if (rup.rake > -150.0) and (rup.rake < -30.0):
            fnm = 1.0
            frv = 0.0
        else:
            fnm = 0.0
            frv = 1.0

        fflt_f = (self.CONSTS["c8"] * frv) + (C["c9"] * fnm)
        return fflt_f 
    def _get_fault_dip_term(self, C, rup):
        """
        Returns the fault dip term, defined in equation 8
        """
        if rup.mag <= 4.0:
            return C["z12"] * rup.dip
        elif rup.mag > 5.5:
            return 0.0
        else:
            return C["z12"] * (5.5 - rup.mag) * rup.dip
    def _get_hypocentral_depth_term(self, C, rup):
        """
        Returns the hypocentral depth scaling term defined in equations 7
        """
        if rup.hypo_depth <= 7.0:
            fhyp_h = 0.0
        elif rup.hypo_depth > 20.0:
            fhyp_h = 13.0
        else:
            fhyp_h = rup.hypo_depth - 7.0

        if rup.mag > 6.5:
            fhyp_m = C["z11"]
        else:
            fhyp_m = C["z10"] + ((C["z11"] - C["z10"]) * (rup.mag - 6.5))
        return fhyp_h * fhyp_m
            
    def _get_geometric_attenuation_term(self, C, mag, rrup):
        """
        Returns the geometric attenuation term defined in equation 5
        """
        return (C["z5"] + C["z6"] * mag) * np.log(np.sqrt((rrup ** 2.0) +
               (C["z7"] ** 2.0)))
    def _get_anelastic_attenuation_term(self, C, rrup):
        """
        Returns the anelastic attenuation term defined in equation 9
        """
        f_atn = np.zeros(len(rrup))
        idx = rrup > 80.0
        f_atn[idx] = (C["z13"] + C["Dz13"]) * (rrup[idx] - 80.0)
        return f_atn

    def _get_site_scaling(self, C, pga_rock, vs30):
        """
        Returns the shallow site response term defined in equations 10
        """
        vs_mod = vs30 / C["k1"]
        # Get linear global site response term
        f_site_g = C["z14"] * np.log(vs_mod)
        idx = vs30 > C["k1"]
        f_site_g[idx] = ((f_site_g[idx] + (C["k2"] * self.CONSTS["n"])) *
                        np.log(vs_mod[idx]))

        # Get nonlinear site response term
        idx = np.logical_not(idx)
        if np.any(idx):
            f_site_g[idx] = f_site_g[idx] + C["k2"] * (
                np.log(pga_rock[idx] +
                self.CONSTS["c"] * (vs_mod[idx] ** self.CONSTS["n"])) -
                np.log(pga_rock[idx] + self.CONSTS["c"])
                )
        return f_site_g

    def _get_stddevs(C):
        """
        Returns the aleatory uncertainty terms described in equations (11) to
        (13)
        """
        return C["σtotal"]


    COEFFS = CoeffsTable(sa_damping=5, table="""\
IMT  	  z1	  z2	   z3	   z4	   z5	   z6	  z7	  z8	  z9		  z10     z11	  z12	  z13	   z14      k1(m=s)	  k2	Δz13	τ	   ϕS2S   	ϕSS	    σtotal
PGA	    0.6755	0.362	-0.1889	1.0966	-0.8165	-0.0189	6.1175	0.0829	 0.0008		-0.0291	-0.061	-0.0025 	0        1.4323    865	-1.186	0		0.351	0.3482	0.568	0.753
0.04	0.9298	0.1165	-0.1944	1.0609	-1.0658	 0.0052	6.9438	0.1049	 0.0297		-0.0245	-0.0661	-0.0034 	0	     1.5027    865	-1.186	0		0.4256	0.3881	0.6366	0.8585
0.042	0.9749	0.0967	-0.1905	1.0305	-1.1055	 0.0103	7.0195	0.1063	 0.02		-0.0251	-0.0665	-0.0034 	0  	     1.5463	   865	-1.219	0		0.4328	0.3889	0.6399	0.8649
0.044	1.0408	0.1188	-0.1782	1.0308	-1.1043	 0.0085	6.999	0.1131	 0.0127		-0.0252	-0.0666	-0.0034 	0	     1.6095	   908	-1.273	0		0.4399	0.3913	0.6409	0.8703
0.05	1.2242	0.1259	-0.1679	1.0342	-1.1286	 0.0088	6.9802	0.1092	-0.0176		-0.0268	-0.0656	-0.0031 	0	     1.7041	   1054	-1.346	0		0.4471	0.4018	0.6401	0.8781
0.075	1.66	0.0212	-0.192	0.9548	-1.181	 0.0076	7.9789	0.14	-0.0747		-0.0329	-0.0687	-0.0035 	0	     1.8662	   1086	-1.471	0		0.4436	0.4027	0.6502	0.8841
0.1	    2.0911	0.0992	-0.2315	1.053	-0.9284	-0.0408	9.6673	0.1452	-0.0817		-0.0448	-0.0754	-0.0041    -0.0013	 2.0431	   1032	-1.624	0		0.4187	0.4258	0.6422	0.8769
0.15	2.0353	0.3265	-0.2677	1.2345	-0.5399	-0.0953	9.9547	0.1376	-0.0854		-0.0389	-0.0775	-0.0042    -0.0011	 2.3308	   878	-1.931	0		0.3836	0.4196	0.6422	0.8577
0.2	    1.8916	0.6147	-0.2189	1.2388	-0.3386	-0.1172	9.9145	0.0752	-0.1339		-0.0325	-0.0728	-0.0035    -0.0006   2.6048	   748	-2.188	0		0.3691	0.419	0.6355	0.846
0.26	1.6678	0.5766	-0.2461	1.1239	-0.4767	-0.0882	9.3351	0.0653	-0.099		-0.0278	-0.0555	-0.0023    -0.0009	 2.7557	   654	-2.381	0		0.3525	0.3946	0.648	0.8366
0.3	    1.528	0.5608	-0.2253	0.9742	-0.6159	-0.0625	8.5564	0.0598	-0.0667		-0.027	-0.0431	-0.0014    -0.0015	 2.8993	   587	-2.518	0		0.341	0.387	0.6443	0.8253
0.4	    0.9768	0.4991	-0.3047	1.0477	-0.5605	-0.0564	7.2139	0.0329	-0.1425		-0.0296	-0.0392	-0.0013    -0.0014	 2.9942	   503	-2.657	0		0.3433	0.3956	0.6377	0.8252
0.5	    0.6189	0.2368	-0.4144	1.0003	-0.7503	-0.0186	6.2354	0.006	-0.124		-0.0384	-0.0343	-0.0009    -0.0013	 2.9821	   457	-2.669	0		0.3329	0.3974	0.6407	0.8242
0.75   -0.0155	0.0406	-0.5258	1.0279	-0.9273	 0.0181	4.891	0.0135	-0.0489		-0.0384	-0.0246	-0.0009 	0	     2.6478	   410	-2.401	0		0.3359	0.4694	0.6201	0.8472
1	   -0.5112 -0.0313	-0.591	1.0189	-1.0528	 0.0444	3.7002	0.0571	-0.0505		-0.0298	-0.007	-0.0005 	0	     2.1147	   400	-1.955	0		0.3318	0.4957	0.6296	0.8673
1.5	   -1.0965	0.0807	-0.5343	0.9274	-1.1721	 0.0648	2.5564	0.1053	-0.0635		-0.0442	-0.0157	-0.0021 	0	     0.9805	   400	-1.025	0		0.3465	0.5206	0.627	0.8856
2      -1.5241 -0.0773	-0.597	0.8714	-1.2985	 0.0861	2.4747	0.1032	-0.101		-0.0677	-0.0311	-0.0038 	0	     0.1017	   400	-0.299	0		0.3612	0.5163	0.612	0.8784
3	   -1.9509 -0.033	-0.689	0.974	-1.1284	 0.0588	2.5339	0.0619	-0.2605		-0.0843	-0.0349	-0.005  	0	    -0.2572	   400	 0	    0		0.5145	0.4871	0.5637	0.9054
""")

    CONSTS = {
        "c8": 0,
        "Mh": 6.5,
        "n": 1.18,
        "c": 1.88}
