# Copyright (c) 2010-2014, GEM Foundation.
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
from openquake.engine.tests.utils import helpers

from openquake.engine.db import models

# FIXME(lp). This is a regression test. Data has not been validated
# by an alternative reliable implemantation


class EventBasedRiskCase2TestCase(risk.BaseRiskQATestCase):
    output_type = "gmf"

    @noseattr('qa', 'risk', 'event_based')
    def test(self):
        self._run_test()

    def get_hazard_job(self):
        job = helpers.get_job(
            helpers.get_data_path("event_based_hazard/job.ini"))
        helpers.create_gmf_from_csv(job, self._test_path('gmf.csv'))

        return job

    def actual_data(self, job):
        data = ([curve.poes
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
        return data

    def expected_data(self):
        poes_1 = [0.999996627985, 0.999849266925, 0.550671035883,
                  0.329679953964, 0.329679953964, 0.181269246922,
                  0.181269246922, 0.181269246922, 0.0]
        poes_2 = [0.999998484856, 0.999998484856, 0.999917275934,
                  0.993262053001, 0.925726421786, 0.834701111778,
                  0.698805788088, 0.550671035883, 0.0]
        poes_3 = [0.999997239227, 0.999997239227, 0.997521247823,
                  0.834701111778, 0.698805788088, 0.451188363906,
                  0.329679953964, 0.181269246922, 0.0]
        losses_1 = [0.0, 0.0110999061875, 0.0221998123751, 0.0332997185626,
                    0.0443996247501, 0.0554995309376, 0.0665994371252,
                    0.0776993433127, 0.0887992495002]
        losses_2 = [0.0, 0.00197070366487, 0.00394140732973, 0.0059121109946,
                    0.00788281465947, 0.00985351832434, 0.0118242219892,
                    0.0137949256541, 0.0157656293189]
        losses_3 = [0.0, 0.00627183973737, 0.0125436794747, 0.0188155192121,
                    0.0250873589495, 0.0313591986868, 0.0376310384242,
                    0.0439028781616, 0.0501747178989]
        expected_aggregate_losses = [
            0.0, 41.5569324154, 83.1138648309, 124.670797246, 166.227729662,
            207.784662077, 249.341594493, 290.898526908, 332.455459323]

        expected_event_loss_table = [
            332.455459323, 221.05497273, 164.077337072, 118.399426421,
            115.406897066, 108.925518713, 104.67570929, 104.295934513,
            96.7416846911, 94.4460331092]

        loss_fraction = [2847.6635362969, 1.0]

        return [poes_1, poes_2, poes_3, losses_1, losses_2, losses_3,
                expected_aggregate_losses, expected_event_loss_table,
                loss_fraction]

    def actual_xml_outputs(self, job):
        """
        do not check file outputs
        """
        return []

    def expected_outputs(self):
        return []
