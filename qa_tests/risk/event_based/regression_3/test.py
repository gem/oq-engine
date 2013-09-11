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
        expected_losses = [  # ordered by rupture.id
            (79863, 0.203958707753),
            (79864, 2.21224010005),
            (79865, 2.60770481222),
            (79866, 0.0892854758558),
            (79869, 0.466600280518),
            (79870, 0.250745715265),
            (79871, 0.66498790008),
            (79872, 0.0130396710319),
            (79873, 3.47032240412),
            (79874, 1.21783516543),
            (79877, 0.404139967036),
            (79883, 0.314635319428),
            (79884, 1.03860779035),
            (79886, 6.80973053605),
            (79888, 2.11361831547),
            (79889, 4.60845052897),
            (79891, 0.595312156869),
            (79893, 1.39366197769),
            (79895, 1.97123851417),
            (79898, 0.70485417345),
            (79900, 0.988359103816),
            (79905, 0.152951104939),
            (79911, 1.18581197446),
            (79925, 0.928539064136),
        ]
        losses = self._run_test().output_set.get(
            output_type="event_loss").event_loss
        actual_losses = sorted(losses, key=lambda l: l.rupture.id)
        for event_loss, (rupture_id, loss) in zip(
                actual_losses, expected_losses):
            self.assertEqual(rupture_id, event_loss.rupture.id)
            self.assertAlmostEqual(
                loss, event_loss.aggregate_loss,
                msg="expected loss for rupture %d is %s (found %s)" % (
                    rupture_id, loss, event_loss.aggregate_loss))
