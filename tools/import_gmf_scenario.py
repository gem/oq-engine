import os
import argparse
from cStringIO import StringIO
from openquake.nrmllib.hazard.parsers import GMFScenarioParser
from openquake.engine.db.models import Output, OqUser
from django.db import connection


def import_gmf_scenario(fname):
    """
    Parse the file with the GMF fields and import it into the table
    gmf_scenario. It also creates a new output record, unrelated to a job.
    Works both with XML files and tab-separated files with format
    (imt, gmvs, location).
    :returns: the generated :class:`openquake.engine.db.models.Output` object
    """
    curs = connection.cursor().cursor.cursor  # DB API cursor
    openquake = OqUser.objects.get(user_name='openquake')
    out = Output.objects.create(
        owner=openquake, display_name='Imported from %r' % fname,
        output_type='gmf_scenario')
    output_id = str(out.id)
    if fname.endswith('.xml'):
        f = StringIO()  # convert the XML into a tab-separated StringIO
        for imt, gmvs, loc in GMFScenarioParser(fname).parse():
            gmvs = '{%s}' % str(gmvs)[1:-1]
            print >> f, '\t'.join([output_id, imt, gmvs, loc])
        f.seek(0)  # rewind
    else:  # assume a tab-separated file
        f = open(fname)
    ## import the file-like object with a COPY FROM
    try:
        curs.copy_expert(
            'copy hzrdr.gmf_scenario (output_id, imt, gmvs, location) '
            'from stdin', f)
    except:
        curs.connection.rollback()
    else:
        curs.connection.commit()
    finally:
        f.close()
    return out


## the test is here waiting for a better location
## should this functionality enter into bin/openquake?
def test_import_gmf_scenario():
    from openquake import nrmllib
    from nose.tools import assert_equal
    repodir = os.path.dirname(os.path.dirname(nrmllib.__path__[0]))
    out = import_gmf_scenario(
        os.path.join(repodir, 'examples', 'gmf-scenario.xml'))
    curs = connection.cursor()
    curs.execute('select count(*) from hzrdr.gmf_scenario where output_id=%s',
                 (out.id,))
    assert_equal(curs.fetchone()[0], 9)  # 9 rows entered
    # just testing that the import does not break, to save us from
    # changes in the schema

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('fname')
    arg = p.parse_args()
    print 'Imported', import_gmf_scenario(arg.fname)
