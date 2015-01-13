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
    case_4a, case_4b, case_4c, case_5a, case_6a, case_8a)

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
        data = block_splitter(
            models.DamageData.objects.filter(
                dmg_state__risk_calculation=job).order_by(
                'exposure_data', 'dmg_state'),
            len(damage_states))
        # this is a test with 5 damage states
        # no_damage, slight, moderate, extreme, complete
        # print [[col.fraction for col in row] for row in data]
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
        return [[0.227843, 0.058247, 0.153393, 0.135054, 0.425463]]


class ClassicalDamageCase4bTestCase(ClassicalDamageCase1aTestCase):
    module = case_4b
    hazard_calculation_fixture = 'Classical Damage Case4b'

    def expected_data(self):
        return [[0.970851, 0.004430, 0.0084097, 0.0052861, 0.0110226]]


class ClassicalDamageCase4cTestCase(ClassicalDamageCase1aTestCase):
    module = case_4c
    hazard_calculation_fixture = 'Classical Damage Case4c'

    def expected_data(self):
        return [[0.227843, 0.058247, 0.153393, 0.135054, 0.42546]]


class ClassicalDamageCase5aTestCase(ClassicalDamageCase1aTestCase):
    module = case_5a
    hazard_calculation_fixture = 'Classical Damage Case5a'

    def expected_data(self):
        return [[4.8542, 0.02215, 0.0420483, 0.0264303, 0.0551130]]


class ClassicalDamageCase6aTestCase(ClassicalDamageCase1aTestCase):
    module = case_6a
    hazard_calculation_fixture = 'Classical Damage Case6a'

    def expected_data(self):
        return [[0.2510254, 0.0685219, 0.1245198, 0.127938, 0.427995],
                [0.4016303, 0.1060677, 0.1600523, 0.126004, 0.206245],
                [0.9369767, 0.0216853, 0.0220220, 0.011158, 0.008157],
                [0.3501431, 0.0890072, 0.1430024, 0.125272, 0.292575],
                [0.5488149, 0.1044122, 0.1376653, 0.092864, 0.116242],
                [0.4016303, 0.1060677, 0.1600523, 0.126004, 0.206245]]


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
