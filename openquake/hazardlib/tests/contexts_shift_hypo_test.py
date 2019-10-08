# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2019 GEM Foundation
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

import os
import unittest
from openquake.commonlib import readinput
from openquake.hazardlib.const import TRT
from openquake.hazardlib.contexts import ContextMaker
from openquake.baselib import parallel
from openquake.hazardlib.calc.filters import SourceFilter
from openquake.hazardlib.calc.hazard_curve import calc_hazard_curves
from openquake.commonlib import readinput

BASE_PATH = os.path.join(os.path.dirname(__file__), 'data', 'context')


class ShiftHypoTestCase(unittest.TestCase):

    def test01(self):
        job_ini = os.path.join(BASE_PATH, 'job.ini')
        oq = readinput.get_oqparam(job_ini)
        assert oq.shift_hypo == True

        csm = readinput.get_composite_source_model(oq)
        lt = readinput.get_gsim_lt(oq)
        sitecol = readinput.get_site_collection(oq)
        gsims = lt.get_gsims(TRT.ACTIVE_SHALLOW_CRUST)
        src_filter = SourceFilter(sitecol, oq.maximum_distance)
        rlzs_assoc = csm.info.get_rlzs_assoc()
        ##
        for i, sm in enumerate(csm.source_models):
            for rlz in rlzs_assoc.rlzs_by_smodel[i]:
                gsim_by_trt = rlzs_assoc.gsim_by_trt[rlz.ordinal]
                hcurves = calc_hazard_curves(
                    sm.src_groups, src_filter, oq.imtls,
                    gsim_by_trt, oq.truncation_level,
                    parallel.Starmap.apply)
            print('rlz=%s, hcurves=%s' % (rlz, hcurves))
