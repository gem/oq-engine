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

dirname = os.path.dirname(__file__)
BASE_PATH = os.path.join(dirname, 'ita04_tables')


class ITA04Base(GMPETable):
    """
    This class is an general class used to implement the GMPEs used for the
    2004 version of the national hazard model for Italy.
    """
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set((const.StdDev.TOTAL,
                                                const.StdDev.INTER_EVENT,
                                                const.StdDev.INTRA_EVENT))

    def get_mean_and_stddevs(self, sctx, rctx, dctx, imt, stddev_types):
        """
        Returns the mean and standard deviations
        """
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
    gmpe_table = os.path.join(BASE_PATH, "asb96_normal.hdf5")


class AmbraseysEtAl1996Reverse(ITA04Base):
    gmpe_table = os.path.join(BASE_PATH, "asb96_reverse.hdf5")


class AmbraseysEtAl1996Strike(ITA04Base):
    gmpe_table = os.path.join(BASE_PATH, "asb96_strike.hdf5")


class AmbraseysEtAl1996Undef(ITA04Base):
    gmpe_table = os.path.join(BASE_PATH, "asb96_undef.hdf5")


class SabettaPugliese1996Normal(ITA04Base):
    gmpe_table = os.path.join(BASE_PATH, "sp96_normal.hdf5")


class SabettaPugliese1996Reverse(ITA04Base):
    gmpe_table = os.path.join(BASE_PATH, "sp96_reverse.hdf5")


class SabettaPugliese1996Strike(ITA04Base):
    gmpe_table = os.path.join(BASE_PATH, "sp96_strike.hdf5")


class SabettaPugliese1996Undef(ITA04Base):
    gmpe_table = os.path.join(BASE_PATH, "sp96_undef.hdf5")


class REG1(ITA04Base):
    gmpe_table = os.path.join(BASE_PATH, "reg1.hdf5")


class REG2(ITA04Base):
    gmpe_table = os.path.join(BASE_PATH, "reg2.hdf5")


class REG3(ITA04Base):
    gmpe_table = os.path.join(BASE_PATH, "reg3.hdf5")


class VULC30bar(ITA04Base):
    gmpe_table = os.path.join(BASE_PATH, "vulc30bar.hdf5")


class VULC50bar(ITA04Base):
    gmpe_table = os.path.join(BASE_PATH, "vulc50bar.hdf5")
