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


# FIXME(lp). This is a regression test. Data has not been validated
# by an alternative reliable implemantation


class EventBasedRiskCase2TestCase(risk.BaseRiskQATestCase):
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

        return gmf_set.gmf_collection.output.id

    def actual_data(self, job):
        return ([curve.poes
                for curve in models.LossCurveData.objects.filter(
                    loss_curve__output__oq_job=job,
                    loss_curve__aggregate=False,
                    loss_curve__insured=False).order_by('asset_ref')] +
                [curve.loss_ratios
                for curve in models.LossCurveData.objects.filter(
                    loss_curve__output__oq_job=job,
                    loss_curve__aggregate=False,
                    loss_curve__insured=False).order_by('asset_ref')] +
                [curve.losses
                for curve in models.AggregateLossCurveData.objects.filter(
                    loss_curve__output__oq_job=job,
                    loss_curve__aggregate=True,
                    loss_curve__insured=False)] +
                [[el.aggregate_loss
                 for el in models.EventLoss.objects.filter(
                output__oq_job=job).order_by('-aggregate_loss')[0:10]]])

    def expected_data(self):

        poes_1 = [1., 1., 0.98168436, 0.86466472, 0.86466472,
                  0.63212056, 0.63212056, 0.63212056, 0.]
        poes_2 = [1., 1., 1., 1., 0.99999774,
                  0.99987659, 0.99908812, 0.98168436, 0.]
        poes_3 = [1., 1., 1., 0.99987659, 0.99752125,
                  0.98168436, 0.86466472, 0.63212056, 0.]

        losses_1 = [0., 0.01082792, 0.02165583, 0.03248375, 0.04331167,
                    0.05413958, 0.0649675, 0.07579541, 0.08662333]

        losses_2 = [0., 0.00194445, 0.00388891, 0.00583336, 0.00777782,
                    0.00972227, 0.01166673, 0.01361118, 0.01555564]

        losses_3 = [0., 0.00620783, 0.01241566, 0.01862349, 0.02483132,
                    0.03103915, 0.03724697, 0.0434548, 0.04966263]

        expected_aggregate_losses = [0., 40.74183549, 81.48367098,
                                     122.22550648, 162.96734197, 203.70917746,
                                     244.45101295,  285.19284844, 325.93468394]

        expected_event_loss_table = [325.93468394, 226.10203138, 161.34708564,
                                     114.59153235, 114.5070817, 107.55192352,
                                     107.16635393, 104.94262851, 94.90879987,
                                     93.52459622]

        return [poes_1, poes_2, poes_3, losses_1, losses_2, losses_3,
                expected_aggregate_losses, expected_event_loss_table]

    def actual_xml_outputs(self, job):
        """
        do not check file outputs
        """
        return []

    def expected_outputs(self):
        return []
