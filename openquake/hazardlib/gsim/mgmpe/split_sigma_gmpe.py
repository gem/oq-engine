# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
# 
# Copyright (C) 2019, GEM Foundation
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
Module :mod:`openquake.hazardlib.mgmpe.split_sigma_gmpe` implements
:class:`~openquake.hazardlib.mgmpe.SplitSigmaGMPE`
"""

import numpy as np
from openquake.hazardlib.gsim.base import GMPE, registry
from openquake.hazardlib import const


class SplitSigmaGMPE(GMPE):
    """
    This modified GMPE adds within event and between event stds to GMPE that
    do not originally contain these standard deviation types.

    :param string gmpe_name:
        The name of a GMPE class used for the calculation.
    :param within_absolute:
        A scalar defining the values of the within event standard deviation
    :param string corr_func:
        A scalar defining the values of the between event standard deviation
    """
    REQUIRES_SITES_PARAMETERS = set()
    REQUIRES_DISTANCES = set()
    REQUIRES_RUPTURE_PARAMETERS = set()
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set()
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = ''
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}
    DEFINED_FOR_TECTONIC_REGION_TYPE = ''
    DEFINED_FOR_REFERENCE_VELOCITY = None

    def __init__(self, gmpe_name, within_absolute=None, between_absolute=None,
                 **kwargs):
        super().__init__(gmpe_name=gmpe_name, within_absolute=within_absolute,
                         between_absolute=between_absolute, **kwargs)
        # Create the original GMPE
        self.gmpe = registry[gmpe_name]()
        self.set_parameters()

        # Set options for obtaining within and between stds
        self.between_absolute = between_absolute
        self.within_absolute = within_absolute

        # Set the supported stds
        self.DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
            const.StdDev.TOTAL,
            const.StdDev.INTER_EVENT,
            const.StdDev.INTRA_EVENT
        ])

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stds_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        # compute mean and standard deviation
        stds_total_type = [const.StdDev.TOTAL]
        mean, std_total = self.gmpe.get_mean_and_stddevs(
            sites, rup, dists, imt, stds_total_type)
        stddvs = self._get_stddvs(np.array(std_total[0]), stds_types)
        return mean, stddvs

    def _get_stddvs(self, total, stds_types):
        """
        This computes the between and within event std given the total std.

        :param total:
            A 1D :class:`numpy.ndarray` with the total standard deviation
            values.
        :param stds_types:
            A list with the type of std requested.
        :return:
            A list of 1D :class:`numpy.ndarray`
        """
        # Compute missing standard deviations
        new_stds = {'total': total}
        if np.isscalar(self.between_absolute):
            between = np.ones_like(total) * self.between_absolute
            if np.any(total - between < 0):
                raise ValueError('Between event std larger than total')
            within = np.sqrt(total**2 - between**2)
            new_stds['between'] = between
            new_stds['within'] = within
        elif np.isscalar(self.within_absolute):
            within = np.ones_like(total) * self.within_absolute
            if np.any(total - within < 0):
                raise ValueError('Within event std larger than total')
            between = np.sqrt(total**2 - within**2)
            new_stds['between'] = between
            new_stds['within'] = within
        else:
            pass
        stds = []
        for key in stds_types:
            if key == const.StdDev.TOTAL:
                stds.append(new_stds['total'])
            elif key == const.StdDev.INTER_EVENT:
                stds.append(new_stds['between'])
            elif key == const.StdDev.INTRA_EVENT:
                stds.append(new_stds['within'])
            else:
                raise ValueError('Unsupported std type')
        return stds
