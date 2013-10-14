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

        expected_losses = [
            575.158581474, 62.0838902553, 16.8038438054, 10.8225018447,
            5.69282841628, 4.58897724248, 3.61951297492, 3.15036072868,
            3.07173042505, 2.84652273841, 1.94160856895, 1.34319495662,
            1.16606682534, 1.10389156052, 0.919850588692, 0.5620683954,
            0.348229057828, 0.334522875484, 0.26346907182, 0.256668814205,
            0.248928183728, 0.125025819158, 0.0920938564152, 0.0611487447609,
            0.0244550662875]

        losses = self._run_test().output_set.get(
            output_type="event_loss").event_loss

        for event_loss, expected in zip(losses, expected_losses):

            self.assertAlmostEqual(
                expected, event_loss.aggregate_loss,
                msg="loss for rupture %r is %s (expected %s)" % (
                    event_loss.rupture.tag, event_loss.aggregate_loss,
                    expected))
