#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2014, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import random
import logging

import numpy

from openquake.hazardlib.calc import filters
from openquake.hazardlib.calc.gmf import GmfComputer
from openquake.commonlib import readinput, parallel
from openquake.commonlib.export import export
from openquake.baselib.general import AccumDict

from openquake.commonlib.calculators import base, calc


@parallel.litetask
def calc_gmfs(tag_seed_pairs, computer, monitor):
    """
    Computes several GMFs in parallel, one for each tag and seed.

    :param tag_seed_pairs:
        list of pairs (rupture tag, rupture seed)
    :param computer:
        :class:`openquake.hazardlib.calc.gmf.GMFComputer` instance
    :param monitor:
        :class:`openquake.commonlib.parallel.PerformanceMonitor` instance
    :returns:
        a dictionary tag -> {imt: gmf}
    """
    result = AccumDict({(0, str(gsim)): AccumDict()
                        for gsim in computer.gsims})
    with monitor:
        for tag, seed in tag_seed_pairs:
            for gsim_str, gmvs in computer.compute(seed):
                result[0, gsim_str][tag] = gmvs
    return result


@base.calculators.add('scenario')
class ScenarioCalculator(base.HazardCalculator):
    """
    Scenario hazard calculator
    """
    core_func = calc_gmfs
    result_kind = 'gmfs_by_trt_gsim'

    def pre_execute(self):
        """
        Read the site collection and initialize GmfComputer, tags and seeds
        """
        super(ScenarioCalculator, self).pre_execute()
        self.imts = readinput.get_imts(self.oqparam)
        trunc_level = self.oqparam.truncation_level
        correl_model = readinput.get_correl_model(self.oqparam)
        n_gmfs = self.oqparam.number_of_ground_motion_fields
        rupture = readinput.get_rupture(self.oqparam)

        # filter the sites
        self.sites = filters.filter_sites_by_distance_to_rupture(
            rupture, self.oqparam.maximum_distance, self.sitecol)
        if self.sites is None:
            raise RuntimeError(
                'All sites were filtered out! '
                'maximum_distance=%s km' % self.oqparam.maximum_distance)

        self.tags = ['scenario-%010d' % i for i in xrange(n_gmfs)]
        self.computer = GmfComputer(
            rupture, self.sites, self.imts, self.gsims,
            trunc_level, correl_model)
        rnd = random.Random(self.oqparam.random_seed)
        self.tag_seed_pairs = [(tag, rnd.randint(0, calc.MAX_INT))
                               for tag in self.tags]

    def execute(self):
        """
        Compute the GMFs in parallel and return a dictionary key -> imt -> gmfs
        """
        logging.info('Computing the GMFs')
        args = (self.tag_seed_pairs, self.computer, self.monitor('calc_gmfs'))
        result = {}
        res = parallel.apply_reduce(
            self.core_func.__func__, args,
            concurrent_tasks=self.oqparam.concurrent_tasks)
        for (trt_id, gsim), dic in res.iteritems():
            result[trt_id, gsim] = {  # build N x R matrices
                imt: numpy.array(
                    [dic[tag][imt] for tag in self.tags]).T
                for imt in map(str, self.imts)}
        return result

    def post_execute(self, result):
        """
        :param result: a dictionary imt -> gmfs
        :returns: a dictionary {('gmf', 'xml'): <gmf.xml filename>}
        """
        logging.info('Exporting the result')
        out = AccumDict()
        if not self.oqparam.exports:
            return out
        exports = self.oqparam.exports.split(',')
        for (trt_id, gsim), gmfs_by_imt in result.iteritems():
            for fmt in exports:
                fname = '%s_gmf.%s' % (gsim, fmt)
                out += export(
                    ('gmf', fmt), self.oqparam.export_dir, fname, self.sites,
                    self.tags, gmfs_by_imt)
        return out
