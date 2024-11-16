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

import numpy as np
from openquake.hazardlib.gsim.base import GMPE, registry, CoeffsTable
from openquake.hazardlib.const import StdDev
from openquake.hazardlib.imt import from_string
from openquake.hazardlib.gsim.mgmpe.nrcan15_site_term import (
    NRCan15SiteTerm, BA08_AB06)
from openquake.hazardlib.gsim.mgmpe.cy14_site_term import _get_cy14_site_term
from openquake.hazardlib.gsim.chiou_youngs_2014 import ChiouYoungs2014
from openquake.hazardlib.gsim.mgmpe.cb14_basin_term import _get_cb14_basin_term
from openquake.hazardlib.gsim.mgmpe.m9_basin_term import _apply_m9_basin_term

from openquake.hazardlib.gsim.nga_east import (
    TAU_EXECUTION, get_phi_ss, TAU_SETUP, PHI_SETUP, get_tau_at_quantile,
    get_phi_ss_at_quantile)
from openquake.hazardlib.gsim.usgs_ceus_2019 import get_stewart_2019_phis2s

IMT_DEPENDENT_KEYS = ["set_scale_median_vector",
                      "set_scale_total_sigma_vector",
                      "set_fixed_total_sigma"]


# ################ BEGIN FUNCTIONS MODIFYING mean_stds ################## #

def sigma_model_alatik2015(ctx, imt, me, si, ta, ph,
                           ergodic, tau_model, phi_ss_coetab, tau_coetab):
    """
    This function uses the sigma model of Al Atik (2015) as the standard
    deviation of a specified GMPE
    """
    phi = get_phi_ss(imt, ctx.mag, phi_ss_coetab)
    if ergodic:
        phi_s2s = get_stewart_2019_phis2s(imt, ctx.vs30)
        phi = np.sqrt(phi ** 2. + phi_s2s ** 2.)
    tau = TAU_EXECUTION[tau_model](imt, ctx.mag, tau_coetab)
    si[:] = np.sqrt(tau ** 2. + phi ** 2.)
    ta[:] = tau
    ph[:] = phi


def nrcan15_site_term(ctx, imt, me, si, ta, ph, kind):
    """
    This function adds the NRCan15 site term to GMMs requiring it
    """
    C = NRCan15SiteTerm.COEFFS_BA08[imt]
    C2 = NRCan15SiteTerm.COEFFS_AB06r[imt]
    exp_mean = np.exp(me)
    fa = BA08_AB06(kind, C, C2, ctx.vs30, imt, exp_mean)
    me[:] = np.log(exp_mean * fa)


def cy14_site_term(ctx, imt, me, si, ta, phi):
    """
    This function adds the CY14 site term to GMMs requiring it
    """
    C = ChiouYoungs2014.COEFFS[imt]
    fa = _get_cy14_site_term(C, ctx.vs30, me) # Ref mean must be in natural log
    me[:] += fa


def cb14_basin_term(ctx, imt, me, si, ta, phi):
    """
    This function adds the CB14 basin term to GMMs requiring it.
    """
    me[:] += _get_cb14_basin_term(imt, ctx)


def m9_basin_term(ctx, imt, me, si, ta, phi):
    """
    This function applies the M9 basin adjustment
    """
    me = _apply_m9_basin_term(ctx, imt, me)
    

def add_between_within_stds(ctx, imt, me, si, ta, ph, with_betw_ratio):
    """
    This adds the between and within standard deviations to a model which has
    only the total standard deviation. This function requires a ratio between
    the within-event standard deviation and the between-event one.

    :param with_betw_ratio:
        The ratio between the within and between-event standard deviations
    """
    ta[:] = (si**2 / (1 + with_betw_ratio**2))**0.5
    ph[:] = with_betw_ratio * ta


def apply_swiss_amplification(ctx, imt, me, si, ta, ph):
    """
    Adds amplfactor to mean
    """
    me[:] += ctx.amplfactor


def apply_swiss_amplification_sa(ctx, imt, me, si, ta, ph):
    """
    Adjust Swiss GMPEs to add amplification and correct intra-event residuals
    """

    if imt.period == 0.3:
        phis2s = ctx.ch_phis2s03
        phiss = ctx.ch_phiss03
        me[:] += ctx.ch_ampl03
    elif imt.period == 0.6:
        phis2s = ctx.ch_phis2s06
        phiss = ctx.ch_phiss06
        me[:] += ctx.ch_ampl06

    phi_star = np.sqrt(phis2s**2 + phiss**2)
    total_stddev_star = np.sqrt(ta**2 + phi_star**2)

    ph[:] = phi_star
    si[:] = total_stddev_star


def set_between_epsilon(ctx, imt, me, si, ta, ph, epsilon_tau):
    """
    :param epsilon_tau:
        the epsilon value used to constrain the between event variability
    """
    # index for the between event standard deviation
    me[:] += epsilon_tau * ta

    # set between event variability to 0
    ta[:] = 0

    # set total variability equal to the within-event one
    si[:] = ph


