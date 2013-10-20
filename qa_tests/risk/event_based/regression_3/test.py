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
            99.7440695666, 24.5663795349, 15.2574877424, 4.3459573556,
            3.62888022928, 2.80494146456, 2.21605881421, 2.02810331131,
            1.7891705299, 1.41674954242, 1.26314581555, 1.24794775436,
            1.16374553877, 0.5620683954, 0.394335695369, 0.353275527684,
            0.34729830941, 0.334522875484, 0.252993137494, 0.21144108574,
            0.142304403795, 0.125025819158, 0.0808149878014, 0.0482149371277,
            0.023587467724, 0.013685031793]

        losses = self._run_test().output_set.get(
            output_type="event_loss").event_loss

        for event_loss, expected in zip(losses, expected_losses):

            self.assertAlmostEqual(
                expected, event_loss.aggregate_loss,
                msg="loss for rupture %r is %s (expected %s)" % (
                    event_loss.rupture.tag, event_loss.aggregate_loss,
                    expected))
