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

from nose.plugins.attrib import attr as noseattr

from qa_tests import risk
from tests.utils import helpers

from openquake.engine.db import models

# FIXME(lp). This is a regression test. Data has not been validated
# by an alternative reliable implemantation


class EventBasedRiskCase2TestCase(risk.BaseRiskQATestCase):
    output_type = "gmf"

    @noseattr('qa', 'risk', 'event_based')
    def test(self):
        self._run_test()

    def get_hazard_job(self):
        job = helpers.get_hazard_job(
            helpers.get_data_path("event_based_hazard/job.ini"))
        helpers.create_gmf_from_csv(job, self._test_path('gmf.csv'))

        return job

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
                 for el in models.EventLossData.objects.filter(
                event_loss__output__oq_job=job).order_by(
                    '-aggregate_loss')[0:10]]] +
                list(
                    models.LossFraction.objects.get(
                        variable="coordinate",
                        output__oq_job=job).iteritems())[0][1].values())

    def expected_data(self):

        poes_1 = [1., 1., 0.98168436, 0.86466472, 0.86466472,
                  0.63212056, 0.63212056, 0.63212056, 0.]
        poes_2 = [1., 1., 1., 1., 0.99999774,
                  0.99987659, 0.99908812, 0.98168436, 0.]
        poes_3 = [1., 1., 1., 0.99987659, 0.99752125,
                  0.98168436, 0.86466472, 0.63212056, 0.]

        losses_1 = [0., 0.01103294, 0.02206588, 0.03309883, 0.04413177,
                    0.05516471, 0.06619765, 0.07723059, 0.08826354]

        losses_2 = [0., 0.00197485, 0.00394969, 0.00592454, 0.00789938,
                    0.00987423, 0.01184907, 0.01382392, 0.01579877]

        losses_3 = [0., 0.00627624, 0.01255247, 0.01882871, 0.02510495,
                    0.03138118, 0.03765742, 0.04393365, 0.05020989]

        expected_aggregate_losses = [0., 41.41612985, 82.8322597, 124.24838954,
                                     165.66451939, 207.08064924, 248.49677909,
                                     289.91290894, 331.32903879]

        expected_event_loss_table = [331.32903879, 221.56606968, 163.03223466,
                                     117.41787935, 115.83607453,  108.22215086,
                                     106.1758451, 105.35853998, 97.05754656,
                                     94.89922324]

        return [poes_1, poes_2, poes_3, losses_1, losses_2, losses_3,
                expected_aggregate_losses, expected_event_loss_table,
                [2.84407157e+03, 1.00000000e+00]]

    def actual_xml_outputs(self, job):
        """
        do not check file outputs
        """
        return []

    def expected_outputs(self):
        return []
