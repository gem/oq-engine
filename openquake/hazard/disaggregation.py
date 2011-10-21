# -*- coding: utf-8 -*-
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


from openquake import java
from openquake import job

from openquake.job import config as job_cfg
from openquake.job import config_text_to_list


def compute_disagg_matrix(job_id, site, realization, poe):
    """ Compute a complete 5D Disaggregation matrix. This task leans heavily
    on the DisaggregationCalculator (in the OpenQuake Java lib) to handle this
    computation.

    :param job_id: id of the job record in the KVS
    :type job_id: `str`
    :param site: a single site of interest
    :type site: :class:`openquake.shapes.Site` instance`
    :param realization: the logic tree sample iteration number
    :type realization: `int`
    :param poe: Probability of Exceedence
    :type poe: `float`

    :returns: ???
    """
    the_job = job.Job.from_kvs(job_id)

    lat_bin_lims = config_text_to_list(the_job[job_cfg.LAT_BIN_LIMITS], float)
    lon_bin_lims = config_text_to_list(the_job[job_cfg.LON_BIN_LIMITS], float)
    mag_bin_lims = config_text_to_list(the_job[job_cfg.MAG_BIN_LIMITS], float)
    eps_bin_lims = config_text_to_list(the_job[job_cfg.EPS_BIN_LIMITS], float)

    jd = list_to_jdouble_array

    disagg_calc = java.jclass('DisaggregationCalculator')(
        jd(lat_bin_lims), jd(lon_bin_lims),
        jd(mag_bin_lims), jd(eps_bin_lims))

    erf = None
    gmpe_map = None

    disagg_calc.computeMatrix(
        site.latitude, site.longitude, erf, gmpe_map, poe)
    return disagg_calc

def list_to_jdouble_array(float_list):
    """Convert a 1D list of floats to a 1D Java Double[] (as a jpype object).
    """
    jdouble = java.jvm().JArray(java.jvm().java.lang.Double)(len(float_list))

    for i, val in enumerate(float_list):
        jdouble[i] = java.jvm().JClass('java.lang.Double')(val)

    return jdouble
