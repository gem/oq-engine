import os
import time
import argparse
import collections

from openquake.hazardlib.imt import from_string
from openquake.commonlib.node import LiteralNode, read_nodes
from openquake.commonlib import valid

from openquake.engine.db import models
from openquake.engine import writer, engine
from openquake.engine.calculators.hazard.scenario.core \
    import create_db_ruptures

from openquake.hazardlib.geo.point import Point
from openquake.hazardlib.geo.surface.planar import PlanarSurface
from openquake.hazardlib.source.rupture import ParametricProbabilisticRupture


class DuplicatedTag(Exception):
    """
    Raised when reading a GMF XML file containing a duplicated ruptureId
    attribute.
    """


class GmfNode(LiteralNode):
    """
    Class used to convert nodes such as

    <gmf IMT="PGA" ruptureId="scenario-0000000001" >
       <node gmv="0.365662734506" lat="0.0" lon="0.0"/>
       <node gmv="0.256181251586" lat="0.1" lon="0.0"/>
       <node gmv="0.110685275111" lat="0.2" lon="0.0"/>
    </gmf>

    into LiteralNode objects.
    """
    validators = valid.parameters(
        gmv=valid.positivefloat,
        lon=valid.longitude,
        lat=valid.latitude)


def fake_rupture():
    """
    Generate a fake rupture from which a models.ProbabilisticRupture
    record is generated. This is needed to satisfy the foreign key
    constraints at the database level.
    """
    rupture = ParametricProbabilisticRupture(
        mag=1., rake=0,
        tectonic_region_type="NA",
        hypocenter=Point(0, 0, 0.1),
        surface=PlanarSurface(
            10, 11, 12, Point(0, 0, 1), Point(1, 0, 1),
            Point(1, 0, 2), Point(0, 0, 2)),
        occurrence_rate=1.0,
        source_typology='rupture',
        temporal_occurrence_model=None)
    return rupture


def read_data(fileobj):
    """
    Convert a file into a generator over rows.

    :param fileobj: the XML files containing the GMFs
    :returns: (imts, rupture_tags, rows)
    """
    tags = collections.defaultdict(set)
    rows = []
    for gmf in read_nodes(
            fileobj, lambda n: n.tag.endswith('gmf'), GmfNode):
        tag = gmf['ruptureId']
        imt = gmf['IMT']
        if imt == 'SA':
            imt = 'SA(%s)' % gmf['saPeriod']
        data = []
        for node in gmf:
            data.append(('POINT(%(lon)s %(lat)s)' % node, node['gmv']))
        if tag in tags[imt]:
            raise DuplicatedTag(tag)
        tags[imt].add(tag)
        rows.append((imt, tag, data))
    # check consistency of the tags
    expected_tags = tags[imt]
    for tagvalues in tags.values():
        assert tagvalues == expected_tags, (expected_tags, tagvalues)
    return set(tags), sorted(expected_tags), rows


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
    ses_coll = models.SESCollection.create(output=output)

    # create gmf output
    output = models.Output.objects.create(
        oq_job=job,
        display_name="Imported from %r'" % fname,
        output_type="gmf_scenario")
    gmf = models.Gmf.objects.create(output=output)
    return ses_coll, gmf


def import_rows(job, ses_coll, gmf_coll, sorted_tags, rows):
    """
    Import a list of records into the gmf_data and hazard_site tables.

    :param job:
        :class:`openquake.engine.db.models.OqJob` instance
    :param gmf_coll:
        :class:`openquake.engine.db.models.Gmf` instance
    :param rows:
        a list of records (imt_type, sa_period, sa_damping, gmvs, wkt)
    """
    gmfs = []  # list of GmfData instance
    site_id = {}  # dictionary wkt -> site id
    rupture = fake_rupture()
    prob_rup_id, ses_rup_ids, seeds = create_db_ruptures(
        rupture, ses_coll, sorted_tags, seed=42)
    tag2id = dict(zip(sorted_tags, ses_rup_ids))

    for imt_str, tag, data in rows:
        imt = from_string(imt_str)
        rup_id = tag2id[tag]
        for wkt, gmv in data:
            if wkt not in site_id:  # create a new site
                site_id[wkt] = models.HazardSite.objects.create(
                    hazard_calculation=job, location=wkt).id
            gmfs.append(
                models.GmfData(
                    imt=imt[0], sa_period=imt[1], sa_damping=imt[2],
                    gmvs=[gmv], rupture_ids=[rup_id],
                    site_id=site_id[wkt], gmf=gmf_coll, task_no=0))
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

    job = engine.create_job()

    ses_coll, gmf_coll = create_ses_gmf(job, fname)
    imts, tags, rows = read_data(fileobj)
    import_rows(job, ses_coll, gmf_coll, tags, rows)
    job.save_params(
        dict(
            base_path=os.path.dirname(fname),
            description='Scenario importer, file %s' % os.path.basename(fname),
            calculation_mode='scenario',
            intensity_measure_types_and_levels=dict.fromkeys(imts),
            inputs={},
            number_of_ground_motion_fields=len(rows) // len(imts)
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
