import os
from django.db import connection
from openquake.engine.tools import import_gmf_scenario
from openquake import nrmllib
from nose.tools import assert_equal


# this is just testing that the import does not break, to save us from
# changes in the schema
def test_import_gmf_scenario():
    repodir = os.path.dirname(os.path.dirname(nrmllib.__path__[0]))
    out = import_gmf_scenario.import_gmf_scenario(
        os.path.join(repodir, 'examples', 'gmf-scenario.xml'))
    curs = connection.cursor()
    curs.execute('select count(*) from hzrdr.gmf_scenario where output_id=%s',
                 (out.id,))
    assert_equal(curs.fetchone()[0], 9)  # 9 rows entered
