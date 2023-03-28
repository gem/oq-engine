# The Hazard Library
# Copyright (C) 2023 GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
Test cases 01–10 are based on the verification tests described in the
USGS ShakeMap 4.1 Manual.
Ref: Worden, C. B., E. M. Thompson, M. Hearne, and D. J. Wald (2020). 
ShakeMap Manual Online: technical manual, user’s guide, and software guide, 
U.S. Geological Survey. DOI: https://doi.org/10.5066/F7D21VPQ, see
https://usgs.github.io/shakemap/manual4_0/tg_verification.html`.
"""

import numpy
import pandas

from openquake.hazardlib import const, valid
from openquake.hazardlib.correlation import BaseCorrelationModel
from openquake.hazardlib.cross_correlation import CrossCorrelation, CrossCorrelationBetween
from openquake.hazardlib.geo import Point
from openquake.hazardlib.gsim.base import GMPE
from openquake.hazardlib.imt import IMT, PGA, SA
from openquake.hazardlib.site import Site, SiteCollection
from openquake.hazardlib.source.rupture import PointRupture
from openquake.hazardlib.tom import PoissonTOM
from openquake.hazardlib.calc.filters import IntegrationDistance

MAG = 6.0
LON = -122
LAT = 38
DEP = 5
VS30 = 780
MAX_DIST = IntegrationDistance.new('300')

RUP = PointRupture(
    mag=MAG,
    rake=0,
    tectonic_region_type=const.TRT.ACTIVE_SHALLOW_CRUST,
    hypocenter=Point(LON, LAT, DEP),
    strike=0,
    dip=90,
    occurrence_rate=1,
    temporal_occurrence_model=PoissonTOM(1.0),
    zbot=DEP,
)

CASE01_STATION_SITECOL = CASE02_STATION_SITECOL = SiteCollection(
    [
        Site(location=Point(-122.17083, 38.00000), custom_site_id="AZ.BZN"),
        Site(location=Point(-121.83750, 38.00000), custom_site_id="AZ.CRY"),
    ]
)

CASE03_STATION_SITECOL = CASE08_STATION_SITECOL = SiteCollection(
    [
        Site(location=Point(-122.17083, 38.00000), custom_site_id="AZ.AAA"),
    ]
)

CASE04_STATION_SITECOL = CASE05_STATION_SITECOL = SiteCollection(
    [
        Site(location=Point(-122.17083, 38.00000), custom_site_id="AZ.AAA"),
        Site(location=Point(-122.17083, 38.00000), custom_site_id="AZ.BBB"),
    ]
)

CASE04B_STATION_SITECOL = SiteCollection(
    [
        Site(location=Point(-122.17083, 38.00000), custom_site_id="AZ.AAA"),
        Site(location=Point(-121.17083, 38.00000), custom_site_id="AZ.BBB"),
    ]
)

CASE06_STATION_SITECOL = SiteCollection(
    [
        Site(location=Point(-122.75000, 38.00000), custom_site_id="AZ.AAA"),
        Site(location=Point(-122.70000, 38.00000), custom_site_id="AZ.BBB"),
        Site(location=Point(-122.65000, 38.00000), custom_site_id="AZ.CCC"),
        Site(location=Point(-122.60000, 38.00000), custom_site_id="AZ.DDD"),
        Site(location=Point(-122.55000, 38.00000), custom_site_id="AZ.EEE"),
        Site(location=Point(-122.50000, 38.00000), custom_site_id="AZ.FFF"),
        Site(location=Point(-122.45000, 38.00000), custom_site_id="AZ.GGG"),
        Site(location=Point(-122.40000, 38.00000), custom_site_id="AZ.HHH"),
        Site(location=Point(-122.35000, 38.00000), custom_site_id="AZ.III"),
        Site(location=Point(-122.30000, 38.00000), custom_site_id="AZ.JJJ"),
        Site(location=Point(-122.25000, 38.00000), custom_site_id="AZ.KKK"),
        Site(location=Point(-122.20000, 38.00000), custom_site_id="AZ.LLL"),
        Site(location=Point(-122.15000, 38.00000), custom_site_id="AZ.MMM"),
        Site(location=Point(-122.10000, 38.00000), custom_site_id="AZ.NNN"),
        Site(location=Point(-122.05000, 38.00000), custom_site_id="AZ.OOO"),
        Site(location=Point(-122.00000, 38.00000), custom_site_id="AZ.PPP"),
        Site(location=Point(-121.95000, 38.00000), custom_site_id="AZ.QQQ"),
        Site(location=Point(-121.90000, 38.00000), custom_site_id="AZ.RRR"),
        Site(location=Point(-121.85000, 38.00000), custom_site_id="AZ.SSS"),
        Site(location=Point(-121.80000, 38.00000), custom_site_id="AZ.TTT"),
        Site(location=Point(-122.80000, 38.00000), custom_site_id="BZ.AAA"),
        Site(location=Point(-122.85000, 38.00000), custom_site_id="BZ.BBB"),
        Site(location=Point(-122.90000, 38.00000), custom_site_id="BZ.CCC"),
        Site(location=Point(-122.95000, 38.00000), custom_site_id="BZ.DDD"),
        Site(location=Point(-123.00000, 38.00000), custom_site_id="BZ.EEE"),
        Site(location=Point(-123.05000, 38.00000), custom_site_id="BZ.FFF"),
        Site(location=Point(-123.10000, 38.00000), custom_site_id="BZ.GGG"),
        Site(location=Point(-123.15000, 38.00000), custom_site_id="BZ.HHH"),
        Site(location=Point(-123.20000, 38.00000), custom_site_id="BZ.III"),
        Site(location=Point(-123.25000, 38.00000), custom_site_id="BZ.JJJ"),
        Site(location=Point(-123.30000, 38.00000), custom_site_id="BZ.KKK"),
        Site(location=Point(-123.35000, 38.00000), custom_site_id="BZ.LLL"),
        Site(location=Point(-123.40000, 38.00000), custom_site_id="BZ.MMM"),
        Site(location=Point(-123.45000, 38.00000), custom_site_id="BZ.NNN"),
        Site(location=Point(-123.50000, 38.00000), custom_site_id="BZ.OOO"),
        Site(location=Point(-123.55000, 38.00000), custom_site_id="BZ.PPP"),
        Site(location=Point(-123.60000, 38.00000), custom_site_id="BZ.QQQ"),
        Site(location=Point(-123.65000, 38.00000), custom_site_id="BZ.RRR"),
        Site(location=Point(-123.70000, 38.00000), custom_site_id="BZ.SSS"),
        Site(location=Point(-123.75000, 38.00000), custom_site_id="BZ.TTT"),
    ]
)

CASE07_STATION_SITECOL = SiteCollection(
    [
        Site(location=Point(-122.00000, 38.00000), custom_site_id="AZ.BZN"),
    ]
)

CASE09_STATION_SITECOL = SiteCollection(
    [
        Site(location=Point(-122.55833, 38.00000), custom_site_id="AZ.AAA"),
        Site(location=Point(-122.45417, 38.00000), custom_site_id="AZ.BBB"),
        Site(location=Point(-122.14167, 38.00000), custom_site_id="AZ.CCC"),
        Site(location=Point(-121.82917, 38.00000), custom_site_id="AZ.DDD"),
        Site(location=Point(-121.72500, 38.00000), custom_site_id="AZ.EEE"),
    ]
)

CASE10_STATION_SITECOL = SiteCollection(
    [
        Site(location=Point(-122.43333, 38.00000), custom_site_id="AZ.AAA"),
        Site(location=Point(-122.28750, 38.00000), custom_site_id="AZ.BBB"),
        Site(location=Point(-122.14167, 38.00000), custom_site_id="AZ.CCC"),
        Site(location=Point(-121.99583, 38.00000), custom_site_id="AZ.DDD"),
        Site(location=Point(-121.85000, 38.00000), custom_site_id="AZ.EEE"),
    ]
)

CASE01_TARGET_SITECOL = SiteCollection(
    [
        Site(location=Point(lon, lat), vs30=VS30)
        for (lon, lat) in list(
            zip(numpy.round(numpy.linspace(-122.5, -121.5, 241), 5), numpy.repeat(38.0, 241))
        )
    ]
)
CASE02_TARGET_SITECOL = SiteCollection(
    [
        Site(location=Point(lon, lat), vs30=VS30)
        for (lon, lat) in list(
            zip(numpy.round(numpy.linspace(-123, -121, 481), 5), numpy.repeat(38.0, 481))
        )
    ]
)
CASE03_TARGET_SITECOL = CASE02_TARGET_SITECOL
CASE04_TARGET_SITECOL = CASE02_TARGET_SITECOL
CASE05_TARGET_SITECOL = CASE02_TARGET_SITECOL
CASE06_TARGET_SITECOL = CASE02_TARGET_SITECOL
CASE07_TARGET_SITECOL = SiteCollection(
    [
        Site(location=Point(-122, 38), vs30=VS30),
    ]
)
CASE08_TARGET_SITECOL = CASE02_TARGET_SITECOL
CASE09_TARGET_SITECOL = CASE02_TARGET_SITECOL
CASE10_TARGET_SITECOL = CASE02_TARGET_SITECOL

CASE01_OBSERVED_IMTS = ["PGA"]
CASE02_OBSERVED_IMTS = ["PGA"]
CASE03_OBSERVED_IMTS = ["PGA"]
CASE04_OBSERVED_IMTS = ["PGA"]
CASE05_OBSERVED_IMTS = ["PGA"]
CASE06_OBSERVED_IMTS = ["PGA"]
CASE07_OBSERVED_IMTS = ["SA(1.0)"]
CASE08_OBSERVED_IMTS = ["PGA"]
CASE09_OBSERVED_IMTS = ["PGA"]
CASE10_OBSERVED_IMTS = ["PGA"]

CASE01_TARGET_IMTS = [PGA()]
CASE02_TARGET_IMTS = [PGA()]
CASE03_TARGET_IMTS = [PGA()]
CASE04_TARGET_IMTS = [PGA()]
CASE05_TARGET_IMTS = [PGA()]
CASE06_TARGET_IMTS = [PGA()]
CASE07_TARGET_IMTS = [SA(str(period)) for period in numpy.logspace(-1, 1, 199)]
CASE08_TARGET_IMTS = [PGA()]
CASE09_TARGET_IMTS = [PGA()]
CASE10_TARGET_IMTS = [PGA()]

CASE01_STATION_DATA = pandas.DataFrame({"PGA_mean": numpy.exp([0, 0]), "PGA_std": [0, 0]})
CASE02_STATION_DATA = pandas.DataFrame({"PGA_mean": numpy.exp([1, -1]), "PGA_std": [0, 0]})
CASE03_STATION_DATA = pandas.DataFrame({"PGA_mean": numpy.exp([1]), "PGA_std": [0]})
CASE04_STATION_DATA = pandas.DataFrame({"PGA_mean": numpy.exp([1, 1]), "PGA_std": [0, 0]})
CASE05_STATION_DATA = pandas.DataFrame({"PGA_mean": numpy.exp([1, -1]), "PGA_std": [0, 0]})
CASE06_STATION_DATA = pandas.DataFrame({"PGA_mean": numpy.exp([1] * 40), "PGA_std": [0] * 40})
CASE07_STATION_DATA = pandas.DataFrame({"SA(1.0)_mean": numpy.exp([1]), "SA(1.0)_std": [0]})
CASE08A_STATION_DATA = pandas.DataFrame({"PGA_mean": numpy.exp([1]), "PGA_std": [0]})
CASE08B_STATION_DATA = pandas.DataFrame({"PGA_mean": numpy.exp([1]), "PGA_std": [0.75]})
CASE08C_STATION_DATA = pandas.DataFrame({"PGA_mean": numpy.exp([1]), "PGA_std": [1.5]})
CASE08D_STATION_DATA = pandas.DataFrame({"PGA_mean": numpy.exp([1]), "PGA_std": [3.0]})
CASE08E_STATION_DATA = pandas.DataFrame({"PGA_mean": numpy.exp([1]), "PGA_std": [6.0]})
CASE08_STATION_DATA_LIST = [CASE08A_STATION_DATA, CASE08B_STATION_DATA, CASE08C_STATION_DATA,
                            CASE08D_STATION_DATA, CASE08E_STATION_DATA]
CASE09_STATION_DATA = CASE10_STATION_DATA = pandas.DataFrame(
    {"PGA_mean": numpy.exp([1, 1, 0.75, 1, 1]), "PGA_std": [0.2] * 5}
)

CASE08_STD_ADDON_D = numpy.array([0.0, 0.75, 1.5, 3.0, 6.0])
CASE08_VAR_ADDON_D = CASE08_STD_ADDON_D ** 2
CASE08_OBS = 1
CASE08_MU = 0
CASE08_TAU = 0.6
CASE08_PHI = 0.8
CASE08_VAR_HD_YD = 1.0 / (1.0 + CASE08_TAU ** 2 / (CASE08_PHI ** 2 + CASE08_VAR_ADDON_D))
CASE08_MU_HD_YD = CASE08_TAU / (CASE08_PHI ** 2 + CASE08_VAR_ADDON_D) * (CASE08_OBS - CASE08_MU) * CASE08_VAR_HD_YD
CASE08_BD_YD = CASE08_MU_HD_YD * CASE08_TAU
CASE08_MU_YD_OBS = CASE08_MU + CASE08_BD_YD + CASE08_PHI ** 2 / (CASE08_PHI ** 2 + CASE08_VAR_ADDON_D) * (CASE08_OBS - CASE08_MU - CASE08_BD_YD)
CASE08_MU_YD_FAR = CASE08_MU + CASE08_BD_YD + 0 / (CASE08_PHI ** 2 + CASE08_VAR_ADDON_D) * (CASE08_OBS - CASE08_MU - CASE08_BD_YD)
CASE08_C_OBS = CASE08_TAU * (1.0 - CASE08_PHI ** 2 / (CASE08_PHI ** 2 + CASE08_VAR_ADDON_D))
CASE08_C_FAR = CASE08_TAU * (1.0 - 0 / (CASE08_PHI ** 2 + CASE08_VAR_ADDON_D))
CASE08_COV_WY_WY_WD_OBS = CASE08_PHI ** 2 * (1.0 - CASE08_PHI ** 2 / (CASE08_PHI ** 2 + CASE08_VAR_ADDON_D)) 
CASE08_COV_WY_WY_WD_FAR = CASE08_PHI ** 2 * (1.0 - 0 / (CASE08_PHI ** 2 + CASE08_VAR_ADDON_D)) 
CASE08_COV_Y_Y_YD_OBS = CASE08_COV_WY_WY_WD_OBS + CASE08_C_OBS ** 2 * CASE08_VAR_HD_YD
CASE08_COV_Y_Y_YD_FAR = CASE08_COV_WY_WY_WD_FAR + CASE08_C_FAR ** 2 * CASE08_VAR_HD_YD
CASE08_SIG_YD_OBS = numpy.sqrt(CASE08_COV_Y_Y_YD_OBS)
CASE08_SIG_YD_FAR = numpy.sqrt(CASE08_COV_Y_Y_YD_FAR)

class ZeroMeanGMM(GMPE):
    """
    Implements the GMM used for the verification tests for the conditioned
    ground motion fields calculator. The GMM used in these tests always
    returns a mean of 0 (in log space) for all locations, and reports a
    between-event standard deviation of 0.6 and a within-event standard
    deviation of 0.8 (making the total standard deviation a convenient 1.0).

    Ref: Worden, C. B., E. M. Thompson, M. Hearne, and D. J. Wald (2020).
    ShakeMap Manual Online: technical manual, user’s guide, and software guide,
    U.S. Geological Survey. DOI: https://doi.org/10.5066/F7D21VPQ, see
    https://usgs.github.io/shakemap/manual4_0/tg_verification.html`.
    """

    #: Supported tectonic region type is active shallow crust
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Supported intensity measure types are spectral acceleration,
    #: and peak ground acceleration
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, SA}

    #: Supported intensity measure component is the geometric mean of
    #: two horizontal components
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GEOMETRIC_MEAN

    #: Supported standard deviation type include the total, and the
    #: between-event and within-event components
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL, const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT}

    #: No site parameters required
    REQUIRES_SITES_PARAMETERS = set()

    #: Required rupture parameter is only the magnitude
    REQUIRES_RUPTURE_PARAMETERS = {"mag"}

    #: Required distance measure is rjb (Joyner-Boore distance)
    REQUIRES_DISTANCES = {"rjb"}

    # Shear-wave velocity for reference soil conditions in [m/s])
    DEFINED_FOR_REFERENCE_VELOCITY = 780

    def compute(self, ctx: numpy.recarray, imts, mean, sig, tau, phi):
        """
        :param ctx: a RuptureContext object or a numpy recarray of size N
        :param imts: a list of M Intensity Measure Types
        :param mean: an array of shape (M, N) for the means
        :param sig: an array of shape (M, N) for the TOTAL stddevs
        :param tau: an array of shape (M, N) for the INTER_EVENT stddevs
        :param phi: an array of shape (M, N) for the INTRA_EVENT stddevs
        """
        for m, _ in enumerate(imts):
            mean[m] = 0.0
            sig[m] = 1.0
            tau[m] = 0.6
            phi[m] = 0.8


class DummySpatialCorrelationModel(BaseCorrelationModel):
    """
    Trivial spatial correlation model to be used only in simple
    test cases, where the correlation is simply exp(-h/10),
    in which h is the separation distance. *Not* meant to be
    used in real calculations.
    """

    def __init__(self):
        self.cache = {}  # imt -> correlation model

    def _get_correlation_matrix(self, distance_matrix, imt):
        
        return numpy.exp(-0.1 * distance_matrix)


class DummyCrossCorrelationWithin(CrossCorrelation):
    """
    Trivial cross-period correlation model to be used only in simple test
    cases, where the correlation is simply the ratio of the spectral periods
    (that is, Ts/Tl where Ts is the smaller period and Tl is the larger).
    *Not* meant to be used in real calculations.
    """

    cache = {}  # periods -> correlation matrix

    def get_correlation(self, from_imt: IMT, to_imt: IMT) -> float:
        """
        :returns: a scalar in the range 0..1
        """
        if from_imt == to_imt:
            return 1

        T1 = from_imt.period
        T2 = to_imt.period
        Ts = min(T1, T2)
        Tl = max(T1, T2)
        return Ts/Tl
    

class DummyCrossCorrelationBetween(CrossCorrelationBetween):
    """
    Trivial cross-period correlation model to be used only in simple test
    cases, where the correlation is simply the ratio of the spectral periods
    (that is, Ts/Tl where Ts is the smaller period and Tl is the larger).
    *Not* meant to be used in real calculations.
    """
    cache = {}  # periods -> correlation matrix

    def get_correlation(self, from_imt: IMT, to_imt: IMT) -> float:
        """
        :returns: a scalar in the range 0..1
        """
        if from_imt == to_imt:
            return 1

        T1 = from_imt.period
        T2 = to_imt.period
        Ts = min(T1, T2)
        Tl = max(T1, T2)
        return Ts/Tl
    
    def get_inter_eps(self, imts, num_events):
        pass

    def _get_correlation_matrix(self, imts):
        # cached on the periods
        periods = tuple(imt.period for imt in imts)
        try:
            return self.cache[periods]
        except KeyError:
            self.cache[periods] = corma = numpy.zeros((len(imts), len(imts)))
        for i, imi in enumerate(imts):
            for j, imj in enumerate(imts):
                corma[i, j] = self.get_correlation(imi, imj)
        return corma