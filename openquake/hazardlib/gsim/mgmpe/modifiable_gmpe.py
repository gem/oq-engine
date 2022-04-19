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
import warnings
import numpy as np
from openquake.hazardlib.gsim.base import GMPE, registry, CoeffsTable
from openquake.hazardlib.contexts import STD_TYPES, get_mean_stds
from openquake.hazardlib.const import StdDev
from openquake.hazardlib import const
from openquake.hazardlib.imt import from_string
from openquake.hazardlib.const import IMC
from openquake.hazardlib.gsim.mgmpe.nrcan15_site_term import (
    NRCan15SiteTerm, BA08_AB06)

from openquake.hazardlib.gsim.nga_east import (
    TAU_EXECUTION, get_phi_ss, TAU_SETUP, PHI_SETUP, get_tau_at_quantile,
    get_phi_ss_at_quantile)
from openquake.hazardlib.gsim.usgs_ceus_2019 import get_stewart_2019_phis2s


IMT_DEPENDENT_KEYS = ["set_scale_median_vector",
                      "set_scale_total_sigma_vector",
                      "set_fixed_total_sigma"]

COEFF = {IMC.GMRotI50: [1, 1, 0.03, 0.04, 1],
         IMC.RANDOM_HORIZONTAL: [1, 1, 0.07, 0.11, 1.05],
         IMC.GREATER_OF_TWO_HORIZONTAL:
         [0.1, 1.117, 0.53, 1.165, 4.48, 1.195, 8.70, 1.266, 1.266],
         IMC.RotD50:
         [0.09, 1.009, 0.58, 1.028, 4.59, 1.042, 8.93, 1.077, 1.077]}

COEFF_PGA_PGV = {IMC.GMRotI50: [1, 0.02, 1, 1, 0.03, 1],
                 IMC.RANDOM_HORIZONTAL: [1, 0.07, 1.03],
                 IMC.GREATER_OF_TWO_HORIZONTAL: [1.117, 0, 1, 1, 0, 1],
                 IMC.RotD50: [1.009, 0, 1, 1, 0, 1]}


def sigma_model_alatik2015(self, ctx, imt, ergodic, tau_model, phi_ss_coetab,
                           tau_coetab):
    """
    This function uses the sigma model of Al Atik (2015) as the standard
    deviation of a specified GMPE
    """
    phi = get_phi_ss(imt, ctx.mag, phi_ss_coetab)
    if ergodic:
        phi_s2s = get_stewart_2019_phis2s(imt, ctx.vs30)
        phi = np.sqrt(phi ** 2. + phi_s2s ** 2.)
    tau = TAU_EXECUTION[tau_model](imt, ctx.mag, tau_coetab)
    std_total = np.sqrt(tau ** 2. + phi ** 2.)
    setattr(self, const.StdDev.TOTAL, std_total)
    setattr(self, const.StdDev.INTER_EVENT, tau)
    setattr(self, const.StdDev.INTRA_EVENT, phi)


def nrcan15_site_term(self, ctx, imt, kind):
    """
    This function adds a site term to GMMs missing it
    """
    C = NRCan15SiteTerm.COEFFS_BA08[imt]
    C2 = NRCan15SiteTerm.COEFFS_AB06r[imt]
    fa = BA08_AB06(kind, C, C2, ctx.vs30, imt, np.exp(self.mean))
    self.mean = np.log(np.exp(self.mean) * fa)


