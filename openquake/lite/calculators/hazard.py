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

import logging

from openquake.commonlib.readinput import (
    get_site_collection, get_sitecol_assets)

from openquake.lite.calculators import calculator, calc, BaseCalculator
from openquake.lite.export import export


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


@calculator.add('scenario')
class ScenarioCalculator(BaseCalculator):
    """
    Scenario hazard calculator
    """
    def pre_execute(self):
        logging.info('Reading the site collection')
        if 'exposure' in self.oqparam.inputs:
            self.sitecol, _assets = get_sitecol_assets(self.oqparam)
        else:
            self.sitecol = get_site_collection(self.oqparam)

    def execute(self):
        logging.info('Computing the GMFs')
        return calc.calc_gmfs(self.oqparam, self.sitecol)

    def post_execute(self, gmfs_by_imt):
        logging.info('Exporting the result')
        scenario_tags = ['scenario-%010d' % i for i in xrange(
                         self.oqparam.number_of_ground_motion_fields)]
        out = export(
            'gmf_xml', self.oqparam.export_dir,
            self.sitecol, scenario_tags, gmfs_by_imt)
        return [out]
