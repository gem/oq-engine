# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2021 GEM Foundation
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
"""
Module exports :class:`AvgPoeGMPE`, which can create a composite of
multiple GMPEs with different weights. The syntax to use in the
logic tree file is as in this example::

              <logicTreeBranch branchID="b1">
                <uncertaintyModel>
                  [AvgPoeGMPE]
                  b1.AkkarBommer2010.weight=0.20
                  b2.CauzziFaccioli2008.weight=0.20
                  b3.ChiouYoungs2008.weight=0.20
                  b4.ToroEtAl2002SHARE.weight=0.20
                  b5.Campbell2003SHARE.weight=0.20
                </uncertaintyModel>
                <uncertaintyWeight>1</uncertaintyWeight>
              </logicTreeBranch>

This syntax is exactly the same as for an `AvgGMPE`; the difference is
in the semantic, since the `AvgGMPE` performs averages on the log(intensities)
while `AvgPoeGMPE` performs averages on the PoEs.
"""
import numpy as np
from openquake.hazardlib import const
from openquake.hazardlib.gsim.base import GMPE, registry


class AvgPoeGMPE(GMPE):
    """
    The AvgPoeGMPE returns mean PoEs from a set of underlying
    GMPEs with the given weights.
    """
    experimental = True

    #: Supported tectonic region type is undefined
    DEFINED_FOR_TECTONIC_REGION_TYPE = ""

    #: Supported intensity measure types are not set
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set()

    #: Supported intensity measure component is horizontal
    #: :attr:`~openquake.hazardlib.const.IMC.HORIZONTAL`,
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.HORIZONTAL

    #: Supported standard deviation type
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([const.StdDev.TOTAL])

    #: Required site parameters will be set from selected GMPES
    REQUIRES_SITES_PARAMETERS = set()

    #: Required rupture parameter will be set later
    REQUIRES_RUPTURE_PARAMETERS = set()

    #: Required distance metrics will be set by the GMPEs
    REQUIRES_DISTANCES = set()

    def __init__(self, **kwargs):
        """
        Instantiate a dictionary branch_name -> gmpe_name -> gmpe_params
        """
        super().__init__(**kwargs)
        weights = []
        self.gsims = []
        rrp = set()
        rd = set()
        rsp = set()
        def_for_stddevs = []
        for branchid, branchparams in kwargs.items():
            [(gsim_name, params)] = branchparams.items()
            weights.append(params.pop('weight'))
            gsim = registry[gsim_name](**params)
            rd.update(gsim.REQUIRES_DISTANCES)
            rsp.update(gsim.REQUIRES_SITES_PARAMETERS)
            rrp.update(gsim.REQUIRES_RUPTURE_PARAMETERS)
            def_for_stddevs.append(gsim.DEFINED_FOR_STANDARD_DEVIATION_TYPES)
            self.gsims.append(gsim)
        self.REQUIRES_DISTANCES = frozenset(rd)
        self.REQUIRES_SITES_PARAMETERS = frozenset(rsp)
        self.REQUIRES_RUPTURE_PARAMETERS = frozenset(rrp)
        # if the sets DEFINED_FOR_STANDARD_DEVIATION_TYPES of the underlying
        # gsims are all the same, then the AvgGMPE should use the same
        if all(d == def_for_stddevs[0] for d in def_for_stddevs[1:]):
            self.DEFINED_FOR_STANDARD_DEVIATION_TYPES = def_for_stddevs[0]
        self.weights = np.array(weights)

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """Do nothing: the work is done in get_poes"""
        sig[:] = 1E-10  # to stop the error for zero sigma
