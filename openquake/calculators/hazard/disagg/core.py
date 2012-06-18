# -*- coding: utf-8 -*-
# Copyright (c) 2010-2012, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

"""Core functionality for the Disaggregation Hazard calculator."""

import errno
import h5py
import numpy
import os
import random
import uuid

from celery.task import task

from openquake import java
from openquake import logs
from openquake.java import list_to_jdouble_array
from openquake.job import config as job_cfg
from openquake.output import hazard_disagg as hazard_output
from openquake.utils import config
from openquake.utils.tasks import get_running_job
from openquake.calculators.hazard.disagg import FULL_DISAGG_MATRIX
from openquake.calculators.hazard.disagg import subsets
from openquake.calculators.hazard import general


LOG = logs.LOG


# pylint: disable=R0914
@java.unpack_exception
def compute_disagg_matrix(job_ctxt, site, poe, result_dir):
    """ Compute a complete 5D Disaggregation matrix. This task leans heavily
    on the DisaggregationCalculator (in the OpenQuake Java lib) to handle this
    computation.

    The 5D matrix returned from the java calculator will be saved to a file in
    HDF5 format.

    :param job_ctxt:
        A :class:`openquake.engine.JobContext` which holds all of the
        data we need to run this computation.
    :param site: a single site of interest
    :type site: :class:`openquake.shapes.Site` instance`
    :param poe: Probability of Exceedence
    :type poe: `float`
    :param result_dir: location for the Java code to write the matrix in an
        HDF5 file (in a distributed environment, this should be the path of a
        mounted NFS)

    :returns: 2-tuple of (ground_motion_value, path_to_h5_matrix_file)
    """
    lat_bin_lims = job_ctxt[job_cfg.LAT_BIN_LIMITS]
    lon_bin_lims = job_ctxt[job_cfg.LON_BIN_LIMITS]
    mag_bin_lims = job_ctxt[job_cfg.MAG_BIN_LIMITS]
    eps_bin_lims = job_ctxt[job_cfg.EPS_BIN_LIMITS]

    jd = list_to_jdouble_array

    disagg_calc = java.jclass('DisaggregationCalculator')(
        jd(lat_bin_lims), jd(lon_bin_lims),
        jd(mag_bin_lims), jd(eps_bin_lims))

    cache = java.jclass('KVS')(
        config.get('kvs', 'host'),
        int(config.get('kvs', 'port')))

    erf = general.generate_erf(job_ctxt.job_id, cache)
    gmpe_map = general.generate_gmpe_map(job_ctxt.job_id, cache)
    general.set_gmpe_params(gmpe_map, job_ctxt.params)

    imls = general.get_iml_list(job_ctxt['INTENSITY_MEASURE_LEVELS'],
                                job_ctxt['INTENSITY_MEASURE_TYPE'])

    site_model = general.get_site_model(job_ctxt.oq_job.id)

    if site_model is not None:
        sm_data = general.get_closest_site_model_data(site_model, site)
        vs30_type = sm_data.vs30_type.capitalize()
        vs30 = sm_data.vs30
        z1pt0 = sm_data.z1pt0
        z2pt5 = sm_data.z2pt5
    else:
        jp = job_ctxt.oq_job_profile

        vs30_type = jp.vs30_type.capitalize()
        vs30 = jp.reference_vs30_value
        z1pt0 = jp.depth_to_1pt_0km_per_sec
        z2pt5 = jp.reference_depth_to_2pt5km_per_sec_param

    matrix_result = _compute_matrix(
        disagg_calc, site.latitude, site.longitude, erf, gmpe_map, poe, imls,
        vs30_type, vs30, z1pt0, z2pt5)

    matrix_path = save_5d_matrix_to_h5(result_dir,
                                       numpy.array(matrix_result.getMatrix()))

    return (matrix_result.getGMV(), matrix_path)


