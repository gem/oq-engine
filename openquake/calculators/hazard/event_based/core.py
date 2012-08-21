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

"""Core functionality for Event-Based hazard calculations."""

import functools
import hashlib
import math
import os
import random

from celery.task import task

from openquake import java
from openquake import kvs
from openquake import logs
from openquake import shapes
from openquake.calculators.hazard import general
from openquake.output import hazard as hazard_output
from openquake.utils import config
from openquake.utils import stats
from openquake.utils import tasks as utils_tasks

LOG = logs.LOG

# Module-private kvs connection cache, to be used by create_java_cache().
__KVS_CONN_CACHE = {}


def create_java_cache(fn):
    """A decorator for creating java cache object"""

    @functools.wraps(fn)
    def decorated(self, *args, **kwargs):  # pylint: disable=C0111
        kvs_data = (config.get("kvs", "host"), int(config.get("kvs", "port")))

        if kvs.cache_connections():
            key = hashlib.md5(repr(kvs_data)).hexdigest()
            if key not in __KVS_CONN_CACHE:
                __KVS_CONN_CACHE[key] = java.jclass("KVS")(*kvs_data)
            self.cache = __KVS_CONN_CACHE[key]
        else:
            self.cache = java.jclass("KVS")(*kvs_data)

        return fn(self, *args, **kwargs)

    return decorated


@task
@java.unpack_exception
@stats.progress_indicator("h")
def compute_ground_motion_fields(job_id, sites, history, realization, seed):
    """ Generate ground motion fields """
    calculator = utils_tasks.calculator_for_task(job_id, 'hazard')

    calculator.compute_ground_motion_fields(
        sites, history, realization, seed)


class EventBasedHazardCalculator(general.BaseHazardCalculator):
    """Probabilistic Event Based method for performing Hazard calculations."""

    @java.unpack_exception
    @create_java_cache
    def execute(self):
        """Main hazard processing block.

        Loops through various random realizations, spawning tasks to compute
        GMFs."""
        source_model_generator = random.Random()
        source_model_generator.seed(
            self.job_ctxt['SOURCE_MODEL_LT_RANDOM_SEED'])

        gmpe_generator = random.Random()
        gmpe_generator.seed(self.job_ctxt['GMPE_LT_RANDOM_SEED'])

        gmf_generator = random.Random()
        gmf_generator.seed(self.job_ctxt['GMF_RANDOM_SEED'])

        histories = self.job_ctxt['NUMBER_OF_SEISMICITY_HISTORIES']
        realizations = self.job_ctxt['NUMBER_OF_LOGIC_TREE_SAMPLES']
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
                        self.job_ctxt.job_id,
                        self.job_ctxt.sites_to_compute(),
                        i, j, gmf_generator.getrandbits(32)))

            for each_task in pending_tasks:
                each_task.wait()
                if each_task.status != 'SUCCESS':
                    raise Exception(each_task.result)

            for j in range(0, realizations):
                stochastic_set_key = kvs.tokens.stochastic_set_key(
                    self.job_ctxt.job_id, i, j)
                LOG.info("Writing output for ses %s" % stochastic_set_key)
                ses = kvs.get_value_json_decoded(stochastic_set_key)
                if ses:
                    self.serialize_gmf(ses)

    def serialize_gmf(self, ses):
        """
        Write each GMF to an NRML file or to DB depending on job configuration.
        """
        iml_list = self.job_ctxt['INTENSITY_MEASURE_LEVELS']

        LOG.debug("IML: %s" % (iml_list))
        files = []

        nrml_path = ''

        for event_set in ses:
            for rupture in ses[event_set]:

                if self.job_ctxt['SAVE_GMFS']:
                    common_path = os.path.join(
                        self.job_ctxt.base_path, self.job_ctxt['OUTPUT_DIR'],
                        "gmf-%s-%s" % (str(event_set.replace("!", "_")),
                        str(rupture.replace("!", "_"))))
                    nrml_path = "%s.xml" % common_path

                gmf_writer = hazard_output.create_gmf_writer(
                    self.job_ctxt.job_id,
                    self.job_ctxt.serialize_results_to,
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

    @create_java_cache
    def compute_ground_motion_fields(self, site_list, history, realization,
                                     seed):
        """Ground motion field calculation, runs on the workers."""
        jpype = java.jvm()

        jsite_list = self.parameterize_sites(site_list)
        key = kvs.tokens.stochastic_set_key(self.job_ctxt.job_id, history,
                                            realization)
        correlate = self.job_ctxt['GROUND_MOTION_CORRELATION']
        stochastic_set_id = "%s!%s" % (history, realization)
        java.jclass("HazardCalculator").generateAndSaveGMFs(
                self.cache, key, stochastic_set_id, jsite_list,
                self.generate_erf(),
                self.generate_gmpe_map(),
                java.jclass("Random")(seed),
                jpype.JBoolean(correlate))
