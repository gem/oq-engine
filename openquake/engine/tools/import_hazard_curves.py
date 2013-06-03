import os
import argparse
from cStringIO import StringIO

from django.db import connections

from openquake.nrmllib.hazard.parsers import HazardCurveParser
from openquake.engine.db import models
from openquake.engine.engine import get_current_user


def import_hazard_curves(fileobj, user=None):
    """
    Parse the file with the hazard curves and import it into the tables
    hazard_curve and hazard_curve_data. It also creates a new output record,
    unrelated to a job.

    :param fileobj:
        a file-like object associated to an XML file
    :returns:
        the generated :class:`openquake.engine.db.models.Output` object
        and the generated :class:`openquake.engine.db.models.HazardCalculation`
        object.
    """
    fname = fileobj.name
    curs = connections['reslt_writer'].cursor().cursor.cursor  # DB API cursor
    owner = models.OqUser.objects.get(user_name=user) \
        if user else get_current_user()

    hc = models.HazardCalculation.objects.create(
        owner=owner,
        base_path=os.path.dirname(fname),
        description='HazardCurve importer, file %s' % os.path.basename(fname),
        calculation_mode='classical', maximum_distance=100)
    # XXX: what about the maximum_distance?

    out = models.Output.objects.create(
        owner=owner, display_name='Imported from %r' % fname,
        output_type='hazard_curve')

    f = StringIO()
    # convert the XML into a tab-separated StringIO
    hazcurve = HazardCurveParser(fileobj).parse()
    haz_curve = models.HazardCurve.objects.create(
        investigation_time=hazcurve.investigation_time,
        imt=hazcurve.imt,
        imls=hazcurve.imls,
        quantile=hazcurve.quantile,
        statistics=hazcurve.statistics,
        sa_damping=hazcurve.sa_damping,
        sa_period=hazcurve.sa_period,
        output=out)
    hazard_curve_id = str(haz_curve.id)
    for poes, loc in hazcurve:
        poes = '{%s}' % str(poes)[1:-1]
        print >> f, '\t'.join([hazard_curve_id, poes, 'SRID=4326;' + loc])
    f.reset()
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
    return out, hc

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('fname')
    arg = p.parse_args()
    print 'Imported', import_hazard_curves(arg.fname)
