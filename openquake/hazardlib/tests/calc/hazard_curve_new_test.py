# The Hazard Library
# Copyright (C) 2016-2020 GEM Foundation
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

import os
import unittest
import numpy
import numpy.testing as npt

from openquake.baselib.general import DictArray
from openquake.hazardlib.source import NonParametricSeismicSource
from openquake.hazardlib.source.rupture import BaseRupture
from openquake.hazardlib.sourceconverter import SourceConverter
from openquake.hazardlib.const import TRT
from openquake.hazardlib.geo.surface import PlanarSurface, SimpleFaultSurface
from openquake.hazardlib.geo import Point, Line
from openquake.hazardlib.geo.geodetic import point_at
from openquake.hazardlib.calc.filters import SourceFilter
from openquake.hazardlib.calc.hazard_curve import calc_hazard_curves
from openquake.hazardlib.calc.hazard_curve import classical
from openquake.hazardlib.gsim.sadigh_1997 import SadighEtAl1997
from openquake.hazardlib.gsim.si_midorikawa_1999 import SiMidorikawa1999SInter
from openquake.hazardlib.gsim.campbell_2003 import Campbell2003
from openquake.hazardlib.site import Site, SiteCollection
from openquake.hazardlib.pmf import PMF
from openquake.hazardlib.sourceconverter import SourceGroup
from openquake.hazardlib import nrml


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
    surface = PlanarSurface.from_corner_points(
        Point(lonp, -1, 0.), Point(lonp, +1, 0.),
        Point(lonp, +1, 5.), Point(lonp, -1, 5.))
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
    return BaseRupture(mag, rake, tectonic_region_type, hypocenter,
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
        site = Site(Point(0.0, 0.0), 800, z1pt0=100., z2pt5=1.)
        s_filter = SourceFilter(SiteCollection([site]), {})
        self.sites = s_filter
        self.imtls = DictArray({'PGA': [0.01, 0.1, 0.3]})
        gsim = SadighEtAl1997()
        gsim.minimum_distance = 12  # test minimum_distance
        self.gsim_by_trt = {TRT.ACTIVE_SHALLOW_CRUST: gsim}

    def test_hazard_curve_X(self):
        # Test the former calculator
        curves = calc_hazard_curves([self.src2],
                                    self.sites,
                                    self.imtls,
                                    self.gsim_by_trt,
                                    truncation_level=None)
        crv = curves[0][0]
        npt.assert_almost_equal([0.30000, 0.2646, 0.0625], crv, decimal=4)

    def test_hazard_curve_A(self):
        # Test back-compatibility
        # Classical case i.e. independent sources in a list instance
        curves = calc_hazard_curves([self.src2],
                                    self.sites,
                                    self.imtls,
                                    self.gsim_by_trt,
                                    truncation_level=None)
        crv = list(curves[0][0])
        npt.assert_almost_equal([0.30000, 0.2646, 0.0625],
                                crv, decimal=4)

    def test_hazard_curve_B(self):
        # Test simple calculation
        group = SourceGroup(
            TRT.ACTIVE_SHALLOW_CRUST, [self.src2], 'test', 'indep', 'indep')
        groups = [group]
        curves = calc_hazard_curves(groups,
                                    self.sites,
                                    self.imtls,
                                    self.gsim_by_trt,
                                    truncation_level=None)
        npt.assert_almost_equal(numpy.array([0.30000, 0.2646, 0.0625]),
                                curves[0][0], decimal=4)


class HazardCurvePerGroupTest(HazardCurvesTestCase01):

    def test_mutually_exclusive_ruptures(self):
        # Test the calculation of hazard curves using mutually exclusive
        # ruptures for a single source
        gsim_by_trt = [SadighEtAl1997()]
        rupture = _create_rupture(10., 6.)
        data = [(rupture, PMF([(0.7, 0), (0.3, 1)])),
                (rupture, PMF([(0.6, 0), (0.4, 1)]))]
        data[0][0].weight = 0.5
        data[1][0].weight = 0.5
        src = NonParametricSeismicSource('0', 'test', TRT.ACTIVE_SHALLOW_CRUST,
                                         data)
        src.id = 0
        src.grp_id = 0
        src.et_id = 0
        src.mutex_weight = 1
        group = SourceGroup(
            src.tectonic_region_type, [src], 'test', 'mutex', 'mutex')
        param = dict(imtls=self.imtls,
                     src_interdep=group.src_interdep,
                     rup_interdep=group.rup_interdep,
                     grp_probability=group.grp_probability)
        crv = classical(group, self.sites, gsim_by_trt, param)['pmap'][0]
        npt.assert_almost_equal(numpy.array([0.35000, 0.32497, 0.10398]),
                                crv.array[:, 0], decimal=4)

    def test_raise_error_non_uniform_group(self):
        # Test that the uniformity of a group (in terms of tectonic region)
        # is correctly checked
        self.assertRaises(
            AssertionError, SourceGroup, TRT.ACTIVE_SHALLOW_CRUST,
            [self.src1, self.src3], 'test', 'indep', 'indep')


class HazardCurvesTestCase02(HazardCurvesTestCase01):

    def test_hazard_curve_A(self):
        # Test classical case i.e. independent sources in a list instance
        curves = calc_hazard_curves([self.src1],
                                    self.sites,
                                    self.imtls,
                                    self.gsim_by_trt,
                                    truncation_level=None)
        crv = curves[0][0]
        npt.assert_almost_equal(numpy.array([0.40000, 0.36088, 0.07703]),
                                crv, decimal=4)

    def test_hazard_curve_B(self):
        # Test classical case i.e. independent sources in a list instance
        curves = calc_hazard_curves([self.src1, self.src2],
                                    self.sites,
                                    self.imtls,
                                    self.gsim_by_trt,
                                    truncation_level=None)
        crv = curves[0][0]
        npt.assert_almost_equal(numpy.array([0.58000, 0.53, 0.1347]),
                                crv, decimal=4)


class NankaiTestCase(unittest.TestCase):
    # use a source model for the Nankai region provided by M. Pagani
    # also tests the case of undefined rake
    def test(self):
        source_model = os.path.join(os.path.dirname(__file__), 'nankai.xml')
        groups = nrml.to_python(source_model, SourceConverter(
            investigation_time=50., rupture_mesh_spacing=2.))
        site = Site(Point(135.68, 35.68), 400, z1pt0=100., z2pt5=1.)
        s_filter = SourceFilter(SiteCollection([site]), {})
        imtls = DictArray({'PGV': [20, 40, 80]})
        gsim_by_trt = {'Subduction Interface': SiMidorikawa1999SInter()}
        hcurves = calc_hazard_curves(groups, s_filter, imtls, gsim_by_trt)
        npt.assert_almost_equal(
            [1.1262869e-01, 3.9968668e-03, 3.1005840e-05],
            hcurves['PGV'][0])


class MultiPointTestCase(unittest.TestCase):
    def test(self):
        d = os.path.dirname(os.path.dirname(__file__))
        source_model = os.path.join(d, 'source_model/multi-point-source.xml')
        groups = nrml.to_python(source_model, SourceConverter(
            investigation_time=50., rupture_mesh_spacing=2.))
        site = Site(Point(0.1, 0.1), 800, z1pt0=100., z2pt5=1.)
        sitecol = SiteCollection([site])
        imtls = DictArray({'PGA': [0.01, 0.02, 0.04, 0.08, 0.16]})
        gsim_by_trt = {'Stable Continental Crust': Campbell2003()}
        hcurves = calc_hazard_curves(groups, sitecol, imtls, gsim_by_trt)
        expected = [9.999978e-01, 9.084040e-01, 1.489753e-01, 3.690966e-03,
                    2.763261e-05]
        npt.assert_allclose(hcurves['PGA'][0], expected, rtol=3E-4)

        # splitting in point sources
        [[mps1, mps2]] = groups
        psources = list(mps1) + list(mps2)
        hcurves = calc_hazard_curves(psources, sitecol, imtls, gsim_by_trt)
        npt.assert_allclose(hcurves['PGA'][0], expected, rtol=3E-4)
