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


# FIXME(lp). This is just a regression test
class EventBasedRiskCase1TestCase(risk.BaseRiskQATestCase):
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
                [curve.stddev_loss_ratio
                 for curve in models.LossCurveData.objects.filter(
                loss_curve__output__oq_job=job,
                loss_curve__aggregate=False,
                loss_curve__insured=False).order_by('asset_ref')] +
                [curve.average_loss
                 for curve in models.AggregateLossCurveData.objects.filter(
                loss_curve__output__oq_job=job,
                loss_curve__aggregate=True,
                loss_curve__insured=False)] +
                [curve.stddev_loss
                 for curve in models.AggregateLossCurveData.objects.filter(
                loss_curve__output__oq_job=job,
                loss_curve__aggregate=True,
                loss_curve__insured=False)] +
                [[point.value
                  for point in models.LossMapData.objects.filter(
                loss_map__output__oq_job=job).order_by(
                    'asset_ref', 'loss_map__poe')]] +
                [[el.aggregate_loss
                 for el in models.EventLossData.objects.filter(
                event_loss__output__oq_job=job).order_by(
                    '-aggregate_loss')[0:10]]])

    def expected_data(self):
        # FIXME(lp). Event Loss Table data do not come from a reliable
        # implementation. This is just a regression test
        expected_event_loss_table = [330.0596974, 222.4581073, 162.7511019,
                                     115.9594444, 115.8300568, 107.8437644,
                                     105.7095923, 105.0259645, 96.6493404,
                                     93.7629886]

        return [
            [0.07021910798], [0.015239297], [0.04549904],
            [0.0569212190852481], [0.00779260434], [0.0],
            [0.0059876], [0.0022866], [0.0053434],
            [278.904436],
            [46.0207855534291],
            [263.37280611, 262.51974659, 261.66668707,
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
