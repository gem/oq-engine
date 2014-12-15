import os
import argparse
from cStringIO import StringIO

from django.db import connections

from openquake.commonlib import nrml
from openquake.engine.db import models
from openquake.engine import engine


def import_hazard_curves(fileobj):
    """
    Parse the file with the hazard curves and import it into the tables
    hazard_curve and hazard_curve_data. It also creates a new output record,
    unrelated to a job.

    :param fileobj:
        a file-like object associated to an XML file
    :returns:
        the generated :class:`openquake.engine.db.models.Output` object
        and the generated :class:`openquake.engine.db.models.OqJob` object.
    """
    fname = fileobj.name
    hazcurves = nrml.read(fileobj).hazardCurves
    imt = imt_str = hazcurves['IMT']
    if imt == 'SA':
        imt_str += '(%s)' % hazcurves['saPeriod']
    imls = ~hazcurves.IMLs
    hc_nodes = hazcurves[1:]

    curs = connections['job_init'].cursor().cursor.cursor  # DB API cursor
    job = engine.create_job()
    job.save_params(dict(
        base_path=os.path.dirname(fname),
        intensity_measure_types_and_levels={imt_str: imls},
        description='HazardCurve importer, file %s' % os.path.basename(fname),
        calculation_mode='classical'))

    out = models.Output.objects.create(
        display_name='Imported from %r' % fname, output_type='hazard_curve',
        oq_job=job)

    haz_curve = models.HazardCurve.objects.create(
        investigation_time=hazcurves['investigationTime'],
        imt=imt,
        imls=imls,
        quantile=hazcurves.attrib.get('quantileValue'),
        statistics=hazcurves.attrib.get('statistics'),
        sa_damping=hazcurves.attrib.get('saDamping'),
        sa_period=hazcurves.attrib.get('saPeriod'),
        output=out)
    hazard_curve_id = str(haz_curve.id)

    # convert the XML into a tab-separated StringIO
    f = StringIO()
    for node in hc_nodes:
        x, y = ~node.Point.pos
        poes = ~node.poEs
        poes = '{%s}' % str(poes)[1:-1]
        print >> f, '\t'.join([hazard_curve_id, poes,
                               'SRID=4326;POINT(%s %s)' % (x, y)])
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
    job.save()
    return out

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('fname')
    arg = p.parse_args()
    print 'Imported', import_hazard_curves(arg.fname)
