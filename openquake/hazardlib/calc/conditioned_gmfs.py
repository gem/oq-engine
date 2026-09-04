# -*- coding: utf-8 -*-
#
# Copyright (C) 2023-2026 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
"""Condition ground-motion fields on seismic station observations.

The conditioning algebra follows Engler et al. (2022):

Engler, D. T., Worden, C. B., Thompson, E. M., and Jaiswal, K. S.
(2022). Partitioning Ground Motion Uncertainty When Conditioned on
Station Data. Bulletin of the Seismological Society of America, 112(2),
1060–1079. https://doi.org/10.1785/0120210177

The corresponding USGS ShakeMap processing is described at
https://usgs.github.io/shakemap/manual4_0/tg_processing.html. Its main
implementation is in ``shakemap_modules/coremods/model.py`` at
https://code.usgs.gov/ghsc/esi/shakemap-modules.

Basic model
===========

Following Appendix B, ground motion is represented in natural-log units as

``Y = mu_Y + W_Y + T_Y H_D`` and
``Y_D = mu_YD + W_D + T_D H_D``.

``Y`` contains the targets and ``Y_D = y_D`` contains the observations.
``mu`` is the GSIM median in log space, ``W`` is the within-event residual,
and ``H_D`` contains unit-variance normalized between-event residuals for
the contributing IMTs. The capital-tau matrices ``T_Y`` and ``T_D`` map
``H_D`` to targets and observations using the GSIM ``tau`` values. Thus,
the scaled between-event residual is ``B = T H``. The GSIM within-event
standard deviation is ``phi``. Station values are converted to log space
before conditioning.

The module has two calculation paths:

* A spatial-only model uses the historical Engler implementation. It
  conditions each target IMT separately and uses a separable approximation
  when relating different observed and target IMTs. It does not construct
  one jointly correlated target field across IMTs. This path supports the
  existing finite truncated-normal sampler.
* A spatial-cross-IMT model forms one joint vector containing every target
  IMT and site. It conditions that vector in a single Gaussian operation,
  preserving the model's spatial and cross-IMT covariance. Dense sampling is
  retained for small calculations and as the correctness reference. Eligible
  regular grids use the scalable conditional simulation described below.
  Finite truncated sampling is not yet supported here.

The joint path stacks all requested target IMTs rather than applying
Appendix B to one target IMT at a time. Its prior covariance blocks are

``Sigma_YD_YD = Sigma_WD_WD + T_D Sigma_HD_HD T_D.T``,
``Sigma_YY = Sigma_WY_WY + T_Y Sigma_HD_HD T_Y.T``, and
``Sigma_Y_YD = Sigma_WY_WD + T_Y Sigma_HD_HD T_D.T``.

``Sigma_HD_HD`` is the covariance (and correlation) of ``H_D``. Following
the ShakeMap implementation, observation-error variance is added to the
diagonal of ``Sigma_WD_WD``. With ``^+`` denoting a pseudoinverse and
``Sigma_YD_Y = Sigma_Y_YD.T``, the conditional MVN equations give

``mu_Y_yD = mu_Y + Sigma_Y_YD Sigma_YD_YD^+ (y_D - mu_YD)`` and
``Sigma_YY_yD = Sigma_YY - Sigma_Y_YD Sigma_YD_YD^+ Sigma_YD_Y``.

These are the joint form of the mean and covariance in equations (B16) and
(B17). For one target IMT, ``T_Y`` corresponds to the paper's ``T_Y0``.

Scalable conditional simulation
================================

Factoring ``Sigma_YY_yD`` is infeasible for a realistic target grid. The
scalable path instead uses Matheron substitution. It draws paired zero-mean
values ``U_Y`` and ``U_D`` from the same target-and-station prior and forms

``Y_yD = mu_Y + U_Y + Sigma_Y_YD Sigma_YD_YD^+ (zeta_D - U_D)``.

The large regular target field is generated with circulant embedding. A
station coinciding with a grid point takes that same simulated value. An
off-grid station is sampled conditionally on a fourth-order local grid
neighborhood following Bailey et al. (2022), Stat, 11(1), e446,
https://doi.org/10.1002/sta4.446. Stations within one grid box are sampled
jointly across all IMTs. Conditional errors from different boxes are treated
as independent; this is the documented local-kriging approximation.

The target-to-station regression weights are constructed once in site
chunks and retained in float64. Realizations are then generated, conditioned,
converted to GMFs, and returned in memory-bounded batches. This removes the
dense target covariance and posterior factorization while preserving the
small station covariance system.

Relationship to the Engler algorithm
====================================

The historical path retains the paper's partitioned calculation. ``createD``
constructs the terms needed by equations (B8) and (B9),
``Conditioner.get_mu_tau_phi`` evaluates (B8) and the mean in (B16), and
``_compute_target_covs`` evaluates the two covariance terms in (B17).

The joint path is an algebraic generalization rather than a literal sequence
of the Appendix B equations. It first integrates the normalized
between-event residual ``H_D`` into the three total prior covariance blocks,
then applies the standard conditional-MVN equations. Expanding that Schur
complement gives equations (B16) and (B17). It therefore produces the same
untruncated total Gaussian posterior while also allowing one within-event
model to correlate every target IMT and site jointly. It does not retain
separate within- and between-event posterior fields.

OpenQuake also makes the following implementation choices:

* Station-error variance is added to ``Sigma_WD_WD`` following ShakeMap.
  It is not shown explicitly in Appendix B.
* Pseudoinverses replace the paper's inverses so that singular covariance
  systems can be handled when they are mathematically compatible.
* The historical path constructs cross-IMT spatial covariance using a
  separable approximation. A joint spatial-cross-IMT model supplies this
  covariance directly in the joint path.
* The historical path retains elementwise clipping of negative posterior
  covariance entries and its finite truncated-normal sampler. Neither step
  is part of the Engler derivation. The joint Gaussian path performs neither.

Basic flow
==========

1. ``ConditionedGmfComputer`` collects the conditionable target and
   observed IMTs, configures the correlation models, and creates the
   calculation input. MMI is excluded from residual conditioning.
2. ``get_precomputed`` builds rupture contexts, filters distant sites, and
   creates the required target/station distance matrices.
3. ``build_precomputed`` evaluates ``mu``, total sigma, ``tau``, and ``phi``
   at every target and station for each GSIM.
4. ``conditioned`` selects the spatial-only or joint path. The former builds
   one Engler posterior per target IMT; the latter first builds one joint
   station system and then the joint target blocks.
5. With zero truncation, posterior means are repeated for all requested
   fields. Small random calculations construct and sample the dense
   covariance. Eligible regular grids instead use paired CE prior fields and
   Matheron substitution, streaming the resulting GMFs in bounded batches.

Notation and dimensions
=======================

Subscripts and indices
----------------------

``D``
  Data: observed IMT values at station sites.
``Y``
  Prediction targets: requested IMT values at target sites.
``W``
  Within-event residual.
``B``
  Between-event residual after scaling by ``tau``.
``H``
  Unit-variance normalized between-event residual.
``W_D``
  Within-event residual at the observation sites.
``_yD``
  Suffix denoting conditioning on the observed values ``Y_D = y_D``.
``_wD``
  Legacy suffix denoting conditioning on station within-event residuals.
``K``
  Number of target grid points in Appendix B.
``L``
  Number of stations in Appendix B.
``N``
  Number of target sites in OpenQuake arrays; equivalent to Appendix B's
  ``K``.
``N_D``
  Number of station sites in OpenQuake arrays; equivalent to Appendix B's
  ``L``.
``D``
  Local name for ``N_D`` in the chunked-mean implementation.
``M``
  Number of target IMTs in OpenQuake. In Appendix B, ``M + 1`` instead
  counts one native target IMT and the nonnative observed IMTs.
``M_D``
  Number of observed IMTs in OpenQuake.
``J``
  Local name for ``M_D`` in the chunked-mean implementation.
``E``
  Number of ground-motion fields.
``G``
  Number of GSIMs.
``g``
  GSIM index.
``m``
  Target-IMT index. Joint vectors are flattened in IMT-major order.

Input values and GSIM statistics
--------------------------------

``y_D``
  Logged station observations.
``mu_YD``
  GSIM mean at observation sites.
``mu_Y``
  GSIM mean at target sites.
``zeta_D``
  OpenQuake shorthand for the raw station residual ``y_D - mu_YD``. The
  Appendix B equations write this difference explicitly.
``phi_D``
  GSIM within-event standard deviations at observation sites.
``phi_Y``
  GSIM within-event standard deviations at target sites.
``tau_D``
  GSIM between-event standard deviations at observation sites.
``tau_Y``
  GSIM between-event standard deviations at target sites.
``observation_variance``
  Squared station ``*_std`` values added to the station covariance diagonal.
``sigma_D_epsilon^2``
  ShakeMap notation for ``observation_variance``. It is folded into
  ``Sigma_WD_WD`` before conditioning.
``observation_mask``
  Boolean IMT-major mask removing missing values from the joint station
  system.
``full_phi_D``
  Unmasked station within-event standard deviations used to construct
  covariance blocks before applying ``observation_mask``.
``mean_stds_D``
  Station GSIM array whose first dimension contains ``mu``, total sigma,
  ``tau``, and ``phi``. The remaining dimensions are GSIM, IMT, and site.
``mean_stds_Y``
  Target GSIM array with the same axes as ``mean_stds_D``.

Distances and covariance blocks
-------------------------------

Names such as ``cov_WY_WD`` denote ``Cov(W_Y, W_D)``. Joint-path names
omit the residual component because they contain both within- and
between-event covariance.

``DD``
  Station-to-station distance matrix.
``YY``
  Target-to-target distance matrix.
``YD``
  Target-to-station distance matrix.
``DY``
  Station-to-target distance matrix. Distance matrices contain site
  distances only; covariance builders expand them across IMTs.
``cov_WD_WD``
  Within-event station covariance ``Sigma_WD_WD``, including station-error
  variance.
``cov_WY_WD``
  Within-event target-to-station covariance ``Sigma_WY_WD``.
``cov_WD_WY``
  Within-event station-to-target covariance ``Sigma_WD_WY``.
``cov_WY_WY``
  Within-event target covariance ``Sigma_WY_WY``.
``cov_YD_YD``
  Joint-path total station prior covariance ``Sigma_YD_YD``.
``cov_Y_YD``
  Joint-path total target-to-station prior covariance ``Sigma_Y_YD``.
``cov_YY``
  Joint-path total target prior covariance ``Sigma_YY``.
``cov_WD_WD_inv``
  Pseudoinverse of the historical within-event station covariance.
``cov_YD_YD_inv``
  Pseudoinverse of the joint total station covariance.
``Sigma_YY_yD``
  Total posterior covariance returned by ``posterior_covariance``.

Between-event and regression terms
----------------------------------

``cov_HD_HD``
  Prior ``Sigma_HD_HD`` of normalized between-event residuals for the
  contributing IMTs.
``T_D``
  Appendix B's capital-tau mapping from normalized between-event residuals
  to station values; its nonzero entries are the corresponding ``tau_D``
  values. The joint path generalizes the same matrix to all target IMTs.
``T_Y``
  Joint target mapping corresponding to ``T_Y0`` in Appendix B.
``mu_HD_yD``
  Historical-path posterior mean of the normalized between-event residual.
``cov_HD_HD_yD``
  Historical-path posterior covariance of that normalized residual.
``mu_BD_yD``
  Historical-path posterior mean after mapping ``H_D`` to ``B_D``.
``cov_BD_BD_yD``
  Historical-path posterior covariance after that mapping.
``nominal_bias_mean``
  Scalar summary of the conditional between-event residual mean.
``nominal_bias_stddev``
  Scalar summary of the conditional between-event residual standard
  deviation.
``RC``
  Legacy within-event regression matrix
  ``cov_WY_WD @ cov_WD_WD_inv``.
``C``
  Legacy target scaling matrix for conditional between-event covariance.
``cov_WY_WY_wD``
  Historical-path conditional within-event target covariance.
``cov_BY_BY_yD``
  Historical-path conditional between-event target covariance.

Sampling and output
-------------------

``mu_Y_yD``
  Conditional target mean.
``unconditional_D``
  Zero-mean station draw from the joint prior for Matheron substitution.
``unconditional_Y``
  Paired zero-mean target draw from that same joint prior.
``cutoff``
  Small diagonal covariance increment used to handle numerical roundoff
  during sampling.
``tlw``
  Truncation level for within-event residuals.
``tlb``
  Truncation level for between-event residuals.
``lb_w``
  Lower bound for historical within-event residual sampling.
``ub_w``
  Upper bound for historical within-event residual sampling.
``lb_b``
  Lower bound for historical between-event residual sampling.
``ub_b``
  Upper bound for historical between-event residual sampling.
``z_w_truncated``
  Sampled historical within-event residual fields.
``z_b_truncated``
  Sampled historical between-event residual fields.
``MNE``
  Output array with shape ``(M, N, E + 1)``. The first ``E`` slices contain
  log-space conditioned fields and the final slice contains their posterior
  mean. ``compute_all`` subsequently converts applicable IMTs from log space.
"""

