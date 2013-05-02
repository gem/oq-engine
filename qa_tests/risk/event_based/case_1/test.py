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

import os
import csv
import numpy

from nose.plugins.attrib import attr as noseattr

from qa_tests import risk
from tests.utils import helpers

from openquake.engine.db import models
from openquake.engine.calculators.hazard.event_based.post_processing import \
    populate_gmf_agg


# FIXME(lp). This is just a regression test
class EventBasedRiskCase1TestCase(risk.BaseRiskQATestCase):
    cfg = os.path.join(os.path.dirname(__file__), 'job.ini')

    @noseattr('qa', 'risk', 'event_based')
    def test(self):
        self._run_test()

    def hazard_id(self):
        job = helpers.get_hazard_job(
            helpers.demo_file("event_based_hazard/job.ini"))

        job.hazard_calculation = models.HazardCalculation.objects.create(
            owner=job.hazard_calculation.owner,
            truncation_level=job.hazard_calculation.truncation_level,
            maximum_distance=job.hazard_calculation.maximum_distance,
            intensity_measure_types_and_levels=(
                job.hazard_calculation.intensity_measure_types_and_levels),
            calculation_mode="event_based",
            investigation_time=50,
            ses_per_logic_tree_path=1)
        job.save()
        hc = job.hazard_calculation

        lt_realization = models.LtRealization.objects.create(
            hazard_calculation=job.hazard_calculation,
            ordinal=1, seed=1, weight=None,
            sm_lt_path="test_sm", gsim_lt_path="test_gsim",
            is_complete=False, total_items=1, completed_items=1)

        gmf_set = models.GmfSet.objects.create(
            gmf_collection=models.GmfCollection.objects.create(
                output=models.Output.objects.create_output(
                    job, "Test Hazard output", "gmf"),
                lt_realization=lt_realization),
            investigation_time=hc.investigation_time,
            ses_ordinal=1)

        with open(os.path.join(
                os.path.dirname(__file__), 'gmf.csv'), 'rb') as csvfile:
            gmfreader = csv.reader(csvfile, delimiter=',')
            locations = gmfreader.next()

            gmv_matrix = numpy.array([[float(x) for x in row]
                                      for row in gmfreader]).transpose()

            rupture_ids = helpers.get_rupture_ids(
                job, hc, lt_realization, len(gmv_matrix[0]))

            for i, gmvs in enumerate(gmv_matrix):
                models.Gmf.objects.create(
                    gmf_set=gmf_set,
                    imt="PGA", gmvs=gmvs,
                    rupture_ids=map(str, rupture_ids),
                    result_grp_ordinal=1,
                    location="POINT(%s)" % locations[i])

            populate_gmf_agg(job.hazard_calculation)

        return gmf_set.gmf_collection.output.id

    def actual_data(self, job):
        return ([curve.average_loss_ratio
                 for curve in models.LossCurveData.objects.filter(
                loss_curve__output__oq_job=job,
                loss_curve__aggregate=False,
                loss_curve__insured=False).order_by('asset_ref')] +
                [curve.average_loss_ratio
                 for curve in models.LossCurveData.objects.filter(
                loss_curve__output__oq_job=job,
                loss_curve__aggregate=False,
                loss_curve__insured=True).order_by('asset_ref')] +
                [curve.average_loss
                 for curve in models.AggregateLossCurveData.objects.filter(
                loss_curve__output__oq_job=job,
                loss_curve__aggregate=True,
                loss_curve__insured=False)] +
                [[point.value
                  for point in models.LossMapData.objects.filter(
                loss_map__output__oq_job=job).order_by(
                    'asset_ref', 'loss_map__poe')]] +
                [[el.aggregate_loss
                 for el in models.EventLoss.objects.filter(
                output__oq_job=job).order_by('-aggregate_loss')[0:10]]])

    def expected_data(self):
        # FIXME(lp). Event Loss Table data do not come from a reliable
        # implementation. This is just a regression test
        expected_event_loss_table = [330.0596974, 222.4581073, 162.7511019,
                                     115.9594444, 115.8300568, 107.8437644,
                                     105.7095923, 105.0259645, 96.6493404,
                                     93.7629886]

        return [
            [0.07021910798], [0.015239297], [0.04549904],
            [0.07021910797], [0.015239291], [0.03423366],
            [278.904436],
            [148.35539647, 147.87487616, 147.39435584,
             30.96750422, 30.89424056, 30.82097689, 49.45179882, 49.29162539,
             49.13145195],
            expected_event_loss_table]

    def actual_xml_outputs(self, job):
        """
        Event Loss is in CSV format
        """
        return models.Output.objects.none()

    def expected_outputs(self):
        return []
