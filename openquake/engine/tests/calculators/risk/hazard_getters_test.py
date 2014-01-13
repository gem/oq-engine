# Copyright (c) 2010-2013, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.


import numpy
import mock
from openquake.engine.tests.utils import helpers
import unittest
from scipy import stats
import cPickle as pickle

from openquake.hazardlib.site import Site, SiteCollection
from openquake.hazardlib.geo.surface.planar import PlanarSurface
from openquake.hazardlib.geo import Point
from openquake.hazardlib.source.rupture import ProbabilisticRupture
from openquake.hazardlib.correlation import JB2009CorrelationModel

from openquake.engine.db import models
from openquake.engine.calculators.risk import hazard_getters
from openquake.engine.calculators.risk.base import RiskCalculator

from openquake.engine.tests.utils.helpers import get_data_path


class HazardCurveGetterPerAssetTestCase(unittest.TestCase):

    hazard_demo = get_data_path('simple_fault_demo_hazard/job.ini')
    risk_demo = get_data_path('classical_psha_based_risk/job.ini')
    hazard_output_type = 'curve'
    getter_class = hazard_getters.HazardCurveGetterPerAsset
    taxonomy = 'VF'

    def setUp(self):
        self.job, _ = helpers.get_fake_risk_job(
            self.risk_demo, self.hazard_demo, self.hazard_output_type)

        # need to run pre-execute to parse exposure model
        calc = RiskCalculator(self.job)
        models.JobStats.objects.create(oq_job=self.job)
        calc.pre_execute()

        self._assets = models.ExposureData.objects.filter(
            exposure_model=self.job.risk_calculation.exposure_model).order_by(
                'asset_ref')

        self.getter = self.getter_class(self.ho(), self.assets(), 500, "PGA")

    def test_is_pickleable(self):
        pickle.dumps(self.getter)  # raises an error if not

    def ho(self):
        return [self.job.risk_calculation.hazard_output]

    def test_call(self):
        _hid, assets, values = self.getter().next()
        self.assertEqual([a.id for a in self.assets()], [a.id for a in assets])
        numpy.testing.assert_allclose(
            [[(0.1, 0.1), (0.2, 0.2), (0.3, 0.3)],
             [(0.1, 0.1), (0.2, 0.2), (0.3, 0.3)],
             [(0.1, 0.1), (0.2, 0.2), (0.3, 0.3)]], values)

    def assets(self):
        return self._assets.filter(taxonomy=self.taxonomy)

    def test_filter(self):
        self.getter.max_distance = 0.00001  # 1 cm
        _hid, assets, curves = self.getter().next()
        self.assertEqual([], curves)
        self.assertEqual([], assets)


class GroundMotionValuesGetterTestCase(HazardCurveGetterPerAssetTestCase):

    hazard_demo = get_data_path('event_based_hazard/job.ini')
    risk_demo = get_data_path('event_based_risk/job.ini')
    hazard_output_type = 'gmf'
    getter_class = hazard_getters.GroundMotionValuesGetter
    taxonomy = 'RM'

    def test_call(self):
        _hid, assets, (gmfs, _ruptures) = self.getter().next()
        for gmvs in gmfs:
            numpy.testing.assert_allclose([0.1, 0.2, 0.3], gmvs)

    def test_filter(self):
        self.getter.max_distance = 0.00001  # 1 cm
        _hid, assets, (gmvs, ruptures) = self.getter().next()
        self.assertEqual([], gmvs)
        self.assertEqual([], ruptures)
        self.assertEqual([], assets)


class GroundMotionScenarioGetterTestCase(HazardCurveGetterPerAssetTestCase):

    hazard_demo = get_data_path('scenario_hazard/job.ini')
    risk_demo = get_data_path('scenario_risk/job.ini')
    hazard_output_type = 'gmf_scenario'
    getter_class = hazard_getters.GroundMotionValuesGetter
    taxonomy = 'RM'

    def test_call(self):
        hazard = list(self.getter())
        self.assertEqual(1, len(hazard))
        _hid, _assets, gmfs = hazard[0]
        for gmvs in gmfs:
            numpy.testing.assert_allclose([0.1, 0.2, 0.3], gmvs)

    def test_filter(self):
        self.getter.max_distance = 0.00001  # 1 cm
        _hid, _assets, data = self.getter().next()
        self.assertEqual([], data[0])  # no assets


