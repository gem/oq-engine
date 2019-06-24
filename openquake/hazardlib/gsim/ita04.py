# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2013-2019 GEM Foundation
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

"""
Module exports :class:`ITA04Base`
"""
import os
import numpy as np
from openquake.hazardlib.gsim.gmpe_table import GMPETable
from openquake.hazardlib import const


class ITA04Base(GMPETable):
    """
    This class is an general class used to implement the GMPEs used for the
    2004 version of the national hazard model for Italy.
    """

    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set((const.StdDev.TOTAL,
                                                const.StdDev.INTER_EVENT,
                                                const.StdDev.INTRA_EVENT))

    def __init__(self, gmpe_table):
        """
        """
        super().__init__(gmpe_table=gmpe_table)

    def get_mean_and_stddevs(self, sctx, rctx, dctx, imt, stddev_types):
        """
        Returns the mean and standard deviations
        """
        print(rctx.mag)
        # Return Distance Tables
        imls = self._return_tables(rctx.mag, imt, "IMLs")
        # Get distance vector for the given magnitude
        idx = np.searchsorted(self.m_w, rctx.mag)
        dists = self.distances[:, 0, idx - 1]
        # Get mean and standard deviations
        mean = self._get_mean(imls, dctx, dists)
        stddevs = self.get_stddevs()
        return np.log(mean), stddevs

    def get_stddevs(self, mag, imt, stddev_types, num_sites):
        """
        """
        tau = self._get_tau(imt, mag)
        phi = self._get_phi(imt, mag)
        sigma = np.sqrt(tau ** 2. + phi ** 2.)
        stddevs = []
        for stddev_type in stddev_types:
            assert stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
            if stddev_type == const.StdDev.TOTAL:
                stddevs.append(sigma + np.zeros(num_sites))
            elif stddev_type == const.StdDev.INTRA_EVENT:
                stddevs.append(phi + np.zeros(num_sites))
            elif stddev_type == const.StdDev.INTER_EVENT:
                stddevs.append(tau + np.zeros(num_sites))
        return stddevs


class AmbraseysEtAl1996Normal(ITA04Base):
    """
    """
    TABLE_PATH = os.path.abspath("./ita04_tables/asb96_normal.hdf5")

    def __init__(self):
        if not self.TABLE_PATH:
            raise NotImplementedError("This ")
        super().__init__(gmpe_table=self.TABLE_PATH)
