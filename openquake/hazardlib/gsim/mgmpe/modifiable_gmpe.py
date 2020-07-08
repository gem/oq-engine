# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2020, GEM Foundation
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
Module :mod:`openquake.hazardlib.mgmpe.modifiable_gmpe` implements
:class:`~openquake.hazardlib.mgmpe.ModifiableGMPE`
"""

import copy
import numpy as np
from openquake.hazardlib.gsim.base import GMPE, registry
from openquake.hazardlib import const


class ModifiableGMPE(GMPE):
    """
    This is a fully configurable GMPE

    :param string gmpe_name:
        The name of a GMPE class used for the calculation.
    :param params:
        A dictionary where the key defines the required modification and the
        value is a list with the required parameters. The modifications
        currently supported are:
        - 'set_between_epsilon' This sets the epsilon of the between event
           variability i.e. the returned mean is the original + tau * episilon
           and sigma tot is equal to sigma_within
    """
    REQUIRES_SITES_PARAMETERS = set()
    REQUIRES_DISTANCES = set()
    REQUIRES_RUPTURE_PARAMETERS = set()
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set()
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = ''
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}
    DEFINED_FOR_TECTONIC_REGION_TYPE = ''
    DEFINED_FOR_REFERENCE_VELOCITY = None

    def __init__(self, gmpe_name, params=None, **kwargs):

        # Initialize the superclass
        super().__init__(gmpe_name=gmpe_name)

        # Create the original GMPE
        self.gmpe = registry[gmpe_name](**kwargs)
        self.set_parameters()

        self.params = params
        self.mean = None

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stds_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """

        working_std_types = copy.copy(stds_types)

        if 'set_between_epsilon' in [self.params[k]['meth'] for k in
                                     self.params]:
            if (const.StdDev.INTER_EVENT not in 
                    self.gmpe.DEFINED_FOR_STANDARD_DEVIATION_TYPES):
                raise ValueError('The GMPE does not have between event std')
            working_std_types.append(const.StdDev.INTER_EVENT)
            working_std_types.append(const.StdDev.INTRA_EVENT)

        # Compute the original mean and standard deviations
        omean, ostds = self.gmpe.get_mean_and_stddevs(sites, rup, dists, imt,
                                                      working_std_types)

        # Save the stds
        for key, val in zip(working_std_types, ostds):
            setattr(self, key, val)
        self.mean = omean

        # Apply sequentially the modifications
        for key in self.params:
            meth = getattr(self, self.params[key]['meth'])
            meth(self.params[key]['params'])

        # Return the standard deviation types as originally requested
        outs = []
        for key in stds_types:
            outs.append(getattr(self, key))

        return self.mean, outs

    def set_between_epsilon(self, params):
        """
        :param par:
            A list of parameters. In this case it contains the epsilon value
            used to constrain the between event variability
        """

        epsilon = params['epsilon_tau']

        # Index for the between event standard deviation
        key = const.StdDev.INTER_EVENT
        self.mean = self.mean + epsilon * getattr(self, key)

        # Set between event variability to 0
        keya = const.StdDev.TOTAL
        setattr(self, key, np.zeros_like(getattr(self, keya)))

        # Set total variability equal to the within-event one
        keyb = const.StdDev.INTRA_EVENT
        setattr(self, keya, getattr(self, keyb))
