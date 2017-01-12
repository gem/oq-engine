# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2017 GEM Foundation
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
import numpy

from openquake.hazardlib.calc import filters
from openquake.hazardlib.calc.gmf import GmfComputer
from openquake.commonlib import readinput, source, calc
from openquake.calculators.export.hazard import gmv_dt
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
        super(ScenarioCalculator, self).pre_execute()
        oq = self.oqparam
        trunc_level = oq.truncation_level
        correl_model = oq.get_correl_model()
        rup = readinput.get_rupture(oq)
        rup.seed = self.oqparam.random_seed
        self.gsims = readinput.get_gsims(oq)
        maxdist = oq.maximum_distance['default']
        with self.monitor('filtering sites', autoflush=True):
            self.sitecol = filters.filter_sites_by_distance_to_rupture(
                rup, maxdist, self.sitecol)
        if self.sitecol is None:
            raise RuntimeError(
                'All sites were filtered out! maximum_distance=%s km' %
                maxdist)
        # eid, ses, occ, sample
        events = numpy.array(
            [(eid, 1, 1, 0)
             for eid in range(oq.number_of_ground_motion_fields)],
            calc.event_dt)
        rupture = calc.EBRupture(
            rup, self.sitecol.sids, events, 'single_rupture', 0, 0)
        self.datastore['ruptures/grp-00/0'] = rupture
        self.computer = GmfComputer(
            rupture, self.sitecol, oq.imtls, self.gsims,
            trunc_level, correl_model)
        gsim_lt = readinput.get_gsim_lt(oq)
        cinfo = source.CompositionInfo.fake(gsim_lt)
        self.datastore['csm_info'] = cinfo
        self.rlzs_assoc = cinfo.get_rlzs_assoc()

    def init(self):
        pass

    def execute(self):
        """
        Compute the GMFs and return a dictionary rlzi -> array gmv_dt
        """
        res = collections.defaultdict(list)
        sids = self.sitecol.sids
        self.gmfa = {}
        with self.monitor('computing gmfs', autoflush=True):
            n = self.oqparam.number_of_ground_motion_fields
            for i, gsim in enumerate(self.gsims):
                gmfa = self.computer.compute(gsim, n)
                self.gmfa[gsim] = gmfa
                for (imti, sid, eid), gmv in numpy.ndenumerate(gmfa):
                    res[i].append((sids[sid], eid, imti, gmv))
            return {rlzi: numpy.array(res[rlzi], gmv_dt) for rlzi in res}

    def post_execute(self, gmfa_by_rlzi):
        """
        :param gmfa: a dictionary rlzi -> gmfa
        """
        with self.monitor('saving gmfs', autoflush=True):
            for rlzi, gsim in enumerate(self.gsims):
                rlzstr = 'gmf_data/sm-0000/%04d' % rlzi
                self.datastore[rlzstr] = gmfa_by_rlzi[rlzi]
                self.datastore.set_attrs(rlzstr, gsim=str(gsim))
            self.datastore.set_nbytes('gmf_data')
