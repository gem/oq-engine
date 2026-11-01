# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2026 GEM Foundation
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

import numpy
import pytest
from openquake.baselib import hdf5
from openquake.baselib.performance import Monitor
from openquake.commonlib.oqvalidation import OqParam
from openquake.hazardlib import logictree
from openquake.hazardlib.map_array import rates_dt
from openquake.calculators import classical, getters


@pytest.mark.parametrize('fastmean', [False, True])
def test_empty_hazard_chunk(tmp_path, fastmean):
    oq = OqParam(calculation_mode='classical', concurrent_tasks='4',
                 intensity_measure_types_and_levels='{"PGA": [.1, .2]}',
                 investigation_time='1', poes='.1', mean='true',
                 use_rates='true', inputs={'job_ini': '<in-memory>'},
                 individual_rlzs='false' if fastmean else 'true')
    rates = numpy.array([(0, 0, 0, .2), (0, 1, 0, .1),
                         (2, 0, 0, .4), (2, 1, 0, .3)], rates_dt)
    with hdf5.File(str(tmp_path / 'rates.hdf5'), 'w') as dstore:
        dstore['oqparam'] = oq
        dstore['full_lt'] = logictree.FullLogicTree.fake().init()
        dstore['sitecol/sids'] = numpy.uint32([0, 2])
        classical._store(rates, 2, dstore)
        populated, empty = getters.map_getters(dstore)
        assert populated.sids.tolist() == [0, 2]
        assert empty.sids.tolist() == []
        for getter in (populated, empty):
            assert getter.init().shape == (getter.N, 2, 1)
            assert getter.init() is getter.array
            if fastmean:
                result = classical.fast_mean(getter)
            else:
                result = classical.postclassical(
                    getter, oq.hazard_stats(), True, None, Monitor())
            for maps in result.values():
                for pmap in maps:
                    assert pmap.array.shape[0] == getter.N
            numpy.testing.assert_allclose(
                result['hcurves-stats'][0].array[:, 0],
                -numpy.expm1(-getter.array[:, :, 0]), rtol=1E-6)
        assert empty.sid2idx == {}
