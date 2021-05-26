# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2018-2021 GEM Foundation
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
Module exports :class:`AvgGMPE`, which can create a composite of
multiple GMPEs with different weights. The syntax to use in the
logic tree file is as in this example::

              <logicTreeBranch branchID="b1">
                <uncertaintyModel>
                  [AvgGMPE]
                  b1.AkkarBommer2010.weight=0.20
                  b2.CauzziFaccioli2008.weight=0.20
                  b3.ChiouYoungs2008.weight=0.20
                  b4.ToroEtAl2002SHARE.weight=0.20
                  b5.Campbell2003SHARE.weight=0.20
                </uncertaintyModel>
                <uncertaintyWeight>1</uncertaintyWeight>
              </logicTreeBranch>
"""
import inspect
import numpy
from openquake.hazardlib import const
from openquake.hazardlib.gsim.base import GMPE, registry


class AvgGMPE(GMPE):
    """
    The AvgGMPE returns mean and stddevs from a set of underlying
    GMPEs with the given weights.
    """
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
            gsim_cls = registry[gsim_name]
            sig = inspect.signature(gsim_cls.__init__)
            if list(sig.parameters) == ['self']:  # trivial signature
                gsim = gsim_cls()
            else:
                gsim = gsim_cls(**params)
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
        self.weights = numpy.array(weights)

    def get_mean_and_stddevs(self, sctx, rctx, dctx, imt, stddev_types):
        """
        Call the underlying GMPEs and return the weighted mean and stddev
        """
        means = []
        std2 = [[] for _ in stddev_types]
        for g, gsim in enumerate(self.gsims):
            mean, stddevs = gsim.get_mean_and_stddevs(
                sctx, rctx, dctx, imt, stddev_types)
            means.append(mean)
            for s, stddev in enumerate(stddevs):
                std2[s].append(stddev**2)
        mean = self.weights @ means
        stddevs = [numpy.sqrt(self.weights @ s) for s in std2]
        return mean, stddevs