class GroundMotionValuesCalcGetterTestCase(unittest.TestCase):
    def setUp(self):
        self.imt = "SA(0.15)"

        points = [Point(0, 0), Point(10, 10), Point(20, 20)]
        sites = [Site(point, 10, False, 2, 3, id=i)
                 for i, point in enumerate(points)]
        self.sites = models.SiteCollection(sites)

        assets = [mock.Mock] * 5
        self.sites_assets = ((0, assets[0:1]),
                             (1, assets[1:]),
                             (2, assets[2:]))

        self.gsims = mock.Mock()
        self.gsims.__getitem__ = mock.Mock(return_value=mock.Mock())
        self.cormo = JB2009CorrelationModel(vs30_clustering=False)

    def test_init(self):
        calc = hazard_getters.GroundMotionValuesCalcGetter(
            self.imt, self.sites, self.sites_assets, None, self.gsims, None)

        self.assertTrue(calc.generate_epsilons)
        self.assertEqual(type(stats.norm()), type(calc.distribution))
        self.assertEqual((), calc.distribution.args)
        self.assertIsNone(calc.correlation_matrix)

        calc = hazard_getters.GroundMotionValuesCalcGetter(
            self.imt, self.sites, self.sites_assets, 3, self.gsims, self.cormo)

        self.assertTrue(calc.generate_epsilons)
        self.assertEqual(type(stats.truncnorm(-5, 5)), type(calc.distribution))
        self.assertEqual((-3, 3), calc.distribution.args)
        self.assertEqual((3, 3), calc.correlation_matrix.shape)

        calc = hazard_getters.GroundMotionValuesCalcGetter(
            self.imt, self.sites, self.sites_assets, 0, self.gsims, self.cormo)

        self.assertFalse(calc.generate_epsilons)

    def test_sites_of_interest(self):
        calc = hazard_getters.GroundMotionValuesCalcGetter(
            self.imt, self.sites, self.sites_assets, 0, self.gsims, None)

        r = ProbabilisticRupture(
            mag=5.5,
            rake=123.45,
            tectonic_region_type=mock.Mock(),
            hypocenter=Point(5, 6, 7),
            surface=PlanarSurface(10, 11, 12,
                                  Point(0, 0, 1), Point(1, 0, 1),
                                  Point(1, 0, 2), Point(0, 0, 2)
                                  ),
            occurrence_rate=1,
            temporal_occurrence_model=mock.Mock(),
            source_typology=mock.Mock())

        r.source_typology.filter_sites_by_distance_to_rupture = mock.Mock(
            return_value=None)
        sites, _idxs = calc.sites_of_interest(r, 0)
        self.assertEqual([], sites)

        ret = SiteCollection(list(iter(self.sites)))
        ret.indices = [1]
        r.source_typology.filter_sites_by_distance_to_rupture = mock.Mock(
            return_value=ret)
        sites, idxs = calc.sites_of_interest(r, 100)
        self.assertEqual(1, len(sites))
        self.assertEqual(1, len(idxs))
        self.assertEqual(1, idxs[0])
        self.assertEqual(1, sites.get_by_id(1).id)

        ret.indices = [0, 2]
        r.source_typology.filter_sites_by_distance_to_rupture = mock.Mock(
            return_value=ret)
        sites, idxs = calc.sites_of_interest(r, 1000)
        self.assertEqual(2, len(sites))
        self.assertEqual([0, 2], idxs)

    def test_epsilons(self):
        calc = hazard_getters.GroundMotionValuesCalcGetter(
            self.imt, self.sites, self.sites_assets, 0, self.gsims, self.cormo)

        self.assertEqual((None, None, None), calc.epsilons(
                         mock.Mock(), mock.Mock(), mock.Mock()))

        calc = hazard_getters.GroundMotionValuesCalcGetter(
            self.imt, self.sites, self.sites_assets, None, self.gsims, None)

        tot, inter, intra = calc.epsilons(1, [0, 1], True)
        self.assertIsNone(inter)
        self.assertIsNone(intra)
        numpy.testing.assert_allclose([1.62434536, -0.61175641], tot)

        calc = hazard_getters.GroundMotionValuesCalcGetter(
            self.imt, self.sites, self.sites_assets, None, self.gsims, None)

        tot, inter, intra = calc.epsilons(1, [0, 1], False)
        self.assertIsNone(tot)
        numpy.testing.assert_allclose([1.62434536], inter)
        numpy.testing.assert_allclose([-0.61175641, -0.52817175], intra)

        calc = hazard_getters.GroundMotionValuesCalcGetter(
            self.imt, self.sites, self.sites_assets, 3, self.gsims, self.cormo)

        tot, inter, intra = calc.epsilons(1, [0, 1], False)
        self.assertIsNone(tot)
        numpy.testing.assert_allclose([-0.20894387], inter)
        numpy.testing.assert_allclose([0.58203861, -2.975205], intra)
