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
            (79868, 19.9055378), (79867, 4.8712398), (79884, 3.4814816),
            (79881, 3.2980766), (79870, 2.8507847), (79909, 2.3475407),
            (79892, 1.7721695), (79893, 1.7009114), (79900, 1.2081667),
            (79862, 1.1857208), (79882, 1.1170384), (79925, 1.0547829),
            (79901, 0.5913165), (79883, 0.5539488), (79898, 0.4428787),
            (79872, 0.2768999), (79887, 0.2451369), (79905, 0.1332209),
            (79869, 0.1292060), (79879, 0.1026115), (79911, 0.0865134),
            (79895, 0.0856290), (79888, 0.0808917), (79904, 0.0325448),
            (79863, 0.0095395)]

        for event_loss, (rupture_id, loss) in zip(
                self._run_test().output_set.get(
                    output_type="event_loss").event_loss,
                event_losses):
            #            self.assertEqual(rupture_id, event_loss.rupture.id)
            self.assertAlmostEqual(
                loss, event_loss.aggregate_loss,
                msg="expected loss for rupture %d is %s (found %s)" % (
                    rupture_id, loss, event_loss.aggregate_loss))
