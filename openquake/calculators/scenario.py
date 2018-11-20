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
from openquake.hazardlib.source.rupture import (EBRupture, get_eids_by_rlz)
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
        oq = self.oqparam
        cinfo = source.CompositionInfo.fake(readinput.get_gsim_lt(oq))
        self.datastore['csm_info'] = cinfo
        if 'rupture_model' not in oq.inputs:
            logging.warn('There is no rupture_model, the calculator will just '
                         'import data without performing any calculation')
            super().pre_execute()
            return
        self.rup = readinput.get_rupture(oq)
        self.gsims = readinput.get_gsims(oq)
        R = len(self.gsims)
        self.cmaker = ContextMaker(self.gsims, oq.maximum_distance,
                                   {'filter_distance': oq.filter_distance})
        super().pre_execute()
        self.datastore['oqparam'] = oq
        self.rlzs_assoc = cinfo.get_rlzs_assoc()
        rlzs_by_gsim = self.rlzs_assoc.get_rlzs_by_gsim(0)
        E = oq.number_of_ground_motion_fields
        events = numpy.zeros(E * R, readinput.stored_event_dt)
        n_occ = numpy.array([E])
        for rlz, eids in get_eids_by_rlz(
                n_occ, rlzs_by_gsim, 1, self.rup.serial).items():
            events[rlz * E: rlz * E + E]['eid'] = eids
            events[rlz * E: rlz * E + E]['rlz'] = rlz
        ebr = EBRupture(self.rup, 0, 0, self.sitecol.sids, n_occ)
        self.datastore['events'] = events
        rupser = calc.RuptureSerializer(self.datastore)
        rupser.save([ebr], len(self.gsims))
        rupser.close()
        self.computer = GmfComputer(
            ebr, self.sitecol, oq.imtls, self.cmaker, oq.truncation_level,
            oq.correl_model)

    def init(self):
        pass

    def execute(self):
        """
        Compute the GMFs and return a dictionary gsim -> array(N, E, I)
        """
        self.gmfa = collections.OrderedDict()
        if 'rupture_model' not in self.oqparam.inputs:
            return self.gmfa
        with self.monitor('computing gmfs'):
            E = self.oqparam.number_of_ground_motion_fields
            for gsim in self.gsims:
                gmfa = self.computer.compute(gsim, E)  # shape (I, N, E)
                self.gmfa[gsim] = gmfa.transpose(1, 2, 0)  # shape (N, E, I)
        return self.gmfa

    def post_execute(self, dummy):
        if self.gmfa:
            with self.monitor('saving gmfs', autoflush=True):
                base.save_gmf_data(
                    self.datastore, self.sitecol,
                    numpy.array(list(self.gmfa.values())), self.oqparam.imtls)
