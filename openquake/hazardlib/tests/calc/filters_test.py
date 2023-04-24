# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (c) 2017-2023 GEM Foundation
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
    IntegrationDistance, SourceFilter, angular_distance, split_source)


class AngularDistanceTestCase(unittest.TestCase):
    def test(self):
        aae(angular_distance(km=1000, lat=80), 51.7897747)
        aae(angular_distance(km=1000, lat=88), 257.68853)


class IntegrationDistanceTestCase(unittest.TestCase):
    def test_bounding_box(self):
        maxdist = IntegrationDistance.new('400')
        bb = maxdist.get_bounding_box(0, 10, 'ANY_TRT')
        aae(bb, [-3.6527738, 6.40272, 3.6527738, 13.59728])

    def test_maximum_magnitude(self):
        maxdist = IntegrationDistance.new(
            '[(4, 200), (7, 200), (7.01, 0), (8, 0)]')
        interp = maxdist('default')
        aae(interp([5, 6, 7, 7.2, 8]), [200., 200., 200.,   0.,   0.])


class SourceFilterTestCase(unittest.TestCase):

    def test_international_date_line(self):
        # from a bug affecting a calculation in New Zealand
        fname = gettemp(characteric_source)
        [[src]] = nrml.to_python(fname)
        os.remove(fname)
        maxdist = IntegrationDistance.new('200')
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


class SplitSourcesTestCase(unittest.TestCase):
    def test(self):
        # make sure the trt_smr is transferred also for single split
        # sources, since this caused hard to track bugs
        fname = gettemp(characteric_source)
        [[char]] = nrml.to_python(fname)
        char.id = 1
        char.trt_smr = 1
        os.remove(fname)
        [src] = split_source(char)
        self.assertEqual(char.id, src.id)
        self.assertEqual(char.source_id, src.source_id)
        self.assertEqual(char.trt_smr, src.trt_smr)
