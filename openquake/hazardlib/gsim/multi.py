# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2018-2025 GEM Foundation
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
Module exports :class:`MultiGMPE`, which can create a composite of
multiple GMPEs for different IMTs when passed a dictionary of ground motion
models organised by IMT type or by a string describing the association
"""
import numpy as np
from openquake.hazardlib import const, contexts
from openquake.hazardlib.gsim.base import GMPE, registry
from openquake.hazardlib import imt as imt_module

uppernames = '''
DEFINED_FOR_INTENSITY_MEASURE_TYPES
DEFINED_FOR_STANDARD_DEVIATION_TYPES
REQUIRES_SITES_PARAMETERS
REQUIRES_RUPTURE_PARAMETERS
REQUIRES_DISTANCES
'''.split()


class MultiGMPE(GMPE):
    """
    The MultiGMPE can call ground motions for various IMTs when instantiated
    with a dictionary of ground motion models organised by IMT or a string
    describing the association.
    In the case of spectral accelerations the period of the IMT must be
    defined explicitly and only SA for that period will be computed.
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

    #: Required site parameters will be set be selected GMPES
    REQUIRES_SITES_PARAMETERS = set()

    #: Required rupture parameter is magnitude, others will be set later
    REQUIRES_RUPTURE_PARAMETERS = {'mag'}

    #: Required distance metrics will be set by the GMPEs
    REQUIRES_DISTANCES = set()

    def __init__(self, **kwargs):
        """
        Instantiate with a dictionary of GMPEs organised by IMT
        """
        self.kwargs = {}
        for name in uppernames:
            setattr(self, name, set(getattr(self, name)))
        for imt, gsim_dic in kwargs.items():
            [(gsim_name, kw)] = gsim_dic.items()
            self.kwargs[imt] = gsim = registry[gsim_name](**kw)
            name = "SA" if imt.startswith("SA") else imt
            imt_factory = getattr(imt_module, name)
            if imt_factory not in gsim.DEFINED_FOR_INTENSITY_MEASURE_TYPES:
                raise ValueError("IMT %s not supported by %s" % (imt, gsim))
            for name in uppernames:
                getattr(self, name).update(getattr(gsim, name))

    def __iter__(self):
        yield from self.kwargs

    def __getitem__(self, imt):
        return self.kwargs[imt]

    def __len__(self):
        return len(self.kwargs)

    def __hash__(self):
        items = tuple((imt, str(gsim)) for imt, gsim in
                      sorted(self.kwargs.items()))
        return hash(items)

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        Call the get mean and stddevs of the GMPE for the respective IMT
        """
        gsims = [self.kwargs[imt.string] for imt in imts]
        mean[:], sig[:], tau[:], phi[:] = contexts.get_mean_stds(
            gsims, ctx, imts)
