# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2018 GEM Foundation
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
import collections
import logging
import numpy

from openquake.hazardlib.calc.gmf import GmfComputer
from openquake.hazardlib.gsim.base import ContextMaker
from openquake.commonlib import readinput, source, calc
from openquake.hazardlib.source.rupture import EBRupture
from openquake.calculators import base


@base.calculators.add('scenario')
class ScenarioCalculator(base.HazardCalculator):
    """
    Scenario hazard calculator
    """
    is_stochastic = True

    def pre_execute(self):
        """
        Read the site collection and initialize GmfComputer and seeds
        """
        super().pre_execute()
        oq = self.oqparam
        gsim_lt = readinput.get_gsim_lt(oq)
        cinfo = source.CompositionInfo.fake(gsim_lt)
        self.datastore['csm_info'] = cinfo
        self.datastore['oqparam'] = oq
        self.rlzs_assoc = cinfo.get_rlzs_assoc()
        if 'rupture_model' not in oq.inputs:
            logging.warn('There is no rupture_model, the calculator will just '
                         'import data without performing any calculation')
            return
        rup = readinput.get_rupture(oq)
        self.gsims = readinput.get_gsims(oq)
        trunc_level = oq.truncation_level
        correl_model = oq.get_correl_model()
        cmaker = ContextMaker(self.gsims, oq.maximum_distance,
                              oq.filter_distance)
        self.sitecol, dctx = cmaker.filter(self.sitecol, rup)
        n = oq.number_of_ground_motion_fields
        events = numpy.zeros(n, readinput.stored_event_dt)
        events['eid'] = numpy.arange(n)
        ebr = EBRupture(rup, self.sitecol.sids, events)
        self.datastore['events'] = ebr.events
        rupser = calc.RuptureSerializer(self.datastore)
        rupser.save([ebr])
        rupser.close()
        self.computer = GmfComputer(
            ebr, self.sitecol, oq.imtls, cmaker, trunc_level, correl_model)

    def init(self):
        pass

    def execute(self):
        """
        Compute the GMFs and return a dictionary gsim -> array(N, E, I)
        """
        self.gmfa = collections.OrderedDict()
        if 'rupture_model' not in self.oqparam.inputs:
            return self.gmfa
        with self.monitor('computing gmfs', autoflush=True):
            n = self.oqparam.number_of_ground_motion_fields
            for gsim in self.gsims:
                gmfa = self.computer.compute(gsim, n)  # shape (I, N, E)
                self.gmfa[gsim] = gmfa.transpose(1, 2, 0)  # shape (N, E, I)
        return self.gmfa

    def post_execute(self, dummy):
        if self.gmfa:
            with self.monitor('saving gmfs', autoflush=True):
                base.save_gmf_data(
                    self.datastore, self.sitecol,
                    numpy.array(list(self.gmfa.values())))
