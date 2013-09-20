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
            141.4061738, 17.7611222856, 4.09522758016, 3.76525596508,
            3.21816337776, 2.9186856439, 2.86641396465, 1.97531074874,
            1.44797867282, 1.35901422448, 1.20639427753, 0.993833679239,
            0.924562361744, 0.740587007803, 0.544386574808, 0.534670090278,
            0.485769830166, 0.481694006612, 0.440383989379, 0.281221895051,
            0.0209633644322, 0.00729990319192, 0.00365613600187]

        losses = self._run_test().output_set.get(
            output_type="event_loss").event_loss

        for event_loss, expected in zip(losses, expected_losses):

            self.assertAlmostEqual(
                expected, event_loss.aggregate_loss,
                msg="loss for rupture %r is %s (expected %s)" % (
                    event_loss.rupture.tag, event_loss.aggregate_loss,
                    expected))
