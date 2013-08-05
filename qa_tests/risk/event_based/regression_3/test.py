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
            (40142, 218.4381405), (40140, 2.9125074), (40151, 2.4479393),
            (40135, 2.4346134), (40167, 2.1889858), (40155, 1.9902672),
            (40181, 1.8315612), (40173, 1.3342211), (40165, 1.1462989),
            (40172, 1.1109195),  (40146, 0.9104988), (40197, 0.8659434),
            (40162, 0.8620880), (40152, 0.6739254), (40166, 0.6498746),
            (40168, 0.3292965), (40174, 0.2835871), (40139, 0.2326437),
            (40170, 0.1958384), (40183, 0.1891531), (40164, 0.1507551),
            (40171, 0.1243396), (40177, 0.0635226), (40176, 0.0227906)]

        for event_loss, (rupture_id, loss) in zip(
                self._run_test().output_set.get(
                    output_type="event_loss").event_loss,
                event_losses):
            self.assertEqual(rupture_id, event_loss.rupture.id)
            self.assertAlmostEqual(
                loss, event_loss.aggregate_loss,
                msg="expected loss for rupture %d is %s (found %s)" % (
                    rupture_id, loss, event_loss.aggregate_loss))
