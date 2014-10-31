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

import abc
import operator

import numpy

from openquake.risklib.workflows import RiskInput
from openquake.commonlib import readinput, general
from openquake.commonlib.parallel import apply_reduce

get_taxonomy = operator.attrgetter('taxonomy')
get_weight = operator.attrgetter('weight')
get_imt = operator.attrgetter('imt')


class BaseCalculator(object):
    """
    Abstract base class for all calculators
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, oqparam, monitor):
        self.oqparam = oqparam
        self.monitor = monitor
        self.monitor.write('operation pid time_sec memory_mb'.split())

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

    @abc.abstractmethod
    def pre_execute(self):
        """
        Initialization phase.
        """

    @abc.abstractmethod
    def execute(self):
        """
        Execution phase. Usually will run in parallel the core
        function and return a dictionary with the results.
        """

    @abc.abstractmethod
    def post_execute(self, result):
        """
        Post-processing phase of the aggregated output. It must be
        overridden with the export code. It will return a dictionary
        of output files.
        """


class BaseRiskCalculator(BaseCalculator):
    """
    Base class for all risk calculators. A risk calculator must set the
    attributes .riskmodel, .sitecol, .assets_by_site, .exposure
    .riskinputs in the pre_execute phase.
    """

    def pre_execute(self):
        """
        Set the attributes .riskmodel, .sitecol, .assets_by_site
        """
        self.riskmodel = readinput.get_risk_model(self.oqparam)
        self.exposure = readinput.get_exposure(self.oqparam)
        self.sitecol, self.assets_by_site = readinput.get_sitecol_assets(
            self.oqparam, self.exposure)

    def build_riskinputs(self, hazards_by_imt):
        """
        :param hazards_by_imt:
            a dictionary IMT -> numpy array of length equal to the
            number of hazard sites associated to the given assets
        :returns:
            a list of RiskInputs objects, sorted by IMT.
        """
        riskinputs = []
        idx_weight_pairs = [(i, len(assets))
                            for i, assets in enumerate(self.assets_by_site)]
        blocks = general.split_in_blocks(
            idx_weight_pairs,
            self.oqparam.concurrent_tasks + 1,
            weight=operator.itemgetter(1))
        for block in blocks:
            idx = numpy.array([idx for idx, _weight in block])
            groups = [general.group(assets, key=get_taxonomy)
                      for assets in self.assets_by_site[idx]]
            for imt, hazards_by_site in hazards_by_imt.iteritems():
                riskinputs.append(RiskInput(imt, hazards_by_site[idx], groups))
        return sorted(riskinputs, key=get_imt)

    def execute(self):
        """
        Parallelize on the riskinputs and returns a dictionary of results.
        Require a `.core_func` to be defined with signature
        (riskinputs, riskmodel, monitor).
        """
        monitor = self.monitor.copy(self.core_func.__name__)
        return apply_reduce(
            self.core_func.__func__,
            (self.riskinputs, self.riskmodel, monitor),
            agg=operator.add,
            concurrent_tasks=self.oqparam.concurrent_tasks,
            weight=get_weight, key=get_imt)
