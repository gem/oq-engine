# The Hazard Library
# Copyright (C) 2012-2023 GEM Foundation
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

import pathlib
import unittest

from openquake.hazardlib.geo import Point
from openquake.hazardlib.geo.surface import PlanarSurface
from openquake.hazardlib.source.rupture import BaseRupture
from openquake.hazardlib.const import TRT
from openquake.hazardlib.scalerel.wc1994 import WC1994
from openquake.hazardlib.gsim.zhao_2016 import ZhaoEtAl2016SSlabPErg

HERE = pathlib.Path(__file__)


def get_rupture(lon, lat, dep, msr, mag, aratio, strike, dip, rake, trt,
                ztor=None):
    """
    Creates a rupture given the hypocenter position
    """
    hypoc = Point(lon, lat, dep)
    srf = PlanarSurface.from_hypocenter(hypoc, msr, mag, aratio, strike, dip,
                                        rake, ztor)
    rup = BaseRupture(mag, rake, trt, hypoc, srf)
    rup.hypo_depth = dep
    return rup


class TestZhao2016PErg(unittest.TestCase):

    def setUp(self):

        lon = 0.0
        lat = 0.0
        dep = 10.0
        msr = WC1994()
        mag = 7.0
        aratio = 2.0
        strike = 270.0
        dip = 30.0
        rake = 90.0
        trt = TRT.SUBDUCTION_INTERFACE
        ztor = 0.0
        rup = get_rupture(lon, lat, dep, msr, mag, aratio, strike, dip,
                          rake, trt, ztor)

    def test01(self):

        path = HERE.parent / 'data' / 'ZHAO16PERG' / 'test_volc.geojson'
        gmm = ZhaoEtAl2016SSlabPErg(path)
