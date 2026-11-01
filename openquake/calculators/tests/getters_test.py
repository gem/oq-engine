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

from pathlib import Path
import numpy
import pytest
from openquake.baselib import hdf5
from openquake.baselib.performance import Monitor
from openquake.commonlib.oqvalidation import OqParam
from openquake.hazardlib import logictree
from openquake.hazardlib.geo import Point
from openquake.hazardlib.gsim_lt import GsimLogicTree
from openquake.hazardlib.site import Site
from openquake.hazardlib.scalerel import WC1994
from openquake.hazardlib.map_array import rates_dt
from openquake.hazardlib.calc.stochastic import get_rup_array
from openquake.hazardlib.source.rupture import get_planar, EBRupture
from openquake.calculators import classical, getters
from openquake.qa_tests_data.event_based import case_16


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


def test_ebruptures_preserve_tectonic_regions(tmp_path):
    case = Path(case_16.__file__).parent
    gsim_lt = GsimLogicTree(str(case / 'gmpe_logic_tree.xml'))
    trts = list(gsim_lt.values)
    assert len(trts) > 1
    site = Site(Point(0., 0.), vs30=760., z1pt0=100., z2pt5=1.)
    ebrs = []
    for i, trt in enumerate(trts):
        rup = get_planar(site, WC1994(), 6., 1., 0., 45., 90., trt)
        # Include a source-model index in the low bits of trt_smr.
        ebrs.append(EBRupture(
            rup, trt_smr=i * 2**24 + 7, id=i, seed=42))
    aw = get_rup_array(ebrs, lambda mag: 1000.)
    aw.array['geom_id'] = numpy.arange(len(ebrs))
    with hdf5.File(str(tmp_path / 'ruptures.hdf5'), 'w') as dstore:
        dstore['full_lt/gsim_lt'] = gsim_lt
        dstore['full_lt'].attrs['trts'] = hdf5.array_of_vstr(trts)
        dstore['ruptures'] = aw.array
        dstore.save_vlen('rupgeoms', [numpy.float32(g) for g in aw.geom])
        extracted = getters.get_ebruptures(dstore)
    assert [ebr.tectonic_region_type for ebr in extracted] == trts
    assert [ebr.trt_smr for ebr in extracted] == [
        ebr.trt_smr for ebr in ebrs]
