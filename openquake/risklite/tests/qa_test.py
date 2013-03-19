import os
import unittest
from openquake.concurrent.futures import ProcessPoolExecutor
from openquake.risklite.parallel import run_calc, Runner, BaseRunner

from nose.plugins.attrib import attr

DATADIR = os.path.join(os.path.dirname(__file__),  'data')


@attr('slow')
class EngineTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.seq_runner = BaseRunner()
        cls.par_runner = Runner(ProcessPoolExecutor())

    def test_scenario_damage_seq(self):
        run_calc(DATADIR, self.seq_runner, 'job_damage.ini')

    def test_scenario_damage_par(self):
        run_calc(DATADIR, self.par_runner, 'job_damage.ini')

    def test_scenario_seq(self):
        run_calc(DATADIR, self.seq_runner, 'job_risk.ini')

    def test_scenario_par(self):
        run_calc(DATADIR, self.par_runner, 'job_risk.ini')

    @classmethod
    def tearDownClass(cls):
        cls.par_runner.executor.shutdown()
