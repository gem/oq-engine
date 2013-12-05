import os
import argparse
from openquake.nrmllib.hazard.parsers import GMFScenarioParser
from openquake.hazardlib.imt import from_string
from openquake.engine.db import models
from openquake.engine import writer


def import_rows(hc, gmf_coll, rows):
    """
    Import a list of records into the gmf_data and hazard_site tables.

    :param hc: :class:`openquake.engine.db.models.HazardCalculation` instance
    :param gmf_coll: :class:`openquake.engine.db.models.Gmf` instance
    :param rows: a list of records (imt_type, sa_period, sa_damping, gmvs, wkt)
    """
    gmfs = []
    site_id = {}  # dictionary wkt -> site id
    for imt_type, sa_period, sa_damping, gmvs, wkt in rows:
        if wkt not in site_id:  # create a new site
            site_id[wkt] = models.HazardSite.objects.create(
                hazard_calculation=hc, location=wkt).id
        gmfs.append(
            models.GmfData(
                imt=imt_type, sa_period=sa_period, sa_damping=sa_damping,
                gmvs=gmvs, site_id=site_id[wkt], gmf=gmf_coll))
    del site_id
    writer.CacheInserter.saveall(gmfs)


def import_gmf_scenario(fileobj):
    """
    Parse the file with the GMF fields and import it into the table
    gmf_scenario. It also creates a new output record, unrelated to a job.
    Works both with XML files and tab-separated files with format
    (imt, gmvs, location).
    :returns: the generated :class:`openquake.engine.db.models.Output` object
    and the generated :class:`openquake.engine.db.models.HazardCalculation`
    object.
    """
    fname = fileobj.name

    hc = models.HazardCalculation.objects.create(
        base_path=os.path.dirname(fname),
        description='Scenario importer, file %s' % os.path.basename(fname),
        calculation_mode='scenario', maximum_distance=100)
    # XXX: probably the maximum_distance should be entered by the user

    out = models.Output.objects.create(
        display_name='Imported from %r' % fname, output_type='gmf_scenario')

    gmf_coll = models.Gmf.objects.create(output=out)

    rows = []
    if fname.endswith('.xml'):
        # convert the XML into a tab-separated StringIO
        for imt, gmvs, loc in GMFScenarioParser(fileobj).parse():
            imt_type, sa_period, sa_damping = from_string(imt)
            sa_period = '\N' if sa_period is None else str(sa_period)
            sa_damping = '\N' if sa_damping is None else str(sa_damping)
            gmvs = '{%s}' % str(gmvs)[1:-1]
            rows.append([imt_type, sa_period, sa_damping, gmvs, loc])
    else:  # assume a tab-separated file
        for line in fileobj:
            rows.append(line.split('\t'))
    import_rows(hc, gmf_coll, rows)
    return out, hc

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('fname')
    arg = p.parse_args()
    print 'Imported', import_gmf_scenario(arg.fname)
