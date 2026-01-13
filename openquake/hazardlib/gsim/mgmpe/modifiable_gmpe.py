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
from openquake.hazardlib.imt import PGA
from openquake.hazardlib.gsim.base import GMPE, registry, CoeffsTable
from openquake.hazardlib.const import StdDev
from openquake.hazardlib.imt import from_string

from openquake.hazardlib.gsim.chiou_youngs_2014 import ChiouYoungs2014

# Site terms imports
from openquake.hazardlib.gsim.mgmpe.nrcan15_site_term import (
    NRCan15SiteTerm, BA08_AB06)
from openquake.hazardlib.gsim.mgmpe.cy14_site_term import _get_cy14_site_term
from openquake.hazardlib.gsim.mgmpe.ba08_site_term import _get_ba08_site_term
from openquake.hazardlib.gsim.mgmpe.bssa14_site_term import _get_bssa14_site_term
 
# Basin terms imports
from openquake.hazardlib.gsim.mgmpe.cb14_basin_term import _get_cb14_basin_term
from openquake.hazardlib.gsim.mgmpe.m9_basin_term import _apply_m9_basin_term

# CEUS 2020 site term imports
from openquake.hazardlib.gsim.nga_east import (
    TAU_EXECUTION, get_phi_ss, TAU_SETUP, PHI_SETUP, get_tau_at_quantile,
    get_phi_ss_at_quantile)
from openquake.hazardlib.gsim.usgs_ceus_2019 import get_stewart_2019_phis2s

from openquake.hazardlib.gsim.mgmpe.stewart2020 import (
    stewart2020_linear_scaling)
from openquake.hazardlib.gsim.mgmpe.hashash2020 import (
    hashash2020_non_linear_scaling)


# ############## HANDLER FUNCTIONS FOR CONDITIONAL GMPES ################ #

def conditional_gmpe_compute(self, imts, ctx_copy, mean, sig, tau, phi):
    """
    This function:
        1) Compute the means and standard deviations for the IMTs
           required by the conditional GMPEs.
        2) Compute the means and standard deviations for the other IMTs
    """
    # Compute the means and std devs for IMTs required by conditional GMPEs
    imts_req = self.imts_req
    sh = (len(imts_req), len(ctx_copy))
    mean_b, sig_b, tau_b, phi_b = (np.empty(sh), np.empty(sh),
                                   np.empty(sh), np.empty(sh))
    self.gmpe.compute(ctx_copy, imts_req, mean_b, sig_b, tau_b, phi_b)

    # Store them for use in conditional GMPE(s) later
    preds = self.params["conditional_gmpe"]["base_preds"] = {
               imt.string: {} for imt in imts_req}  # imt -> stat -> array
    for i, imt in enumerate(imts_req):
        preds[imt.string]["mean"] = mean_b[i]
        preds[imt.string]["sig"] = sig_b[i]
        preds[imt.string]["tau"] = tau_b[i]
        preds[imt.string]["phi"] = phi_b[i]
        
    # Sometimes need underlying GSIM within conditional GMPEs compute method
    # if has ctx-dependent conditioning periods like possible within
    # AbrahamsonBhasin2020
    preds["base"] = self.gmpe

    # Now get the IMTs we wish to compute using the underlying GSIM
    imt_names = {imt.__name__ for imt in
                self.gmpe.DEFINED_FOR_INTENSITY_MEASURE_TYPES}
    imts_base = {imt for imt in imts if imt.name in imt_names}

    # NOTE: 'imts_base' can be empty if all IMTs in job file will be
    # computed using conditional GMPEs (e.g. classical/case_09 test
    # where only IA from Macedo 2019 is required). In this case the
    # the means and std devs will be returned as zeroed arrays
    if imts_base:
        # Need to map original order of IMTs for reordering
        imts_map = {imt: i for i, imt in enumerate(imts)}

        # Compute the original mean and std devs for required IMTs
        self.gmpe.compute(ctx_copy, imts_base, mean, sig, tau, phi)
        arrays = [mean.copy(), sig.copy(), tau.copy(), phi.copy()]

        # For instance in test case_90 one has
        # imts_map = {PGA: 0, PGV: 1, IA: 2, SA(0.2): 3, SA(1.0): 4}
        # and imts_base = {SA(1.0), SA(0.2), PGA}
        # then `m` takes the values [4, 3, 0] for `idx` in [0, 1, 2]
        for idx, imt in enumerate(imts_base):
            m = imts_map[imt]
            mean[m] = arrays[0][idx]
            sig[m] = arrays[1][idx]
            tau[m] = arrays[2][idx]
            phi[m] = arrays[3][idx]