import logging
from dataclasses import dataclass, replace
from collections import namedtuple

import psutil
import numpy
import pandas
from openquake.baselib import config, performance
from openquake.baselib.general import humansize
from openquake.hazardlib.truncated_mvn import TruncatedMVN
from openquake.hazardlib.calc.gmf import (
    CE_MIN_SITES, GmfComputer, TRUNCATION_THRESHOLD)
from openquake.hazardlib.const import StdDev
from openquake.hazardlib.correlation_models.base import (
    ResidualComponent, SpatialCorrelationModel)
from openquake.hazardlib.correlation_models.circulant_embedding import (
    CirculantEmbeddingFactor, GRID_TOLERANCE, RegularGridLayout)
from openquake.hazardlib.correlation_models.cross_imt.baker_jayaram_2008 \
    import BakerJayaram2008
from openquake.hazardlib.correlation_models.cross_imt.goda_atkinson_2009 \
    import GodaAtkinson2009
from openquake.hazardlib.correlation_models.local_kriging import (
    covariance_root, LocalKrigingFactor)
from openquake.hazardlib.correlation_models.spatial.jayaram_baker_2009 \
    import JayaramBaker2009
from openquake.hazardlib.geo.geodetic import geodetic_distance

U32 = numpy.uint32
F32 = numpy.float32

Precomputed = namedtuple('Precomputed', 'ctx_Y ctx_D YY YD DY DD conditioners')


def conditionable_imts(imts):
    """Return the IMTs supported by ground-motion conditioning."""
    return [imt for imt in imts if imt.string != 'MMI']


def _gsim_supports_imt(gsim, imt):
    supported = gsim.DEFINED_FOR_INTENSITY_MEASURE_TYPES
    return (supported is None or
            imt.name in {imt_type.__name__ for imt_type in supported})


def select_observed_imts(
        target_imts, observed_imts, gsim, correlation_models):
    """Return station IMTs supported by the GSIM and correlation models."""
    for model in correlation_models:
        model.validate_imts(target_imts)

    selected = []
    for candidate in conditionable_imts(observed_imts):
        if not _gsim_supports_imt(gsim, candidate):
            continue
        trial = list(dict.fromkeys([*target_imts, *selected, candidate]))
        try:
            for model in correlation_models:
                model.validate_imts(trial)
        except ValueError:
            continue
        selected.append(candidate)
    return selected


def get_precomputed(rupture, cmaker, inp, compute_covs=True):
    """
    :param compute_covs: build matrices required only for random fields
    :returns: (ctx_Y, ctx_D, dist)
    """
    if hasattr(rupture, 'rupture'):
        rupture = rupture.rupture

    # Generate the contexts for stations sites and target sites
    [ctx_D] = cmaker.get_ctxs([rupture], inp.sites_D)
    [ctx_Y] = cmaker.get_ctxs([rupture], inp.sites_Y)

    # filter sites
    mask_Y = numpy.isin(inp.sites_Y.sids, ctx_Y.sids)
    inp.sites_Y = inp.sites_Y.filter(mask_Y)
    mask_D = numpy.isin(inp.sites_D.sids, ctx_D.sids)
    inp.sites_D = inp.sites_D.filter(mask_D)
    inp.stations = inp.stations[mask_D].copy()

    joint_model = not isinstance(
        inp.within_event_model, SpatialCorrelationModel)
    if compute_covs:
        YY = compute_distance_matrix(inp.sites_Y, inp.sites_Y)
        DY = None if joint_model else compute_distance_matrix(
            inp.sites_D, inp.sites_Y)
    else:
        YY = DY = None
    if compute_covs or not joint_model:
        YD = compute_distance_matrix(inp.sites_Y, inp.sites_D)
    else:
        YD = None
    DD = compute_distance_matrix(inp.sites_D, inp.sites_D)
    return Precomputed(ctx_Y, ctx_D, YY, YD, DY, DD, [])


