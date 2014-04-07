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
        poes_1 = [0.999996627985, 0.999898960598, 0.550671035883,
                  0.329679953964, 0.329679953964, 0.181269246922,
                  0.181269246922, 0.181269246922, 0.0]
        poes_2 = [0.999998484856, 0.999998484856, 0.999898960598,
                  0.991770252951, 0.925726421786, 0.834701111778,
                  0.753403036058, 0.451188363906, 0.0]
        poes_3 = [0.999997239227, 0.999997239227, 0.997521247823,
                  0.834701111778, 0.698805788088, 0.550671035883,
                  0.329679953964, 0.181269246922, 0.0]

        losses_1 = [0.0, 0.0110586307001, 0.0221172614003, 0.0331758921004,
                    0.0442345228005, 0.0552931535006, 0.0663517842008,
                    0.0774104149009, 0.088469045601]

        losses_2 = [0.0, 0.00198098963098, 0.00396197926196, 0.00594296889294,
                    0.00792395852392, 0.00990494815491, 0.0118859377859,
                    0.0138669274169, 0.0158479170478]

        losses_3 = [0.0, 0.0061922011659, 0.0123844023318, 0.0185766034977,
                    0.0247688046636, 0.0309610058295, 0.0371532069954,
                    0.0433454081613, 0.0495376093272]

        expected_aggregate_losses = [
            0.0, 41.5307144349, 83.0614288697, 124.592143305, 166.122857739,
            207.653572174, 249.184286609, 290.715001044, 332.245715479]

        expected_event_loss_table = [
            332.245715479, 223.204310173, 164.19438666, 116.380966128,
            115.672019893, 108.551104801, 106.099663772, 105.279399539,
            97.6816116451, 94.7074655294]

        return [poes_1, poes_2, poes_3, losses_1, losses_2, losses_3,
                expected_aggregate_losses, expected_event_loss_table,
                [2850.8972117638, 1.0]]

    def actual_xml_outputs(self, job):
        """
        do not check file outputs
        """
        return []

    def expected_outputs(self):
        return []
