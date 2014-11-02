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
import operator

import numpy

from openquake.hazardlib.calc.gmf import GmfComputer
from openquake.commonlib import readinput, parallel
from openquake.commonlib.general import AccumDict

from openquake.commonlib.calculators import calculators, base
from openquake.commonlib.export import export


@calculators.add('classical')
class ClassicalCalculator(base.BaseCalculator):
    """
    Classical PSHA calculators
    """
    def pre_execute(self):
        pass

    def execute(self):
        pass

    def post_execute(self, result):
        pass


@calculators.add('event_based')
class EventBasedCalculator(base.BaseCalculator):
    """
    Event based PSHA calculators
    """
    def pre_execute(self):
        pass

    def execute(self):
        pass

    def post_execute(self, result):
        pass


@calculators.add('disaggregation')
class DisaggregationCalculator(base.BaseCalculator):
    """
    Classical disaggregation PSHA calculators
    """
    def pre_execute(self):
        pass

    def execute(self):
        pass

    def post_execute(self, result):
        pass


def calc_gmfs(tag_seed_pairs, computer, monitor):
    """
    Computer several GMFs in parallel, one for each tag and seed.

    :param tag_seed_pairs:
        list of pairs (rupture tag, rupture seed)
    :param computer:
        :class:`openquake.hazardlib.calc.gmf.GMFComputer` instance
    :param monitor:
        :class:`openquake.commonlib.parallel.PerformanceMonitor` instance
    """
    with monitor:
        res = AccumDict()  # tag -> {imt: gmvs}
        for tag, seed in tag_seed_pairs:
            res += {tag: dict(computer.compute(seed))}
    return res


@calculators.add('scenario')
class ScenarioCalculator(base.BaseCalculator):
    """
    Scenario hazard calculator
    """
    core_func = calc_gmfs

    def init_tags(self):
        self.imts = readinput.get_imts(self.oqparam)
        gsim = readinput.get_gsim(self.oqparam)
        trunc_level = getattr(self.oqparam, 'truncation_level', None)
        correl_model = readinput.get_correl_model(self.oqparam)
        n_gmfs = self.oqparam.number_of_ground_motion_fields
        rupture = readinput.get_rupture(self.oqparam)

        self.tags = ['scenario-%010d' % i for i in xrange(n_gmfs)]
        self.computer = GmfComputer(rupture, self.sitecol, self.imts, gsim,
                                    trunc_level, correl_model)
        rnd = random.Random(getattr(self.oqparam, 'random_seed', 42))
        self.tag_seed_pairs = [(tag, rnd.randint(0, 2 ** 31 - 1))
                               for tag in self.tags]

    def pre_execute(self):
        logging.info('Reading the site collection')
        if 'exposure' in self.oqparam.inputs:
            self.sitecol, _assets = readinput.get_sitecol_assets(self.oqparam)
        else:
            self.sitecol = readinput.get_site_collection(self.oqparam)
        self.init_tags()

    def execute(self):
        logging.info('Computing the GMFs')
        return parallel.apply_reduce(
            self.core_func.__func__,
            (self.tag_seed_pairs, self.computer, self.monitor('calc_gmfs')),
            operator.add, concurrent_tasks=self.oqparam.concurrent_tasks)

    def post_execute(self, result):
        logging.info('Exporting the result')
        gmfs_by_imt = {  # build N x R matrices
            imt: numpy.array(
                [result[tag][imt] for tag in self.tags]).T
            for imt in map(str, self.imts)}
        out = export(
            'gmf_xml', self.oqparam.export_dir,
            self.sitecol, self.tags, gmfs_by_imt)
        return out
