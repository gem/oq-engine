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

"""Core functionality for Event-Based hazard calculations."""

import math
import os
import random

from celery.task import task

from openquake import java
from openquake import kvs
from openquake import logs
from openquake import shapes
from openquake.output import hazard as hazard_output
from openquake.utils import stats
from openquake.utils import tasks as utils_tasks
from openquake.calculators.hazard import general

LOG = logs.LOG


@task
@java.unpack_exception
@stats.progress_indicator
def compute_ground_motion_fields(job_id, sites, history, realization, seed):
    """ Generate ground motion fields """
    calculator = utils_tasks.calculator_for_task(job_id, 'hazard')

    calculator.compute_ground_motion_fields(
        sites, history, realization, seed)


class EventBasedHazardCalculator(general.BasePSHAMixin):
    """Probabilistic Event Based method for performing Hazard calculations.

    Implements the JobMixin, which has a primary entry point of execute().
    Execute is responsible for dispatching celery tasks.
    """

    @java.unpack_exception
    @general.create_java_cache
    def execute(self):
        """Main hazard processing block.

        Loops through various random realizations, spawning tasks to compute
        GMFs."""
        source_model_generator = random.Random()
        source_model_generator.seed(
            self.calc_proxy['SOURCE_MODEL_LT_RANDOM_SEED'])

        gmpe_generator = random.Random()
        gmpe_generator.seed(self.calc_proxy['GMPE_LT_RANDOM_SEED'])

        gmf_generator = random.Random()
        gmf_generator.seed(self.calc_proxy['GMF_RANDOM_SEED'])

        histories = self.calc_proxy['NUMBER_OF_SEISMICITY_HISTORIES']
        realizations = self.calc_proxy['NUMBER_OF_LOGIC_TREE_SAMPLES']
        LOG.info(
            "Going to run hazard for %s histories of %s realizations each."
            % (histories, realizations))

        for i in range(0, histories):
            pending_tasks = []
            for j in range(0, realizations):
                self.store_source_model(source_model_generator.getrandbits(32))
                self.store_gmpe_map(gmpe_generator.getrandbits(32))
                pending_tasks.append(
                    compute_ground_motion_fields.delay(
                        self.calc_proxy.job_id, self.sites_to_compute(),
                        i, j, gmf_generator.getrandbits(32)))

            for each_task in pending_tasks:
                each_task.wait()
                if each_task.status != 'SUCCESS':
                    raise Exception(each_task.result)

            for j in range(0, realizations):
                stochastic_set_key = kvs.tokens.stochastic_set_key(
                    self.calc_proxy.job_id, i, j)
                LOG.info("Writing output for ses %s" % stochastic_set_key)
                ses = kvs.get_value_json_decoded(stochastic_set_key)
                if ses:
                    self.serialize_gmf(ses)

    def serialize_gmf(self, ses):
        """
        Write each GMF to an NRML file or to DB depending on job configuration.
        """
        iml_list = self.calc_proxy['INTENSITY_MEASURE_LEVELS']

        LOG.debug("IML: %s" % (iml_list))
        files = []

        nrml_path = ''

        for event_set in ses:
            for rupture in ses[event_set]:

                if self.calc_proxy['GMF_OUTPUT']:
                    common_path = os.path.join(self.base_path,
                            self.calc_proxy['OUTPUT_DIR'],
                            "gmf-%s-%s" % (str(event_set.replace("!", "_")),
                                           str(rupture.replace("!", "_"))))
                    nrml_path = "%s.xml" % common_path

                gmf_writer = hazard_output.create_gmf_writer(
                    self.calc_proxy.job_id,
                    self.calc_proxy.serialize_results_to,
                    nrml_path)
                gmf_data = {}
                for site_key in ses[event_set][rupture]:
                    site = ses[event_set][rupture][site_key]
                    site_obj = shapes.Site(site['lon'], site['lat'])
                    gmf_data[site_obj] = \
                        {'groundMotion': math.exp(float(site['mag']))}

                gmf_writer.serialize(gmf_data)
                files.append(nrml_path)
        return files

    @general.create_java_cache
    def compute_ground_motion_fields(self, site_list, history, realization,
                                     seed):
        """Ground motion field calculation, runs on the workers."""
        jpype = java.jvm()

        jsite_list = self.parameterize_sites(site_list)
        key = kvs.tokens.stochastic_set_key(self.calc_proxy.job_id, history,
                                            realization)
        correlate = self.calc_proxy['GROUND_MOTION_CORRELATION']
        stochastic_set_id = "%s!%s" % (history, realization)
        java.jclass("HazardCalculator").generateAndSaveGMFs(
                self.cache, key, stochastic_set_id, jsite_list,
                self.generate_erf(),
                self.generate_gmpe_map(),
                java.jclass("Random")(seed),
                jpype.JBoolean(correlate))
