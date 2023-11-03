# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2023 GEM Foundation
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
Module exports: :class:`ConditionalGMPE`
"""


from typing import Tuple
import numpy as np
from openquake.hazardlib import const
from openquake.hazardlib.imt import from_string
from openquake.hazardlib.gsim.base import GMPE, registry


class ConditionalGMPE(GMPE):
    """Base Class for a form of GMPE in which the output ground
    motion level is conditional upon other measures of ground motion.

    This class functions for two cases:

    1. The case that the conditioning ground motion values (e.g. PGA, Sa(T)
    etc.) are known a priori and input via the context array. If so, these must
    be specified in the `ctx` recarray with both the MEAN and TOTAL_STDDEV (the
    TOTAL_STDDEV can be 0), e.g. PGA_MEAN, PGA_TOTAL_STDDEV, SA(0.2)_MEAN,
    SA(0.2)_TOTAL_STDDEV etc. The IMT string must be such that it can be
    transformed into an IMT object via the `from_string` function. Optionally,
    the between- and within-event standard deviation of the input ground
    motions can also be specified using the same syntax, i.e.
    PGA_INTER_EVENT_STDDEV, SA(1.0)_INTRA_EVENT_STDDEV etc.

    2. The case that the conditioning groung motion values are not known a
    priori and must therefore be calculated using a GMPE, which the user passes
    as input to the function.

    If no conditioning ground motion values are input in `ctx` and no GMPE is
    specified then an error will be raised.
    """
    REQUIRES_SITES_PARAMETERS = set()
    REQUIRES_DISTANCES = set()
    REQUIRES_RUPTURE_PARAMETERS = set()
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set()
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = ''
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}
    DEFINED_FOR_TECTONIC_REGION_TYPE = ''
    DEFINED_FOR_REFERENCE_VELOCITY = None

    # Specific to the Conditional GMPE class. Should be a set
    # containing string representations of the required IMTs
    REQUIRES_IMTS = set()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if "gmpe" in kwargs:
            # Create the original GMPE
            [(gmpe_name, kw)] = kwargs.pop('gmpe').items()
            self.params = kwargs  # non-gmpe parameters
            g = globals()
            for k in self.params:
                if k not in g:
                    raise ValueError('Unknown %r in ModifiableGMPE' % k)
            self.gmpe = registry[gmpe_name](**kw)
            self.gmpe_table = hasattr(self.gmpe, 'gmpe_table')
            self.set_parameters()
        else:
            self.gmpe = None
            self.gmpe_table = None

    def get_conditioning_ground_motions(
        self,
        ctx: np.recarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Retreives the ground motions upon which the model
        is conditioned. If the MEAN and TOTAL_STDDEV of the ground
        motion are found in the ctx then these are taken directly,
        otherwise the mean and total standard deviation are determined
        from the specified GMPE
        """
        imt_dtypes = np.dtype([(imt, float) for imt in self.REQUIRES_IMTS])

        nimts = len(self.REQUIRES_IMTS)
        n = len(ctx)
        mean_gms = np.recarray(n, imt_dtypes)
        sigma_gms = np.recarray(n, imt_dtypes)
        tau_gms = np.recarray(n, imt_dtypes)
        phi_gms = np.recarray(n, imt_dtypes)

        for imt_string in self.REQUIRES_IMTS:
            # Get the mean ground motions and total standard deviations
            # for the IMT from the ctx if they are provided
            available_gms = []
            for imt_string in self.REQUIRES_IMTS:
                for param in ["MEAN", "TOTAL_STDDEV"]:
                    label = f"{imt_string}_{param}"
                    available_gms.append(label in ctx.dtype.names)
            if all(available_gms):
                # The required info about the ground motions
                # is in the ctx - therefore this can be taken directly
                for imt_string in self.REQUIRES_IMTS:
                    mean_gms[imt_string] = ctx[f"{imt_string}_MEAN"]
                    sigma_gms[imt_string] = ctx[f"{imt_string}_TOTAL_STDDEV"]
                    # Optionally, get the between and within-event stddev
                    if (f"{imt_string}_INTER_EVENT_STDDEV") in ctx.dtype.names:
                        tau_gms[imt_string] = ctx[
                            f"{imt_string}_INTER_EVENT_STDDEV"]
                    else:
                        tau_gms[imt_string] = np.zeros(n)
                    if (f"{imt_string}_INTRA_EVENT_STDDEV") in ctx.dtype.names:
                        phi_gms[imt_string] = ctx[
                            f"{imt_string}_INTRA_EVENT_STDDEV"]
                    else:
                        phi_gms[imt_string] = np.zeros(n)
            else:
                # Not conditioned on observations found in ctx, so
                # calculate from GMPE
                if self.gmpe is None:
                    raise ValueError("Conditioning ground motions must be "
                                     "specified in ctx or a GMPE must be "
                                     "provided")

                mean = np.zeros([nimts, n])
                sigma = np.zeros_like(mean)
                tau = np.zeros_like(mean)
                phi = np.zeros_like(mean)
                self.gmpe.compute(
                    ctx,
                    [from_string(imt) for imt in self.REQUIRES_IMTS],
                    mean,
                    sigma,
                    tau,
                    phi
                )
                for i, imt in enumerate(self.REQUIRES_IMTS):
                    mean_gms[imt] = np.exp(mean[i, :])
                    sigma_gms[imt] = sigma[i, :]
                    tau_gms[imt] = tau[i, :]
                    phi_gms[imt] = phi[i, :]
        return mean_gms, sigma_gms, tau_gms, phi_gms
