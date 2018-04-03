# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2018 GEM Foundation
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

from openquake.calculators import base
from openquake.commonlib import readinput
from openquake.hazardlib.calc.gmf import ground_motion_fields
from openquake.calculators.export import export


@base.calculators.add('my_scenario')
class MyScenarioCalculator(base.BaseCalculator):
    def pre_execute(self):
        self.sitecol = readinput.get_site_collection(self.oqparam)
        [self.gsim] = readinput.get_gsims(self.oqparam)
        self.imts = readinput.get_imts(self.oqparam)
        self.rupture = readinput.get_rupture(self.oqparam)
        self.etags = [  # used in the export phase
            'etag%d' % i
            for i in range(self.oqparam.number_of_ground_motion_fields)]

    def execute(self):
        gmfs_by_imt = ground_motion_fields(
            self.rupture, self.sitecol, self.imts, self.gsim,
            self.oqparam.truncation_level,
            self.oqparam.number_of_ground_motion_fields,
            correlation_model=readinput.get_correl_model(self.oqparam),
            seed=self.oqparam.random_seed)
        return gmfs_by_imt

    def post_execute(self, result):
        result = {str(imt): gmvs for imt, gmvs in result.items()}
        out = export('gmf_xml', self.oqparam.export_dir, self.sitecol,
                     self.etags, result)
        return out
