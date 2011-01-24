# vim: tabstop=4 shiftwidth=4 softtabstop=4

"""
The following tasks are defined in the hazard engine:
    * generate_erf
    * compute_hazard_curve
    * compute_mgm_intensity
"""

import json

from celery.decorators import task
from celery.task.sets import subtask

from openquake import job
from openquake import kvs

from openquake.hazard import job as hazjob
from openquake.job import mixins, Block
from openquake.kvs import tokens

from celery.decorators import task
from openquake.hazard import classical_psha
from openquake.job import mixins


@task
def generate_erf(job_id):
    """
    Stubbed ERF generator 

    Takes a job_id, returns a job_id. 

    Connects to the Java HazardEngien using hazardwrapper, waits for an ERF to
    be generated, and then writes it to memcached. 
    """

    # TODO(JM): implement real ERF computation

    erf_key = kvs.generate_product_key(job_id, tokens.ERF_KEY_TOKEN)
    kvs.get_client().set(erf_key, json.JSONEncoder().encode([job_id]))

    return job_id

@task
def compute_ground_motion_fields(job_id, site_list, gmf_id, seed):
    """ Generate ground motion fields """
    # TODO(JMC): Use a block_id instead of a site_list
    hazengine = job.Job.from_kvs(job_id)
    with mixins.Mixin(hazengine, hazjob.HazJobMixin, key="hazard"):
        #pylint: disable=E1101
        hazengine.compute_ground_motion_fields(site_list, gmf_id, seed)


def write_out_ses(job_file, stochastic_set_key):
    """ Write out Stochastic Event Set """
    hazengine = job.Job.from_file(job_file)
    with mixins.Mixin(hazengine, hazjob.HazJobMixin, key="hazard"):
        ses = kvs.get_value_json_decoded(stochastic_set_key)
        hazengine.write_gmf_files(ses) #pylint: disable=E1101

@task
def compute_hazard_curve(job_id, site_list, realization, callback=None):
    """ Generate hazard curve for a given site list. """
    hazengine = job.Job.from_kvs(job_id)
    with mixins.Mixin(hazengine, hazjob.HazJobMixin, key="hazard"):
        keys = hazengine.compute_hazard_curve(site_list, realization)

        if callback:
            subtask(callback).delay(job_id, site_list)

        return keys

@task
def compute_mgm_intensity(job_id, block_id, site_id):
    """
    Compute mean ground intensity for a specific site.
    """

    memcached_client = kvs.get_client(binary=False)

    mgm_key = kvs.generate_product_key(job_id, tokens.MGM_KEY_TOKEN,
        block_id, site_id)
    mgm = memcached_client.get(mgm_key)

    if not mgm:
        # TODO(jm): implement hazardwrapper and make this work.
        # TODO(chris): uncomment below when hazardwapper is done

        # Synchronous execution.
        #result = hazardwrapper.apply(args=[job_id, block_id, site_id])
        #mgm = memcached_client.get(mgm_key)
        pass

    return json.JSONDecoder().decode(mgm)


@task(ignore_result=True)
def compute_mean_curves(job_id, sites):
    """Compute the mean hazard curve for each site given."""

    # pylint: disable=E1101
    logger = compute_mean_curves.get_logger()

    logger.info("Computing MEAN curves for %s sites (job_id %s)"
            % (len(sites), job_id))

    classical_psha.compute_mean_hazard_curves(job_id, sites)
    subtask(compute_quantile_curves).delay(job_id, sites)


@task(ignore_result=True)
def compute_quantile_curves(job_id, sites):
    """Compute the quantile hazard curve for each site given."""

    # pylint: disable=E1101
    logger = compute_quantile_curves.get_logger()

    logger.info("Computing QUANTILE curves for %s sites (job_id %s)"
            % (len(sites), job_id))

    engine = job.Job.from_kvs(job_id)
    classical_psha.compute_quantile_hazard_curves(engine, sites)
    subtask(serialize_quantile_curves).delay(job_id, sites)


@task(is_eager=True, ignore_result=True)
def serialize_quantile_curves(job_id, sites):
    """Serialize quantile curves for the given sites."""
    print "Job ID is %s" % job_id
