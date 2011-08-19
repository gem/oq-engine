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
from openquake.utils.tasks import check_job_status


@jtask
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


@jtask
def compute_ground_motion_fields(job_id, site_list, history, realization,
                                 seed):
    """ Generate ground motion fields """
    # TODO(JMC): Use a block_id instead of a site_list
    check_job_status(job_id)
    hazengine = job.Job.from_kvs(job_id)
    with mixins.Mixin(hazengine, hazjob.HazJobMixin):
        hazengine.compute_ground_motion_fields(site_list, history, realization,
                                               seed)


@jtask
def compute_hazard_curve(job_id, site_list, realization, callback=None):
    """ Generate hazard curve for a given site list. """
    check_job_status(job_id)
    hazengine = job.Job.from_kvs(job_id)
    with mixins.Mixin(hazengine, hazjob.HazJobMixin):
        keys = hazengine.compute_hazard_curve(site_list, realization)

        if callback:
            subtask(callback).delay(job_id, site_list)

        return keys


@jtask
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


@jtask
def compute_mean_curves(job_id, sites, realizations):
    """Compute the mean hazard curve for each site given."""

    check_job_status(job_id)
    HAZARD_LOG.info("Computing MEAN curves for %s sites" % len(sites))

    return classical_psha.compute_mean_hazard_curves(job_id, sites,
        realizations)


@jtask
def compute_quantile_curves(job_id, sites, realizations, quantiles):
    """Compute the quantile hazard curve for each site given."""

    check_job_status(job_id)
    HAZARD_LOG.info("Computing QUANTILE curves for %s sites" % len(sites))

    return classical_psha.compute_quantile_hazard_curves(job_id, sites,
        realizations, quantiles)
