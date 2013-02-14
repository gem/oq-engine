from cStringIO import StringIO
import unittest
import mock

from openquake.nrmllib.risk import parsers
from openquake.engine.calculators.risk.scenario_damage.core import \
    ScenarioDamageRiskCalculator

FRAGILITY_FILE = StringIO('''<?xml version='1.0' encoding='utf-8'?>
<nrml xmlns="http://openquake.org/xmlns/nrml/0.4">

    <fragilityModel format="continuous" imlUnit="m" minIML="0.1" maxIML="9.9">
        <description>Fragility model for Pavia (continuous)</description>
        <IML IMT="PGA"/>
        <!-- limit states apply to the entire fragility model -->
        <limitStates>
            slight
            moderate
            extensive
            complete
        </limitStates>

        <!-- fragility function set, each with its own, distinct taxonomy -->
        <ffs noDamageLimit="0.05" type="lognormal">
            <taxonomy>RC/DMRF-D/LR</taxonomy>

            <!-- fragility function in continuous format, 1 per limit state -->
            <ffc ls="slight">
                <params mean="11.19" stddev="8.27" />
            </ffc>

            <ffc ls="moderate">
                <params mean="27.98" stddev="20.677" />
            </ffc>

            <ffc ls="extensive">
                <params mean="48.05" stddev="42.49" />
            </ffc>

            <ffc ls="complete">
                <params mean="108.9" stddev="123.7" />
            </ffc>
        </ffs>
 </fragilityModel>
</nrml>
''')

FMParser = parsers.FragilityModelParser


class FakeJob:
    class rc:
        inputs = mock.Mock()
    risk_calculation = rc


class ScenarioDamageCalculatorTestCase(unittest.TestCase):
    """
    Test the ``set_risk_models method`` of the calculator, i.e.
    the parsing of the inputs and the setting of the taxonomies,
    depending on the parameter ``taxonomies_from_fragility``.
    """

    def setUp(self):
        self.calculator = ScenarioDamageRiskCalculator(FakeJob())
        self.calculator.taxonomies = {'RC/DMRF-D/LR': 2, 'RC': 1}

    def test_taxonomies_from_fragility_true(self):
        self.calculator.job.rc.taxonomies_from_model = True
        with mock.patch('openquake.nrmllib.risk.parsers.FragilityModelParser',
                        lambda p: FMParser(FRAGILITY_FILE)):
            self.calculator.set_risk_models()
        self.assertEqual(sorted(self.calculator.taxonomies), ['RC/DMRF-D/LR'])

    def test_taxonomies_from_fragility_false(self):
        self.calculator.job.rc.taxonomies_from_model = False
        with mock.patch('openquake.nrmllib.risk.parsers.FragilityModelParser',
                        lambda p: FMParser(FRAGILITY_FILE)):
            with self.assertRaises(RuntimeError) as cm:
                self.calculator.set_risk_models()
        self.assertEqual(str(cm.exception),
                         'The following taxonomies are in the exposure '
                         "model but not in the fragility model: ['RC']")
