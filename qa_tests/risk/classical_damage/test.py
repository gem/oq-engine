# Copyright (c) 2015, GEM Foundation.
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


from nose.plugins.attrib import attr

from qa_tests import risk
from openquake.baselib.general import block_splitter
from openquake.qa_tests_data.classical_damage import (
    case_1a, case_1b, case_1c, case_2a, case_2b, case_3a,
    case_4a, case_4b, case_4c, case_5a, case_6a, case_6b,
    case_7a, case_7b, case_7c, case_8a)

from openquake.engine.db import models


class ClassicalDamageCase1aTestCase(risk.FixtureBasedQATestCase):
    module = case_1a
    output_type = 'dmg_per_asset'
    hazard_calculation_fixture = 'Classical Damage Case1a'

    @attr('qa', 'risk', 'classical_damage')
    def test(self):
        self._run_test()

    def actual_data(self, job):
        damage_states = list(models.DmgState.objects.filter(
            risk_calculation=job).order_by('lsi'))
        data = list(block_splitter(
            models.DamageData.objects.filter(
                dmg_state__risk_calculation=job).order_by(
                'exposure_data', 'dmg_state'),
            len(damage_states)))
        # this is a test with 5 damage states
        # no_damage, slight, moderate, extreme, complete
        # NB: you can print the actual values with the command
        # print [[round(col.fraction, 8) for col in row] for row in data]
        return [[col.fraction for col in row] for row in data]

    def expected_data(self):
        return [[0.971702, 0.00488098, 0.0067176, 0.005205, 0.0114946]]


class ClassicalDamageCase1bTestCase(ClassicalDamageCase1aTestCase):
    module = case_1b
    hazard_calculation_fixture = 'Classical Damage Case1b'

    def expected_data(self):
        return [[0.98269, 0.001039, 0.0028866, 0.0032857, 0.01009]]


class ClassicalDamageCase1cTestCase(ClassicalDamageCase1aTestCase):
    module = case_1c
    hazard_calculation_fixture = 'Classical Damage Case1c'

    def expected_data(self):
        return [[0.97199, 0.004783, 0.0066179, 0.005154, 0.011452]]


class ClassicalDamageCase2aTestCase(ClassicalDamageCase1aTestCase):
    module = case_2a
    hazard_calculation_fixture = 'Classical Damage Case2a'

    def expected_data(self):
        return [[0.970723, 0.0045270, 0.0084847, 0.0052886, 0.010976]]


class ClassicalDamageCase2bTestCase(ClassicalDamageCase1aTestCase):
    module = case_2b
    hazard_calculation_fixture = 'Classical Damage Case2b'

    def expected_data(self):
        return [[0.970740, 0.004517, 0.00847858, 0.0052878, 0.0109759]]


class ClassicalDamageCase3aTestCase(ClassicalDamageCase1aTestCase):
    module = case_3a
    hazard_calculation_fixture = 'Classical Damage Case3a'

    def expected_data(self):
        return [[0.9724910, 0.0080209, 0.0105995, 0.00573419, 0.00315432]]


class ClassicalDamageCase4aTestCase(ClassicalDamageCase1aTestCase):
    module = case_4a
    hazard_calculation_fixture = 'Classical Damage Case4a'

    def expected_data(self):
        return [[0.9708513, 0.00443036, 0.00840967, 0.00528607, 0.01102261]]


class ClassicalDamageCase4bTestCase(ClassicalDamageCase1aTestCase):
    module = case_4b
    hazard_calculation_fixture = 'Classical Damage Case4b'

    def expected_data(self):
        return [[0.10875611, 0.04426596, 0.13832666, 0.14414043, 0.56451083]]


class ClassicalDamageCase4cTestCase(ClassicalDamageCase1aTestCase):
    module = case_4c
    hazard_calculation_fixture = 'Classical Damage Case4c'

    def expected_data(self):
        return [[0.10875611, 0.04426596, 0.13832666, 0.14414043, 0.56451083]]


class ClassicalDamageCase5aTestCase(ClassicalDamageCase1aTestCase):
    module = case_5a
    hazard_calculation_fixture = 'Classical Damage Case5a'

    def expected_data(self):
        return [[4.8542, 0.02215, 0.0420483, 0.0264303, 0.0551130]]


