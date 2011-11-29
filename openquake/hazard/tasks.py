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
    * compute_disagg_matrix
"""

import json

from celery.task import task
from celery.task.sets import subtask

from openquake import job
from openquake import kvs

from openquake.hazard import job as hazjob
from openquake.hazard import classical_psha
from openquake import java
from openquake.job import mixins
from openquake.logs import HAZARD_LOG
from openquake.utils import stats
from openquake.utils.tasks import check_job_status


@task
@java.unpack_exception
def generate_erf(job_id):
    """
    Stubbed ERF generator

    Takes a job_id, returns a job_id.

    Connects to the Java HazardEngine using hazardwrapper, waits for an ERF to
    be generated, and then writes it to KVS.
    """

    # TODO(JM): implement real ERF computation

    check_job_status(job_id)
    kvs.get_client().set(kvs.tokens.erf_key(job_id),
                         json.JSONEncoder().encode([job_id]))

    return job_id


@task
@java.unpack_exception
@stats.progress_indicator
def compute_ground_motion_fields(job_id, sites, history, realization,
                                 seed):
    """ Generate ground motion fields """
    # TODO(JMC): Use a block_id instead of a sites
    check_job_status(job_id)
    hazengine = job.Job.from_kvs(job_id)
    with mixins.Mixin(hazengine, hazjob.HazJobMixin):
        hazengine.compute_ground_motion_fields(sites, history, realization,
                                               seed)


@task(ignore_result=True)
@java.unpack_exception
@stats.progress_indicator
def compute_hazard_curve(job_id, sites, realization):
    """ Generate hazard curve for a given site list. """
    check_job_status(job_id)
    hazengine = job.Job.from_kvs(job_id)
    with mixins.Mixin(hazengine, hazjob.HazJobMixin):
        keys = hazengine.compute_hazard_curve(sites, realization)
        return keys


@task
@java.unpack_exception
@stats.progress_indicator
def compute_mgm_intensity(job_id, block_id, site_id):
    """
    Compute mean ground intensity for a specific site.
    """

    check_job_status(job_id)
    kvs_client = kvs.get_client()

    mgm_key = kvs.tokens.mgm_key(job_id, block_id, site_id)
    mgm = kvs_client.get(mgm_key)

    if not mgm:
        # TODO(jm): implement hazardwrapper and make this work.
        # TODO(chris): uncomment below when hazardwapper is done

        # Synchronous execution.
        #result = hazardwrapper.apply(args=[job_id, block_id, site_id])
        #mgm = kvs_client.get(mgm_key)
        pass

    return json.JSONDecoder().decode(mgm)


@task(ignore_result=True)
@java.unpack_exception
@stats.progress_indicator
def compute_mean_curves(job_id, sites, realizations):
    """Compute the mean hazard curve for each site given."""

    check_job_status(job_id)
    HAZARD_LOG.info("Computing MEAN curves for %s sites (job_id %s)"
            % (len(sites), job_id))

    return classical_psha.compute_mean_hazard_curves(job_id, sites,
        realizations)


@task(ignore_result=True)
@java.unpack_exception
@stats.progress_indicator
def compute_quantile_curves(job_id, sites, realizations, quantiles):
    """Compute the quantile hazard curve for each site given."""

    check_job_status(job_id)
    HAZARD_LOG.info("Computing QUANTILE curves for %s sites (job_id %s)"
            % (len(sites), job_id))

    return classical_psha.compute_quantile_hazard_curves(job_id, sites,
        realizations, quantiles)
