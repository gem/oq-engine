# Copyright (c) 2010-2012, GEM Foundation.
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


from tests.utils import helpers
import unittest

from openquake.db import models
from django.contrib.gis.geos.point import Point

from openquake.calculators.risk import hazard_getters


class HazardCurveGetterPerAssetTestCase(unittest.TestCase):
    def setUp(self):
        self.job, _ = helpers.get_risk_job(
            'classical_psha_based_risk/job.ini',
            'simple_fault_demo_hazard/job.ini')

        models.HazardCurveData.objects.create(
            hazard_curve=self.job.risk_calculation.hazard_output.hazardcurve,
            poes=[0.2, 0.3, 0.4],
            location="POINT(3 3)")

    def test_call(self):
        getter = hazard_getters.HazardCurveGetterPerAsset(
            self.job.risk_calculation.hazard_output.hazardcurve.id)

        self.assertEqual([(0.1, 0.1), (0.2, 0.2), (0.3, 0.3)],
                         getter(Point(1, 1)))

        self.assertEqual([(0.1, 0.2), (0.2, 0.3), (0.3, 0.4)],
                         getter(Point(4, 4)))


class GroundMotionValuesGetterTestCase(unittest.TestCase):

    def test_all_sets_at_same_location_merged(self):
        output = self._hazard_output("gmf")

        # we don't use an output type `complete_lt_gmf` here, the
        # flag is just to avoid the creation of all the realization
        # data model.
        collection = models.GmfCollection(output=output,
            complete_logic_tree_gmf=True)
        collection.save()

        models.Gmf(gmf_set=self._gmf_set(collection, 1), imt="PGA",
            location=Point(1.0, 1.0), gmvs=[0.1, 0.2, 0.3],
            result_grp_ordinal=1).save()

        models.Gmf(gmf_set=self._gmf_set(collection, 2), imt="PGA",
            location=Point(1.0, 1.0), gmvs=[0.4, 0.5, 0.6],
            result_grp_ordinal=2).save()

        getter = hazard_getters.GroundMotionValuesGetter(
            hazard_output_id=collection.id,
            imt="PGA", time_span=50.0, tses=20.0)

        # to the event based risk calculator, we must pass all the
        # ground motion values coming from all the stochastic event sets.
        expected = {"TSES": 20.0, "IMLs": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6],
            "TimeSpan": 50.0}

        self.assertEqual(expected, getter(Point(0.5, 0.5)))

    def test_closest_location_selected(self):
        output = self._hazard_output("gmf")

        # we don't use an output type `complete_lt_gmf` here, the
        # flag is just to avoid the creation of all the realization
        # data model.
        collection = models.GmfCollection(output=output,
            complete_logic_tree_gmf=True)
        collection.save()

        # this is the closest ground motion field.
        models.Gmf(gmf_set=self._gmf_set(collection, 1), imt="PGA",
            location=Point(1.0, 1.0), gmvs=[0.1, 0.2, 0.3],
            result_grp_ordinal=1).save()

        models.Gmf(gmf_set=self._gmf_set(collection, 2), imt="PGA",
            location=Point(2.0, 2.0), gmvs=[0.4, 0.5, 0.6],
            result_grp_ordinal=1).save()

        getter = hazard_getters.GroundMotionValuesGetter(
            hazard_output_id=collection.id,
            imt="PGA", time_span=50.0, tses=20.0)

        expected = {"TSES": 20.0, "IMLs": [0.1, 0.2, 0.3],
            "TimeSpan": 50.0}

        self.assertEqual(expected, getter(Point(0.5, 0.5)))

    def test_only_specific_branches_are_supported(self):
        output = self._hazard_output("complete_lt_gmf")
        collection = models.GmfCollection(output=output,
            complete_logic_tree_gmf=True)
        collection.save()

        self.assertRaises(ValueError,
            hazard_getters.GroundMotionValuesGetter,
            collection.id, "PGA", 50.0, 20.0)

    def test_intensity_type_sa(self):
        output = self._hazard_output("gmf")

        # we don't use an output type `complete_lt_gmf` here, the
        # flag is just to avoid the creation of all the realization
        # data model.
        collection = models.GmfCollection(output=output,
            complete_logic_tree_gmf=True)
        collection.save()

        # when IMT==SA we should filter also for `sa_period`
        # and `sa_damping`
        models.Gmf(gmf_set=self._gmf_set(collection, 1), imt="SA",
            location=Point(1.0, 1.0), gmvs=[0.1, 0.2, 0.3], sa_period=1.0,
            sa_damping=5.0, result_grp_ordinal=1).save()

        # different `sa_period`
        models.Gmf(gmf_set=self._gmf_set(collection, 2), imt="SA",
            location=Point(1.0, 1.0), gmvs=[0.4, 0.5, 0.6], sa_period=2.0,
            sa_damping=2.0, result_grp_ordinal=2).save()

        # different `sa_damping`
        models.Gmf(gmf_set=self._gmf_set(collection, 3), imt="SA",
            location=Point(1.0, 1.0), gmvs=[0.7, 0.8, 0.9], sa_period=1.0,
            sa_damping=1.0, result_grp_ordinal=3).save()

        getter = hazard_getters.GroundMotionValuesGetter(
            hazard_output_id=collection.id, imt="SA(1.0)", time_span=50.0,
            tses=20.0)

        expected = {"TSES": 20.0, "IMLs": [0.1, 0.2, 0.3], "TimeSpan": 50.0}
        self.assertEqual(expected, getter(Point(0.5, 0.5)))

    def _gmf_set(self, collection, ses_ordinal, investigation_time=50.0):
        gmf_set = models.GmfSet(gmf_collection=collection,
            investigation_time=investigation_time, ses_ordinal=ses_ordinal)
        gmf_set.save()

        return gmf_set

    def _hazard_output(self, output_type):
        organization = models.Organization(name="TEST Organization")
        organization.save()

        user, _ = models.OqUser.objects.get_or_create(user_name="Test",
            defaults={"full_name": "Test", "organization": organization})

        job = models.OqJob(owner=user)
        job.save()

        output = models.Output(owner=user, oq_job=job, display_name="TEST",
            output_type=output_type)
        output.save()

        return output
