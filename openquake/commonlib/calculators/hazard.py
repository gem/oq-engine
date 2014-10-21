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
import collections

import numpy

from openquake.hazardlib.calc.gmf import GmfComputer
from openquake.commonlib import readinput, parallel
from openquake.commonlib.general import AccumDict

from openquake.commonlib.calculators import calculator, core, BaseCalculator
from openquake.commonlib.export import export


@calculator.add('classical')
class ClassicalCalculator(BaseCalculator):
    """
    Classical PSHA calculator
    """


@calculator.add('event_based')
class EventBasedCalculator(BaseCalculator):
    """
    Event based PSHA calculator
    """


@calculator.add('disaggregation')
class DisaggregationCalculator(BaseCalculator):
    """
    Classical disaggregation PSHA calculator
    """

SESRupture = collections.namedtuple(
    'SESRupture', 'tag seed rupture')


@calculator.add('scenario')
class ScenarioCalculator(BaseCalculator):
    """
    Scenario hazard calculator
    """
    def pre_execute(self):
        logging.info('Reading the site collection')
        if 'exposure' in self.oqparam.inputs:
            self.sitecol, _assets = readinput.get_sitecol_assets(self.oqparam)
        else:
            self.sitecol = readinput.get_site_collection(self.oqparam)

        correl_model = readinput.get_correl_model(self.oqparam)
        rnd = random.Random(getattr(self.oqparam, 'random_seed', 42))
        imts = readinput.get_imts(self.oqparam)
        gsim = readinput.get_gsim(self.oqparam)
        trunc_level = getattr(self.oqparam, 'truncation_level', None)
        n_gmfs = getattr(self.oqparam, 'number_of_ground_motion_fields', 1)
        rupture = readinput.get_rupture(self.oqparam)

        self.tags = ['scenario-%010d' % i for i in xrange(
                     self.oqparam.number_of_ground_motion_fields)]
        self.sesruptures = [
            SESRupture(tag, rnd.randint(0, 2 ** 31 - 1), rupture)
            for tag in self.tags]
        computer = GmfComputer(rupture, self.sitecol, imts, [gsim],
                               trunc_level, correl_model)
        self.computer_seeds = [(computer, rnd.randint(0, 2 ** 31 - 1))
                               for _ in xrange(n_gmfs)]

    def execute(self):
        logging.info('Computing the GMFs')
        return parallel.apply_reduce(
            self.core, (self.sesruptures, self.sitecol), operator.add)

    def post_execute(self, result):
        gmfs_by_imt = {  # build N x R matrices
            imt: numpy.array([result[tag][imt] for tag in self.tags]).T
            for imt in self.imts}

        logging.info('Exporting the result')
        out = export(
            'gmf_xml', self.oqparam.export_dir,
            self.sitecol, self.tags, gmfs_by_imt)
        return [out]


@core(ScenarioCalculator)
def calc_gmfs(sesruptures, sitecol, imts, gsim, trunc_level, correl_model):
    """
    Computer several GMFs in parallel, one for each computer and seed.
    """
    res = AccumDict()  # imt -> gmf
    for sesrupture in sesruptures:
        computer = GmfComputer(sesrupture.rupture, sitecol, imts, [gsim],
                               trunc_level, correl_model)
        res += {sesrupture.tag: computer.compute(sesrupture.seed)}
    return res
