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


from math import log

from openquake import java
from openquake import job

from openquake.job import config as job_cfg
from openquake.job import config_text_to_list
from openquake.utils import config
from openquake.hazard.general import (
    generate_erf, generate_gmpe_map, set_gmpe_params)


@java.jexception
def compute_disagg_matrix(job_id, site, realization, poe, result_dir):
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
    :param result_dir: location for the Java code to write the matrix in an
        HDF5 file (in a distributed environment, this should be the path of a
        mounted NFS)

    :returns: 2-tuple of (ground_motion_value, path_to_h5_matrix_file)
    """
    def make_disagg_calc(a_job):
        """Encapsulates DisaggregationCalculator creation.

        :param a_job: a job
        :type a_job: :class:`openquake.job.Job` instance
        :returns: jpype instance of `org.gem.calc.DisaggregationCalculator`
        """

        lat_bin_lims = config_text_to_list(
            a_job[job_cfg.LAT_BIN_LIMITS], float)
        lon_bin_lims = config_text_to_list(
            a_job[job_cfg.LON_BIN_LIMITS], float)
        mag_bin_lims = config_text_to_list(
            a_job[job_cfg.MAG_BIN_LIMITS], float)
        eps_bin_lims = config_text_to_list(
            a_job[job_cfg.EPS_BIN_LIMITS], float)

        jd = list_to_jdouble_array

        disagg_calc = java.jclass('DisaggregationCalculator')(
            jd(lat_bin_lims), jd(lon_bin_lims),
            jd(mag_bin_lims), jd(eps_bin_lims))

        return disagg_calc

    the_job = job.Job.from_kvs(job_id)

    disagg_calc = make_disagg_calc(the_job)

    cache = java.jclass('KVS')(
        config.get('kvs', 'host'),
        int(config.get('kvs', 'port')))

    erf = generate_erf(job_id, cache)
    gmpe_map = generate_gmpe_map(job_id, cache)
    set_gmpe_params(gmpe_map, the_job.params)

    iml_arraylist = java.jclass('ArrayList')()
    iml_vals = job.config_text_to_list(
        the_job['INTENSITY_MEASURE_LEVELS'], float)
    # Map `log` (natural log) to each IML value before passing to the
    # calculator.
    iml_vals = [log(x) for x in iml_vals]
    iml_arraylist.addAll(iml_vals)
    vs30_value = float(the_job['REFERENCE_VS30_VALUE'])
    depth_to_2pt5 = float(the_job['REFERENCE_DEPTH_TO_2PT5KM_PER_SEC_PARAM'])

    matrix_result = disagg_calc.computeAndWriteMatrix(
        site.latitude, site.longitude, erf, gmpe_map, poe, iml_arraylist,
        vs30_value, depth_to_2pt5, result_dir)

    return (matrix_result.getGMV(), matrix_result.getMatrixPath())

def list_to_jdouble_array(float_list):
    """Convert a 1D list of floats to a 1D Java Double[] (as a jpype object).
    """
    jdouble = java.jvm().JArray(java.jvm().java.lang.Double)(len(float_list))

    for i, val in enumerate(float_list):
        jdouble[i] = java.jvm().JClass('java.lang.Double')(val)

    return jdouble
