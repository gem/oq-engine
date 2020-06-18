# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2020 GEM Foundation
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
import numpy

from openquake.hazardlib.calc.gmf import GmfComputer
from openquake.hazardlib.gsim.base import ContextMaker
from openquake.hazardlib.calc.stochastic import get_rup_array
from openquake.hazardlib.source.rupture import EBRupture
from openquake.commonlib import readinput, logictree, calc
from openquake.calculators import base, getters

U16 = numpy.uint16


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
        if 'rupture_model' not in oq.inputs:
            logging.warning(
                'There is no rupture_model, the calculator will just '
                'import data without performing any calculation')
            super().pre_execute()
            return
        self.rup = readinput.get_rupture(oq)
        self.gsims = readinput.get_gsims(oq)
        self.cmaker = ContextMaker('*', self.gsims,
                                   {'maximum_distance': oq.maximum_distance,
                                    'filter_distance': oq.filter_distance})
        super().pre_execute()
        if oq.inputs['rupture_model'].endswith('.csv'):
            base.import_rups(self.datastore, oq.inputs['rupture_model'])
        self.datastore['oqparam'] = oq
        self.store_rlz_info({})
        n_occ = numpy.array([oq.number_of_ground_motion_fields])
        ebr = EBRupture(self.rup, 0, 0, n_occ)
        ebr.e0 = 0
        rup_array = get_rup_array([ebr], self.src_filter()).array
        if len(rup_array) == 0:
            maxdist = oq.maximum_distance(
                self.rup.tectonic_region_type, self.rup.mag)
            raise RuntimeError('There are no sites within the maximum_distance'
                               ' of %s km from the rupture' % maxdist)
        calc.RuptureImporter(self.datastore).import_array(rup_array)
        self.computer = GmfComputer(
            ebr, self.sitecol, oq.imtls, self.cmaker, oq.truncation_level,
            oq.correl_model, self.amplifier)
        self.sig_eps_dt = getters.sig_eps_dt(self.oqparam.imtls)

    def init(self):
        gsim_lt = readinput.get_gsim_lt(self.oqparam)
        fake = logictree.FullLogicTree.fake(gsim_lt)
        self.realizations = fake.get_realizations()
        self.datastore['full_lt'] = fake

    def execute(self):
        """
        Compute the GMFs and return a dictionary gsim -> array(N, E, I)
        """
        arrays = []
        if 'rupture_model' not in self.oqparam.inputs:
            return ()
        n = self.oqparam.number_of_ground_motion_fields
        with self.monitor('computing gmfs'):
            ei = 0
            for g, gsim in enumerate(self.gsims):
                gmfa, sig, eps = self.computer.compute(gsim, n)
                lst = []
                for s, e in zip(sig.T, eps.T):  # shape (M, E) -> (E, M)
                    lst.append((ei, g) + tuple(s) + tuple(e))
                    ei += 1
                arrays.append(gmfa.transpose(1, 2, 0))  # shape (N, n, I)
        self.datastore['gmf_data/sigma_epsilon'] = numpy.array(
            lst, self.sig_eps_dt)
        return numpy.concatenate(arrays, axis=1)  # shape (N, E, I)

    def post_execute(self, gmfa):
        if len(gmfa) == 0:  # no rupture_model
            return
        with self.monitor('saving gmfs'):
            base.save_gmf_data(
                self.datastore, self.sitecol, gmfa,
                self.oqparam.imtls, self.datastore['events'])