# Disabling 'Too many arguments'
# pylint: disable=R0913
def _compute_matrix(calc, lat, lon, erf, gmpe_map, poe, imls, vs30_type, vs30,
                    z1pt0, z2pt5):
    """Helper function for executing `computeMatrix` in the java calculator.

    As a separate function, this makes it easier to mock (since we can't really
    mock the java code).

    See also :function:`compute_disagg_matrix`.

    :param calc:
        jpype `org.gem.calc.DisaggregationCalculator` object.
    :param float lat:
        Site latitude.
    :param float lon:
        Site longitude.
    :param erf:
        Earthquake Rupture Forecast; a jpype object which implements
        `org.opensha.sha.earthquake.EqkRupForecastAPI`.
    :param gmpe_map:
        jpype `Map<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>`.
    :param float poe:
        Probability of Exceedence value.
    :param imls:
        jpype `Double` array of intensity measure levels.
    :param vs30_type:
        'measured' or 'inferred'. Identifies if vs30 value has been measured or
        inferred.
    :param float vs30:
        Average shear wave velocity for top 30 m. Units m/s.
    :param float z1pt0:
        Depth to shear wave velocity of 1.0 km/s. Units m.
    :param float z2pt5:
        Depth to shear wave velocity of 2.5 km/s. Units km.

    :returns:
        jpype `org.gem.calc.DisaggregationResult` object containing the 5d
        disaggregation matrix and the ground motion value for this site.
    """
    return calc.computeMatrix(
        lat, lon, erf, gmpe_map, poe, imls, vs30_type, vs30, z1pt0, z2pt5)


def save_5d_matrix_to_h5(directory, matrix):
    """Save a full disaggregation matrix to the specified directory with a
    random unique filename (using uuid).

    NOTE: For a distributed computation environment, the specified directory
    should be the location of a mounted network file system.

    :param str directory: directory where the hdf5 file shall be saved
    :param matrix: 5-dimensional :class:`numpy.ndarray`

    :returns: full path (including filename) where the hdf5 file was saved
    """
    file_name = '%s.h5' % str(uuid.uuid4())
    file_path = os.path.join(directory, file_name)

    with h5py.File(file_path, 'w') as target:
        target.create_dataset(FULL_DISAGG_MATRIX, data=matrix)

    return file_path


