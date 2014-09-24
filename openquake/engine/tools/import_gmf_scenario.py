import os
import time
import argparse
from openquake.nrmllib.hazard.parsers import GMFScenarioParser
from openquake.hazardlib.imt import from_string
from openquake.engine.db import models
from openquake.engine import writer, engine


def create_ses_gmf(job, fname):
    """
    Create SES and GMF output records.

    :param job: an :class:`openquake.engine.db.models.OqJob` instance
    :param fname: name of the file containing the GMF data
    """
    output = models.Output.objects.create(
        oq_job=job,
        display_name='SES Collection',
        output_type='ses')
    ses_coll = models.SESCollection.objects.create(
        output=output, lt_model=None, ordinal=0)

    # create gmf output
    output = models.Output.objects.create(
        oq_job=job,
        display_name="Imported from %r'" % fname,
        output_type="gmf_scenario")
    gmf = models.Gmf.objects.create(output=output)
    return ses_coll, gmf


def import_rows(job, gmf_coll, rows):
    """
    Import a list of records into the gmf_data and hazard_site tables.

    :param job: :class:`openquake.engine.db.models.OqJob` instance
    :param gmf_coll: :class:`openquake.engine.db.models.Gmf` instance
    :param rows: a list of records (imt_type, sa_period, sa_damping, gmvs, wkt)
    """
    gmfs = []
    site_id = {}  # dictionary wkt -> site id
    for imt_type, sa_period, sa_damping, gmvs, wkt in rows:
        if wkt not in site_id:  # create a new site
            site_id[wkt] = models.HazardSite.objects.create(
                hazard_calculation=job, location=wkt).id
        gmfs.append(
            models.GmfData(
                imt=imt_type, sa_period=sa_period, sa_damping=sa_damping,
                gmvs=gmvs, rupture_ids=range(len(gmvs)),
                site_id=site_id[wkt], gmf=gmf_coll, task_no=0))
    del site_id
    writer.CacheInserter.saveall(gmfs)


def import_gmf_scenario(fileobj):
    """
    Parse the file with the GMF fields and import it into the table
    gmf_scenario. It also creates a new output record, unrelated to a job.
    Works both with XML files and tab-separated files with format
    (imt, gmvs, location).
    :returns: the generated :class:`openquake.engine.db.models.Output` object
    and the generated :class:`openquake.engine.db.models.OqJob`
    object.
    """
    t0 = time.time()
    fname = fileobj.name

    job = engine.prepare_job()

    # XXX: probably the maximum_distance should be entered by the user

    ses_coll, gmf_coll = create_ses_gmf(job, fname)

    rows = []
    imts = set()
    if fname.endswith('.xml'):
        # convert the XML into a tab-separated StringIO
        for imt, gmvs, loc in GMFScenarioParser(fileobj).parse():
            imts.add(imt)
            imt_type, sa_period, sa_damping = from_string(imt)
            sa_period = '\N' if sa_period is None else str(sa_period)
            sa_damping = '\N' if sa_damping is None else str(sa_damping)
            gmvs = '{%s}' % str(gmvs)[1:-1]
            rows.append([imt_type, sa_period, sa_damping, gmvs, loc])
    else:  # assume a tab-separated file
        for line in fileobj:
            rows.append(line.split('\t'))
    import_rows(job, gmf_coll, rows)
    job.save_params(
        dict(
            base_path=os.path.dirname(fname),
            description='Scenario importer, file %s' % os.path.basename(fname),
            calculation_mode='scenario',
            maximum_distance=100,
            intensity_measure_types=list(imts),
            inputs={},
            number_of_ground_motion_fields=len(rows)
            ))

    job.duration = time.time() - t0
    job.status = 'complete'
    job.save()
    return gmf_coll.output

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('fname')
    arg = p.parse_args()
    print 'Imported', import_gmf_scenario(arg.fname)
