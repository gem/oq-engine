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

import os
import unittest

from nose.plugins.attrib import attr
import numpy
from numpy.testing import assert_almost_equal as aae

from qa_tests import risk
from openquake.qa_tests_data.event_based_risk import case_1, case_2

from openquake.engine.db import models
from openquake.commonlib.readers import read_composite_array
from openquake.commonlib.writers import scientificformat

# the engine tests are skipped since the numbers refer to before the fix in
# https://github.com/gem/oq-risklib/pull/263; also, the engine implementation
# is frozen and will be soon replaced by the oq-lite implementation which is
# fully tested


@unittest.SkipTest
class EventBaseQATestCase1(risk.CompleteTestCase, risk.FixtureBasedQATestCase):
    module = case_1

    hazard_calculation_fixture = "PEB QA test 1"

    @attr('qa', 'risk', 'event_based')
    def test(self):
        self._run_test()

    expected_elt_b2 = [  # the first 10 values for structural
        ('col=00|ses=0899|src=3|rup=006-01', 6.75, 5000.70195926),
        ('col=00|ses=1652|src=3|rup=003-01', 5.85, 1695.73806676),
        ('col=00|ses=0986|src=3|rup=001-01', 5.25, 1616.02519712),
        ('col=00|ses=0410|src=3|rup=001-01', 5.25, 1541.65889955),
        ('col=00|ses=0833|src=3|rup=006-01', 6.75, 1537.37564177),
        ('col=00|ses=1250|src=3|rup=002-01', 5.55, 1493.81917509),
        ('col=00|ses=0236|src=3|rup=004-01', 6.15, 1434.79598377),
        ('col=00|ses=1395|src=3|rup=001-01', 5.25, 734.205956121),
        ('col=00|ses=1159|src=3|rup=001-02', 5.25, 680.828016553),
        ('col=00|ses=0296|src=3|rup=002-01', 5.55, 546.435038991),
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
        aae(actual_lm1, [678.477001592533, 280.814859739759,
                         661.73629005541, 777.092150609068])
        actual_lm2 = [
            point.value for point in models.LossMapData.objects.filter(
                loss_map=lm2).order_by('asset_ref', 'loss_map__poe')]
        aae(actual_lm2, [401.951863344031, 232.793896122415,
                         644.37214688894, 834.012565907811])

    def check_loss_map_stats(self, job):
        mean_maps = models.LossMap.objects.filter(
            output__oq_job=job, statistics='mean',
            loss_type='structural').order_by('poe')
        data = numpy.zeros((3, 4, 4))
        # 3 clp x (3 quantiles + 1 mean) x 4 assets
        for j, mm in enumerate(mean_maps):
            dataset = mm.lossmapdata_set.order_by('asset_ref')
            data[j][0] = [d.value for d in dataset]

            quantile_maps = models.LossMap.objects.filter(
                output__oq_job=job, statistics='quantile', poe=mm.poe,
                loss_type='structural').order_by('quantile')
            for i, qm in enumerate(quantile_maps, 1):
                dataset = qm.lossmapdata_set.order_by('asset_ref')
                data[j][i] = [d.value for d in dataset]

        # compare with oq-lite means
        means = read_composite_array(
            self._test_path('expected/mean-structural-loss_maps.csv'))
        aae(means['poe~0.1'], data[0, 0], decimal=4)  # (P, 0, N)
        aae(means['poe~0.5'], data[1, 0])
        aae(means['poe~0.9'], data[2, 0])

        # compare with oq-lite first quantile
        q025 = read_composite_array(
            self._test_path('expected/quantile-0.25-structural-loss_maps.csv'))
        aae(q025['poe~0.1'], data[0, 1], decimal=4)  # (P, 1, N)
        aae(q025['poe~0.5'], data[1, 1], decimal=4)
        aae(q025['poe~0.9'], data[2, 1], decimal=4)


class EventBaseQATestCase2(risk.CompleteTestCase, risk.FixtureBasedQATestCase):
    """
    This is a fast test of the event_loss_table, which is quite stringent
    """
    module = case_2
    hazard_calculation_fixture = "PEB QA test 2"

    @attr('qa', 'risk', 'event_based')
    def test(self):
        self._run_test()

    def check_event_loss_asset(self, job):
        el = models.EventLoss.objects.get(
            output__output_type='event_loss_asset', output__oq_job=job)
        path = self._test_path("expected/event_loss_asset.csv")
        expectedlines = open(path).read().split()
        gotlines = [
            scientificformat([row.rupture.tag, row.asset.asset_ref, row.loss],
                             fmt='%11.8E', sep=',')
            for row in el.eventlossasset_set.order_by(
                'rupture__tag', 'asset__asset_ref')]
        if gotlines != expectedlines:
            actual_dir = self._test_path("actual")
            if not os.path.exists(actual_dir):
                os.mkdir(actual_dir)
            open(os.path.join(actual_dir, "event_loss_asset.csv"), 'w').write(
                '\n'.join(gotlines))
        self.assertEqual(expectedlines, gotlines)
