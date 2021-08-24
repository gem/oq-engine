# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2021, GEM Foundation
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
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import pandas
from openquake.baselib.general import AccumDict
from openquake.hazardlib import read_input
from openquake.hazardlib.calc.gmf import GmfComputer
from openquake.hazardlib.calc.filters import MagDepDistance
from openquake.hazardlib.calc.stochastic import sample_ebruptures


def main(params):
    inp = read_input(params)
    print(inp)
    print(inp.gsim_lt.get_rlzs_by_gsim_trt())
    acc = AccumDict(accum=[])
    for ebr in sample_ebruptures(inp.groups, inp.cmakerdict):
        cmaker = inp.cmakerdict[ebr.rupture.tectonic_region_type]
        gmf_dict, _ = GmfComputer(ebr, inp.sitecol, cmaker).compute_all()
        acc += gmf_dict
    print(pandas.DataFrame(acc))


if __name__ == '__main__':
    params = dict(maximum_distance=MagDepDistance.new('300'),
                  imtls={'PGA': [0]},
                  source_model_file="source_model.xml",
                  area_source_discretization=10,
                  ses_seed=42,
                  investigation_time=5,
                  site_model_file="site_model.csv",
                  gsim_logic_tree_file="gmpe_logic_tree.xml")
    main(params)
