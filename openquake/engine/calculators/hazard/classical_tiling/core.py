# Copyright (c) 2014-2015, GEM Foundation.
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

"""
Core functionality for the classical tilint PSHA hazard calculator.
"""
import math
from openquake.baselib.general import split_in_blocks
from openquake.commonlib import readinput
from openquake.hazardlib.site import SiteCollection

from openquake.engine.calculators import calculators
from openquake.engine.calculators.hazard.general import BaseHazardCalculator
from openquake.engine.logs import LOG


@calculators.add('classical_tiling')
class ClassicalTilingHazardCalculator(BaseHazardCalculator):
    """
    Classical tiling PSHA hazard calculator.
    """

    def run_tile(self, i, tile):
        classical = calculators['classical'](self.job)
        classical.tilepath = ('tile%d' % i,)
        classical.site_collection = SiteCollection(tile)
        classical.initialize_sources()
        classical.init_zeros_ones()
        classical.execute()
        classical.post_execute()
        classical.post_process()

    def pre_execute(self):
        self.oqparam = self.job.get_oqparam()
        source_model_lt = readinput.get_source_model_lt(self.oqparam)
        source_models = list(readinput.get_source_models(
            self.oqparam, source_model_lt))
        self.parse_risk_model()
        self.initialize_site_collection()
        info = readinput.get_job_info(
            self.oqparam, source_models, self.site_collection)
        self.imtls = self.oqparam.intensity_measure_types_and_levels
        weight = info['n_sites'] * info['n_levels'] * info['max_realizations']
        nblocks = math.ceil(weight / self.oqparam.maximum_tile_weight)
        self.tiles = list(split_in_blocks(self.site_collection, nblocks))
        self.num_tiles = len(self.tiles)

    def execute(self):
        for i, tile in enumerate(self.tiles, 1):
            LOG.progress('Running tile %d of %d, %s sites',
                         i, self.num_tiles, len(tile))
            self.run_tile(i, tile)

    def post_execute(self):
        pass

    def post_process(self):
        pass