@task
@java.unpack_exception
def compute_disagg_matrix_task(job_id, site, realization, poe,
                               result_dir):
    """ Compute a complete 5D Disaggregation matrix. This task leans heavily
    on the DisaggregationCalculator (in the OpenQuake Java lib) to handle this
    computation.

    :param job_id: id of the calculation record in the KVS
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
    job_ctxt = get_running_job(job_id)

    log_msg = (
        "Computing full disaggregation matrix for job_id=%s, site=%s, "
        "realization=%s, PoE=%s. Matrix results will be serialized to `%s`.")
    log_msg %= (job_ctxt.job_id, site, realization, poe, result_dir)
    LOG.info(log_msg)

    return compute_disagg_matrix(job_ctxt, site, poe, result_dir)


class DisaggHazardCalculator(general.BaseHazardCalculator):
    """The Python part of the Disaggregation calculator. This calculator
    computes disaggregation matrix results in the following manner:

    1) Compute full disaggregation matrix results asynchronously. One task is
        created per site per realization per PoE value. Each task serializes
        the resulting matrix to an HDF5 file. (Note: In a distributed
        environment, it is assumed that all HDF5 files are serialized to a
        directory on an NFS (Network File System).
    2) Next, tasks are distributed to extract the matrix subsets (requested in
        the job config) and serialize them to HDF5.
    3) Finally, the jobber collects the calculation results (including paths to
        matrix subset files) and serializes a set of NRML files to represent
        the final output.
    """

    @general.preload
    def execute(self):
        """Main execution point for the Disaggregation calculator.

        The workflow is structured like so:
        1) Store source and GMPE models in the KVS (so the workers can rapidly
            access that data).
        2) Create a result dir (on the NFS) for storing matrices.
        3) Distribute full disaggregation matrix computation to workers.
        4) Distribute matrix subset extraction (using full disagg. results as
            input.
        5) Finally, write an NRML/XML wrapper around the disagg. results.
        """
        # matrix results for this job will go here:
        result_dir = DisaggHazardCalculator.create_result_dir(
            config.get('nfs', 'base_dir'), self.job_ctxt.job_id)

        realizations = self.job_ctxt['NUMBER_OF_LOGIC_TREE_SAMPLES']
        poes = self.job_ctxt['POES']
        sites = self.job_ctxt.sites_to_compute()

        log_msg = ("Computing disaggregation for job_id=%s,  %s sites, "
            "%s realizations, and PoEs=%s")
        log_msg %= (self.job_ctxt.job_id, len(sites), realizations, poes)
        LOG.info(log_msg)

        full_disagg_results = self.distribute_disagg(sites, realizations, poes,
                                                     result_dir)

        subset_types = self.job_ctxt['DISAGGREGATION_RESULTS']

        subset_results = self.distribute_subsets(full_disagg_results,
                                                 subset_types, result_dir)

        DisaggHazardCalculator.serialize_nrml(self.job_ctxt, subset_types,
                                              subset_results)

    @staticmethod
    def create_result_dir(base_path, job_id):
        """Create the directory to store intermediate and final disaggregation
        results and return the new directory path. The full storage path is
        constructed like so: <base_path>/disagg-results/job-<job_id>.

        For example:
        >>> DisaggHazardCalculator.create_result_dir(
        ... '/tmp/openquake', 123456789)
        '/tmp/openquake/disagg-results/job-123456789'

        :param base_path: base result storage directory (a path to an NFS
            mount, for example)
        :param int job_id: numeric job id
        :returns: full path to the newly created result dir
        """
        output_path = os.path.join(
            base_path, 'disagg-results', 'job-%s' % job_id)
        try:
            os.makedirs(output_path)
        except OSError, err:
            # If the path already exists, make sure it's a dir.
            if err.errno == errno.EEXIST:
                # If it isn't a dir, this is a problem.
                if not os.path.isdir(output_path):
                    raise
            else:
                raise
        return output_path

    def distribute_disagg(self, sites, realizations, poes, result_dir):
        """Compute disaggregation by splitting up the calculation over sites,
        realizations, and PoE values.

        :param the_job:
            JobContext definition
        :type the_job:
            :class:`openquake.engine.JobContext` instance
        :param sites:
            List of :class:`openquake.shapes.Site` objects
        :param poes:
            Probability of Exceedence levels for the calculation
        :type poes:
            List of floats
        :param result_dir:
            Path where full disaggregation results should be stored
        :returns:
            Result data in the following form::
                [(realization_1, poe_1,
                  [(site_1, gmv_1, matrix_path_1),
                   (site_2, gmv_2, matrix_path_2)]
                 ),
                 (realization_1, poe_2,
                  [(site_1, gmv_1, matrix_path_3),
                   (site_2, gmv_2, matrix_path_4)]
                 ),
                 ...
                 (realization_N, poe_N,
                  [(site_1, gmv_1, matrix_path_N-1),
                   (site_2, gmv_2, matrix_path_N)]
                 ),
                ]

            A single matrix result in this form looks like this::
                [(1, 0.1,
                  [(Site(0.0, 0.0), 0.2257,
                    '/var/lib/openquake/disagg-results/job-372/some_guid.h5'),]
                 ),
                ]
        """
        # accumulates the final results of this method
        full_da_results = []

        # accumulates task data across the realization and poe loops
        task_data = []

        src_model_rnd = random.Random()
        src_model_rnd.seed(self.job_ctxt['SOURCE_MODEL_LT_RANDOM_SEED'])
        gmpe_rnd = random.Random()
        gmpe_rnd.seed(self.job_ctxt['GMPE_LT_RANDOM_SEED'])

        for rlz in xrange(1, realizations + 1):  # 1 to N, inclusive
            # cache the source model and gmpe model in the KVS
            # so the Java code can access it

            general.store_source_model(self.job_ctxt.job_id,
                                       src_model_rnd.getrandbits(32),
                                       self.job_ctxt.params, self.calc)
            general.store_gmpe_map(
                self.job_ctxt.job_id, gmpe_rnd.getrandbits(32), self.calc)

            for poe in poes:
                task_site_pairs = []
                for site in sites:
                    a_task = compute_disagg_matrix_task.delay(
                        self.job_ctxt.job_id, site, rlz, poe, result_dir)

                    task_site_pairs.append((a_task, site))

                task_data.append((rlz, poe, task_site_pairs))

        for rlz, poe, task_site_pairs in task_data:

            # accumulates all data for a given (realization, poe) pair
            rlz_poe_data = []
            for a_task, site in task_site_pairs:
                a_task.wait()
                if not a_task.successful():
                    msg = (
                        "Full Disaggregation matrix computation task"
                        " for job %s with task_id=%s, realization=%s, PoE=%s,"
                        " site=%s has failed with the following error: %s")
                    msg %= (
                        self.job_ctxt.job_id, a_task.task_id, rlz, poe,
                        site, a_task.result)
                    LOG.critical(msg)
                    raise RuntimeError(msg)
                else:
                    gmv, matrix_path = a_task.result
                    rlz_poe_data.append((site, gmv, matrix_path))

            full_da_results.append((rlz, poe, rlz_poe_data))

        return full_da_results

    def distribute_subsets(self, full_disagg_results, subset_types,
                           target_dir):
        """Given the results of the first phase of the disaggregation
        calculation, extract the matrix subsets (as requested in the job
        configuration).

        :param full_disagg_results:
            Results of :method:`DisaggHazardCalculator.distribute_disagg`.
        :param subset_types:
            The matrix subset results requested in the job config.
        :param target_dir:
            Directory where subset matrix results should be stored (a directory
            connected to an NFS, for example).

        :returns:
            Subset result data in the following form::
                [(realization_1, poe_1,
                  [(site_1, gmv_1, matrix_path_1),
                   (site_2, gmv_2, matrix_path_2)]
                 ),
                 (realization_1, poe_2,
                  [(site_1, gmv_1, matrix_path_3),
                   (site_2, gmv_2, matrix_path_4)]
                 ),
                 ...
                 (realization_N, poe_N,
                  [(site_1, gmv_1, matrix_path_N-1),
                   (site_2, gmv_2, matrix_path_N)]
                 ),
                ]

            A single matrix result in this form looks like this::
                [(1, 0.1,
                  [(Site(0.0, 0.0), 0.2257,
                   'disagg-results-sample:1-gmv:0.2257-lat:0.0-lon:0.0.h5'),]
                 ),
                ]
        """
        lat_bin_lims = self.job_ctxt[job_cfg.LAT_BIN_LIMITS]
        lon_bin_lims = self.job_ctxt[job_cfg.LON_BIN_LIMITS]
        mag_bin_lims = self.job_ctxt[job_cfg.MAG_BIN_LIMITS]
        eps_bin_lims = self.job_ctxt[job_cfg.EPS_BIN_LIMITS]
        dist_bin_lims = self.job_ctxt[job_cfg.DIST_BIN_LIMITS]

        rlz_poe_task_data = []

        for rlz, poe, data_list in full_disagg_results:
            task_data = []
            for site, gmv, matrix_path in data_list:

                subset_file = (
                    'disagg-results-sample:%s-gmv:%.7f-lat:%.7f-lon:%.7f.h5')
                subset_file %= (rlz, gmv, site.latitude, site.longitude)
                target_file = os.path.join(target_dir, subset_file)

                a_task = subsets.extract_subsets.delay(
                    self.job_ctxt.job_id, site, matrix_path, lat_bin_lims,
                    lon_bin_lims, mag_bin_lims, eps_bin_lims, dist_bin_lims,
                    target_file, subset_types)

                task_data.append((a_task, site, gmv, matrix_path, target_file))

            rlz_poe_task_data.append((rlz, poe, task_data))

        final_results = []

        for rlz, poe, task_data in rlz_poe_task_data:
            rlz_poe_results = []  # list of data/results per (rlz, poe) pair
            for a_task, site, gmv, matrix_path, target_file in task_data:

                a_task.wait()
                if not a_task.successful():
                    msg = (
                        "Matrix subset extraction task for job %s with"
                        " task_id=%s, realization=%s, PoE=%s, target_file=%s"
                        " has failed with the following error: %s")
                    msg %= (self.job_ctxt.job_id, a_task.task_id, poe,
                            target_file, a_task.result)
                    LOG.critical(msg)
                    raise RuntimeError(msg)
                else:
                    rlz_poe_results.append((site, gmv, target_file))

                # We don't need the full matrix file anymore.
                os.unlink(matrix_path)

            final_results.append((rlz, poe, rlz_poe_results))

        return final_results

    @staticmethod
    def serialize_nrml(the_job, subset_types, subsets_data):
        """Write a NRML/XML wrapper around the disaggregation subset results.

        :param the_job:
            The job configuration.
        :type the_job:
            :class:`openquake.engine.JobContext` instance
        :param subset_types:
            The matrix subset results requested in the job config.
        :param subsets_data:
            Results of :method:`DisaggHazardCalculator.distribute_subsets`.
        """
        LOG.info("Serializing XML results for job=%s" % the_job.job_id)
        imt = the_job['INTENSITY_MEASURE_TYPE']

        base_output_dir = os.path.join(the_job['BASE_PATH'],
                                       the_job['OUTPUT_DIR'])

        if not os.path.exists(base_output_dir):
            LOG.info("Creating output directory `%s`" % base_output_dir)
            os.makedirs(base_output_dir)

        for rlz, poe, data in subsets_data:

            file_name = 'disagg-results-sample:%s-PoE:%s.xml'
            file_name %= (rlz, poe)
            path = os.path.join(base_output_dir, file_name)
            LOG.info("Serializing XML results to %s" % path)
            writer = hazard_output.DisaggregationBinaryMatrixXMLWriter(
                path, poe, imt, subset_types, end_branch_label=rlz)

            writer.open()

            for site, gmv, matrix_path in data:
                node_data = dict(groundMotionValue=gmv, path=matrix_path)
                writer.write(site, node_data)

            writer.close()