def horiz_comp_to_geom_mean(self, ctx, imt):
    """
    This function converts ground-motion obtained for a given description of
    horizontal component into ground-motion values for geometric_mean.
    The conversion equations used are from:
        - Beyer and Bommer (2006): for arithmetic mean, GMRot and random
        - Boore and Kishida (2017): for RotD50
    """

    # Get the definition of the horizontal component using in the original GMM
    horcom = self.gmpe.DEFINED_FOR_INTENSITY_MEASURE_COMPONENT

    # IMT period
    T = imt.period

    # Get the string defining the horizontal component
    comp = str(horcom).split('.')[1]

    # List of the horizontal component definitions that can be converted into
    # geometric mean
    tmp = ['GMRotI50', 'RANDOM_HORIZONTAL',
           'GREATER_OF_TWO_HORIZONTAL', 'RotD50']

    # Apply the conversion
    if comp in tmp:
        # Conversion coefficients
        C = COEFF[horcom]
        C_PGA_PGV = COEFF_PGA_PGV[horcom]

        imt_name = imt.__repr__()
        if imt_name == 'PGA':
            conv_median = C_PGA_PGV[0]
            conv_sigma = C_PGA_PGV[1]
            rstd = C_PGA_PGV[2]
        elif imt_name == 'PGV':
            conv_median = C_PGA_PGV[3]
            conv_sigma = C_PGA_PGV[4]
            rstd = C_PGA_PGV[5]
        else:
            if comp in ['RotD50', 'GREATER_OF_TWO_HORIZONTAL']:
                term1 = C[1] + (C[3]-C[1]) / np.log(C[2]/C[0])*np.log(T/C[0])
                term2 = C[3] + (C[5]-C[3]) / np.log(C[4]/C[2])*np.log(T/C[2])
                term3 = C[5] + (C[7]-C[5]) / np.log(C[6]/C[4])*np.log(T/C[4])
                term4 = C[8]
                tmp_max = np.maximum(np.minimum(term1, term2),
                                     np.minimum(term3, term4))
                conv_median = np.maximum(C[1], tmp_max)
                conv_sigma = 0
                rstd = 1
            else:
                if T <= 0.15:
                    conv_median = C[0]
                    conv_sigma = C[2]
                elif T > 0.8:
                    conv_median = C[1]
                    conv_sigma = C[3]
                else:
                    conv_median = (C[0] + (C[1]-C[0]) *
                                   np.log10(T/0.15)/np.log10(0.8/0.15))
                    conv_sigma = (C[2] + (C[3]-C[2]) *
                                  np.log10(T/0.15)/np.log10(0.8/0.15))
                rstd = C[4]
    elif comp in ['GEOMETRIC_MEAN']:
        conv_median = 1
        conv_sigma = 0
        rstd = 1
    else:
        conv_median = 1
        conv_sigma = 0
        rstd = 1
        msg = f'Conversion not applicable for {comp}'
        warnings.warn(msg, UserWarning)

    # Original total STD
    total_stddev = getattr(self, const.StdDev.TOTAL)

    # Converted values
    std = ((total_stddev**2-conv_sigma**2)/rstd**2)**0.5
    self.mean = np.log(np.exp(self.mean)/conv_median)
    setattr(self, const.StdDev.TOTAL, std)


def add_between_within_stds(self, ctx, imt, with_betw_ratio):
    """
    This adds the between and within standard deviations to a model which has
    only the total standatd deviation. This function requires a ratio between
    the within-event standard deviation and the between-event one.

    :param with_betw_ratio:
        The ratio between the within and between-event standard deviations
    """
    total = getattr(self, StdDev.TOTAL)
    between = (total**2 / (1 + with_betw_ratio**2))**0.5
    within = with_betw_ratio * between
    setattr(self, 'DEFINED_FOR_STANDARD_DEVIATION_TYPES',
            {StdDev.TOTAL, StdDev.INTRA_EVENT, StdDev.INTER_EVENT})
    setattr(self, StdDev.INTER_EVENT, between)
    setattr(self, StdDev.INTRA_EVENT, within)


def apply_swiss_amplification(self, ctx, imt):
    """
    Adds amplfactor to mean
    """
    self.mean += ctx.amplfactor


def set_between_epsilon(self, ctx, imt, epsilon_tau):
    """
    :param epsilon_tau:
        the epsilon value used to constrain the between event variability
    """
    # index for the between event standard deviation
    self.mean += epsilon_tau * getattr(self, StdDev.INTER_EVENT)

    # set between event variability to 0
    setattr(self, StdDev.INTER_EVENT,
            np.zeros_like(getattr(self, StdDev.TOTAL)))

    # set total variability equal to the within-event one
    setattr(self, StdDev.TOTAL, getattr(self, StdDev.INTRA_EVENT))


def set_scale_median_scalar(self, ctx, imt, scaling_factor):
    """
    :param scaling_factor:
        Simple scaling factor (in linear space) to increase/decrease median
        ground motion, which applies to all IMTs
    """
    self.mean += np.log(scaling_factor)


def set_scale_median_vector(self, ctx, imt, scaling_factor):
    """
    :param scaling_factor:
        IMT-dependent median scaling factors (in linear space) as
        a CoeffsTable
    """
    C = scaling_factor[imt]
    self.mean += np.log(C["scaling_factor"])


def set_scale_total_sigma_scalar(self, ctx, imt, scaling_factor):
    """
    Scale the total standard deviations by a constant scalar factor
    :param scaling_factor:
        Factor to scale the standard deviations
    """
    total_stddev = getattr(self, StdDev.TOTAL)
    total_stddev *= scaling_factor
    setattr(self, StdDev.TOTAL, total_stddev)


def set_scale_total_sigma_vector(self, ctx, imt, scaling_factor):
    """
    Scale the total standard deviations by a IMT-dependent scalar factor
    :param scaling_factor:
        IMT-dependent total standard deviation scaling factors as a
        CoeffsTable
    """
    C = scaling_factor[imt]
    total_stddev = getattr(self, StdDev.TOTAL)
    total_stddev *= C["scaling_factor"]
    setattr(self, StdDev.TOTAL, total_stddev)


def set_fixed_total_sigma(self, ctx, imt, total_sigma):
    """
    Sets the total standard deviations to a fixed value per IMT
    :param total_sigma:
        IMT-dependent total standard deviation as a CoeffsTable
    """
    C = total_sigma[imt]
    shp = getattr(self, StdDev.TOTAL).shape
    setattr(self, StdDev.TOTAL, C["total_sigma"] + np.zeros(shp))


