# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2018 GEM Foundation
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
Module exports :class:`MultiGMPE`, which can create a composite of
multiple GMPEs for different IMTs when passed a dictionary of ground motion
models organised by IMT type or by a string describing the association
"""
import os
import re
from collections import OrderedDict
from openquake.hazardlib.gsim import get_available_gsims
from openquake.hazardlib.gsim.base import GMPE
from openquake.hazardlib.gsim.gmpe_table import GMPETable
from openquake.hazardlib import const
from openquake.hazardlib.imt import from_string


GSIM_LIST = get_available_gsims()


class MultiGMPE(GMPE):
    """
    The WrapperGMPE can call ground motions for various IMTs when instantiated
    with a dictionary of ground motion models organised by IMT or a string
    describing the association.

    In the case of spectral accelerations the period of the IMT must be
    defined explicitly and only SA for that period will be computed.
    """
    #: Supported tectonic region type is undefined
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.UNDEFINED

    #: Supported intensity measure types are not set
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set(())

    #: Supported intensity measure component is horizontal
    #: :attr:`~openquake.hazardlib.const.IMC.HORIZONTAL`,
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.HORIZONTAL

    #: Supported standard deviation type
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL
    ])

    #: Required site parameters will be set be selected GMPES
    REQUIRES_SITES_PARAMETERS = set(())

    #: Required rupture parameter is magnitude, others will be set by the GMPEs
    REQUIRES_RUPTURE_PARAMETERS = set(('mag', ))

    #: Required distance metrics will be set by the GMPEs
    REQUIRES_DISTANCES = set(())

    def __init__(self, gmpes_by_imt):
        """
        Instantiate with a dictionary of GMPEs organised by IMT
        """
        super().__init__()
        self.gmpes = OrderedDict([])
        if isinstance(gmpes_by_imt, str):
            gmpes_by_imt = self._gmpe_str_to_dict(gmpes_by_imt)
        for imt, gmpe in list(gmpes_by_imt.items()):
            # IMT should be a string
            gmpe_imt = from_string(imt)
            if gmpe.startswith("GMPETable"):
                # Assumes the format is
                # GMPETable(gmpe_table=path/to/table.hdf5)
                key, path = re.search(r"\((.*)\)", gmpe).group(1).split("=")
                if not os.path.isabs(path):
                    path = os.path.abspath(path)
                self.gmpes[gmpe_imt] = GMPETable(**dict([(key, path)]))
            else:
                self.gmpes[gmpe_imt] = GSIM_LIST[gmpe]()
            if gmpe_imt.__class__ not in self.gmpes[gmpe_imt].\
                    DEFINED_FOR_INTENSITY_MEASURE_TYPES:
                raise ValueError("IMT %s not supported by %s" % (imt, gmpe))
            self.DEFINED_FOR_INTENSITY_MEASURE_TYPES = (
                self.DEFINED_FOR_INTENSITY_MEASURE_TYPES |
                self.gmpes[gmpe_imt].DEFINED_FOR_INTENSITY_MEASURE_TYPES)
            self.DEFINED_FOR_STANDARD_DEVIATION_TYPES = (
                self.DEFINED_FOR_STANDARD_DEVIATION_TYPES |
                self.gmpes[gmpe_imt].DEFINED_FOR_STANDARD_DEVIATION_TYPES)
            self.REQUIRES_SITES_PARAMETERS = (
                self.REQUIRES_SITES_PARAMETERS |
                self.gmpes[gmpe_imt].REQUIRES_SITES_PARAMETERS)
            self.REQUIRES_RUPTURE_PARAMETERS = (
                self.REQUIRES_RUPTURE_PARAMETERS |
                self.gmpes[gmpe_imt].REQUIRES_RUPTURE_PARAMETERS)
            self.REQUIRES_DISTANCES = (self.REQUIRES_DISTANCES |
                                       self.gmpes[gmpe_imt].REQUIRES_DISTANCES)

    @staticmethod
    def _gmpe_str_to_dict(gmpes_by_imt):
        """
        Converts a string to a dictionary organised by IMT and GMPE
        """
        content = re.search(r"\{(.*)\}", gmpes_by_imt).group(1)
        gmpe_dict = []
        for keyval in content.split(","):
            imt_str, gmpe_str = keyval.split(":")
            gmpe_dict.append((imt_str.strip(), gmpe_str.strip()))
        return OrderedDict(gmpe_dict)

    @classmethod
    def from_string(cls, gmpes_by_imt):
        """
        Instantiated the GMPE from a string
        """
        gmpes_by_imt = cls._gmpe_str_to_dict(gmpes_by_imt)
        return cls(gmpes_by_imt=gmpes_by_imt)

    def get_mean_and_stddevs(self, sctx, rctx, dctx, imt, stddev_types):
        """
        Call the get mean and stddevs of the GMPE for the respective IMT
        """
        if imt not in self.gmpes:
            raise KeyError("IMT %s not defined for MultiGMPE" % str(imt))
        return self.gmpes[imt].get_mean_and_stddevs(sctx, rctx, dctx, imt,
                                                    stddev_types)
