import argparse
from cStringIO import StringIO

from django.db import connections

from openquake.nrmllib.hazard.parsers import HazardCurveParser
from openquake.engine.db.models import Output, OqUser, HazardCurve
from openquake.engine.engine import get_current_user


def import_hazard_curves(fileobj, user=None):
    """
    Parse the file with the hazard curves and import it into the tables
    hazard_curve and hazard_curve_data. It also creates a new output record,
    unrelated to a job.

    :returns:
        the generated :class:`openquake.engine.db.models.Output` object
    """
    fname = fileobj.name
    curs = connections['reslt_writer'].cursor().cursor.cursor  # DB API cursor
    owner = OqUser.objects.get(user_name=user) if user else get_current_user()
    out = Output.objects.create(
        owner=owner, display_name='Imported from %r' % fname,
        output_type='gmf_scenario')
    f = StringIO()
    # convert the XML into a tab-separated StringIO
    rows = list(HazardCurveParser(fileobj).parse())
    attr = rows[0]
    hazard_curve_id = str(HazardCurve.objects.create(output=out, **attr).id)
    for poes, loc in rows[1:]:
        poes = '{%s}' % str(poes)[1:-1]
        print >> f, '\t'.join([hazard_curve_id, poes, 'SRID=4326;' + loc])
    f.seek(0)  # rewind
    ## import the file-like object with a COPY FROM
    try:
        curs.copy_expert(
            'copy hzrdr.hazard_curve_data (hazard_curve_id, poes, location) '
            'from stdin', f)
    except:
        curs.connection.rollback()
        raise
    else:
        curs.connection.commit()
    finally:
        f.close()
    return out

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('fname')
    arg = p.parse_args()
    print 'Imported', import_hazard_curves(arg.fname)
