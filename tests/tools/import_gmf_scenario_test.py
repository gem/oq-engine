import os
from openquake.engine.db import models
from openquake.engine.tools import import_gmf_scenario
from openquake import nrmllib
from nose.tools import assert_equal
from io import StringIO


# this is just testing that the import does not break, to save us from
# changes in the schema
def test_import_gmf_scenario():
    repodir = os.path.dirname(os.path.dirname(nrmllib.__path__[0]))
    fileobj = open(os.path.join(repodir, 'examples', 'gmf-scenario.xml'))
    out = import_gmf_scenario.import_gmf_scenario(fileobj, 'openquake')
    n = models.GmfAgg.objects.filter(gmf_collection__output=out).count()
    assert_equal(n, 9)  # 9 rows entered


# test that a tab-separated file can be imported
def test_import_gmf_scenario_csv():
    test_data = StringIO(unicode('''\
SA	0.025	\N	{0.2}	POINT(0.0 0.0)
SA	0.025	\N	{1.4}	POINT(1.0 0.0)
SA	0.025	\N	{0.6}	POINT(0.0 1.0)
PGA	\N	\N	{0.2,0.3}	POINT(0.0 0.0)
PGA	\N	\N	{1.4,1.5}	POINT(1.0 0.0)
PGA	\N	\N	{0.6,0.7}	POINT(0.0 1.0)
PGV	\N	\N	{0.2}	POINT(0.0 0.0)
PGV	\N	\N	{1.4}	POINT(1.0 0.0)
'''))
    test_data.name = 'test_data'
    out = import_gmf_scenario.import_gmf_scenario(test_data, 'openquake')
    n = models.GmfAgg.objects.filter(gmf_collection__output=out).count()
    assert_equal(n, 8)  # 8 rows entered