class NoInterIntraStdDevs(Exception):
    def __init__(self, gsim):
        self.gsim = gsim

    def __str__(self):
        return """\
You cannot use the conditioned ground shaking module with the GSIM %s,
that defines only the total standard deviation. If you wish to use the
conditioned ground shaking module you have to select a GSIM that provides
the inter and intra event standard deviations, or use the ModifiableGMPE
with `add_between_within_stds.with_betw_ratio`.
""" % self.gsim.__class__.__name__


class ConditionedGmfComputer(GmfComputer):
    """
    Given an earthquake rupture, and intensity observations from
    recording station data, the conditioned ground motion field computer
    computes ground shaking over a set of sites, by randomly sampling a
    ground shaking intensity model whose mean and within-event and
    between-event terms have been conditioned upon the observations.

    NB: using truncation_level = 0 totally disables the random part
    and the generated GMFs become deterministic (equal for all events).

    :param rupture:
        Rupture to calculate ground motion fields radiated from.

    :param :class:`openquake.hazardlib.site.SiteCollection` target_sitecol:
        the hazard sites excluding the stations

    :param cmaker:
        a :class:`openquake.hazardlib.gsim.base.ContextMaker` instance

    :param within_event_model:
        Instance of a within-event correlation model object. See
        :mod:`openquake.hazardlib.correlation_models`. Can be ``None``, in which
        case non-correlated ground motion fields are calculated.
        Correlation model is not used if ``truncation_level`` is zero.

    :param between_event_model:
        Instance of a between-event correlation model object. See
        :mod:`openquake.hazardlib.correlation_models`. Can be ``None``, in which
        case non-cross-correlated ground motion fields are calculated.

    :param amplifier:
        None or an instance of Amplifier

    :param sec_perils:
        Tuple of secondary perils. See
        :mod:`openquake.hazardlib.sep`. Can be ``None``, in which
        case no secondary perils need to be evaluated.
    """
    def __init__(
            self, rupture, sitecol, station_sitecol, station_data,
            observed_imts, cmaker, within_event_model=None,
            between_event_model=None, within_event_correlation_params=None,
            number_of_ground_motion_fields=1, amplifier=None, sec_perils=(),
            **legacy):
        aliases = {
            'spatial_correl': 'within_event_model',
            'cross_correl_between': 'between_event_model',
            'ground_motion_correlation_params':
            'within_event_correlation_params'}
        values = {
            'within_event_model': within_event_model,
            'between_event_model': between_event_model,
            'within_event_correlation_params':
            within_event_correlation_params}
        for old_name, new_name in aliases.items():
            if old_name in legacy:
                if values[new_name] is not None:
                    raise TypeError(f'Pass only {new_name}')
                values[new_name] = legacy.pop(old_name)
        if legacy:
            raise TypeError('Unknown arguments: %s' % sorted(legacy))
        within_event_model = values['within_event_model']
        between_event_model = values['between_event_model']
        within_event_correlation_params = (
            values['within_event_correlation_params'] or {})
        assert len(station_data) == len(station_sitecol), (
            len(station_data), len(station_sitecol))
        GmfComputer.__init__(
            self, rupture=rupture, sitecol=sitecol, cmaker=cmaker,
            within_event_model=within_event_model,
            between_event_model=between_event_model,
            amplifier=amplifier, sec_perils=sec_perils)

        clust = within_event_correlation_params.get(
            "vs30_clustering", True)
        self.rupture = rupture

        target_imts = conditionable_imts(self.imts)
        within_event_model = within_event_model or JayaramBaker2009(clust)
        between_event_model = between_event_model or GodaAtkinson2009()
        separable_cross_imt_model = BakerJayaram2008()

        self.inp = Input(
            sitecol, station_sitecol,
            target_imts, observed_imts, station_data,
            within_event_model, between_event_model,
            separable_cross_imt_model, self.correlation_context)

    def _compute_mvn(self, mu_Y, cov_WY_WY, cov_BY_BY, E):
        rng = numpy.random.default_rng(self.seed)
        N = len(cov_WY_WY)
        cutoff = F32(self.cmaker.oq.correlation_cutoff)
        cutoff *= numpy.eye(N, dtype=F32)
        # NB: the cutoff is needed to remove negative eigenvalues
        if (self.cmaker.oq.truncated_mvn is False or
                self.cmaker.truncation_level == 99):
            # do not truncate
            cov_Y_Y = cov_WY_WY + cov_BY_BY + cutoff
            # eig0, _ = numpy.linalg.eigh(cov_WY_WY + cov_BY_BY)
            # eig, _ = numpy.linalg.eigh(cov_Y_Y)
            arr = rng.multivariate_normal(
                mu_Y.flatten(), cov_Y_Y, size=E,
                check_valid="raise", tol=1e-5, method="cholesky").T
            return arr

        # NB: truncated MVN is used in the scenario risk tests
        # conditioned_stations, case_21_stations, case_26_stations
        cov_WY_WY = cov_WY_WY + cutoff
        cov_BY_BY = cov_BY_BY + cutoff

        lb_w, ub_w = self.get_symmetric_bounds(cov_WY_WY, self.tlw)
        seed_w = int(rng.integers(0, numpy.iinfo(numpy.int32).max))

        z_w_truncated = TruncatedMVN(
            numpy.zeros(N, F32), cov_WY_WY, F32(lb_w), F32(ub_w), seed=seed_w
        ).sample(E)

        lb_b, ub_b = self.get_symmetric_bounds(cov_BY_BY, self.tlb)
        seed_b = int(rng.integers(0, numpy.iinfo(numpy.int32).max))
        z_b_truncated = TruncatedMVN(
            numpy.zeros(N, F32), cov_BY_BY, F32(lb_b), F32(ub_b), seed=seed_b
        ).sample(E)

        arr = mu_Y.flatten()[:, numpy.newaxis] + z_w_truncated + z_b_truncated
        return arr


@dataclass
class Input:
    """
    Container for the conditioned GMFs parameters
    """
    sites_Y: list = ()
    sites_D: list = ()
    imts_Y: list = ()
    imts_D: list = ()
    stations: pandas.DataFrame = ()
    within_event_model: object = 0
    between_event_model: object = 0
    separable_cross_imt_model: object = 0
    correlation_context: object = None


@dataclass
class StationConditioning:
    """All-IMT station system used by joint Gaussian conditioning."""
    zeta_D: numpy.ndarray
    observed_imts: tuple
    latent_imts: tuple
    observation_mask: numpy.ndarray
    observed_imt_indices: numpy.ndarray
    full_phi_D: numpy.ndarray
    phi_D: numpy.ndarray
    tau_D: numpy.ndarray
    observation_stddev: numpy.ndarray
    T_D: numpy.ndarray
    cov_HD_HD: numpy.ndarray
    cov_YD_YD: numpy.ndarray
    cov_YD_YD_inv: numpy.ndarray

    def solve(self, right_hand_side):
        """Apply the precomputed station covariance pseudoinverse."""
        return self.cov_YD_YD_inv @ right_hand_side


