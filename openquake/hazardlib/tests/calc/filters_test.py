# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (c) 2017-2018 GEM Foundation
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
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
import os
import unittest
from numpy.testing import assert_almost_equal as aae
from openquake.baselib.general import gettemp
from openquake.hazardlib import nrml
from openquake.hazardlib.geo.point import Point
from openquake.hazardlib.site import Site, SiteCollection
from openquake.hazardlib.calc.filters import (
    IntegrationDistance, MAX_DISTANCE, SourceFilter, angular_distance)


class AngularDistanceTestCase(unittest.TestCase):
    def test(self):
        aae(angular_distance(km=1000, lat=80), 51.7897747)
        aae(angular_distance(km=1000, lat=88), 257.68853)


class IntegrationDistanceTestCase(unittest.TestCase):
    def test_bounding_box(self):
        maxdist = IntegrationDistance({'default': [
            (3, 30), (4, 40), (5, 100), (6, 200), (7, 300), (8, 400)]})

        aae(maxdist('ANY_TRT'), MAX_DISTANCE)  # 2000 km
        bb = maxdist.get_bounding_box(0, 10, 'ANY_TRT')
        aae(bb, [-18.2638692, -7.9864, 18.2638692, 27.9864])

        aae(maxdist('ANY_TRT', mag=7.1), 400)
        bb = maxdist.get_bounding_box(0, 10, 'ANY_TRT', mag=7.1)
        aae(bb, [-3.6527738, 6.40272, 3.6527738, 13.59728])

        aae(maxdist('ANY_TRT', mag=6.9), 300)
        bb = maxdist.get_bounding_box(0, 10, 'ANY_TRT', mag=6.9)
        aae(bb, [-2.7395804, 7.30204, 2.7395804, 12.69796])


class SourceFilterTestCase(unittest.TestCase):
    def test_get_bounding_boxes(self):
        maxdist = IntegrationDistance({'default': [
            (3, 30), (4, 40), (5, 100), (6, 200), (7, 300), (8, 400)]})
        sitecol = SiteCollection([
            Site(location=Point(10, 20, 30),
                 vs30=1.2, vs30measured=True,
                 z1pt0=3.4, z2pt5=5.6, backarc=True),
            Site(location=Point(-1.2, -3.4, -5.6),
                 vs30=55.4, vs30measured=False,
                 z1pt0=66.7, z2pt5=88.9, backarc=False)])
        srcfilter = SourceFilter(sitecol, maxdist)
        bb1, bb2 = srcfilter.get_bounding_boxes(mag=4.5)
        # bounding boxes in the form min_lon, min_lat, max_lon, max_lat
        aae(bb1, (9.0429636, 19.10068, 10.9570364, 20.89932))
        aae(bb2, (-2.1009057, -4.29932, -0.2990943, -2.50068))

    def test_international_date_line(self):
        maxdist = IntegrationDistance({'default': [
            (3, 30), (4, 40), (5, 100), (6, 200), (7, 300), (8, 400)]})
        sitecol = SiteCollection([
            Site(location=Point(179, 80),
                 vs30=1.2, vs30measured=True,
                 z1pt0=3.4, z2pt5=5.6, backarc=True),
            Site(location=Point(-179, 80),
                 vs30=55.4, vs30measured=False,
                 z1pt0=66.7, z2pt5=88.9, backarc=False)])
        srcfilter = SourceFilter(sitecol, maxdist)
        bb1, bb2 = srcfilter.get_bounding_boxes(mag=4.5)
        # bounding boxes in the form min_lon, min_lat, max_lon, max_lat
        aae(bb1, (173.8210225, 79.10068, 184.1789775, 80.89932))
        aae(bb2, (-184.1789775, 79.10068, -173.8210225, 80.89932))

    def test_international_date_line_2(self):
        # from a bug affecting a calculation in New Zealand
        fname = gettemp(characteric_source)
        [[src]] = nrml.to_python(fname)
        os.remove(fname)
        maxdist = IntegrationDistance({'default': 200})
        sitecol = SiteCollection([
            Site(location=Point(176.919, -39.489),
                 vs30=760, vs30measured=True, z1pt0=100, z2pt5=5)])
        srcfilter = SourceFilter(sitecol, maxdist)
        sites = srcfilter.get_close_sites(src)
        self.assertIsNotNone(sites)

# from https://groups.google.com/d/msg/openquake-users/P03SxJsfW_s/nCdcxj8WAAAJ
characteric_source = '''\
<?xml version="1.0" encoding="utf-8"?>
<nrml
xmlns="http://openquake.org/xmlns/nrml/0.4"
xmlns:gml="http://www.opengis.net/gml"
>
    <sourceModel
    name="Seismic Source Model"
    >
        <characteristicFaultSource
        id="21454"
        name="HikHBaymax"
        tectonicRegion="Subduction Interface"
        >
            <incrementalMFD
            binWidth="1.0000000E-01"
            minMag="8.3000000E+00"
            >
                <occurRates>
                    7.1428571E-04
                </occurRates>
            </incrementalMFD>
            <rake>
                9.0000000E+01
            </rake>
            <surface>
                <simpleFaultGeometry>
                    <gml:LineString>
                        <gml:posList>
                            1.7891000E+02 -3.9418000E+01
                            1.7774500E+02 -4.0980000E+01
                        </gml:posList>
                    </gml:LineString>
                    <dip>
                        8.5000000E+00
                    </dip>
                    <upperSeismoDepth>
                        5.0000000E+00
                    </upperSeismoDepth>
                    <lowerSeismoDepth>
                        2.0000000E+01
                    </lowerSeismoDepth>
                </simpleFaultGeometry>
            </surface>
        </characteristicFaultSource>
    </sourceModel>
</nrml>'''
