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
            (40142, 30.2163791), (40152, 17.5868035), (40151, 2.8766444),
            (40192, 2.6660042), (40165, 1.9753107), (40140, 1.6903534),
            (40166, 1.3590142), (40135, 1.3265135), (40167, 0.9938337),
            (40144, 0.9895948), (40156, 0.9250677), (40173, 0.9245624),
            (40197, 0.8933618), (40181, 0.6939962), (40155, 0.6450982),
            (40168, 0.5443866), (40174, 0.4857698), (40139, 0.4816940),
            (40164, 0.4403840), (40162, 0.1272359), (40157, 0.1103932),
            (40163, 0.0609694), (40146, 0.0573895), (40159, 0.0284193),
            (40148, 0.0280016), (40182, 0.0146607), (40161, 0.0027207)]

        for event_loss, (rupture_id, loss) in zip(
                self._run_test().output_set.get(
                    output_type="event_loss").event_loss,
                event_losses):
            self.assertEqual(rupture_id, event_loss.rupture.id)
            self.assertAlmostEqual(
                loss, event_loss.aggregate_loss,
                msg="expected loss for rupture %d is %s (found %s)" % (
                    rupture_id, loss, event_loss.aggregate_loss))
