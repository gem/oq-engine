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

import operator
import logging

from openquake.risklib import workflows
from openquake.commonlib.general import import_all, CallableDict
from openquake.commonlib import readinput
from openquake.commonlib.parallel import apply_reduce
from openquake.commonlib.calculators import calc

calculators = CallableDict(operator.attrgetter('calculation_mode'))


class BaseCalculator(object):
    """
    To be subclassed.
    """
    def __init__(self, oqparam):
        self.oqparam = oqparam

    def run(self):
        """
        Run the calculation and return the exported files
        """
        self.pre_execute()
        result = self.execute()
        return self.post_execute(result)

    def core_func(*args):
        """
        Core routine running on the workers, usually set by the
        @core decorator.
        """
        raise NotImplementedError

    def pre_execute(self):
        """
        Initialization phase.
        """
        raise NotImplementedError(self.oqparam.calculation_mode)

    def execute(self):
        """
        Execution phase. Usually will run in parallel the core
        function and return a dictionary with the results.
        """
        raise NotImplementedError(self.oqparam.calculation_mode)

    def post_execute(self, result):
        """
        Post-processing phase of the aggregated output. It must be
        overridden with the export code. It will return a dictionary
        of output files.
        """
        raise NotImplementedError(self.oqparam.calculation_mode)


class BaseScenarioCalculator(BaseCalculator):
    """
    Base class for all risk scenario calculators
    """
    def pre_execute(self):
        logging.info('Reading the exposure')
        sitecol, self.assets_by_site = readinput.get_sitecol_assets(
            self.oqparam)

        logging.info('Computing the GMFs')
        gmvdict_by_site = calc.calc_gmvdict_by_site(self.oqparam, sitecol)

        logging.info('Preparing the risk input')
        self.riskmodel = readinput.get_risk_model(self.oqparam)
        self.riskinputs = []
        for site, gmvdict, assets in zip(
                sitecol, gmvdict_by_site, self.assets_by_site):
            self.riskinputs.append(
                workflows.HazardGetter([site.id], [gmvdict], [assets]))

    def execute(self):
        """
        Parallelize on the riskinputs and returns a dictionary of results.
        """
        return apply_reduce(
            self.core_func.__func__,
            (self.riskinputs, self.riskmodel),
            agg=operator.add,
            concurrent_tasks=self.oqparam.concurrent_tasks,
            weight=operator.attrgetter('weight'))


## now make sure the `calculators` dictionary is populated
import_all('openquake.commonlib.calculators')
