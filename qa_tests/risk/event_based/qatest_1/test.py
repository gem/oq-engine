# Copyright (c) 2014, GEM Foundation.
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

from openquake.engine.db import models

from numpy.testing import assert_almost_equal as aae


class EventBaseQATestCase1(risk.CompleteTestCase, risk.FixtureBasedQATestCase):
    hazard_calculation_fixture = "PEB QA test 1"

    @noseattr('qa', 'risk', 'event_based')
    def test(self):
        self._run_test()

    expected_elt_b2 = [  # the first 10 values for structural
        ('smlt=00|ses=1250|src=3|rup=002-01', 5.55, 4598.15454207),
        ('smlt=00|ses=0899|src=3|rup=006-01', 6.75, 3229.03853895),
        ('smlt=00|ses=0236|src=3|rup=004-01', 6.15, 1429.41738598),
        ('smlt=00|ses=0833|src=3|rup=006-01', 6.75, 1333.06460009),
        ('smlt=00|ses=1159|src=3|rup=001-02', 5.25, 1027.93870557),
        ('smlt=00|ses=1395|src=3|rup=001-01', 5.25, 1004.52792749),
        ('smlt=00|ses=0410|src=3|rup=001-01', 5.25, 801.220856365),
        ('smlt=00|ses=1652|src=3|rup=003-01', 5.85, 710.514040648),
        ('smlt=00|ses=0986|src=3|rup=001-01', 5.25, 661.852362756),
        ('smlt=00|ses=0296|src=3|rup=002-01', 5.55, 605.144033155),
    ]

    def expected_output_data(self):
        branches = dict(
            b1=models.Output.HazardMetadata(
                investigation_time=50.0,
                statistics=None, quantile=None,
                sm_path=('b1',), gsim_path=('b1',)),
            b2=models.Output.HazardMetadata(
                investigation_time=50.0,
                statistics=None, quantile=None,
                sm_path=('b1',), gsim_path=('b2',)))

        assets = ["a0", "a1", "a2", "a3"]
        costs = ["nonstructural", "structural", "contents"]

        def gen_loss_curves(branches, costs):
            for branch, metadata in branches:
                for cost in costs:
                    csv_name = "%s_%s" % (branch, cost)
                    data = self._csv(csv_name)
                    yield csv_name, None
                    for i, asset in enumerate(assets):
                        descriptor = (u'event_loss_curve', metadata, None,
                                      None, False, False, cost, asset)
                        asset_value = data[i * 2 + 1, 0]
                        curve = models.LossCurveData(
                            asset_value=asset_value,
                            loss_ratios=data[i * 2, 2:],
                            poes=data[i * 2 + 1, 2:])
                        yield descriptor, curve

        loss_curves = (
            list(gen_loss_curves(branches.items(), costs)) +
            list(gen_loss_curves([("b1", branches["b1"])], ["fatalities"])))

        data = self._csv("aggregates")

        aggregate_loss_curves = [
            ('aggregates', None)] + [
            ((u'agg_loss_curve', branch, None,
              None, True, False, "structural"),
             models.AggregateLossCurveData(
                 losses=data[i * 2, 2:],
                 poes=data[i * 2 + 1, 2:]))
            for i, branch in enumerate(branches.values())]

        return loss_curves + aggregate_loss_curves

    def check_event_loss_table(self, job):
        # we check only the first 10 values of the event loss table
        # for loss_type=structural and branch b2
        tags = [row[0] for row in self.expected_elt_b2]

        el_b2 = models.EventLoss.objects.get(
            hazard_output__gmf__lt_realization__gsim_lt_path=['b2'],
            output__output_type='event_loss',
            output__oq_job=job,
            loss_type='structural')
        elt = models.EventLossData.objects.filter(
            event_loss=el_b2.id, rupture__tag__in=tags
        ).order_by('-aggregate_loss')
        for e, row in zip(elt, self.expected_elt_b2):
            self.assertEqual(e.rupture.tag, row[0])
            self.assertEqual(e.rupture.rupture.mag, row[1])
            self.assertAlmostEqual(e.aggregate_loss, row[2])

    def check_loss_map(self, job):
        lm_with_stats = models.LossMap.objects.filter(
            output__oq_job=job, statistics__isnull=True,
            loss_type='structural').order_by('poe', 'hazard_output')
        self.assertEqual(lm_with_stats.count(), 6)
        lm1, lm2 = lm_with_stats[:2]  # loss maps for poe=0.1 for 2 rlzs
        actual_lm1 = [
            point.value for point in models.LossMapData.objects.filter(
                loss_map=lm1).order_by('asset_ref', 'loss_map__poe')]
        aae(actual_lm1, [644.42878691, 234.89986442,
                         664.82432932, 753.55988728])

        actual_lm2 = [
            point.value for point in models.LossMapData.objects.filter(
                loss_map=lm2).order_by('asset_ref', 'loss_map__poe')]
        aae(actual_lm2, [376.21304957, 219.38682742,
                         639.86715118,  801.07318199])

    def check_loss_map_mean(self, job):
        lm_with_stats = models.LossMap.objects.filter(
            output__oq_job=job, statistics='mean',
            loss_type='structural').order_by('poe')
        self.assertEqual(lm_with_stats.count(), 3)
        actual = [
            point.value for point in models.LossMapData.objects.filter(
                loss_map__in=lm_with_stats).order_by(
                'asset_ref', 'loss_map__poe')]
        aae(actual, [514.22057893, 0., 0.,
                     227.85575576, 0., 0.,
                     652.50322751, 0., 0.,
                     778.04645901, 0., 0.])

    def check_loss_map_quantile(self, job):
        lm_with_quantile = models.LossMap.objects.filter(
            output__oq_job=job, statistics='quantile',
            loss_type='structural').order_by('poe')
        self.assertEqual(lm_with_quantile.count(), 9)
        actual_0 = [
            point.value for point in models.LossMapData.objects.filter(
                loss_map=lm_with_quantile[0]).order_by(
                'asset_ref', 'loss_map__poe')]
        aae(actual_0, [376.24261986, 219.38682742,
                       639.86715118, 753.55988728])