def conditional_gmpe(ctx, imt, me, si, ta, ph, **kwargs):
    """
    This function applies a conditional GMPE for the computing of the
    ground-motion for the given intensity measure type.
    """
    # Get the conditional GMPE per IMT
    conditional_gmpes = {k: v for k, v in kwargs.items() if k != "base_preds"}

    # Get predictions per IMT required by the conditional GMPEs
    base_preds = kwargs.get('base_preds')
    
    # If the imt is requested from a conditional gmpe... 
    if imt.string in conditional_gmpes: 

        # Get the conditional GMM specified for the given IMT
        cond = conditional_gmpes[imt.string]["gsim"]

        # Check that conditional GMPE supports the IMT we want to use it for
        imt_names = {func.__name__ for func in cond.
                     DEFINED_FOR_INTENSITY_MEASURE_TYPES}
        if imt.name not in imt_names:
            raise ValueError(
                f"{cond.__class__.__name__} does not support {imt}")

        # Check that we have required predictions from the underlying GMM
        # for use in the conditional GMM
        cond_imts = [imt_cond.string for imt_cond in cond.REQUIRES_IMTS]
        missing = [imt_req for imt_req in cond_imts
                   if imt_req not in base_preds.keys()]
        if missing:
            raise ValueError(
                f"To use {cond.__class__.__name__} for the calculation "
                f"of {imt}, the user must provide a GMM which is defined for "
                f"the following IMTS: {cond_imts} (Missing = {missing})"
            )

        # Compute mean and sigma for IMT conditioned
        me_c, sig_c, tau_c, phi_c = cond.compute(ctx, base_preds)

        # Assign the mean and sigma of the conditioned GMPE
        me[:] = me_c
        si[:] = sig_c
        ta[:] = tau_c
        ph[:] = phi_c


# ################ SITE TERMS AND BASIN TERMS ################## #


SITE_TERMS = ["cy14_site_term",
              "ba08_site_term",
              "bssa14_site_term",
              "nrcan15_site_term",
              "ceus2020_site_term"]


def nrcan15_site_term(ctx, imt, me, si, ta, ph, kind):
    """
    This function adds the NRCan15 site term to GMMs requiring it
    """
    C = NRCan15SiteTerm.COEFFS_BA08[imt]
    C2 = NRCan15SiteTerm.COEFFS_AB06r[imt]
    exp_mean = np.exp(me)
    fa = BA08_AB06(kind, C, C2, ctx.vs30, imt, exp_mean)
    me[:] = np.log(exp_mean * fa)


def ceus2020_site_term(
        ctx, imt, me, si, ta, phi, wimp, ref_vs30, ref_pga, usgs=False):
    """
    This function adds the Stewart et al. (2020; EQS) site term that uses as
    a reference 760 m/s.

    :param wimp:
        The 'wimp' factor in eq. 5 of Stewart et al. (2020)
    :param ref_vs30:
        The reference Vs30 value
    :param ref_pga:
        The reference PGA value computed for a vs30 corresponding to `ref_vs30`
    """
    if not hasattr(ref_pga, '__len__'):
        ref_pga = np.array([ref_pga])
    assert len(ref_pga) == len(ctx.vs30)

    # Compute the linear term
    slin = stewart2020_linear_scaling(imt, ctx.vs30, wimp, usgs)

    # Compute the nonlinear term
    snlin = hashash2020_non_linear_scaling(imt, ctx.vs30, ref_pga, ref_vs30)

    # Final mean
    me[:] += (slin + snlin)


def cy14_site_term(ctx, imt, me, si, ta, phi):
    """
    This function adds the CY14 site term to GMMs requiring it.
    """
    C = ChiouYoungs2014.COEFFS[imt]
    fa = _get_cy14_site_term(C, ctx.vs30, me)  # Ref mean must be in nat log
    me[:] += fa


def ba08_site_term(ctx, imt, me, si, ta, phi):
    """
    This function adds the BA08 site term to GMMs requiring it.
    """
    me[:] += _get_ba08_site_term(imt, ctx)


def bssa14_site_term(ctx, imt, me, si, ta, phi):
    """
    This function adds the BSSA14 site term to GMMs requiring it.
    """
    me[:] += _get_bssa14_site_term(imt, ctx)


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


# ################ FUNCTIONS MODIFYING mean_stds ################## #


IMT_DEPENDENT_ADJ = ["set_scale_median_vector",
                     "set_scale_total_sigma_vector",
                     "set_fixed_total_sigma"]


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


def _dict_to_coeffs_table(input_dict, name):
    """
    Transform a dictionary of parameters organised by IMT into a
    coefficient table
    """
    coeff_dict = {from_string(k): {name: input_dict[k]} for k in input_dict}
    return {name: CoeffsTable.fromdict(coeff_dict)}


