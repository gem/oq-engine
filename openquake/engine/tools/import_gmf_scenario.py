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

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('fname')
    arg = p.parse_args()
    print 'Imported', import_gmf_scenario(arg.fname)
