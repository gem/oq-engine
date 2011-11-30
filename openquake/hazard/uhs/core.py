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


"""Core functionality of the Uniform Hazard Spectra calculator."""


import h5py
import numpy
import os
import uuid

from celery.task import task

from openquake import java
from openquake.job import Job
from openquake.logs import LOG
from openquake.utils import list_to_jdouble_array
from openquake.hazard.general import (
    generate_erf, generate_gmpe_map, set_gmpe_params, get_iml_list)
from openquake.utils import config
from openquake.utils import tasks as utils_tasks


@task(ignore_result=True)
def touch_result_file(job_id, path, sites, n_samples, n_periods):
    """Given a path (including the file name), create an empty HDF5 result file
    containing 1 empty data set for each site. Each dataset will be a matrix
    with the number of rows = number of samples and number of cols = number of
    UHS periods.

    :param int job_id:
        ID of the job record in the DB/KVS.
    :param str path:
        Location (including a file name) on an NFS where the empty
        result file should be created.
    :param sites:
        List of :class:`openquake.shapes.Site` objects.
    :param int n_samples:
        Number of logic tree samples (the y-dimension of each dataset).
    :param int n_periods:
        Number of UHS periods (the x-dimension of each dataset).
    """
    utils_tasks.check_job_status(job_id)
    # TODO: Generate the sites, instead of pumping them through rabbit?
    with h5py.File(path, 'w') as h5_file:
        for site in sites:
            ds_name = 'lon:%s-lat:%s' % (site.longitude, site.latitude)
            ds_shape = (n_samples, n_periods)
            h5_file.create_dataset(ds_name, dtype=numpy.float64,
                                   shape=ds_shape)


@task(ignore_results=True)
@java.unpack_exception
def compute_uhs_task(job_id, realization, site, result_dir):
    """Compute Uniform Hazard Spectra for a given site of interest and 1 or
    more Probability of Exceedance values. The bulk of the computation will
    be done by utilizing the `UHSCalculator` class in the Java code.

    UHS results (for each poe) will be written as a 1D array into temporary
    HDF5 files. (The files will later be collected and 'reduced' into final
    result files.)

    :param int job_id:
        ID of the job record in the DB/KVS.
    :param realization:
        Logic tree sample number (from 1 to N, where N is the
        NUMBER_OF_LOGIC_TREE_SAMPLES param defined in the job config.
    :param site:
        The site of interest (a :class:`openquake.shapes.Site` object).
    :param result_dir:
        NFS result directory path. For each poe, a subfolder will be created to
        contain intermediate calculation results. (Each call to this task will
        generate 1 result file per poe.)
    :returns:
        A list of the resulting file names (1 per poe).
    """
    utils_tasks.check_job_status(job_id)

    the_job = Job.from_kvs(job_id)

    log_msg = (
        "Computing UHS for job_id=%s, site=%s, realization=%s."
        " UHS results will be serialized to `%s`.")
    log_msg %= (the_job.job_id, site, realization, result_dir)
    LOG.info(log_msg)

    uhs_results = compute_uhs(the_job, site)

    return write_uhs_results(result_dir, uhs_results)


def compute_uhs(the_job, site):
    """Given a `Job` and a site of interest, compute UHS. The Java
    `UHSCalculator` is called to do perform the core computation.

    :param the_job:
        :class:`openquake.job.Job` instance.
    :param site:
        :class:`openquake.shapes.Site` instance.
    :returns:
        An `ArrayList` (Java object) of `UHSResult` objects, one per PoE.
    """

    periods = list_to_jdouble_array(the_job['UHS_PERIODS'])
    poes = list_to_jdouble_array(the_job['POES'])
    imls = get_iml_list(the_job['INTENSITY_MEASURE_LEVELS'],
                        the_job['INTENSITY_MEASURE_TYPE'])
    max_distance = the_job['MAXIMUM_DISTANCE']

    cache = java.jclass('KVS')(
        config.get('kvs', 'host'),
        int(config.get('kvs', 'port')))

    erf = generate_erf(the_job.job_id, cache)
    gmpe_map = generate_gmpe_map(the_job.job_id, cache)
    set_gmpe_params(gmpe_map, the_job.params)

    uhs_calc = java.jclass('UHSCalculator')(periods, poes, imls, erf, gmpe_map,
                                            max_distance)

    uhs_results = uhs_calc.computeUHS(
        site.latitude,
        site.longitude,
        the_job['VS30_TYPE'],
        the_job['REFERENCE_VS30_VALUE'],
        the_job['DEPTHTO1PT0KMPERSEC'],
        the_job['REFERENCE_DEPTH_TO_2PT5KM_PER_SEC_PARAM'])

    return uhs_results


def write_uhs_results(result_dir, uhs_results):
    """Write intermediate (temporary) UHS results to the specified directory.
    Results will later be collected and written to the final results file(s).

    :param result_dir:
        NFS result directory path. For each poe, a subfolder will be created to
        contain intermediate calculation results. (Each call to this task will
        generate 1 result file per poe.
    :param uhs_results:
        A sequence of `UHSResult` jpype Java objects.
    :returns:
        A list of the resulting file names (1 per poe).
    """
    result_files = []

    for result in uhs_results:
        poe = result.getPoe()
        uhs = result.getUhs()  # This is a Java Double[]

        # We want intermediate calc results to be organized by PoE,
        # so that they can be collected and reduced into a single result file
        # per PoE.
        # Having results separated this way means that a result collector
        # is simply assigned a directory to poll and grabs any result files
        # that it finds (without having to do much/any fitering or searching).
        poe_path = os.path.join(result_dir, 'poe:%s' % poe)
        if not os.path.exists(poe_path):
            os.makedirs(poe_path)

        file_path = os.path.join(poe_path, str(uuid.uuid4()))

        with h5py.File(file_path, 'w') as h5_file:
            h5_file.create_dataset(
                'uhs',
                # We have to get the primitive 'value' for each Double in the
                # Double[]
                data=numpy.array([x.value for x in uhs], dtype=numpy.float64))

        result_files.append(file_path)

    return result_files