def build_station_conditioning(inp, mean_stds_D, DD):
    """Build the small joint covariance system at observation sites."""
    imts_D = tuple(inp.imts_D)
    num_stations = len(inp.sites_D)
    y_D = numpy.array([
        numpy.log(inp.stations[imt.string + '_mean'].to_numpy(float))
        for imt in imts_D])
    observation_stddev = numpy.array([
        inp.stations[imt.string + '_std'].to_numpy(float)
        for imt in imts_D])
    valid = numpy.isfinite(y_D) & numpy.isfinite(observation_stddev)
    valid = valid.reshape(-1)
    if not valid.any():
        raise ValueError('The station data contains no usable observations')

    mu_YD = numpy.asarray(mean_stds_D[0, 0], dtype=numpy.float64)
    tau = numpy.asarray(mean_stds_D[2, 0], dtype=numpy.float64)
    phi = numpy.asarray(mean_stds_D[3, 0], dtype=numpy.float64)
    zeta_D = (y_D - mu_YD).reshape(-1)[valid]
    tau_D = tau.reshape(-1)[valid]
    phi_D = phi.reshape(-1)[valid]

    latent_imts = tuple(dict.fromkeys([*inp.imts_Y, *imts_D]))
    latent_index = {imt: i for i, imt in enumerate(latent_imts)}
    observed_imt_indices = numpy.repeat(
        [latent_index[imt] for imt in imts_D], num_stations)[valid]
    T_D = numpy.zeros(
        (len(zeta_D), len(latent_imts)), dtype=numpy.float64)
    T_D[numpy.arange(len(zeta_D)), observed_imt_indices] = tau_D

    full_phi_D = phi.reshape(-1)
    cov_WD_WD = compute_within_event_covariance_matrix(
        inp.within_event_model, inp.separable_cross_imt_model, DD,
        imts_D, imts_D, full_phi_D, full_phi_D,
        inp.correlation_context, dtype=numpy.float64)
    cov_WD_WD = numpy.asarray(cov_WD_WD, dtype=numpy.float64)
    cov_WD_WD = cov_WD_WD[numpy.ix_(valid, valid)]
    observation_variance = observation_stddev.reshape(-1)[valid] ** 2
    numpy.fill_diagonal(
        cov_WD_WD, numpy.diag(cov_WD_WD) + observation_variance)

    cov_HD_HD = numpy.asarray(
        inp.between_event_model.correlation_matrix(latent_imts),
        dtype=numpy.float64)
    cov_YD_YD = cov_WD_WD + T_D @ cov_HD_HD @ T_D.T
    cov_YD_YD_inv = numpy.linalg.pinv(cov_YD_YD, hermitian=True)
    projected_residual = cov_YD_YD @ cov_YD_YD_inv @ zeta_D
    if not numpy.allclose(
            projected_residual, zeta_D, rtol=1E-9, atol=1E-12):
        raise ValueError(
            'Station observations are incompatible with their singular '
            'covariance matrix')
    return StationConditioning(
        zeta_D, imts_D, latent_imts, valid, observed_imt_indices,
        full_phi_D, phi_D, tau_D, observation_stddev.reshape(-1)[valid],
        T_D, cov_HD_HD, cov_YD_YD,
        cov_YD_YD_inv)


def _target_grid(inp):
    """Return the regular target sites after excluding station locations."""
    is_station = numpy.isin(inp.sites_Y.sids, inp.sites_D.sids)
    grid_sites = inp.sites_Y.filter(~is_station)
    if grid_sites is None or len(grid_sites) < 4:
        raise ValueError(
            'Circulant conditioning requires at least four non-station '
            'target grid sites')
    return grid_sites


def _conditioning_layout(inp, order):
    """Fit the target lattice and pad it around the station sites."""
    layout = RegularGridLayout.from_sites(_target_grid(inp))
    return layout.expanded(inp.sites_D, order)


def _target_locations(inp, layout):
    """Map target sites to grid cells or matching off-grid stations."""
    rows, columns = layout.grid_coordinates(inp.sites_Y)
    rounded_rows = numpy.rint(rows)
    rounded_columns = numpy.rint(columns)
    on_grid = (
        (numpy.abs(rows - rounded_rows) <= GRID_TOLERANCE) &
        (numpy.abs(columns - rounded_columns) <= GRID_TOLERANCE))
    on_grid_targets = numpy.flatnonzero(on_grid)
    on_grid_rows = rounded_rows[on_grid].astype(int)
    on_grid_columns = rounded_columns[on_grid].astype(int)
    if (numpy.any(on_grid_rows < 0) or
            numpy.any(on_grid_rows >= layout.grid_shape[0]) or
            numpy.any(on_grid_columns < 0) or
            numpy.any(on_grid_columns >= layout.grid_shape[1])):
        raise ValueError('An on-grid target lies outside the CE grid')
    grid_cells = (
        on_grid_rows * layout.grid_shape[1] + on_grid_columns)

    off_grid_targets = numpy.flatnonzero(~on_grid)
    station_by_sid = {
        sid: index for index, sid in enumerate(inp.sites_D.sids)}
    try:
        station_indices = numpy.array([
            station_by_sid[inp.sites_Y.sids[index]]
            for index in off_grid_targets], dtype=numpy.int64)
    except KeyError as exc:
        raise ValueError(
            'An off-grid target does not correspond to a station') from exc
    return (on_grid_targets, grid_cells, off_grid_targets,
            station_indices)


@dataclass(frozen=True)
class CirculantConditioningSampler:
    """Generate paired target and station draws from one joint prior."""

    grid_factor: CirculantEmbeddingFactor
    station_factor: LocalKrigingFactor
    target_imt_indices: numpy.ndarray
    on_grid_targets: numpy.ndarray
    target_grid_cells: numpy.ndarray
    off_grid_targets: numpy.ndarray
    target_station_indices: numpy.ndarray
    observation_field_indices: numpy.ndarray
    between_root: numpy.ndarray

    @property
    def nbytes(self):
        """Return bytes retained by the CE and station factors."""
        arrays = (
            self.grid_factor.spectral_root,
            self.grid_factor.site_indices,
            self.target_imt_indices,
            self.on_grid_targets,
            self.target_grid_cells,
            self.off_grid_targets,
            self.target_station_indices,
            self.observation_field_indices,
            self.between_root)
        return (sum(array.nbytes for array in arrays) +
                self.station_factor.nbytes)

    @classmethod
    def build(cls, inp, station, order=4, layout=None):
        """Build the CE and local-kriging factors for one station system."""
        model = inp.within_event_model
        if not model.SUPPORTS_CIRCULANT_EMBEDDING:
            raise ValueError(
                f'{model.__class__.__name__} is not enabled for '
                'circulant embedding')
        if layout is None:
            layout = _conditioning_layout(inp, order)
        grid_factor = CirculantEmbeddingFactor.build(
            model, station.latent_imts, layout.grid_shape,
            layout.spacing, ResidualComponent.WITHIN_EVENT,
            inp.correlation_context)
        station_factor = LocalKrigingFactor.build(
            model, station.latent_imts, layout, inp.sites_D, order,
            ResidualComponent.WITHIN_EVENT, inp.correlation_context)
        locations = _target_locations(inp, layout)

        latent_index = {
            imt: index for index, imt in enumerate(station.latent_imts)}
        target_imt_indices = numpy.array([
            latent_index[imt] for imt in inp.imts_Y], dtype=numpy.int64)
        num_stations = len(inp.sites_D)
        observation_sites = numpy.tile(
            numpy.arange(num_stations), len(station.observed_imts))
        observation_sites = observation_sites[station.observation_mask]
        observation_fields = (
            station.observed_imt_indices * num_stations +
            observation_sites)
        return cls(
            grid_factor, station_factor, target_imt_indices,
            *locations, observation_fields,
            covariance_root(station.cov_HD_HD))

    def draw_prior(self, rng, mean_stds_Y, station, num_events, cutoff=0):
        """Draw paired zero-mean target and noisy station prior fields."""
        white = rng.standard_normal(
            (self.grid_factor.input_size, num_events))
        grid_fields = self.grid_factor.apply(white).reshape(
            self.station_factor.num_imts, -1, num_events)
        local_errors = rng.standard_normal(
            (self.station_factor.error_size, num_events))
        station_fields = self.station_factor.apply(
            grid_fields, local_errors)

        M = len(self.target_imt_indices)
        N = mean_stds_Y.shape[-1]
        within_Y = numpy.empty((M, N, num_events))
        for m, latent_index in enumerate(self.target_imt_indices):
            within_Y[m, self.on_grid_targets] = grid_fields[
                latent_index, self.target_grid_cells]
            within_Y[m, self.off_grid_targets] = station_fields[
                latent_index, self.target_station_indices]
        phi_Y = numpy.asarray(mean_stds_Y[3, 0], dtype=numpy.float64)
        tau_Y = numpy.asarray(mean_stds_Y[2, 0], dtype=numpy.float64)
        unconditional_Y = phi_Y[:, :, None] * within_Y

        flat_stations = station_fields.reshape(
            self.station_factor.num_imts *
            self.station_factor.num_stations, num_events)
        unconditional_D = (
            station.phi_D[:, None] *
            flat_stations[self.observation_field_indices])
        H = self.between_root @ rng.standard_normal(
            (len(self.between_root), num_events))
        unconditional_Y += (
            tau_Y[:, :, None] *
            H[self.target_imt_indices, None, :])
        unconditional_D += station.T_D @ H
        unconditional_D += (
            station.observation_stddev[:, None] *
            rng.standard_normal(unconditional_D.shape))
        unconditional_Y = unconditional_Y.reshape(M * N, num_events)
        if cutoff:
            unconditional_Y += numpy.sqrt(cutoff) * rng.standard_normal(
                unconditional_Y.shape)
        return unconditional_Y, unconditional_D


