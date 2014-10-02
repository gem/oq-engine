import os
import unittest
from openquake.engine.db import models
from openquake.engine.tools import import_gmf_scenario
from openquake import nrmllib
from nose.tools import assert_equal
from io import StringIO


class ImportGMFScenarioTestCase(unittest.TestCase):

    # test that the example file gmf-scenario.xml can be imported
    def test_import_gmf_scenario(self):
        repodir = os.path.dirname(os.path.dirname(nrmllib.__path__[0]))
        fileobj = open(os.path.join(repodir, 'examples', 'gmf-scenario.xml'))
        out = import_gmf_scenario.import_gmf_scenario(fileobj)
        hc = out.oq_job.get_oqparam()
        n = models.GmfData.objects.filter(gmf__output=out).count()
        assert_equal(hc.calculation_mode, 'scenario')
        assert_equal(hc.number_of_ground_motion_fields, n)
        assert_equal(n, 12)  # 12 rows entered
        assert_equal(hc.description,
                     'Scenario importer, file gmf-scenario.xml')

        # now test that exporting the imported data gives back the
        # original data
        [gmfset] = list(out.gmf)
        self.assertEqual(str(gmfset), '''\
GMFsPerSES(investigation_time=0.000000, stochastic_event_set_id=1,
GMF(imt=PGA sa_period=None sa_damping=None rupture_id=scenario-0000000000
<X=  0.00000, Y=  0.00000, GMV=0.2000000>
<X=  0.00000, Y=  0.00000, GMV=0.3000000>
<X=  0.00000, Y=  1.00000, GMV=0.6000000>
<X=  0.00000, Y=  1.00000, GMV=0.7000000>
<X=  1.00000, Y=  0.00000, GMV=1.4000000>
<X=  1.00000, Y=  0.00000, GMV=1.5000000>)
GMF(imt=PGV sa_period=None sa_damping=None rupture_id=scenario-0000000000
<X=  0.00000, Y=  0.00000, GMV=0.2000000>
<X=  0.00000, Y=  1.00000, GMV=0.6000000>
<X=  1.00000, Y=  0.00000, GMV=1.4000000>)
GMF(imt=SA sa_period=0.025 sa_damping=5.0 rupture_id=scenario-0000000000
<X=  0.00000, Y=  0.00000, GMV=0.2000000>
<X=  0.00000, Y=  1.00000, GMV=0.6000000>
<X=  1.00000, Y=  0.00000, GMV=1.4000000>))''')

    # test that a tab-separated file can be imported
    def test_import_gmf_scenario_csv(self):
        test_data = StringIO(unicode('''\
SA	0.025	5.0	{0.2}	{1}	POINT(0.0 0.0)
SA	0.025	5.0	{1.4}	{1}	POINT(1.0 0.0)
SA	0.025	5.0	{0.6}	{1}	POINT(0.0 1.0)
PGA	\N	\N	{0.2,0.3}	{1,2}	POINT(0.0 0.0)
PGA	\N	\N	{1.4,1.5}	{1,2}	POINT(1.0 0.0)
PGA	\N	\N	{0.6,0.7}	{1,2}	POINT(0.0 1.0)
PGV	\N	\N	{0.2}	{1}	POINT(0.0 0.0)
PGV	\N	\N	{1.4}	{1}	POINT(1.0 0.0)
'''))
        test_data.name = 'test_data'
        out = import_gmf_scenario.import_gmf_scenario(test_data)
        n = models.GmfData.objects.filter(gmf__output=out).count()
        assert_equal(n, 8)  # 8 rows entered
