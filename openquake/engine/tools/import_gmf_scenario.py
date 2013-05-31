import argparse
from cStringIO import StringIO
from openquake.nrmllib.hazard.parsers import GMFScenarioParser
from openquake.engine.db import models
from openquake.engine.engine import get_current_user
from django.db import connections


def import_gmf_scenario(fileobj, user=None):
    """
    Parse the file with the GMF fields and import it into the table
    gmf_scenario. It also creates a new output record, unrelated to a job.
    Works both with XML files and tab-separated files with format
    (imt, gmvs, location).
    :returns: the generated :class:`openquake.engine.db.models.Output` object
    """
    fname = fileobj.name
    curs = connections['reslt_writer'].cursor().cursor.cursor  # DB API cursor
    owner = models.OqUser.objects.get(user_name=user) \
        if user else get_current_user()
    out = models.Output.objects.create(
        owner=owner, display_name='Imported from %r' % fname,
        output_type='gmf_scenario')
    coll_id = str(models.GmfCollection.objects.create(output=out).id)
    f = StringIO()
    if fname.endswith('.xml'):
        # convert the XML into a tab-separated StringIO
        for imt, gmvs, loc in GMFScenarioParser(fileobj).parse():
            imt_type, sa_period, sa_damping = models.parse_imt(imt)
            sa_period = '\N' if sa_period is None else str(sa_period)
            sa_damping = '\N' if sa_damping is None else str(sa_damping)
            gmvs = '{%s}' % str(gmvs)[1:-1]
            print >> f, '\t'.join([coll_id, imt_type, sa_period, sa_damping,
                                   gmvs, loc])
    else:  # assume a tab-separated file
        for line in fileobj:
            f.write('\t'.join([coll_id, line]))
    f.seek(0)  # rewind
    ## import the file-like object with a COPY FROM
    try:
        curs.copy_expert(
            'copy hzrdr.gmf_agg (gmf_collection_id, '
            'imt, sa_period, sa_damping, gmvs, location) '
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
    print 'Imported', import_gmf_scenario(arg.fname)