def _layout_distances(layout, first, second):
    """Return projected distances in kilometres on a CE grid's CRS."""
    first_rows, first_columns = layout.grid_coordinates(first)
    second_rows, second_columns = layout.grid_coordinates(second)
    spacing_y, spacing_x = layout.spacing
    first_points = numpy.column_stack(
        (first_rows * spacing_y, first_columns * spacing_x))
    second_points = numpy.column_stack(
        (second_rows * spacing_y, second_columns * spacing_x))
    differences = first_points[:, None] - second_points[numpy.newaxis, :]
    return numpy.linalg.norm(differences, axis=-1)


@dataclass(frozen=True)
class ConditioningWeights:
    """Reusable target regression weights for Matheron substitution."""

    mu_Y: numpy.ndarray
    regression: numpy.ndarray
    station: StationConditioning

    @property
    def nbytes(self):
        station_arrays = (
            value for value in vars(self.station).values()
            if isinstance(value, numpy.ndarray))
        return (self.mu_Y.nbytes + self.regression.nbytes +
                sum(array.nbytes for array in station_arrays))

    def posterior_mean(self):
        """Return the conditional mean at all target IMTs and sites."""
        return self.mu_Y + self.regression @ self.station.zeta_D

    def condition(self, unconditional_Y, unconditional_D):
        """Apply Matheron substitution to one batch of paired priors."""
        correction = self.station.zeta_D[:, None] - unconditional_D
        return (self.mu_Y[:, None] + unconditional_Y +
                self.regression @ correction)


