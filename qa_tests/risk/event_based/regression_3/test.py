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
            12.549396129, 7.80660766655, 4.46160417067, 3.0019680832,
            2.798428788, 2.49823443274, 2.1114269624, 1.96082766874,
            1.72350552412, 1.67776723506, 1.47087476638, 0.819693734543,
            0.750911455099, 0.477884759581, 0.455570259614, 0.446506027207,
            0.287998256162, 0.283016256577, 0.275858761073, 0.266755234468,
            0.210867727615, 0.0863716558324, 0.0563040094757, 0.0221484327768,
            0.00517745631929, 0.00214222720113]

        losses = self._run_test().output_set.get(
            output_type="event_loss").event_loss

        for event_loss, expected in zip(losses, expected_losses):

            self.assertAlmostEqual(
                expected, event_loss.aggregate_loss,
                msg="loss for rupture %r is %s (expected %s)" % (
                    event_loss.rupture.tag, event_loss.aggregate_loss,
                    expected))
