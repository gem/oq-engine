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
            28.722855927, 7.49433908606, 7.16808174572, 5.64727698201,
            3.47032240412, 2.60770481222, 2.21224010005, 2.18409163174,
            1.89013672397, 1.70523495972, 1.23545360096, 1.21783516543,
            1.08013865792, 1.03860779035, 0.66498790008, 0.466600280518,
            0.404139967036, 0.357534528073, 0.314635319428, 0.250745715265,
            0.216432336364, 0.203958707753, 0.101291562349, 0.0892854758558,
            0.0654713365107, 0.0130396710319,
        ]
        losses = self._run_test().output_set.get(
            output_type="event_loss").event_loss
        for event_loss, expected in zip(losses, expected_losses):
            self.assertAlmostEqual(
                expected, event_loss.aggregate_loss,
                msg="loss for rupture %r is %s (expected %s)" % (
                    event_loss.rupture.tag, event_loss.aggregate_loss,
                    expected))
