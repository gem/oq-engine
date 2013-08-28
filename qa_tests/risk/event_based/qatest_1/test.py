# Copyright (c) 2013, GEM Foundation.
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


class EventBaseQATestCase1(risk.CompleteTestCase, risk.FixtureBasedQATestCase):
    hazard_calculation_fixture = "PEB QA test 1"

    @noseattr('qa', 'risk', 'event_based')
    def test(self):
        self._run_test()

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
        costs = [u"nonstructural", u"structural", u"contents"]

        def gen_loss_curves(branches, costs):
            for branch, metadata in branches:
                for cost in costs:
                    csv_name = "%s_%s" % (branch, cost)
                    data = self._csv(csv_name)
                    for i, asset in enumerate(assets):
                        descriptor = (u'event_loss_curve', metadata, None,
                                      None, False, False, cost, asset)
                        asset_value = data[i * 2 + 1, 0]
                        curve = models.LossCurveData(
                            asset_value=asset_value,
                            loss_ratios=data[i * 2, 2:] / asset_value,
                            poes=data[i * 2 + 1, 2:])
                        yield descriptor, curve

        loss_curves = (
            list(gen_loss_curves(branches.items(), costs)) +
            list(gen_loss_curves([("b1", branches["b1"])], ["fatalities"])))

        data = self._csv("aggregates")

        aggregate_loss_curves = [
            ((u'agg_loss_curve', branch, None,
              None, True, False, "structural"),
             models.AggregateLossCurveData(
                 losses=data[i * 2, 2:],
                 poes=data[i * 2 + 1, 2:]))
            for i, branch in enumerate(branches.values())]

        # we check only the first 10 values of the event loss table
        data = self._csv('event_loss_table')[1:, 0:3]
        data = sorted(data, key=lambda v: -v[2])[0:10]
        event_loss_table_b1 = [
            ((u'event_loss', branches["b1"], "structural", i),
             models.EventLossData(rupture_id=i, aggregate_loss=j))
            for i, _m, j in data]

        return loss_curves + aggregate_loss_curves + event_loss_table_b1
