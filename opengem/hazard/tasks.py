# vim: tabstop=4 shiftwidth=4 softtabstop=4

"""
The following tasks are defined in the hazard engine:
    * generate_erf
    * compute_hazard_curve
    * compute_mgm_intensity
"""

import json

from opengem import job
from opengem.job import mixins
from opengem import hazard
from opengem import kvs

from celery.decorators import task


@task
def generate_erf(job_id):
    """
    Stubbed ERF generator 

    Takes a job_id, returns a job_id. 

    Connects to the Java HazardEngien using hazardwrapper, waits for an ERF to
    be generated, and then writes it to memcached. 
    """

    # TODO(JM): implement real ERF computation

    erf_key = kvs.generate_product_key(job_id, hazard.ERF_KEY_TOKEN)
    kvs.get_client().set(erf_key, json.JSONEncoder().encode([job_id]))

    return job_id

@task
def compute_ground_motion_fields(job_id, site_list, gmf_id, seed):
    # TODO(JMC): Use a block_id instead of a site_list
    hazengine = job.Job.from_kvs(job_id)
    with mixins.Mixin(hazengine, hazard.job.HazJobMixin, key="hazard"):
        hazengine.compute_ground_motion_fields(site_list, gmf_id, seed)

@task
def compute_hazard_curve(job_id, block_id, site_id=None):
    """
    Stubbed Compute Hazard Curve

    This should connect to the Java HazardEngine using hazard wrapper,
    wait for the hazard curve to be computed, and then write it to 
    memcached.
    """

    def _compute_hazard_curve(job_id, block_id, site_id):
        """
        Inner class to dry things up.
        """
        memcache_client = kvs.get_client(binary=False)

        chf_key = kvs.generate_product_key(job_id, 
            hazard.HAZARD_CURVE_KEY_TOKEN, block_id, site_id)

        chf = memcache_client.get(chf_key)

        if not chf:
            # TODO(jm): implement hazardwrapper and make this work
            # TODO(chris): uncomment below when hazardwrapper is done.

            # Synchronous execution.
            #result = hazardwrapper.apply(args=[job_if, block_id, site_id])
            #chf = memcache_client.get(chf_key)
            pass
        return chf


    memcache_client = kvs.get_client(binary=False)

    if site_id is not None:
        # This has a pretty stupid assumption as to how sites will be written 
        # to memcached. 
        # TODO(chris): Fix this to use kvs.generate_sites_key, or just use
        #              the site_id. 
        site_key = kvs.generate_product_key(job_id, kvs.SITES_KEY_TOKEN, 
            block_id, site_id)

        site = memcache_client.get(site_key)
        sites = [site]
    else:
        # We want all sites for this block.
        sites = kvs.get_sites_from_memcache(job_id, block_id)

    if sites is not None:
        return [_compute_hazard_curve(job_id, block_id, site) for site in sites]

@task
def compute_mgm_intensity(job_id, block_id, site_id):
    """
    Compute mean ground intensity for a specific site.
    """

    memcached_client = kvs.get_client(binary=False)

    mgm_key = kvs.generate_product_key(job_id, hazard.MGM_KEY_TOKEN, block_id, 
        site_id)
    mgm = memcached_client.get(mgm_key)

    if not mgm:
        # TODO(jm): implement hazardwrapper and make this work.
        # TODO(chris): uncomment below when hazardwapper is done

        # Synchronous execution.
        #result = hazardwrapper.apply(args=[job_id, block_id, site_id])
        #mgm = memcached_client.get(mgm_key)
        pass

    return json.JSONDecoder().decode(mgm)
