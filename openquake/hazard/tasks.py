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

from celery.task.sets import subtask

from openquake import job
from openquake import kvs

from openquake.hazard import job as hazjob
from openquake.hazard import classical_psha
from openquake.hazard import disaggregation as disagg
from openquake.java import jtask as task
from openquake.job import mixins
from openquake.logs import HAZARD_LOG
from openquake.utils.tasks import check_job_status


@task
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
def compute_ground_motion_fields(job_id, site_list, history, realization,
                                 seed):
    """ Generate ground motion fields """
    # TODO(JMC): Use a block_id instead of a site_list
    check_job_status(job_id)
    hazengine = job.Job.from_kvs(job_id)
    with mixins.Mixin(hazengine, hazjob.HazJobMixin):
        hazengine.compute_ground_motion_fields(site_list, history, realization,
                                               seed)


@task
def compute_hazard_curve(job_id, site_list, realization, callback=None):
    """ Generate hazard curve for a given site list. """
    check_job_status(job_id)
    hazengine = job.Job.from_kvs(job_id)
    with mixins.Mixin(hazengine, hazjob.HazJobMixin):
        keys = hazengine.compute_hazard_curve(site_list, realization)

        if callback:
            subtask(callback).delay(job_id, site_list)

        return keys


@task
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


@task
def compute_mean_curves(job_id, sites, realizations):
    """Compute the mean hazard curve for each site given."""

    check_job_status(job_id)
    HAZARD_LOG.info("Computing MEAN curves for %s sites (job_id %s)"
            % (len(sites), job_id))

    return classical_psha.compute_mean_hazard_curves(job_id, sites,
        realizations)


@task
def compute_quantile_curves(job_id, sites, realizations, quantiles):
    """Compute the quantile hazard curve for each site given."""

    check_job_status(job_id)
    HAZARD_LOG.info("Computing QUANTILE curves for %s sites (job_id %s)"
            % (len(sites), job_id))

    return classical_psha.compute_quantile_hazard_curves(job_id, sites,
        realizations, quantiles)


@task
def compute_disagg_matrix(job_id, site, realization, poe, result_dir):
    """ Compute a complete 5D Disaggregation matrix. This task leans heavily
    on the DisaggregationCalculator (in the OpenQuake Java lib) to handle this
    computation.

    :param job_id: id of the job record in the KVS
    :type job_id: `str`
    :param site: a single site of interest
    :type site: :class:`openquake.shapes.Site` instance`
    :param int realization: logic tree sample iteration number
    :param poe: Probability of Exceedence
    :type poe: `float`
    :param result_dir: location for the Java code to write the matrix in an
        HDF5 file (in a distributed environment, this should be the path of a
        mounted NFS)

    :returns: 2-tuple of (ground_motion_value, path_to_h5_matrix_file)
    """
    # check and see if the job is still valid (i.e., not complete or failed)
    check_job_status(job_id)

    log_msg = (
        "Computing full disaggregation matrix for job_id=%s, site=%s, "
        "realization=%s, PoE=%s. Matrix results will be serialized to `%s`.")
    log_msg %= (job_id, site, realization, poe, result_dir)
    HAZARD_LOG.info(log_msg)

    # NOTE(LB): We don't need to pass the realization, but we will need to
    # keep track of it somehow when we reduce the final disagg results.
    # When we write the disagg mixin, this should become more clear.
    return disagg.compute_disagg_matrix(job_id, site, poe, result_dir)
