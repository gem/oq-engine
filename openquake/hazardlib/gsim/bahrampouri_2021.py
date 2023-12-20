# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2021 GEM Foundation
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
Module exports :class:`bahrampouriEtAl2021IA`,
class:`bahrampouriEtAl2021Asc`,
class:`bahrampouriEtAl2021SSlab`,
class:`bahrampouriEtAl2021SInter`,
"""
import numpy as np
from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import IA
import shapely.geometry as sg
from shapely.geometry import LineString



# coordinates from the author
# Kyushu - VOLCANIC_FRONT
kyushu = LineString([(127.067, 27.250), (128.983, 28.800), (130.217, 30.433),
                     (130.817, 32.767), (131.600, 33.567), (131.850, 34.367)])
# Honshu - VOLCANIC_FRONT
honshu = LineString([(148.583, 45.417), (146.917, 44.450), (144.717, 43.683),
                     (144.017, 43.600), (142.683, 43.500), (141.517, 43.400),
                     (140.667, 42.050), (141.117, 41.267), (141.000, 40.450),
                     (140.583, 39.033), (140.133, 37.733), (138.367, 36.600),
                     (138.733, 35.383), (139.750, 33.133), (140.300, 30.483),
                     (140.567, 28.317), (141.267, 25.417)])


def _compute_magnitude(ctx, C, trt):
    """
    Compute the source term described in Eq. 7 for ASC and 9 for subduction
    """

    if trt == const.TRT.ACTIVE_SHALLOW_CRUST:
        fsource = (C['a1'] + C['a2'] * ctx.mag +
                   C['a3'] * np.maximum((ctx.mag - C['a4']), 0) +
                   C['a7'] * np.log((ctx.ztor) + 1))
    else:
        if trt == const.TRT.SUBDUCTION_INTERFACE:
            Finter = 1
        elif trt == const.TRT.SUBDUCTION_INTRASLAB:
            Finter = 0
        fsource = (C['a1'] + C['a2'] * ctx.mag +
                   C['a3'] * np.maximum((ctx.mag - C['a4']), 0) +
                   C['a5'] * np.maximum((ctx.mag - C['a6']), 0) +
                   C['a7'] * np.log((ctx.ztor) + 1) + C['a8'] * Finter)
    return fsource


def _get_source_saturation_term(ctx, C):
    """
    Compute the near source saturation as described in Eq. 11
    """
    h = np.zeros_like(ctx.mag)
    h = (C['b9'] + C['b10'] * (ctx.mag - C['b7']) +
         C['b11'] * (ctx.mag - C['b7'])**2 +
         C['b12'] * (ctx.mag - C['b7'])**3)
    before = ctx.mag <= C['b7']
    after = ctx.mag > C['b8']
    h[before] = C['b5'] + C['b6'] * (ctx.mag[before] - C['b7'])
    h[after] = C['b13'] + C['b14'] * (ctx.mag[after] - C['b8'])
    return h


def _get_site_term(ctx, C):
    """
    compute site scaling as described in Eq.12
    Fsite = c1*ln(vs30)

    """
    fsite = C['c1'] * np.log(ctx.vs30)
    return fsite


def _get_stddevs(C):

    sig = C['sig']
    tau = C['tau']
    phi = np.sqrt(C['phi_ss']**2 + C['phi_s2s']**2)
    return sig, tau, phi


def _check_cm_ck(kyushu, honshu, ctx):
    """
    To check if the source to site path crosses either of the volcanic regions.
    - Cm is 1 if the path from the source to the site crosses the volcanic
        front in Honshu and Hokkaido and 0 otherwise;
    - CK is 1 if the path from the source to the site crosses the volcanic
        front in Kyushu and 0 otherwise;
    - There is a possibility that the path may not cross either of the volcanic
        fronts. In such cases, these coefficients are taken as 0.
    """
    tmp = np.array([kyushu.crosses(LineString([(hypo_lon, hypo_lat), (lon, lat)]))
                    for hypo_lon, hypo_lat, lon, lat in
                    zip(ctx.hypo_lon, ctx.hypo_lat, ctx.lon, ctx.lat)])
    tmp_1 = np.array([honshu.crosses(LineString([(hypo_lon, hypo_lat), (lon, lat)]))
                     for hypo_lon, hypo_lat, lon, lat in
                     zip(ctx.hypo_lon, ctx.hypo_lat, ctx.lon, ctx.lat)])
    ck = tmp.astype(int)
    cm = tmp_1.astype(int)
    return cm, ck


def _compute_volcanic_distances(ctx, kyushu, honshu):
    cm, ck = _check_cm_ck(kyushu, honshu, ctx)
    """
    the buffer regions have been chosen in such a way that
    the backarc of Honshu and forearc of Kyushu is calculated.
    These buffer regions helps in understanding if a given site
    belongs to the forearc or backarc of the volcanic front.
    These buffer regions were arbitrarily chosen. There is scope
    for improvement in the future when more information is made
    available about the backarc and forearc of the volcanic fronts.
    """
    buffer_region = honshu.buffer(-3.0, single_sided=True)  # backarc
    buffer_region_1 = kyushu.buffer(-3.0, single_sided=True)  # forearc

    for m, k, lon, lat in zip(cm, ck, ctx.lon, ctx.lat):
        if m == 1:  # the site is in either the forearc or back arc of Honshu
            dst = honshu.distance(sg.Point(lon, lat))
            rrup_b = np.where(sg.Point(lon, lat).within(buffer_region),
                              dst, ctx.rrup - dst)
            rrup_f = np.where(sg.Point(lon, lat).within(buffer_region),
                              ctx.rrup - dst, dst)
        elif k == 1:  # the site is in either the forearc or back arc of Kyushu
            dst = kyushu.distance(sg.Point(lon, lat))
            rrup_f = np.where(sg.Point(lon, lat).within(buffer_region_1),
                              dst, ctx.rrup - dst)
            rrup_b = np.where(sg.Point(lon, lat).within(buffer_region_1),
                              ctx.rrup - dst, dst)
        else:
            # the source to site path does not cross any volcanic front but the site
            # can still be in the backarc of honshu or forearc of Kyushu volcanic front
            tmp = sg.Point(lon, lat).within(buffer_region)
            tmp_1 = sg.Point(lon, lat).within(buffer_region_1)
            if tmp:  # check if the site is in the backarc region of honshu
                rrup_b = honshu.distance(sg.Point(lon, lat))
                rrup_f = ctx.rrup - rrup_b
            elif tmp_1:  # check if the site is in the forearcarc region of Kyushu
                rrup_f = kyushu.distance(sg.Point(lon, lat))
                rrup_b = ctx.rrup - rrup_f
            else:
                # a neutral case wherein the site is not located in the vicinity of
                # either of the volcanic fronts
                rrup_f = 0
                rrup_b = 0
    return rrup_f, rrup_b, cm, ck


def _compute_distance(ctx, C, trt):
    """
    f = forearc
    b = backarc
    """
    rrup_b, rrup_f, cm, ck = _compute_volcanic_distances(ctx, kyushu, honshu)
    sst = _get_source_saturation_term(ctx, C)
    tmp = (10**sst)**2
    if trt == const.TRT.ACTIVE_SHALLOW_CRUST:
        fpath = (C['b1']*(np.log(np.sqrt((ctx.rrup**2) + tmp))) +
                 C['b3b'] * rrup_b + C['b3f'] * rrup_f +
                 C['b4m']*cm + C['b4k']*ck)
    else:
        if trt == const.TRT.SUBDUCTION_INTERFACE:
            Finter = 1
        elif trt == const.TRT.SUBDUCTION_INTRASLAB:
            Finter = 0
        fpath = ((C['b1'] +
                  C['b2']*Finter) * (np.log(np.sqrt((ctx.rrup**2) + tmp))) +
                 C['b3b'] * rrup_b + C['b3f'] * rrup_f +
                 C['b4m']*cm + C['b4k']*ck)
    return fpath


def _get_arias_intensity_term(ctx, C, trt):
    """
    Implementing Eq. 6
    """
    ia_l = (_compute_magnitude(ctx, C, trt) +
            _compute_distance(ctx, C, trt) +
            _get_site_term(ctx, C))
    return ia_l


def _get_arias_intensity_second_term(ctx, C, trt):
    """
    This is the second term in Eq. 5
    """
    t1 = []
    for i, x in enumerate(ctx.vs30):
        g = np.exp(C['c3']*(min(ctx.vs30[i], 1100)-280))
        t1.append(g)
    t2 = np.exp(C['c3']*(1100-280))
    tmp = (np.exp(_get_arias_intensity_term(ctx, C, trt))+C['c4'])/C['c4']
    t3 = np.log(tmp)
    ia_2 = C['c2'] * (t1 - t2) * t3
    return ia_2


class BahrampouriEtAl2021Asc(GMPE):
    """
    Implements GMPE by Mahdi Bahrampouri, Adrian Rodriguez-Marek and Russell A
    Green developed from the Kiban-Kyoshin network (KiK)-net database. This
    GMPE is specifically derived for arias intensity. This GMPE is described in
    a paper published in 2021 on Earthquake Spectra, Volume 37, Pg 428-448 and
    titled 'Ground motion prediction equations for Arias Intensity using the
    Kik-net database'.
    """

    #: Supported tectonic region type is active shallow crust
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Supported intensity measure types are areas intensity
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {IA}

    #: Supported intensity measure component is geometric mean
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GEOMETRIC_MEAN

    #: Supported standard deviation types are inter-event, intra-event
    #: and total, see paragraph "Equations for standard deviations", page
    #: 1046.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL, const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT}

    #: Required site parameters are Vs30 and coordinates of the site
    REQUIRES_SITES_PARAMETERS = {'lon', 'lat', 'vs30'}

    #: Required rupture parameters are magnitude,ztor
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'ztor', 'hypo_lon', 'hypo_lat'}

    #: Required distance measures are rrup (see Table 2, page 1031).
    REQUIRES_DISTANCES = {'rrup'}

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        trt = self.DEFINED_FOR_TECTONIC_REGION_TYPE

        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            # Implements mean model (equation 12)
            mean[m] = (_get_arias_intensity_term(ctx, C, trt) +
                       _get_arias_intensity_second_term(ctx, C, trt))
            sig[m], tau[m], phi[m] = _get_stddevs(C)

    #: For Ia, coefficients are taken from table 3
    COEFFS = CoeffsTable(sa_damping=5, table="""    IMT      a1     a2      a3    a4    a7     b1      b3b    b3f     b4m     b4k      b5    b6   b7   b8     b9    b10    b11     b12     b13   b14     c1      c2      c3    c4   phi_ss    tau    phi_s2s   sig
    ia    -4.2777 2.9352 -2.3986 7.0 0.7008 -2.8299 -0.0039 -0.0016 -0.6542 -0.2876 0.7497 0.43 5.744 7.744 0.7497 0.43 -0.0488 -0.08312 1.4147 0.235 -1.1076 -0.3607 -0.0077 0.35 0.761585 0.77617 0.840053 1.374096
    """)


class BahrampouriEtAl2021SInter(GMPE):
    """
    Implements GMPE by Mahdi Bahrampouri, Adrian Rodriguez-Marek and Russell A
    Green developed from the Kiban-Kyoshin network (KiK)-net database. This
    GMPE is specifically derived for arias intensity. This GMPE is described in
    a paper published in 2021 on Earthquake Spectra, Volume 37, Pg 428-448 and
    titled 'Ground motion prediction equations for Arias Intensity using the
    Kik-net database'.
    """

    #: Supported tectonic region type is SUBDUCTION INTERFACE, see title!
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTERFACE

    #: Supported intensity measure types are areas intensity
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {IA}

    #: Supported intensity measure component is geometric mean
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GEOMETRIC_MEAN

    #: Supported standard deviation types are inter-event, intra-event
    #: and total, see paragraph "Equations for standard deviations", page
    #: 1046.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL, const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT}

    #: Required site parameters are Vs30 and coordinates of the site
    REQUIRES_SITES_PARAMETERS = {'lon', 'lat', 'vs30'}

    #: Required rupture parameters are magnitude,ztor
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'ztor', 'hypo_lon', 'hypo_lat'}

    #: Required distance measures are rrup (see Table 2, page 1031).
    REQUIRES_DISTANCES = {'rrup'}

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        trt = self.DEFINED_FOR_TECTONIC_REGION_TYPE
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            # Implements mean model (equation 12)
            mean[m] = (_get_arias_intensity_term(ctx, C, trt) +
                       _get_arias_intensity_second_term(ctx, C, trt))
            sig[m], tau[m], phi[m] = _get_stddevs(C)

    #: For Ia, coefficients are taken from table 3
    COEFFS = CoeffsTable(sa_damping=5, table="""    IMT      a1      a2      a3   a4      a5     a6    a7      a8      b1      b2      b3b      b3f      b4m      b4k      b5      b6    b7      b8    b9      b10      b11      b12    b13     b14      c1      c2      c3      c4      phi_ss   tau     phi_s2s    sig
    ia    -0.6169  2.5269  1.531  6.5  -3.2923  7.5  0.5462  0.6249  -2.7534  -0.2816  -0.0044  -0.003  -1.2608  -0.2992  0.7497  0.43  5.744  7.744  0.7497  0.43  -0.0488  -0.08312  1.4147  0.235  -1.3763  -0.1003  -0.0069  0.356  0.73761  0.92179  1.12747  1.632469
    """)


class BahrampouriEtAl2021SSlab(GMPE):
    """
    Implements GMPE by Mahdi Bahrampouri, Adrian Rodriguez-Marek and Russell A
    Green developed from the Kiban-Kyoshin network (KiK)-net database. This
    GMPE is specifically derived for arias intensity. This GMPE is described in
    a paper published in 2021 on Earthquake Spectra, Volume 37, Pg 428-448 and
    titled 'Ground motion prediction equations for Arias Intensity using the
    Kik-net database'.
    """

    #: Supported tectonic region type is SUBDUCTION INTERSLAB, see title!
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTRASLAB

    #: Supported intensity measure types are areas intensity
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {IA}

    #: Supported intensity measure component is geometric mean
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GEOMETRIC_MEAN

    #: Supported standard deviation types are inter-event, intra-event
    #: and total, see paragraph "Equations for standard deviations", page
    #: 1046.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL, const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT}

    #: Required site parameters are Vs30 and coordinates of the site
    REQUIRES_SITES_PARAMETERS = {'lon', 'lat', 'vs30'}

    #: Required rupture parameters are magnitude,ztor
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'ztor', 'hypo_lon', 'hypo_lat'}

    #: Required distance measures are rrup (see Table 2, page 1031).
    REQUIRES_DISTANCES = {'rrup'}

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        trt = self.DEFINED_FOR_TECTONIC_REGION_TYPE
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            # Implements mean model (equation 12)
            mean[m] = (_get_arias_intensity_term(ctx, C, trt) +
                       _get_arias_intensity_second_term(ctx, C, trt))
            sig[m], tau[m], phi[m] = _get_stddevs(C)

    #: For Ia, coefficients are taken from table 3
    COEFFS = CoeffsTable(sa_damping=5, table="""    IMT      a1      a2      a3   a4      a5     a6    a7      a8      b1      b2      b3b      b3f      b4m      b4k      b5      b6    b7      b8    b9      b10      b11      b12    b13     b14      c1      c2      c3      c4      phi_ss   tau     phi_s2s    sig
    ia    -0.6169  2.5269  1.531  6.5  -3.2923  7.5  0.5462  0.6249  -2.7534  -0.2816  -0.0044  -0.003  -1.2608  -0.2992  0.7497  0.43  5.744  7.744  0.7497  0.43  -0.0488  -0.08312  1.4147  0.235  -1.3763  -0.1003  -0.0069  0.356  0.73761  0.92179  1.12747  1.632469
    """)
