# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2016 GEM Foundation
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
from openquake.commonlib import readinput
from openquake.calculators import base

U8 = numpy.uint8
U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32

gmv_dt = numpy.dtype([('sid', U16), ('eid', U32), ('imti', U8), ('gmv', F32)])


@base.calculators.add('scenario')
class ScenarioCalculator(base.HazardCalculator):
    """
    Scenario hazard calculator
    """
    is_stochastic = True

    def pre_execute(self):
        """
        Read the site collection and initialize GmfComputer, etags and seeds
        """
        super(ScenarioCalculator, self).pre_execute()
        trunc_level = self.oqparam.truncation_level
        correl_model = readinput.get_correl_model(self.oqparam)
        n_gmfs = self.oqparam.number_of_ground_motion_fields
        rupture = readinput.get_rupture(self.oqparam)
        self.gsims = readinput.get_gsims(self.oqparam)
        self.rlzs_assoc = readinput.get_rlzs_assoc(self.oqparam)
        maxdist = self.oqparam.maximum_distance['default']
        with self.monitor('filtering sites', autoflush=True):
            self.sitecol = filters.filter_sites_by_distance_to_rupture(
                rupture, maxdist, self.sitecol)
        if self.sitecol is None:
            raise RuntimeError(
                'All sites were filtered out! maximum_distance=%s km' %
                maxdist)
        self.etags = numpy.array(
            sorted(['scenario-%010d~ses=1' % i for i in range(n_gmfs)]),
            (bytes, 100))
        self.computer = GmfComputer(
            rupture, self.sitecol, self.oqparam.imtls, self.gsims,
            trunc_level, correl_model)

    def execute(self):
        """
        Compute the GMFs and return a dictionary gmf_by_etag
        """
        res = collections.defaultdict(list)
        rlzs_by_gsim = {gsim: self.rlzs_assoc[0, gsim] for gsim in self.gsims}
        with self.monitor('computing gmfs', autoflush=True):
            n = self.oqparam.number_of_ground_motion_fields
            for eid, imti, rlz, gmf_sids in self.computer.calcgmfs(
                    self.oqparam.random_seed, n, rlzs_by_gsim):
                for gmv, sid in zip(*gmf_sids):
                    res[rlz.ordinal].append((sid, eid, imti, gmv))
            return {rlzi: numpy.array(res[rlzi], gmv_dt) for rlzi in res}

    def post_execute(self, gmfa_by_rlzi):
        """
        :param gmfa: a dictionary rlzi -> gmfa
        """
        with self.monitor('saving gmfs', autoflush=True):
            for rlzi, gsim in enumerate(self.gsims):
                rlzstr = 'gmf_data/%04d' % rlzi
                self.datastore[rlzstr] = gmfa_by_rlzi[rlzi]
                self.datastore.set_attrs(rlzstr, gsim=str(gsim))
            self.datastore.set_nbytes('gmf_data')
