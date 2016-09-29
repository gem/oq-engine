# The Hazard Library
# Copyright (C) 2016, GEM Foundation
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

import unittest
import numpy
import numpy.testing as npt

from openquake.baselib.general import DictArray
from openquake.hazardlib.source import NonParametricSeismicSource
from openquake.hazardlib.source.rupture import Rupture
from openquake.hazardlib.const import TRT
from openquake.hazardlib.geo.surface import PlanarSurface, SimpleFaultSurface
from openquake.hazardlib.geo import Point, Line
from openquake.hazardlib.geo.geodetic import point_at
from openquake.hazardlib.calc.hazard_curve import calc_hazard_curves_ext
from openquake.hazardlib.calc.hazard_curve import calc_hazard_curves
from openquake.hazardlib.calc.hazard_curve import pmap_from_grp
from openquake.hazardlib.gsim.sadigh_1997 import SadighEtAl1997
from openquake.hazardlib.site import Site, SiteCollection
from openquake.hazardlib.pmf import PMF
from openquake.hazardlib.source.base import SourceGroup, SourceGroupCollection


def _create_rupture(distance, magnitude,
                    tectonic_region_type=TRT.ACTIVE_SHALLOW_CRUST):
    # Return a rupture with a fixed geometry located at a given r_jb distance
    # from a site located at (0.0, 0.0).
    # parameter float distance:
    #    Joyner and Boore rupture-site distance
    # parameter float magnitude:
    #    Rupture magnitude

    # Find the point at a given distance
    lonp, latp = point_at(0.0, 0.0, 90., distance)
    mag = magnitude
    rake = 0.0
    tectonic_region_type = tectonic_region_type
    hypocenter = Point(lonp, latp, 2.5)
    surface = PlanarSurface.from_corner_points(0.01,
                                               Point(lonp, -1, 0.),
                                               Point(lonp, +1, 0.),
                                               Point(lonp, +1, 5.),
                                               Point(lonp, -1, 5.))
    surface = SimpleFaultSurface.from_fault_data(
        fault_trace=Line([Point(lonp, -1), Point(lonp, 1)]),
        upper_seismogenic_depth=0.0,
        lower_seismogenic_depth=5.0,
        dip=90.0,
        mesh_spacing=1.0)
    # check effective rupture-site distance
    from openquake.hazardlib.geo.mesh import Mesh
    mesh = Mesh(numpy.array([0.0]), numpy.array([0.0]))
    assert abs(surface.get_joyner_boore_distance(mesh)-distance) < 1e-2
    return Rupture(mag, rake, tectonic_region_type, hypocenter,
                   surface, NonParametricSeismicSource)


def _create_non_param_sourceA(rjb, magnitude, pmf,
                              tectonic_region_type=TRT.ACTIVE_SHALLOW_CRUST):
    # Create a non-parametric source
    rupture = _create_rupture(rjb, magnitude)
    pmf = pmf
    data = [(rupture, pmf)]
    return NonParametricSeismicSource('0', 'test', tectonic_region_type, data)


class HazardCurvesTestCase01(unittest.TestCase):

    def setUp(self):
        self.src1 = _create_non_param_sourceA(15., 6.3,
                                              PMF([(0.6, 0), (0.4, 1)]))
        self.src2 = _create_non_param_sourceA(10., 6.0,
                                              PMF([(0.7, 0), (0.3, 1)]))
        self.src3 = _create_non_param_sourceA(10., 6.0,
                                              PMF([(0.7, 0), (0.3, 1)]),
                                              TRT.GEOTHERMAL)
        site = Site(Point(0.0, 0.0), 800, True, z1pt0=100., z2pt5=1.)
        site = Site(Point(0.0, 0.0), 800, True, z1pt0=100., z2pt5=1.)
        self.sites = SiteCollection([site])
        self.imtls = DictArray({'PGA': [0.01, 0.1, 0.3]})
        self.gsim_by_trt = {TRT.ACTIVE_SHALLOW_CRUST: SadighEtAl1997()}

    def test_hazard_curve_X(self):
        # Test the former calculator
        curves = calc_hazard_curves([self.src2],
                                    self.sites,
                                    self.imtls,
                                    self.gsim_by_trt,
                                    truncation_level=None)
        crv = curves[0][0]
        self.assertAlmostEqual(0.3, crv[0])

    def test_hazard_curve_A(self):
        # Test back-compatibility
        # Classical case i.e. independent sources in a list instance
        curves = calc_hazard_curves_ext([self.src2],
                                        self.sites,
                                        self.imtls,
                                        self.gsim_by_trt,
                                        truncation_level=None)
        crv = curves[0][0]
        npt.assert_almost_equal(numpy.array([0.30000, 0.27855, 0.08912]),
                                crv, decimal=4)

    def test_hazard_curve_B(self):
        # Test simple calculation using a SourceGroupCollection
        group = SourceGroup([self.src2], 'test', 'indep', 'indep')
        groups = SourceGroupCollection([group])
        curves = calc_hazard_curves_ext(groups,
                                        self.sites,
                                        self.imtls,
                                        self.gsim_by_trt,
                                        truncation_level=None)
        npt.assert_almost_equal(numpy.array([0.30000, 0.27855, 0.08912]),
                                curves[0][0], decimal=4)


class HazardCurvePerGroupTest(HazardCurvesTestCase01):

    def test_mutually_exclusive_ruptures(self):
        # Test the calculation of hazard curves using mutually exclusive
        # ruptures for a single source
        gsim_by_trt = [SadighEtAl1997()]
        rupture = _create_rupture(10., 6.)
        data = [(rupture, PMF([(0.7, 0), (0.3, 1)])),
                (rupture, PMF([(0.6, 0), (0.4, 1)]))]
        src = NonParametricSeismicSource('0', 'test', TRT.ACTIVE_SHALLOW_CRUST,
                                         data)
        group = SourceGroup([src], 'test', 'indep', 'mutex')
        crv = pmap_from_grp(group, self.sites, self.imtls,
                            gsim_by_trt, truncation_level=None)[0]
        npt.assert_almost_equal(numpy.array([0.35000, 0.32497, 0.10398]),
                                crv.array[:, 0], decimal=4)

    def test_raise_error_non_uniform_group(self):
        # Test that the uniformity of a group (in terms of tectonic region)
        # is correctly checked
        gsim_by_trt = [SadighEtAl1997()]
        group = SourceGroup([self.src1, self.src3], 'test', 'indep', 'indep')
        self.assertRaises(AssertionError, pmap_from_grp, group,
                          self.sites, self.imtls, gsim_by_trt,
                          truncation_level=None)


class HazardCurvesTestCase02(HazardCurvesTestCase01):

    def test_hazard_curve_A(self):
        # Test classical case i.e. independent sources in a list instance
        curves = calc_hazard_curves_ext([self.src1],
                                        self.sites,
                                        self.imtls,
                                        self.gsim_by_trt,
                                        truncation_level=None)
        crv = curves[0][0]
        npt.assert_almost_equal(numpy.array([0.40000, 0.36088, 0.07703]),
                                crv, decimal=4)

    def test_hazard_curve_B(self):
        # Test classical case i.e. independent sources in a list instance
        curves = calc_hazard_curves_ext([self.src1, self.src2],
                                        self.sites,
                                        self.imtls,
                                        self.gsim_by_trt,
                                        truncation_level=None)
        crv = curves[0][0]
        npt.assert_almost_equal(numpy.array([0.58000, 0.53891, 0.15929]),
                                crv, decimal=4)