def add_delta_std_to_total_std(self, ctx, imt, delta):
    """
    :param delta:
        A delta std e.g. a phi S2S to be removed from total
    """
    total_stddev = getattr(self, StdDev.TOTAL)
    total_stddev = (total_stddev**2 + np.sign(delta) * delta**2)**0.5
    setattr(self, StdDev.TOTAL, total_stddev)


def set_total_std_as_tau_plus_delta(self, ctx, imt, delta):
    """
    :param delta:
        A delta std e.g. a phi SS to be combined with between std, tau.
    """
    tau = getattr(self, StdDev.INTER_EVENT)
    total_stddev = (tau**2 + np.sign(delta) * delta**2)**0.5
    setattr(self, StdDev.TOTAL, total_stddev)


def _dict_to_coeffs_table(input_dict, name):
    """
    Transform a dictionary of parameters organised by IMT into a
    coefficient table
    """
    coeff_dict = {}
    for key in input_dict:
        coeff_dict[from_string(key)] = {name: input_dict[key]}
    return {name: CoeffsTable.fromdict(coeff_dict)}


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
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {StdDev.TOTAL}
    DEFINED_FOR_TECTONIC_REGION_TYPE = ''
    DEFINED_FOR_REFERENCE_VELOCITY = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.mags = ()  # used in GMPETables

        # Create the original GMPE
        [(gmpe_name, kw)] = kwargs.pop('gmpe').items()
        self.params = kwargs  # non-gmpe parameters
        self.gmpe = registry[gmpe_name](**kw)
        self.set_parameters()
        self.mean = None

        # This is required by the `sigma_model_alatik2015` function
        key = 'sigma_model_alatik2015'
        if key in self.params:

            # Phi S2SS and ergodic param
            # self.params[key]['phi_s2ss'] = None
            self.params[key]['ergodic'] = self.params[key].get("ergodic", True)

            # Tau
            tau_model = self.params[key].get("tau_model", "global")
            if "tau_model" not in self.params:
                self.params[key]['tau_model'] = tau_model
            tau_quantile = self.params[key].get("tau_quantile", None)
            self.params[key]['tau_coetab'] = get_tau_at_quantile(
                TAU_SETUP[tau_model]["MEAN"],
                TAU_SETUP[tau_model]["STD"],
                tau_quantile)

            # Phi SS
            phi_model = self.params[key].get("phi_model", "global")
            if "phi_model" in self.params:
                del self.params[key]["phi_model"]
            phi_ss_quantile = self.params[key].get("phi_ss_quantile", None)
            self.params[key]['phi_ss_coetab'] = get_phi_ss_at_quantile(
                PHI_SETUP[phi_model], phi_ss_quantile)

        # Set params
        for key in self.params:
            if key in IMT_DEPENDENT_KEYS:
                # If the modification is period-dependent
                for subkey in self.params[key]:
                    if isinstance(self.params[key][subkey], dict):
                        self.params[key] = _dict_to_coeffs_table(
                            self.params[key][subkey], subkey)

    # called by the ContextMaker
    def set_tables(self, mags, imts):
        """
        :param mags: a list of magnitudes as strings
        :param imts: a list of IMTs as strings

        Set the .mean_table and .sig_table attributes on the underlying gmpe
        """
        if hasattr(self.gmpe, 'set_tables'):
            self.gmpe.set_tables(mags, imts)
            self.mags = mags

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """

        if ('set_between_epsilon' in self.params or
            'set_total_std_as_tau_plus_delta' in self.params) and (
                StdDev.INTER_EVENT not in
                self.gmpe.DEFINED_FOR_STANDARD_DEVIATION_TYPES):
            raise ValueError('The GMPE does not have between event std')

        if 'apply_swiss_amplification' in self.params:
            self.REQUIRES_SITES_PARAMETERS = frozenset(['amplfactor'])
            self.gmpe.REQUIRES_SITES_PARAMETERS = frozenset(['amplfactor'])

        ctx_rock = copy.copy(ctx)
        if 'nrcan15_site_term' in self.params:
            ctx_rock.vs30 = np.full_like(ctx.vs30, 760.)

        # Compute the original mean and standard deviations
        mean[:], sig[:], tau[:], phi[:] = get_mean_stds(
            self.gmpe, ctx_rock, imts, mags=self.mags)

        g = globals()
        for m, imt in enumerate(imts):

            # Save mean and stds
            kvs = list(zip(STD_TYPES, [sig[m], tau[m], phi[m]]))
            self.mean = mean[m]
            for key, val in kvs:
                setattr(self, key, val)

            # Apply sequentially the modifications
            for methname, kw in self.params.items():
                g[methname](self, ctx, imt, **kw)

            # Read the stored mean and stds
            mean[m] = self.mean
            for key, val in kvs:
                val[:] = getattr(self, key)