class ClassicalDamageCase6aTestCase(ClassicalDamageCase1aTestCase):
    module = case_6a
    hazard_calculation_fixture = 'Classical Damage Case6a'

    def expected_data(self):
        return [[0.06301378, 0.03909675, 0.09508513, 0.12999397, 0.67281037],
                [0.16130693, 0.09645038, 0.18813321, 0.18415595, 0.36995353],
                [0.87792542, 0.04110761, 0.0427084, 0.02201042, 0.01624816],
                [0.12260021, 0.0702528, 0.14604874, 0.16154833, 0.49954991],
                [0.30119781, 0.12550791, 0.19880522, 0.15551612, 0.21897294],
                [0.16130693, 0.09645038, 0.18813321, 0.18415595, 0.36995353]]


class ClassicalDamageCase6bTestCase(ClassicalDamageCase1aTestCase):
    module = case_6b
    hazard_calculation_fixture = 'Classical Damage Case6b'

    def expected_data(self):
        return [[0.05132446, 0.03032147, 0.11238226, 0.13762602, 0.66834579],
                [0.1302479, 0.08925888, 0.2472125, 0.18714448, 0.34613624],
                [0.93318609, 0.03029261, 0.02728063, 0.00595485, 0.00328582],
                [0.10424884, 0.06239919, 0.18409204, 0.16652967, 0.48273026],
                [0.29003432, 0.13273485, 0.25931611, 0.1376464, 0.18026831],
                [0.1302479, 0.08925888, 0.2472125, 0.18714448, 0.34613624]]


class ClassicalDamageCase7aTestCase(ClassicalDamageCase1aTestCase):
    module = case_7a
    hazard_calculation_fixture = 'Classical Damage Case7a'

    def expected_data(self):
        return [[0.06301378, 0.03909675, 0.09508513, 0.12999397, 0.67281037],
                [0.16130693, 0.09645038, 0.18813321, 0.18415595, 0.36995353],
                [0.91903303, 0.0471033, 0.0269629, 0.00571892, 0.00118185],
                [0.19285301, 0.17028299, 0.27374034, 0.18497291, 0.17815075],
                [0.65243418, 0.22209179, 0.08482701, 0.03217498, 0.00847204],
                [0.47516714, 0.28849739, 0.14619763, 0.06741531, 0.02272253]]


class ClassicalDamageCase7bTestCase(ClassicalDamageCase1aTestCase):
    module = case_7b
    hazard_calculation_fixture = 'Classical Damage Case7b'

    def expected_data(self):
        return [[0.06301378, 0.03909675, 0.09508513, 0.12999397, 0.67281037],
                [0.16130693, 0.09645038, 0.18813321, 0.18415595, 0.36995353],
                [0.73342934, 0.14330431, 0.09448068, 0.02288565, 0.00590003],
                [0.11061773, 0.10585034, 0.22465056, 0.21819367, 0.3406877],
                [0.62971368, 0.21550694, 0.09467873, 0.04120754, 0.01889312],
                [0.47753749, 0.26550632, 0.14528757, 0.0724332, 0.03923541]]


class ClassicalDamageCase7cTestCase(ClassicalDamageCase1aTestCase):
    module = case_7c
    hazard_calculation_fixture = 'Classical Damage Case7c'

    def expected_data(self):
        return [[0.06164802, 0.03902175, 0.09523551, 0.1303836, 0.67371112],
                [0.14910587, 0.09583375, 0.19056627, 0.18833682, 0.37615729],
                [0.90143432, 0.05227187, 0.03407395, 0.00919452, 0.00302533],
                [0.12204831, 0.10328133, 0.21936038, 0.2155306, 0.33977939],
                [0.82474478, 0.10879111, 0.04283268, 0.01778066, 0.00585077],
                [0.69657784, 0.17673021, 0.07871599, 0.03504793, 0.01292803]]


# test with two realizations
class ClassicalDamageCase8aTestCase(ClassicalDamageCase1aTestCase):
    module = case_8a
    hazard_calculation_fixture = 'Classical Damage Case8a'

    def actual_data(self, job):
        damage_states = list(models.DmgState.objects.filter(
            risk_calculation=job).order_by('lsi'))
        outs = models.Output.objects.filter(oq_job=job).order_by('id')
        rows = []
        for out in outs:
            data = [[
                col.fraction for col in row] for row in block_splitter(
                models.DamageData.objects.filter(
                    damage=out.damage).order_by(
                    'exposure_data', 'dmg_state'),
                len(damage_states))]
            rows.append(data)
        # this is a test with 5 damage states
        # no_damage, slight, moderate, extreme, complete
        return rows

    def expected_data(self):
        return [
            [[0.97199275, 0.00478318, 0.0066179, 0.0051539, 0.011452]],
            [[0.97385963, 0.00522663, 0.0068353, 0.0049527, 0.009126]]]
