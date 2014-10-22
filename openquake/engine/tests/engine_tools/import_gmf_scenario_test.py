import os
import unittest
from openquake.engine.db import models
from openquake.engine.tools import import_gmf_scenario
from nose.tools import assert_equal

THISDIR = os.path.dirname(__file__)


class ImportGMFScenarioTestCase(unittest.TestCase):

    def test_import_gmf_scenario(self):
        # gmfdata.xml is a file containing 2 IMTs, 5 ruptures and 3 sites
        fileobj = open(os.path.join(THISDIR, 'gmfdata.xml'))
        out = import_gmf_scenario.import_gmf_scenario(fileobj)
        hc = out.oq_job.get_oqparam()
        imts = sorted(hc.intensity_measure_types_and_levels)
        self.assertEqual(imts, ['PGA', 'PGV'])
        n = models.GmfData.objects.filter(gmf__output=out).count()
        assert_equal(hc.calculation_mode, 'scenario')
        assert_equal(hc.number_of_ground_motion_fields, 5)
        assert_equal(n, 30)  # 30 rows entered, 2 x 5 x 3
        assert_equal(hc.description,
                     'Scenario importer, file gmfdata.xml')

        # now test that exporting the imported data gives back the
        # original data
        [gmfset] = list(out.gmf)
        self.assertEqual(str(gmfset), '''\
GMFsPerSES(investigation_time=0.000000, stochastic_event_set_id=1,
GMF(imt=PGA sa_period=None sa_damping=None rupture_id=scenario-0000000000
<X=  0.00000, Y=  0.00000, GMV=0.6824957>
<X=  0.00000, Y=  0.10000, GMV=0.1270898>
<X=  0.00000, Y=  0.20000, GMV=0.1603097>)
GMF(imt=PGA sa_period=None sa_damping=None rupture_id=scenario-0000000001
<X=  0.00000, Y=  0.00000, GMV=0.3656627>
<X=  0.00000, Y=  0.10000, GMV=0.2561813>
<X=  0.00000, Y=  0.20000, GMV=0.1106853>)
GMF(imt=PGA sa_period=None sa_damping=None rupture_id=scenario-0000000002
<X=  0.00000, Y=  0.00000, GMV=0.8700834>
<X=  0.00000, Y=  0.10000, GMV=0.2106384>
<X=  0.00000, Y=  0.20000, GMV=0.2232175>)
GMF(imt=PGA sa_period=None sa_damping=None rupture_id=scenario-0000000003
<X=  0.00000, Y=  0.00000, GMV=0.3279292>
<X=  0.00000, Y=  0.10000, GMV=0.2357552>
<X=  0.00000, Y=  0.20000, GMV=0.1781143>)
GMF(imt=PGA sa_period=None sa_damping=None rupture_id=scenario-0000000004
<X=  0.00000, Y=  0.00000, GMV=0.6968686>
<X=  0.00000, Y=  0.10000, GMV=0.2581405>
<X=  0.00000, Y=  0.20000, GMV=0.1351649>)
GMF(imt=PGV sa_period=None sa_damping=None rupture_id=scenario-0000000000
<X=  0.00000, Y=  0.00000, GMV=0.6824957>
<X=  0.00000, Y=  0.10000, GMV=0.1270898>
<X=  0.00000, Y=  0.20000, GMV=0.1603097>)
GMF(imt=PGV sa_period=None sa_damping=None rupture_id=scenario-0000000001
<X=  0.00000, Y=  0.00000, GMV=0.3656627>
<X=  0.00000, Y=  0.10000, GMV=0.2561813>
<X=  0.00000, Y=  0.20000, GMV=0.1106853>)
GMF(imt=PGV sa_period=None sa_damping=None rupture_id=scenario-0000000002
<X=  0.00000, Y=  0.00000, GMV=0.8700834>
<X=  0.00000, Y=  0.10000, GMV=0.2106384>
<X=  0.00000, Y=  0.20000, GMV=0.2232175>)
GMF(imt=PGV sa_period=None sa_damping=None rupture_id=scenario-0000000003
<X=  0.00000, Y=  0.00000, GMV=0.3279292>
<X=  0.00000, Y=  0.10000, GMV=0.2357552>
<X=  0.00000, Y=  0.20000, GMV=0.1781143>)
GMF(imt=PGV sa_period=None sa_damping=None rupture_id=scenario-0000000004
<X=  0.00000, Y=  0.00000, GMV=0.6968686>
<X=  0.00000, Y=  0.10000, GMV=0.2581405>
<X=  0.00000, Y=  0.20000, GMV=0.1351649>))''')

    def test_duplicated_rupture_tag(self):
        fileobj = open(os.path.join(THISDIR, 'gmfdata-wrong.xml'))
        with self.assertRaises(import_gmf_scenario.DuplicatedTag) as ctx:
            import_gmf_scenario.import_gmf_scenario(fileobj)
        self.assertEqual(str(ctx.exception), 'scenario-0000000002')
