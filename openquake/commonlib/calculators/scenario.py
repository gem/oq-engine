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
        a dictionary tag -> gmf
    """
    tags, seeds = zip(*tag_seed_pairs)
    return dict(zip(tags, computer.compute(seeds)))


@base.calculators.add('scenario')
class ScenarioCalculator(base.HazardCalculator):
    """
    Scenario hazard calculator
    """
    core_func = calc_gmfs
    result_kind = 'gmf_by_tag'

    def pre_execute(self):
        """
        Read the site collection and initialize GmfComputer, tags and seeds
        """
        super(ScenarioCalculator, self).pre_execute()
        trunc_level = self.oqparam.truncation_level
        correl_model = readinput.get_correl_model(self.oqparam)
        n_gmfs = self.oqparam.number_of_ground_motion_fields
        rupture = readinput.get_rupture(self.oqparam)
        self.gsims = readinput.get_gsims(self.oqparam)

        # filter the sites
        self.sites = filters.filter_sites_by_distance_to_rupture(
            rupture, self.oqparam.maximum_distance, self.sitecol)
        if self.sites is None:
            raise RuntimeError(
                'All sites were filtered out! '
                'maximum_distance=%s km' % self.oqparam.maximum_distance)
        self.datastore['sites'] = self.sites
        self.tags = ['scenario-%010d' % i for i in xrange(n_gmfs)]
        self.computer = GmfComputer(
            rupture, self.sites, self.oqparam.imtls, self.gsims,
            trunc_level, correl_model)
        rnd = random.Random(self.oqparam.random_seed)
        self.tag_seed_pairs = [(tag, rnd.randint(0, calc.MAX_INT))
                               for tag in self.tags]

    def execute(self):
        """
        Compute the GMFs in parallel and return a dictionary gmf_by_tag
        """
        logging.info('Computing the GMFs')
        args = (self.tag_seed_pairs, self.computer, self.monitor('calc_gmfs'))
        gmf_by_tag = parallel.apply_reduce(
            self.core_func.__func__, args,
            concurrent_tasks=self.oqparam.concurrent_tasks)
        return gmf_by_tag

    def post_execute(self, gmf_by_tag):
        """
        :param gmf_by_tag: a dictionary tag -> gmf
        :returns: a dictionary {('gmf', 'xml'): <gmf.xml filename>}
        """
        logging.info('Exporting the result')
        out = AccumDict()
        if not self.oqparam.exports:
            return out
        exports = self.oqparam.exports.split(',')
        for rlz in self.rlzs_assoc.realizations:
            gsim = str(rlz)
            gmfs = [gmf_by_tag[tag][gsim] for tag in self.tags]
            for fmt in exports:
                fname = '%s_gmf.%s' % (gsim, fmt)
                out += export(
                    ('gmf', fmt), self.oqparam.export_dir, fname, self.sites,
                    self.tags, numpy.array(gmfs, gmfs[0].dtype), rlz.lt_path)
        return out