def init_underlying_gmpes(cond_gmpe_by_imt):
    """
    :param cond_gmpe_by_imt: dictionary describing a conditional GMPE
    """
    # NB: in classical/case_90 cond_gmpe_by_imt is the dictionary
    # {'IA': {'gmpe': {'MacedoEtAl2019SInter': {'region': 'Japan'}}},
    #  'PGV': {'gmpe': {'AbrahamsonBhasin2020PGA': {}}}}

    # Get each conditional GMM's required IMTs and also instantiate them
    imts_req = set()
    for imt in cond_gmpe_by_imt:
        if imt == "base_preds":
            continue

        # Instantiate here and store for later
        [(gmpe_name, kw)] = cond_gmpe_by_imt[imt]["gmpe"].items()
        cond = registry[gmpe_name](**kw)
        cond.from_mgpme = True
        if not hasattr(cond, "REQUIRES_IMTS"):
            raise ValueError(f"{cond.__class__.__name__} lacks the "
                             f"REQUIRES_IMTS attribute - this is "
                             f"required for a conditional GMPE's "
                             f"OpenQuake Engine implementation.")
        if not cond.conditional:
            raise ValueError(f"{cond.__class__.__name__} is not a "
                             f"conditional GMPE - it cannot be used "
                             f"in ModifiableGMPE as a GMPE to predict "
                             f"conditioned ground-motions for {imt}.")

        cond_gmpe_by_imt[imt]["gsim"] = cond

        # Add each required IMT so we compute all using underlying GMM once
        imts_req.update(cond.REQUIRES_IMTS)
    return sorted(imts_req)


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

        if 'ba08_site_term' in self.params or 'bssa14_site_term' in self.params:
            # Require rake and rjb in the ctx for computing bedrock PGA
            if 'rake' not in self.gmpe.REQUIRES_RUPTURE_PARAMETERS:
                self.REQUIRES_RUPTURE_PARAMETERS |= {"rake"}
            if 'rjb' not in self.gmpe.REQUIRES_DISTANCES:
                self.REQUIRES_DISTANCES |= {"rjb"}

        if (any(sm in self.params for sm in SITE_TERMS) and
            'vs30' not in self.gmpe.REQUIRES_SITES_PARAMETERS):
            # Make sure is always Vs30 in the ctx
            self.REQUIRES_SITES_PARAMETERS |= {"vs30"}

        if ((('cb14_basin_term' in self.params) or
             ('m9_basin_term' in self.params)) and
                ('z2pt5' not in self.gmpe.REQUIRES_SITES_PARAMETERS)):
            # Require z2pt5 in ctx
            self.REQUIRES_SITES_PARAMETERS |= {"z2pt5"}

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
            if key in IMT_DEPENDENT_ADJ:
                # If the modification is period-dependent
                for subkey in self.params[key]:
                    if isinstance(self.params[key][subkey], dict):
                        self.params[key] = _dict_to_coeffs_table(
                            self.params[key][subkey], subkey)

        if "conditional_gmpe" in self.params:
            self.imts_req = init_underlying_gmpes(self.params["conditional_gmpe"])

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
        if any(sm in self.params for sm in SITE_TERMS):
            ctx_copy = ctx.copy()
            if 'cy14_site_term' in self.params:
                rock_vs30 = 1130.
            elif ('nrcan15_site_term' or 'ba08_site_term'
                  or 'bssa14_site_term' in self.params):
                rock_vs30 = 760.
            ctx_copy.vs30 = np.full_like(ctx.vs30, rock_vs30) # rock
        else:
            ctx_copy = ctx

        # If necessary, compute the means and std devs for the required
        # IMTs that are not going to be calculated using conditional GMPEs 
        if "conditional_gmpe" in self.params:
            conditional_gmpe_compute(self, imts, ctx_copy, mean, sig, tau, phi)
        else:
            # otherwise, compute the original mean and std devs for all IMTs
            self.gmpe.compute(ctx_copy, imts, mean, sig, tau, phi)

        # Here we compute reference ground-motion for PGA when we need to
        # amplify the motion using the CEUS2020 model
        if 'ceus2020_site_term' in self.params:

            # Arrays for storing results
            ref = np.zeros((1, len(sig[0])))
            tmp = np.zeros((1, len(sig[0])))

            # Update context
            tctx = ctx.copy()
            ref_vs30 = self.params['ceus2020_site_term']['ref_vs30']
            tctx.vs30 = np.ones_like(tctx.vs30) * ref_vs30
            timt = (PGA(),)

            self.gmpe.compute(tctx, timt, ref, tmp, tmp, tmp)

            # 'ref' contains the PGA for the reference Vs30
            ref = np.squeeze(ref)

        # Apply sequentially the modifications
        g = globals()
        for methname, kw in self.params.items():

            # CEUS 2020 site term needs ref PGA stored
            if methname in ['ceus2020_site_term']:
                kw['ref_pga'] = np.exp(ref)

            # Conditional GMPEs
            if methname in ["conditional_gmpe"]:
                kw['base_preds'] = self.params["conditional_gmpe"]["base_preds"]
                
            for m, imt in enumerate(imts):
                me, si, ta, ph = mean[m], sig[m], tau[m], phi[m]
                g[methname](ctx, imt, me, si, ta, ph, **kw)
