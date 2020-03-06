# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2020 GEM Foundation
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

import numpy as np
from openquake.hazardlib import const
from openquake.hazardlib.gsim.base import GMPE, registry, CoeffsTable


class ScalableGMPE(GMPE):
    """
    Implements a modifiable GMPE.

    :param gmpe_name:
        GMPE class that will be adjusted
    :param coeff_file:
        tab-delimited file of scaling factors per IMT, where first column is
        IMT. It includes a header.

    """

    # Parameters
    REQUIRES_SITES_PARAMETERS = set()
    REQUIRES_DISTANCES = set()
    REQUIRES_RUPTURE_PARAMETERS = set()
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = ''
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set()
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}
    DEFINED_FOR_TECTONIC_REGION_TYPE = ''
    DEFINED_FOR_REFERENCE_VELOCITY = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.coeff_file = kwargs.get('coeff_file')
        self.gmpe_name = kwargs['gmpe_name']
        self.gmpe = registry[self.gmpe_name]()
        self.set_parameters()

        with self.open(self.coeff_file) as myfile:
            data = myfile.read().decode('utf-8')
        self.COEFFTAB = CoeffsTable(table=data, sa_damping=5)

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stds_types):
        nsites = len(sites)
        stddevs = self.get_stddevs(rup.mag, imt, stds_types, nsites)
        coeff = self.COEFFTAB[imt]
        mean, _ = self.gmpe.get_mean_and_stddevs(sites, rup, dists, imt,
                                                 stds_types)
        mean += np.log10(coeff)
        return mean, stddevs