def build_ce_weights(inp, mean_stds_Y, station, sampler,
                     max_block_elements):
    """Build target regression weights once in bounded site chunks."""
    M = len(inp.imts_Y)
    N = len(inp.sites_Y)
    Q = len(station.zeta_D)
    full_station_values = len(inp.imts_D) * len(inp.sites_D)
    chunk_size = max(
        1, max_block_elements // (M * full_station_values))
    regression = numpy.empty((M, N, Q), dtype=numpy.float64)
    mu_Y = numpy.asarray(
        mean_stds_Y[0, 0], dtype=numpy.float64).reshape(-1)
    layout = sampler.station_factor.layout
    for start in range(0, N, chunk_size):
        stop = min(start + chunk_size, N)
        positions = numpy.arange(start, stop)
        sites_Y = inp.sites_Y.filtered(positions)
        chunk_inp = replace(inp, sites_Y=sites_Y)
        chunk_stats = mean_stds_Y[:, :, :, start:stop]
        distances = _layout_distances(layout, sites_Y, inp.sites_D)
        joint = build_joint_conditioning(
            chunk_inp, chunk_stats, station, None, distances,
            check_compatibility=start == 0)
        regression[:, start:stop] = (
            joint.cov_Y_YD @ station.cov_YD_YD_inv).reshape(
                M, stop - start, Q)
    return ConditioningWeights(
        mu_Y, regression.reshape(M * N, Q), station)


@dataclass
class JointConditioning:
    """Dense reference representation of an all-IMT target posterior."""
    mu_Y: numpy.ndarray
    cov_YY: numpy.ndarray
    cov_Y_YD: numpy.ndarray
    station: StationConditioning

    def posterior_mean(self):
        """Return the all-IMT posterior mean at the target sites."""
        return self.mu_Y + self.cov_Y_YD @ self.station.solve(
            self.station.zeta_D)

    def posterior_covariance(self, cutoff=0):
        """Return the all-IMT posterior covariance at the target sites."""
        if self.cov_YY is None:
            return None
        solved_DY = self.station.solve(self.cov_Y_YD.T)
        covariance = self.cov_YY.copy()
        covariance -= self.cov_Y_YD @ solved_DY
        covariance = (covariance + covariance.T) / 2
        numpy.fill_diagonal(
            covariance, numpy.diag(covariance) + cutoff)
        return covariance

    def mean_covariance(self):
        """Return the all-IMT posterior mean and covariance."""
        return self.posterior_mean(), self.posterior_covariance()

    def condition(self, unconditional_Y, unconditional_D):
        """Apply Matheron substitution to unconditional prior samples."""
        correction = self.station.solve(
            self.station.zeta_D[:, None] - unconditional_D)
        return (self.mu_Y[:, None] + unconditional_Y +
                self.cov_Y_YD @ correction)

    def sample(self, rng, num_events, cutoff=0):
        """Draw an exact dense Gaussian posterior reference sample."""
        covariance = self.posterior_covariance(cutoff)
        try:
            factor = numpy.linalg.cholesky(covariance)
        except numpy.linalg.LinAlgError:
            eigenvalues, eigenvectors = numpy.linalg.eigh(covariance)
            scale = max(numpy.abs(eigenvalues).max(), 1.0)
            tolerance = len(covariance) * numpy.finfo(float).eps * scale
            if eigenvalues.min() < -tolerance:
                raise ValueError(
                    'The conditioned covariance is not positive '
                    'semidefinite')
            factor = eigenvectors * numpy.sqrt(eigenvalues.clip(min=0))
        samples = factor @ rng.standard_normal(
            (len(covariance), num_events))
        return self.posterior_mean()[:, None] + samples


def build_joint_conditioning(
        inp, mean_stds_Y, station, YY, YD,
        check_compatibility=True):
    """Build a dense all-IMT target prior and target-station block."""
    imts_Y = tuple(inp.imts_Y)
    num_targets = len(inp.sites_Y)
    mu_Y = numpy.asarray(
        mean_stds_Y[0, 0], dtype=numpy.float64).reshape(-1)
    tau_Y = numpy.asarray(
        mean_stds_Y[2, 0], dtype=numpy.float64).reshape(-1)
    phi_Y = numpy.asarray(
        mean_stds_Y[3, 0], dtype=numpy.float64).reshape(-1)

    latent_index = {imt: i for i, imt in enumerate(station.latent_imts)}
    target_imt_indices = numpy.repeat(
        [latent_index[imt] for imt in imts_Y], num_targets)
    T_Y = numpy.zeros(
        (len(mu_Y), len(station.latent_imts)), dtype=numpy.float64)
    T_Y[numpy.arange(len(mu_Y)), target_imt_indices] = tau_Y

    if YY is None:
        cov_WY_WY = None
    else:
        cov_WY_WY = compute_within_event_covariance_matrix(
            inp.within_event_model, inp.separable_cross_imt_model, YY,
            imts_Y, imts_Y, phi_Y, phi_Y, inp.correlation_context,
            dtype=numpy.float64)
    cov_WY_WD = compute_within_event_covariance_matrix(
        inp.within_event_model, inp.separable_cross_imt_model, YD,
        imts_Y, station.observed_imts, phi_Y,
        station.full_phi_D,
        inp.correlation_context, dtype=numpy.float64)
    cov_WY_WD = numpy.asarray(cov_WY_WD, dtype=numpy.float64)
    cov_WY_WD = cov_WY_WD[:, station.observation_mask]

    if cov_WY_WY is None:
        cov_YY = None
    else:
        cov_YY = numpy.asarray(cov_WY_WY, dtype=numpy.float64)
        cov_YY += T_Y @ station.cov_HD_HD @ T_Y.T
    cov_Y_YD = (cov_WY_WD +
                T_Y @ station.cov_HD_HD @ station.T_D.T)
    if check_compatibility:
        projected_YD = (cov_Y_YD @ station.cov_YD_YD_inv @
                        station.cov_YD_YD)
        if not numpy.allclose(
                projected_YD, cov_Y_YD, rtol=1E-9, atol=1E-12):
            raise ValueError(
                'Target-station covariance is incompatible with the '
                'singular station covariance matrix')
    return JointConditioning(mu_Y, cov_YY, cov_Y_YD, station)


def conditioned_mean_in_chunks(
        inp, mean_stds_Y, station, max_block_elements):
    """Compute the exact all-IMT posterior mean in target-site chunks."""
    M = len(inp.imts_Y)
    N = len(inp.sites_Y)
    D = len(inp.sites_D)
    J = len(inp.imts_D)
    chunk_size = max(1, max_block_elements // (M * J * D))
    mean = numpy.empty((M, N), dtype=numpy.float64)
    for start in range(0, N, chunk_size):
        stop = min(start + chunk_size, N)
        positions = numpy.arange(start, stop)
        sites_Y = inp.sites_Y.filtered(positions)
        chunk_inp = replace(inp, sites_Y=sites_Y)
        chunk_stats = mean_stds_Y[:, :, :, start:stop]
        distances = compute_distance_matrix(sites_Y, inp.sites_D)
        joint = build_joint_conditioning(
            chunk_inp, chunk_stats, station, None, distances)
        chunk_mean = joint.posterior_mean()
        mean[:, start:stop] = chunk_mean.reshape(M, stop - start)
    return mean


@dataclass
class DResult:
    """
    Temporary data structure used inside get_mean_covs
    """
    g: int
    m: int
    imt: str
    bracketed_imts: list
    conditioning_imts: list
    native_data_available: bool
    cov_HD_HD: numpy.ndarray = 0
    cov_WD_WD_inv: numpy.ndarray = 0
    phi_D: numpy.ndarray = 0
    T_D: numpy.ndarray = 0
    zeta_D: numpy.ndarray = 0


def _createD(g, m, target_imt, imts_D, sdata):
    # returns (g, m, conditioning_imts, bracketed_imts, native_data_available)

    native_data_available = False

    if target_imt in imts_D:
        # Target IMT is present in the observed IMTs
        conditioning_imts = [target_imt]
        bracketed_imts = conditioning_imts
        native_data_available = True
    else:
        # Find where the target IMT falls in the list of observed IMTs
        all_imts = sorted(imts_D + [target_imt])
        imt_idx = numpy.where(
            target_imt.string == numpy.array(all_imts)[:, 0])[0][0]
        if imt_idx == 0:
            # Target IMT is outside the range of the observed IMT periods
            # and its period is lower than the lowest available in the
            # observed IMTs
            conditioning_imts = [all_imts[1]]
        elif imt_idx == len(all_imts) - 1:
            # Target IMT is outside the range of the observed IMT periods
            # and its period is higher than the highest available in the
            # observed IMTs
            conditioning_imts = [all_imts[-2]]
        else:
            # Target IMT is within the range of the observed IMT periods
            # and its period falls between two periods in the observed IMTs
            conditioning_imts = [all_imts[imt_idx - 1],
                                 all_imts[imt_idx + 1]]
        bracketed_imts = [target_imt] + conditioning_imts

    # Check if the station data for the IMTs shortlisted for conditioning
    # contains NaNs
    for conditioning_imt in conditioning_imts:
        num_null_values = sdata[
            conditioning_imt.string + "_mean"].isna().sum()
        if num_null_values:
            raise ValueError(
                f"The station data contains {num_null_values}"
                f" null values for {target_imt.string}."
                " Please fill or discard these rows.")
    t = DResult(g, m, target_imt, bracketed_imts, conditioning_imts,
                native_data_available)
    return t


def createD(g, m, target_imt, inp, mean_stds_D, DD):
    """
    :returns: a DResult object containing correlation matrices of size DxD
    """
    sdata = {}
    for im, ms in zip(inp.imts_D, mean_stds_D.transpose(2, 0, 1, 3)):
        sdata[im.string + "_mean"] = inp.stations[im.string + "_mean"]
        sdata[im.string + "_std"] = inp.stations[im.string + "_std"]
        sdata[im.string + "_median"] = ms[0, 0]
        sdata[im.string + "_sigma"] = ms[1, 0]
        sdata[im.string + "_tau"] = ms[2, 0]
        sdata[im.string + "_phi"] = ms[3, 0]
    sdata = pandas.DataFrame(sdata)
    t = _createD(g, m, target_imt, inp.imts_D, sdata)

    # Observations (recorded values at the stations)
    y_D = numpy.log(
        sdata[[c_imt.string + "_mean" for c_imt in t.conditioning_imts]]
    ).values.reshape((-1, 1), order="F")

    # Additional sigma for the observations that are uncertain
    # These arise if the values for this particular IMT were not
    # directly recorded, but obtained by conversion equations or
    # cross-correlation functions
    observation_variance = sdata[
        [c_imt.string + "_std" for c_imt in t.conditioning_imts]
    ].values.reshape(-1, order="F") ** 2

    # Predicted mean at the observation points, from GSIM(s)
    mu_YD = sdata[
        [c_imt.string + "_median" for c_imt in t.conditioning_imts]
    ].values.reshape((-1, 1), order="F")
    # Predicted uncertainty components at the observation points
    # from GSIM(s)
    phi_D = sdata[
        [c_imt.string + "_phi" for c_imt in t.conditioning_imts]
    ].values.reshape((-1, 1), order="F")
    tau_D = sdata[
        [c_imt.string + "_tau" for c_imt in t.conditioning_imts]
    ].values.reshape((-1, 1), order="F")

    if t.native_data_available:
        t.T_D = tau_D
    else:
        nss = len(inp.sites_D)  # number of station sites
        t.T_D = numpy.zeros(
            (len(t.conditioning_imts) * nss, len(t.bracketed_imts)))
        for i in range(len(t.conditioning_imts)):
            t.T_D[i * nss: (i + 1) * nss, i + 1] = tau_D[
                i * nss: (i + 1) * nss, 0]

    # The raw residuals
    t.zeta_D = y_D - mu_YD
    t.phi_D = phi_D.flatten()

    cov_WD_WD = compute_within_event_covariance_matrix(
        inp.within_event_model, inp.separable_cross_imt_model, DD,
        t.conditioning_imts, t.conditioning_imts, t.phi_D, t.phi_D,
        inp.correlation_context)

    # Add on the additional variance of the residuals
    # for the cases where the station data is uncertain
    numpy.fill_diagonal(
        cov_WD_WD, numpy.diag(cov_WD_WD) + observation_variance)

    # Get the (pseudo)-inverse of the station data within-event covariance
    # matrix
    t.cov_WD_WD_inv = numpy.linalg.pinv(cov_WD_WD)

    # # The normalized between-event residual and its variance (for the
    # # observation points)
    # # Engler et al. (2022) equations 12 and 13; assumes between event
    # # residuals are perfectly cross-correlated
    # var_H_y2 = 1.0 / (
    #     1.0 + tau_y2.T @ cov_W2_W2_inv @ tau_y2
    # )
    # mu_H_y2 = tau_y2.T @ cov_W2_W2_inv @ zeta * var_H_y2
    # The more generic equations B8 and B9 from Appendix B are used instead
    # requiring the computation of the covariance matrix Σ_HD_HD, which is
    # just the matrix of cross-correlations for the observed IMTs, since
    # H is the normalized between-event residual
    t.cov_HD_HD = inp.between_event_model.correlation_matrix(
        t.bracketed_imts)
    return t


def compute_distance_matrix(sites1, sites2):
    """
    :param sites1: N1 sites
    :param sites2: N2 sites
    :returns:
       a matrix of shape N1 x N2 of float32 distances (~37 GB for 100k sites)
    """
    avail_gb = psutil.virtual_memory().available / 1024**3
    req_gb = len(sites1) * len(sites2) * 8 / 1024**3
    if req_gb > avail_gb:
        raise MemoryError('The distance_matrix of shape (%d, %d) is too large!'
                          % (len(sites1), len(sites2)))
    distance_matrix = geodetic_distance(
        sites1.lons.reshape(-1, 1), sites1.lats.reshape(-1, 1),
        sites2.lons, sites2.lats)
    return distance_matrix


# called only by _get_separable_correlation_matrix
def _get_separable_correlation_block(
        imt_1, imt_2, spatial_model, cross_imt_model, distance_matrix):
    if imt_1 == imt_2:
        # since we have a single IMT, there are no cross-correlation terms
        return spatial_model.correlation_matrix(distance_matrix, imt_1)
    matrix1 = spatial_model.correlation_matrix(distance_matrix, imt_1)
    matrix2 = spatial_model.correlation_matrix(distance_matrix, imt_2)
    spatial_correlation_matrix = numpy.maximum(matrix1, matrix2)
    cross_corr_coeff = cross_imt_model.rho(imt_1, imt_2)
    return spatial_correlation_matrix * F32(cross_corr_coeff)


def _get_separable_correlation_matrix(
        spatial_model, cross_imt_model, distance_matrix, imts1, imts2):
    # The correlation structure for IMs of differing types at differing
    # locations can be reasonably assumed as Markovian in nature, and we
    # assume here that the correlation between differing IMs at differing
    # locations is simply the product of the cross correlation of IMs i and j
    # at the same location and the spatial correlation due to the distance
    # between sites m and n. This branch retains that historical approximation
    # for spatial-only models.
    rho = [[_get_separable_correlation_block(
        imt_1, imt_2, spatial_model, cross_imt_model, distance_matrix)
            for imt_2 in imts2] for imt_1 in imts1]
    return numpy.block(rho)


def compute_within_event_covariance_matrix(
        within_event_model, separable_cross_imt_model, distance_matrix,
        imts1, imts2, stddev1, stddev2, context=None, dtype=F32):
    """Return a scaled within-event covariance block.

    Spatial-only models retain the historical separable approximation.
    Joint models supply the spatial cross-IMT correlation directly.
    """
    if isinstance(within_event_model, SpatialCorrelationModel):
        covariance = _get_separable_correlation_matrix(
            within_event_model, separable_cross_imt_model,
            distance_matrix, imts1, imts2)
    else:
        covariance = within_event_model.correlation_block(
            distance_matrix, imts1, imts2,
            ResidualComponent.WITHIN_EVENT, context)
    expected = (
        len(imts1) * distance_matrix.shape[0],
        len(imts2) * distance_matrix.shape[1])
    if covariance.shape != expected:
        raise ValueError(
            f'Expected within-event correlation shape {expected}, got '
            f'{covariance.shape}')
    covariance = numpy.array(covariance, dtype=dtype, copy=True)
    covariance *= stddev1.astype(dtype)[:, numpy.newaxis]
    covariance *= stddev2.astype(dtype)[numpy.newaxis, :]
    return covariance


# In scenario/case_21 one has
# target_imt = PGA = imts_Y = imts_D
# ctx_Y with 571 elements, like target_sitecol
# station_data has 140 elements like station_sitecol
# 18 sites are discarded
# the total sitecol has 571 + 140 + 18 = 729 sites
# NB: this is run in parallel
class Conditioner:
    def __init__(self, g, gsim, inp, mean_stds, mean_stds_D):
        self.args = (g, gsim, inp, mean_stds, mean_stds_D)

    @property
    def g(self):
        return self.args[0]

    @property
    def gsim(self):
        return self.args[1]

    @property
    def inp(self):
        return self.args[2]

    @property
    def mean_stds_Y(self):
        return self.args[3]

    @property
    def mean_stds_D(self):
        return self.args[4]

    # Using Bayes rule, compute the posterior distribution of the
    # normalized between-event residual H_D | Y_D=y_D, employing
    # Engler et al. (2022), eqns B8 and B9 (also B18 and B19),
    # H|Y2=y2 is normally distributed with mean and covariance
    def get_mu_tau_phi(self, m, target_imt, monitor, compute_covs=True):
        # NB: mean_stds matrices have shape (4, 1, M, N)
        g, gsim, inp, mean_stds, mean_stds_D = self.args

        # build temporary matrices of shape DD (#stations)
        with monitor.shared['DD'] as DD:
            t = createD(g, m, target_imt, inp, mean_stds_D, DD)

        cov_HD_HD_yD = numpy.linalg.pinv(
            t.T_D.T @ t.cov_WD_WD_inv @ t.T_D +
            numpy.linalg.pinv(t.cov_HD_HD))

        mu_HD_yD = (cov_HD_HD_yD @ t.T_D.T @ t.cov_WD_WD_inv @
                    t.zeta_D)

        # Compute the distribution of the conditional between-event
        # residual B|Y2=y2
        mu_BD_yD = t.T_D @ mu_HD_yD
        cov_BD_BD_yD = t.T_D @ cov_HD_HD_yD @ t.T_D.T

        # Get the nominal bias and its standard deviation as the means of the
        # conditional between-event residual mean and standard deviation
        nominal_bias_mean = numpy.mean(mu_BD_yD)
        nominal_bias_stddev = numpy.sqrt(numpy.mean(numpy.diag(cov_BD_BD_yD)))

        msg = ("GSIM: %s, IMT: %s, Nominal bias mean: %.3f, "
               "Nominal bias stddev: %.3f" % (
                   gsim.gmpe if hasattr(gsim, 'gmpe') else gsim,
                   t.imt, nominal_bias_mean, nominal_bias_stddev))

        # Predicted mean at the target sites, from GSIM
        mu_Y = mean_stds[0, 0, m, :, numpy.newaxis]

        # Predicted uncertainty components at the target sites, from GSIM
        tau_Y = mean_stds[2, 0, m, :, numpy.newaxis]
        phi_Y = mean_stds[3, 0, m]

        # Compute the within-event covariance matrices for the
        # target sites and observation sites; the shapes are
        # (nsites, nstations) and (nstations, nsites) respectively
        with monitor.shared['YD'] as YD:
            cov_WY_WD = compute_within_event_covariance_matrix(
                inp.within_event_model, inp.separable_cross_imt_model, YD,
                [t.imt], t.conditioning_imts, phi_Y, t.phi_D,
                inp.correlation_context)

        # Compute the regression coefficient matrix [cov_WY_WD × cov_WD_WD_inv]
        RC = cov_WY_WD @ t.cov_WD_WD_inv  # shape (nsites, nstations)

        # Compute the conditioned mean of the ground motion
        # at the target sites; shape (nsites, 1)
        mu_Y_yD = (mu_Y + tau_Y @ mu_HD_yD[0, numpy.newaxis] +
                   RC @ (t.zeta_D - mu_BD_yD)).astype(F32)

        if not compute_covs:
            return mu_Y_yD, None, None, msg

        cov_WY_WY_wD, cov_BY_BY_yD = _compute_target_covs(
            t, inp, phi_Y, tau_Y, RC, cov_HD_HD_yD, monitor)
        return mu_Y_yD, cov_WY_WY_wD, cov_BY_BY_yD, msg


def _compute_target_covs(
        t, inp, phi_Y, tau_Y, RC, cov_HD_HD_yD, monitor):
    """Compute the covariance matrices required for random fields."""
    with monitor.shared['DY'] as DY:
        cov_WD_WY = compute_within_event_covariance_matrix(
            inp.within_event_model, inp.separable_cross_imt_model, DY,
            t.conditioning_imts, [t.imt], t.phi_D, phi_Y,
            inp.correlation_context)

    # This is the dominant piece, both in time and memory.
    with (monitor.shared['YY'] as YY,
          monitor('computing cov_Y_Y', measuremem=True)):
        cov_WY_WY = compute_within_event_covariance_matrix(
            inp.within_event_model, inp.separable_cross_imt_model, YY,
            [t.imt], [t.imt], phi_Y, phi_Y,
            inp.correlation_context)

        # Historical elementwise clipping is retained for compatibility.
        # It is not part of Engler et al. (2022), equation B17.
        cov_WY_WY_wD = (cov_WY_WY - RC @ cov_WD_WY).clip(
            min=0).astype(F32)

        # Scaling matrix for the conditioned between-event covariance.
        if t.native_data_available:
            C = (tau_Y - RC @ t.T_D).astype(F32)
        else:
            N = len(inp.sites_Y)
            zeros = numpy.zeros((N, len(t.conditioning_imts)), F32)
            C = (numpy.block([tau_Y, zeros]) - RC @ t.T_D).astype(F32)

        # Apply the same historical clipping to the second B17 term.
        cov_BY_BY_yD = (C @ cov_HD_HD_yD.astype(F32) @ C.T).clip(min=0)
    return cov_WY_WY_wD, cov_BY_BY_yD


def build_precomputed(rupture, cmaker, inp, compute_covs=True):
    """
    :param rupture: hazardlib rupture
    :param cmaker: ContextMaker
    :param inp: Input with sites, imts, stations and correlation params
    :param compute_covs: build matrices required only for random fields
    :return: Precomputed(ctx_Y, ctx_D, YY, YD, DY, DD, mtp_args) tuple
    """
    pre = get_precomputed(rupture, cmaker, inp, compute_covs)
    correlation_models = [
        inp.within_event_model, inp.between_event_model]
    if isinstance(inp.within_event_model, SpatialCorrelationModel):
        correlation_models.append(inp.separable_cross_imt_model)
    for g, gsim in enumerate(cmaker.gsims):
        if gsim.DEFINED_FOR_STANDARD_DEVIATION_TYPES == {StdDev.TOTAL}:
            if not (type(gsim).__name__ == "ModifiableGMPE"
                    and "add_between_within_stds" in gsim.kwargs):
                raise NoInterIntraStdDevs(gsim)

        # NB: there are relatively few stations, so cm.get_mean_stds([ctx_D])
        # is fast and done sequentially, while ctx_Y is done in parallel
        imts_D = select_observed_imts(
            inp.imts_Y, inp.imts_D, gsim, correlation_models)
        skipped = [imt.string for imt in conditionable_imts(inp.imts_D)
                   if imt not in imts_D]
        if skipped:
            logging.info(
                'Skipping station IMTs unsupported by %s and its '
                'correlation models: %s', gsim.__class__.__name__,
                ', '.join(skipped))
        if not imts_D:
            raise ValueError(
                'The station data contains no IMTs supported by '
                f'{gsim.__class__.__name__} and its correlation models')
        branch_inp = replace(inp, imts_D=imts_D)
        gdict = {gsim: cmaker.gsims[gsim]}
        cm_D = cmaker.copy(imtls={im.string: [0] for im in imts_D},
                           gsims=gdict)
        mean_stds_D = cm_D.get_mean_stds([pre.ctx_D])
        cm_Y = cmaker.copy(
            imtls={imt.string: [0] for imt in inp.imts_Y}, gsims=gdict)
        mean_stds_Y = cm_Y.get_mean_stds([pre.ctx_Y])  # fast enough
        pre.conditioners.append(Conditioner(
            g, gsim, branch_inp, mean_stds_Y, mean_stds_D))
    return pre


def use_joint_conditioning(computer):
    """Return whether the within-event model requires joint conditioning."""
    return not isinstance(
        computer.inp.within_event_model, SpatialCorrelationModel)


def use_joint_gaussian_sampling(computer):
    """Return whether untruncated joint Gaussian sampling is requested."""
    return (computer.cmaker.oq.truncated_mvn is False or
            (computer.tlw == 99 and computer.tlb == 99))


def use_circulant_conditioning(computer):
    """Return whether the scalable joint conditioning path is eligible."""
    model = computer.inp.within_event_model
    return (use_joint_conditioning(computer) and
            getattr(model, 'SUPPORTS_CIRCULANT_EMBEDDING', False) and
            getattr(computer, 'N', 0) >= CE_MIN_SITES)


def _conditioning_batch_size(computer, sampler, weights, memory_budget):
    """Bound one conditioned batch by workspace memory and output rows."""
    fixed = sampler.nbytes + weights.nbytes
    T = computer.M * computer.N
    Q = len(weights.station.zeta_D)
    per_event = (
        sampler.grid_factor.workspace_bytes_per_realization +
        32 * T + 24 * Q)
    available = memory_budget - fixed
    if available < per_event:
        required = fixed + per_event
        raise ValueError(
            'Circulant conditioning requires at least '
            f'{humansize(required)} of workspace')
    memory_events = max(1, available // per_event)
    output_events = max(
        1, int(config.memory.max_gmvs_chunk) // computer.N)
    return min(memory_events, output_events)


def conditioned_ce(computer, conditioner, memory_budget, monitor):
    """Yield scalable station-conditioned GMF tables in bounded batches."""
    order = 4
    layout = _conditioning_layout(conditioner.inp, order)
    DD = _layout_distances(
        layout, conditioner.inp.sites_D, conditioner.inp.sites_D)
    station = build_station_conditioning(
        conditioner.inp, conditioner.mean_stds_D, DD)
    sampler = CirculantConditioningSampler.build(
        conditioner.inp, station, order, layout)
    weights = build_ce_weights(
        conditioner.inp, conditioner.mean_stds_Y, station, sampler,
        computer.conditioning_block_elements)

    g = conditioner.g
    _gsim, rlzs = list(computer.cmaker.gsims.items())[g]
    indices, = numpy.where(numpy.isin(computer.rlz, rlzs))
    batch_size = _conditioning_batch_size(
        computer, sampler, weights, memory_budget)
    logging.info(
        'Streaming %d conditioned fields in batches of at most %d; '
        'CE factor=%s, regression weights=%s',
        len(indices), batch_size, humansize(sampler.nbytes),
        humansize(weights.nbytes))

    streams = numpy.random.SeedSequence(
        [computer.seed, g]).spawn(2)
    prior_rng = numpy.random.default_rng(streams[0])
    amplifier_rng = numpy.random.default_rng(streams[1])
    mean = weights.posterior_mean().reshape(computer.M, computer.N)
    cutoff = computer.cmaker.oq.correlation_cutoff
    cmon = monitor('conditioning gmfs', measuremem=True)
    umon = monitor('tabulating gmfs', measuremem=True)
    for start in range(0, len(indices), batch_size):
        batch_indices = indices[start:start + batch_size]
        with cmon:
            unconditional_Y, unconditional_D = sampler.draw_prior(
                prior_rng, conditioner.mean_stds_Y, station,
                len(batch_indices), cutoff)
            fields = weights.condition(
                unconditional_Y, unconditional_D).reshape(
                    computer.M, computer.N, len(batch_indices))
        with umon:
            yield computer.tabulate_conditioned(
                fields, mean, g, batch_indices, amplifier_rng)


def conditioned_joint(computer, conditioner, monitor, compute_covs):
    """Return jointly conditioned Gaussian fields for every target IMT."""
    if compute_covs and not use_joint_gaussian_sampling(computer):
        raise ValueError(
            'Finite truncated multivariate-normal sampling is not yet '
            'supported by joint within-event correlation models')
    with monitor.shared['DD'] as DD:
        station = build_station_conditioning(
            conditioner.inp, conditioner.mean_stds_D, DD)
    if compute_covs:
        with monitor.shared['YD'] as YD:
            with monitor.shared['YY'] as YY:
                joint = build_joint_conditioning(
                    conditioner.inp, conditioner.mean_stds_Y,
                    station, YY, YD)

    E = computer.E // len(computer.cmaker.gsims)
    M = len(conditioner.inp.imts_Y)
    N = len(conditioner.inp.sites_Y)
    if M != computer.M:
        raise ValueError('MMI cannot be combined with conditioned GMFs')
    MNE = numpy.zeros((M, N, E + 1), F32)
    if compute_covs:
        mean = joint.posterior_mean()
        rng = numpy.random.default_rng(computer.seed)
        samples = joint.sample(
            rng, E, computer.cmaker.oq.correlation_cutoff)
        MNE[:, :, :E] = samples.reshape(M, N, E)
    else:
        mean = conditioned_mean_in_chunks(
            conditioner.inp, conditioner.mean_stds_Y, station,
            computer.conditioning_block_elements)
        MNE[:, :, :E] = mean[:, :, None]
    MNE[:, :, E] = mean.reshape(M, N)
    return {conditioner.g: MNE}


def conditioned(computer, conditioner, monitor):
    """
    Run the conditioner object and returns meaMNE
    """
    E = computer.E // len(computer.cmaker.gsims)
    MNE = numpy.zeros((computer.M, computer.N, E + 1), F32)
    g = conditioner.g
    compute_covs = max(computer.tlw, computer.tlb) > TRUNCATION_THRESHOLD
    if use_joint_conditioning(computer):
        return conditioned_joint(
            computer, conditioner, monitor, compute_covs)
    for m, imt in enumerate(conditioner.inp.imts_Y):
        mu, ta, ph, _msg = conditioner.get_mu_tau_phi(
            m, imt, monitor, compute_covs)
        if not compute_covs:
            MNE[m, :, :E] = mu.repeat(E, axis=1)
        else:
            MNE[m, :, :E] = computer._compute_mvn(mu, ta, ph, E)
        MNE[m, :, E] = mu[:, 0]  # shape (N, 1) -> N
    return {g: MNE}


# used only in openquake/hazardlib/tests/calc/conditioned_gmfs_test.py
def get_mean_covs(rupture, cmaker, inp, sigma=True):
    """
    :returns: a list of arrays [mea, sig, tau, phi] or [mea, tau, phi]
    """
    pre = build_precomputed(rupture, cmaker, inp)
    G = len(cmaker.gsims)
    M = len(inp.imts_Y)
    N = len(pre.ctx_Y)
    me = numpy.zeros((G, M, N, 1), F32)
    ta = numpy.zeros((G, M, N, N), F32)
    ph = numpy.zeros((G, M, N, N), F32)
    monitor = performance.Monitor()
    monitor.set_shared(YY=pre.YY, YD=pre.YD, DY=pre.DY, DD=pre.DD)
    for cond in pre.conditioners:
        for m, imt in enumerate(inp.imts_Y):
            mu, tau, phi, msg = cond.get_mu_tau_phi(m, imt, monitor)
            me[cond.g, m] = mu
            ta[cond.g, m] = tau
            ph[cond.g, m] = phi
            logging.info(msg)
    if sigma:
        return [me, ta + ph, ta, ph]
    else:
        # save memory since sigma = tau + phi is not needed
        return [me, ta, ph]
