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
            5.33083443369, 3.94728761785, 3.1223425756, 2.6151541546,
            2.56940323354, 2.22498394278, 1.91646046637, 1.66286113136,
            1.35975710337, 1.17446242495, 0.941926305, 0.779054160432,
            0.674043664504, 0.500301641814, 0.424490126232, 0.322237369209,
            0.258284335777, 0.100717305214, 0.0951221948904, 0.0907799964947,
            0.054055642437]

        outputs = self._run_test().output_set
        losses = outputs.get(output_type="event_loss").event_loss
        for event_loss, expected in zip(losses, expected_losses):
            self.assertAlmostEqual(
                expected, event_loss.aggregate_loss,
                msg="loss for rupture %r is %s (expected %s)" % (
                    event_loss.rupture.tag, event_loss.aggregate_loss,
                    expected))
