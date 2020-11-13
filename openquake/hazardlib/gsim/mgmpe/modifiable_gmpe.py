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
from openquake.hazardlib.gsim.base import GMPE, registry, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import from_string

IMT_DEPENDENT_KEYS = ["set_scale_median_vector",
                      "set_scale_total_sigma_vector",
                      "set_fixed_total_sigma"]


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
        - 'apply_swiss_amplification' This applies intensity amplification
           factors to the mean intensity returned by the parent GMPE/IPE based
           on the input 'amplfactor' site parameter
    """
    REQUIRES_SITES_PARAMETERS = set()
    REQUIRES_DISTANCES = set()
    REQUIRES_RUPTURE_PARAMETERS = set()
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set()
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = ''
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}
    DEFINED_FOR_TECTONIC_REGION_TYPE = ''
    DEFINED_FOR_REFERENCE_VELOCITY = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Create the original GMPE
        [(gmpe_name, kw)] = kwargs.pop('gmpe').items()
        self.params = kwargs  # non-gmpe parameters
        self.gmpe = registry[gmpe_name](**kw)
        self.set_parameters()
        self.mean = None
        for key in self.params:
            if key in IMT_DEPENDENT_KEYS:
                # If the modification is period-dependent
                for subkey in self.params[key]:
                    if isinstance(self.params[key][subkey], dict):
                        self.params[key] = self._dict_to_coeffs_table(
                            self.params[key][subkey], subkey)

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        working_std_types = copy.copy(stddev_types)

        if ('set_between_epsilon' in self.params or
                'set_total_std_as_tau_plus_delta' in self.params):
            if (const.StdDev.INTER_EVENT not in
                    self.gmpe.DEFINED_FOR_STANDARD_DEVIATION_TYPES):
                raise ValueError('The GMPE does not have between event std')
            working_std_types.append(const.StdDev.INTER_EVENT)
            working_std_types.append(const.StdDev.INTRA_EVENT)
            working_std_types.append(const.StdDev.TOTAL)

        if 'apply_swiss_amplification' in self.params:
            self.REQUIRES_SITES_PARAMETERS = frozenset(['amplfactor'])

        # Compute the original mean and standard deviations
        omean, ostds = self.gmpe.get_mean_and_stddevs(
            sites, rup, dists, imt, working_std_types)

        # Save the stds
        for key, val in zip(working_std_types, ostds):
            setattr(self, key, val)
        self.mean = omean

        # Apply sequentially the modifications
        for methname, kw in self.params.items():
            getattr(self, methname)(sites, rup, dists, imt, **kw)

        # Return the standard deviation types as originally requested
        outs = []
        for key in stddev_types:
            outs.append(getattr(self, key))

        return self.mean, outs

    def apply_swiss_amplification(self, sites, rup, dists, imt):
        """
        Adds amplfactor to mean
        """
        self.mean = self.mean + sites.amplfactor

    def set_between_epsilon(self, sites, rup, dists, imt, epsilon_tau):
        """
        :param epsilon_tau:
            the epsilon value used to constrain the between event variability
        """
        # Index for the between event standard deviation
        key = const.StdDev.INTER_EVENT
        self.mean = self.mean + epsilon_tau * getattr(self, key)

        # Set between event variability to 0
        keya = const.StdDev.TOTAL
        setattr(self, key, np.zeros_like(getattr(self, keya)))

        # Set total variability equal to the within-event one
        keyb = const.StdDev.INTRA_EVENT
        setattr(self, keya, getattr(self, keyb))

    def set_scale_median_scalar(self, sites, rup, dists, imt, scaling_factor):
        """
        :param scaling_factor:
            Simple scaling factor (in linear space) to increase/decrease median
            ground motion, which applies to all IMTs
        """
        self.mean += np.log(scaling_factor)

    def set_scale_median_vector(self, sites, rup, dists, imt, scaling_factor):
        """
        :param scaling_factor:
            IMT-dependent median scaling factors (in linear space) as
            a CoeffsTable
        """
        C = scaling_factor[imt]
        self.mean += np.log(C["scaling_factor"])

    def set_scale_total_sigma_scalar(self, sites, rup, dists, imt,
                                     scaling_factor):
        """
        Scale the total standard deviations by a constant scalar factor
        :param scaling_factor:
            Factor to scale the standard deviations
        """
        total_stddev = getattr(self, const.StdDev.TOTAL)
        total_stddev *= scaling_factor
        setattr(self, const.StdDev.TOTAL, total_stddev)

    def set_scale_total_sigma_vector(self, sites, rup, dists, imt,
                                     scaling_factor):
        """
        Scale the total standard deviations by a IMT-dependent scalar factor
        :param scaling_factor:
            IMT-dependent total standard deviation scaling factors as a
            CoeffsTable
        """
        C = scaling_factor[imt]
        total_stddev = getattr(self, const.StdDev.TOTAL)
        total_stddev *= C["scaling_factor"]
        setattr(self, const.StdDev.TOTAL, total_stddev)

    def set_fixed_total_sigma(self, sites, rup, dists, imt, total_sigma):
        """
        Sets the total standard deviations to a fixed value per IMT
        :param total_sigma:
            IMT-dependent total standard deviation as a CoeffsTable
        """
        C = total_sigma[imt]
        shp = getattr(self, const.StdDev.TOTAL).shape
        setattr(self, const.StdDev.TOTAL, C["total_sigma"] + np.zeros(shp))

    def add_delta_std_to_total_std(self, sites, rup, dists, imt, delta):
        """
        :param delta:
            A delta std e.g. a phi S2S to be removed from total
        """
        total_stddev = getattr(self, const.StdDev.TOTAL)
        total_stddev = (total_stddev**2 + np.sign(delta) * delta**2)**0.5
        setattr(self, const.StdDev.TOTAL, total_stddev)

    def set_total_std_as_tau_plus_delta(self, sites, rup, dists, imt, delta):
        """
        :param delta:
            A delta std e.g. a phi SS to be combined with between std, tau.
        """
        tau = getattr(self, const.StdDev.INTER_EVENT)
        total_stddev = (tau**2 + np.sign(delta) * delta**2)**0.5
        setattr(self, const.StdDev.TOTAL, total_stddev)

    @staticmethod
    def _dict_to_coeffs_table(input_dict, name):
        """
        Transform a dictionary of parameters organised by IMT into a
        coefficient table
        """
        coeff_dict = {}
        for key in input_dict:
            coeff_dict[from_string(key)] = {name: input_dict[key]}
        return {name: CoeffsTable(sa_damping=5, table=coeff_dict)}