def set_scale_median_scalar(ctx, imt, me, si, ta, ph, scaling_factor):
    """
    :param scaling_factor:
        Simple scaling factor (in linear space) to increase/decrease median
        ground motion, which applies to all IMTs
    """
    me[:] += np.log(scaling_factor)


def set_scale_median_vector(ctx, imt, me, si, ta, ph, scaling_factor):
    """
    :param scaling_factor:
        IMT-dependent median scaling factors (in linear space) as
        a CoeffsTable
    """
    me[:] += np.log(scaling_factor[imt]["scaling_factor"])


def set_scale_total_sigma_scalar(ctx, imt, me, si, ta, ph, scaling_factor):
    """
    Scale the total standard deviations by a constant scalar factor
    :param scaling_factor:
        Factor to scale the standard deviations
    """
    si[:] *= scaling_factor


def set_scale_total_sigma_vector(ctx, imt, me, si, ta, ph, scaling_factor):
    """
    Scale the total standard deviations by a IMT-dependent scalar factor
    :param scaling_factor:
        IMT-dependent total standard deviation scaling factors as a
        CoeffsTable
    """
    si[:] *= scaling_factor[imt]["scaling_factor"]


def set_fixed_total_sigma(ctx, imt, me, si, ta, ph, total_sigma):
    """
    Sets the total standard deviations to a fixed value per IMT
    :param total_sigma:
        IMT-dependent total standard deviation as a CoeffsTable
    """
    si[:] = total_sigma[imt]["total_sigma"]


def add_delta_std_to_total_std(ctx, imt, me, si, ta, ph, delta):
    """
    :param delta:
        A delta std e.g. a phi S2S to be removed from total
    """
    si[:] = (si**2 + np.sign(delta) * delta**2)**0.5


def set_total_std_as_tau_plus_delta(ctx, imt, me, si, ta, ph, delta):
    """
    :param delta:
        A delta std e.g. a phi SS to be combined with between std, tau.
    """
    si[:] = (ta[2]**2 + np.sign(delta) * delta**2)**0.5


# ################ END OF FUNCTIONS MODIFYING mean_stds ################## #


def _dict_to_coeffs_table(input_dict, name):
    """
    Transform a dictionary of parameters organised by IMT into a
    coefficient table
    """
    coeff_dict = {from_string(k): {name: input_dict[k]} for k in input_dict}
    return {name: CoeffsTable.fromdict(coeff_dict)}


class ModifiableGMPE(GMPE):
    """
    This is a class to modify an underlying GMPE.
    It should NEVER be instantiated directly; users should call
    hazardlib.valid.modifiable_gmpe(gmpe, **kwargs) instead.
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
        # Create the original GMPE
        [(gmpe_name, kw)] = kwargs.pop('gmpe').items()
        self.params = kwargs  # non-gmpe parameters
        g = globals()
        for k in self.params:
            if k not in g:
                raise ValueError('Unknown %r in ModifiableGMPE' % k)
        self.gmpe = registry[gmpe_name](**kw)
        if hasattr(self.gmpe, 'gmpe_table'):
            self.gmpe_table = self.gmpe.gmpe_table
        self.set_parameters()

        if ('set_between_epsilon' in self.params or
            'set_total_std_as_tau_plus_delta' in self.params) and (
                StdDev.INTER_EVENT not in
                self.gmpe.DEFINED_FOR_STANDARD_DEVIATION_TYPES):
            raise ValueError('%s does not have between event std' % self.gmpe)

        if 'apply_swiss_amplification' in self.params:
            self.gmpe.REQUIRES_SITES_PARAMETERS = frozenset(['amplfactor'])

        if 'add_between_within_stds' in self.params:
            setattr(self, 'DEFINED_FOR_STANDARD_DEVIATION_TYPES',
                    {StdDev.TOTAL, StdDev.INTRA_EVENT, StdDev.INTER_EVENT})

        if ('cb14_basin_term' in self.params or 'm9_basin_term' in self.params
            ) and ( 'z2pt5' not in self.gmpe.REQUIRES_SITES_PARAMETERS):
            tmp = list(self.gmpe.REQUIRES_SITES_PARAMETERS)
            tmp.append('z2pt5')
            self.gmpe.REQUIRES_SITES_PARAMETERS = frozenset(tmp)

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
            assert len(mags)
            self.gmpe.set_tables(mags, imts)

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        # Set reference Vs30 if required
        if ('nrcan15_site_term' in self.params or
                'cy14_site_term' in self.params):
            ctx_copy = ctx.copy()
            if 'nrcan15_site_term' in self.params:
                rock_vs30 = 760.
            elif 'cy14_site_term' in self.params:
                rock_vs30 = 1130.
            ctx_copy.vs30 = np.full_like(ctx.vs30, rock_vs30) # rock
        else:
            ctx_copy = ctx
        g = globals()

        # Compute the original mean and standard deviations
        self.gmpe.compute(ctx_copy, imts, mean, sig, tau, phi)

        # Apply sequentially the modifications
        for methname, kw in self.params.items():
            for m, imt in enumerate(imts):
                me, si, ta, ph = mean[m], sig[m], tau[m], phi[m]
                g[methname](ctx, imt, me, si, ta, ph, **kw)
