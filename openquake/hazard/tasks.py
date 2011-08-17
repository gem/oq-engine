# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2011, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# only, as published by the Free Software Foundation.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License version 3 for more details
# (a copy is included in the LICENSE file that accompanied this code).
#
# You should have received a copy of the GNU Lesser General Public License
# version 3 along with OpenQuake.  If not, see
# <http://www.gnu.org/licenses/lgpl-3.0.txt> for a copy of the LGPLv3 License.


"""
The following tasks are defined in the hazard engine:
    * generate_erf
    * compute_hazard_curve
    * compute_mgm_intensity
"""

import json

from celery.task.sets import subtask

from openquake import job
from openquake import kvs

from openquake.hazard import job as hazjob
from openquake.hazard import classical_psha
from openquake.java import jtask
from openquake.job import mixins
from openquake.logs import HAZARD_LOG
from openquake.utils.tasks import oq_task


@jtask
@oq_task
def generate_erf(job_id, logger):
    """
    Stubbed ERF generator

    Takes a job_id, returns a job_id.

    Connects to the Java HazardEngine using hazardwrapper, waits for an ERF to
    be generated, and then writes it to KVS.
    """

    # TODO(JM): implement real ERF computation

    erf_key = kvs.generate_product_key(job_id, kvs.tokens.ERF_KEY_TOKEN)
    kvs.get_client().set(erf_key, json.JSONEncoder().encode([job_id]))

    return job_id


@jtask
@oq_task
def compute_ground_motion_fields(job_id, logger, site_list, gmf_id, seed):
    """ Generate ground motion fields """
    # TODO(JMC): Use a block_id instead of a site_list
    hazengine = job.Job.from_kvs(job_id)
    with mixins.Mixin(hazengine, hazjob.HazJobMixin):
        hazengine.compute_ground_motion_fields(site_list, gmf_id, seed)


@jtask
@oq_task
def compute_hazard_curve(job_id, logger, site_list,
                         realization, callback=None):
    """ Generate hazard curve for a given site list. """
    hazengine = job.Job.from_kvs(job_id)
    with mixins.Mixin(hazengine, hazjob.HazJobMixin):
        keys = hazengine.compute_hazard_curve(site_list, realization)

        if callback:
            subtask(callback).delay(job_id, site_list)

        return keys


@jtask
@oq_task
def compute_mgm_intensity(job_id, logger, block_id, site_id):
    """
    Compute mean ground intensity for a specific site.
    """

    kvs_client = kvs.get_client()

    mgm_key = kvs.generate_product_key(job_id, kvs.tokens.MGM_KEY_TOKEN,
        block_id, site_id)
    mgm = kvs_client.get(mgm_key)

    if not mgm:
        # TODO(jm): implement hazardwrapper and make this work.
        # TODO(chris): uncomment below when hazardwapper is done

        # Synchronous execution.
        #result = hazardwrapper.apply(args=[job_id, block_id, site_id])
        #mgm = kvs_client.get(mgm_key)
        pass

    return json.JSONDecoder().decode(mgm)


@jtask
@oq_task
def compute_mean_curves(job_id, logger, sites, realizations):
    """Compute the mean hazard curve for each site given."""

    logger.info("Computing MEAN curves for %s sites" % len(sites))

    return classical_psha.compute_mean_hazard_curves(job_id, sites,
        realizations)


@jtask
@oq_task
def compute_quantile_curves(job_id, logger, sites, realizations, quantiles):
    """Compute the quantile hazard curve for each site given."""

    logger.info("Computing QUANTILE curves for %s sites" % len(sites))

    return classical_psha.compute_quantile_hazard_curves(job_id, sites,
        realizations, quantiles)
