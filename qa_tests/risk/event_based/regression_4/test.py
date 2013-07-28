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


class EventBaseQATestCase(risk.CompleteTestCase, risk.FixtureBasedQATestCase):
    hazard_calculation_fixture = ("QA (regression) test for Risk Event "
                                  "Based from Stochastic Event Set")

    @noseattr('qa', 'risk', 'event_based')
    def test(self):
        event_losses = [
            (40210, 5.4796949),
            (40200, 4.3095791),
            (40199, 4.11539511),
            (40366, 1.7318257),
            (40205, 1.5955741),
            (40198, 1.0677410),
            (40163, 1.0106767),
            (40315, 0.9239069),
            (40162, 0.8238606),
            (40351, 0.8077104),
            (40201, 0.7950468),
            (40207, 0.7676024),
            (40197, 0.5827544),
            (40208, 0.4800674),
            (40206, 0.3131477),
            (40209, 0.3041036),
            (40301, 0.3023419),
            (40159, 0.1189952),
            (40154, 0.1067702),
            (40204, 0.0993114),
            (40318, 0.0599742),
            (40321, 0.0487048),
            (40359, 0.0225967),
            (40157, 0.0008590),
            ]

        for event_loss, (rupture_id, loss) in zip(
                self._run_test().output_set.get(
                    output_type="event_loss").event_loss,
                event_losses):
            self.assertEqual(rupture_id, event_loss.rupture.id)
            self.assertAlmostEqual(
                loss, event_loss.aggregate_loss,
                msg="expected loss for rupture %d is %s (found %s)" % (
                    rupture_id, loss, event_loss.aggregate_loss))
