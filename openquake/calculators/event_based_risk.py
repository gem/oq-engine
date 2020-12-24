# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2020 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

import logging
import operator
import numpy

from openquake.baselib.general import AccumDict
from openquake.baselib.python3compat import zip, encode
from openquake.hazardlib.stats import set_rlzs_stats
from openquake.risklib import riskinput, riskmodels
from openquake.calculators import base, scenario_risk, post_risk
from openquake.calculators.export.loss_curves import get_loss_builder

U8 = numpy.uint8
U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32
F64 = numpy.float64
getweight = operator.attrgetter('weight')


@base.calculators.add('event_based_risk')
class EbrCalculator(scenario_risk.ScenarioRiskCalculator):
    """
    Event based risk calculator
    """
    precalc = 'event_based'
    accept_precalc = ['event_based', 'event_based_risk', 'ebrisk']

    def pre_execute(self):
        oq = self.oqparam
        if not oq.ground_motion_fields:
            return  # this happens in the reportwriter

        parent = self.datastore.parent
        if parent:
            self.datastore['full_lt'] = parent['full_lt']
            ne = len(parent['events'])
            logging.info('There are %d ruptures and %d events',
                         len(parent['ruptures']), ne)

        if oq.investigation_time and oq.return_periods != [0]:
            # setting return_periods = 0 disable loss curves
            eff_time = oq.investigation_time * oq.ses_per_logic_tree_path
            if eff_time < 2:
                logging.warning(
                    'eff_time=%s is too small to compute loss curves',
                    eff_time)
        super().pre_execute()
