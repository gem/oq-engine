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
from openquake.hazardlib.calc.filters import IntegrationDistance
from openquake.hazardlib.calc.stochastic import sample_ebruptures, get_ebr_df


def main(params):
    # example with 2x2=4 realizations with weights .36, .24, .24, .16
    inp = read_input(params)
    print(inp)
    print(inp.gsim_lt.get_rlzs_by_gsim_trt())
    acc = AccumDict(accum=[])
    ebrs = sample_ebruptures(inp.groups, inp.cmakerdict)
    ne = sum(ebr.n_occ for ebr in ebrs)
    print('There are %d ruptures and %d events' % (len(ebrs), ne))
    df = get_ebr_df(ebrs, inp.cmakerdict)
    print(df.groupby('rlz').count())  # there are 8, 9, 11, 8 events per rlz
    for ebr in ebrs:
        cmaker = inp.cmakerdict[ebr.rupture.tectonic_region_type]
        gmf_dict, _ = GmfComputer(ebr, inp.sitecol, cmaker).compute_all()
        acc += gmf_dict
    print(pandas.DataFrame(acc))


if __name__ == '__main__':
    params = dict(maximum_distance=IntegrationDistance.new('200'),
                  imtls={'PGA': [0]},
                  source_model_file="source_model.xml",
                  area_source_discretization=10,
                  ses_seed=24,
                  ses_per_logic_tree_path=20,
                  investigation_time=1,
                  inputs=dict(site_model="site_model.csv",
                              gsim_logic_tree="gmpe_logic_tree.xml"))
    main(params)
