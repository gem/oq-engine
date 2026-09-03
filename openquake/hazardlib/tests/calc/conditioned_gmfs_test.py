# The Hazard Library
# Copyright (C) 2025-2026 GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
Test cases 01–10 are based on the verification tests described in the
USGS ShakeMap 4.1 Manual.
Ref: Worden, C. B., E. M. Thompson, M. Hearne, and D. J. Wald (2020).
ShakeMap Manual Online: technical manual, user’s guide, and software guide,
U.S. Geological Survey. DOI: https://doi.org/10.5066/F7D21VPQ, see
https://usgs.github.io/shakemap/manual4_0/tg_verification.html`.
"""
import unittest
from unittest import mock
from types import SimpleNamespace

import numpy
import pandas

from openquake.baselib import performance
from openquake.hazardlib.contexts import simple_cmaker
from openquake.hazardlib.correlation_models.base import (
    ResidualComponent, SpatialCrossIMTCorrelationModel)
from openquake.hazardlib.correlation_models.cross_imt.no_cross_correlation \
    import NoCrossCorrelation
from openquake.hazardlib.correlation_models.spatial_cross_imt.du_ning_2021 \
    import DuNing2021
from openquake.hazardlib.imt import from_string, MMI, PGA, PGV, SA
from openquake.hazardlib.calc.conditioned_gmfs import (
    build_joint_conditioning, build_precomputed, build_station_conditioning,
    compute_distance_matrix, conditionable_imts, conditioned,
    conditioned_mean_in_chunks, createD,
    compute_within_event_covariance_matrix, get_mean_covs, Input,
    JointConditioning, select_observed_imts, StationConditioning)
from openquake.hazardlib.tests.calc import \
    _conditioned_gmfs_test_data as test_data

aac = numpy.testing.assert_allclose


def test_pgv_is_conditionable():
    assert conditionable_imts([PGA(), PGV(), MMI()]) == [PGA(), PGV()]


def test_observed_imt_support():
    target = [PGA(), SA(0.3)]
    observed = [PGA(), PGV(), SA(0.3), MMI()]
    all_imts = SimpleNamespace(
        DEFINED_FOR_INTENSITY_MEASURE_TYPES={PGA, PGV, SA})
    spectral_only = SimpleNamespace(
        DEFINED_FOR_INTENSITY_MEASURE_TYPES={PGA, SA})
    correlation_models = [DuNing2021(), NoCrossCorrelation()]

    assert select_observed_imts(
        target, observed, all_imts, correlation_models) == observed[:3]
    assert select_observed_imts(
        target, observed, spectral_only, correlation_models) == [
            PGA(), SA(0.3)]


def test_branch_observed_imts():
    class PGVGMM(test_data.ZeroMeanGMM):
        DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, PGV, SA}

    cmaker = simple_cmaker(
        [PGVGMM(), test_data.ZeroMeanGMM()], [],
        maximum_distance=test_data.MAX_DIST, truncation_level=0)
    observed = [PGA(), PGV()]
    inp = Input(
        test_data.CASE07_TARGET_SITECOL,
        test_data.CASE07_STATION_SITECOL,
        [PGA()], observed, test_data.CASE07_STATION_DATA,
        DuNing2021(), NoCrossCorrelation(), None)

    pre = build_precomputed(test_data.RUP, cmaker, inp, compute_covs=False)
    assert pre.conditioners[0].inp.imts_D == observed
    assert pre.conditioners[1].inp.imts_D == [PGA()]


def test_joint_within_covariance():
    correlation = numpy.array([[1.0], [0.5], [0.25], [0.125]])

    class JointModel(SpatialCrossIMTCorrelationModel):
        DEFINED_FOR_RESIDUAL_COMPONENT = ResidualComponent.WITHIN_EVENT

        def correlation_block(
                self, distances, imts1, imts2=None,
                component=None, context=None):
            self.call = distances, imts1, imts2, component, context
            return correlation

    model = JointModel()
    distances = numpy.array([[0.0], [10.0]])
    imts1 = [PGA(), SA(1.0)]
    imts2 = [PGA()]
    stddev1 = numpy.array([2.0, 3.0, 4.0, 5.0])
    stddev2 = numpy.array([6.0])
    context = object()
    covariance = compute_within_event_covariance_matrix(
        model, None, distances, imts1, imts2,
        stddev1, stddev2, context)

    aac(covariance, correlation * stddev1[:, None] * stddev2)
    actual_distances, actual_imts1, actual_imts2, component, ctx = model.call
    assert actual_distances is distances
    assert actual_imts1 is imts1
    assert actual_imts2 is imts2
    assert component == ResidualComponent.WITHIN_EVENT
    assert ctx is context


def test_target_statistics_by_imt():
    class IMTDependentGMM(test_data.ZeroMeanGMM):
        def compute(self, ctx: numpy.recarray, imts,
                    mean, sig, tau, phi):
            periods = numpy.array([imt.period for imt in imts])[:, None]
            mean[:] = periods
            tau[:] = periods + 0.1
            phi[:] = periods + 0.2
            sig[:] = numpy.hypot(tau, phi)

    target_imts = [SA(0.1), SA(1.0)]
    cmaker = simple_cmaker(
        [IMTDependentGMM()], [], maximum_distance=test_data.MAX_DIST,
        truncation_level=0)
    inp = Input(
        test_data.CASE07_TARGET_SITECOL,
        test_data.CASE07_STATION_SITECOL,
        target_imts, [SA(1.0)], test_data.CASE07_STATION_DATA,
        test_data.DummySpatialCorrelationModel(),
        test_data.DummyCrossCorrelationBetween(),
        test_data.DummyCrossCorrelationWithin())

    pre = build_precomputed(test_data.RUP, cmaker, inp, compute_covs=False)
    conditioner = pre.conditioners[0]
    stats = conditioner.mean_stds_Y[:, 0, :, 0]
    aac(stats[0], [0.1, 1.0])
    aac(stats[2], [0.2, 1.1])
    aac(stats[3], [0.3, 1.2])

    monitor = performance.Monitor()
    monitor.set_shared(YD=pre.YD, DD=pre.DD)
    for m, target_imt in enumerate(target_imts):
        mean, _, _, _ = conditioner.get_mu_tau_phi(
            m, target_imt, monitor, compute_covs=False)
        aac(mean[:, 0], target_imt.period)


def test_station_error_diagonal():
    station_data = test_data.CASE01_STATION_DATA.copy()
    station_data['PGA_std'] = [0.25, 1.5]
    cmaker = simple_cmaker(
        [test_data.ZeroMeanGMM()], [],
        maximum_distance=test_data.MAX_DIST)
    inp = Input(
        test_data.CASE01_TARGET_SITECOL,
        test_data.CASE01_STATION_SITECOL,
        [PGA()], [PGA()], station_data,
        test_data.DummySpatialCorrelationModel(),
        test_data.DummyCrossCorrelationBetween(),
        test_data.DummyCrossCorrelationWithin())
    pre = build_precomputed(test_data.RUP, cmaker, inp, compute_covs=False)

    result = createD(
        0, 0, PGA(), inp, pre.conditioners[0].mean_stds_D, pre.DD)
    phi = numpy.full(2, 0.8)
    expected = compute_within_event_covariance_matrix(
        inp.within_event_model, inp.separable_cross_imt_model, pre.DD,
        [PGA()], [PGA()], phi, phi)
    numpy.fill_diagonal(
        expected, numpy.diag(expected) + numpy.array([0.25, 1.5]) ** 2)
    aac(result.cov_WD_WD_inv, numpy.linalg.pinv(expected))


def test_total_station_covariance():
    imts = [PGA(), SA(0.3)]
    station_data = test_data.CASE01_STATION_DATA.copy()
    station_data['PGA_std'] = [0.1, 0.2]
    station_data['SA(0.3)_mean'] = numpy.exp([0.3, -0.2])
    station_data['SA(0.3)_std'] = [0.3, 0.4]
    inp = Input(
        test_data.CASE01_TARGET_SITECOL,
        test_data.CASE01_STATION_SITECOL,
        imts, imts, station_data, DuNing2021(),
        NoCrossCorrelation(), None)
    distances = compute_distance_matrix(inp.sites_D, inp.sites_D)
    mean_stds_D = numpy.zeros((4, 1, 2, 2))
    mean_stds_D[2, 0] = [[0.2, 0.3], [0.4, 0.5]]
    mean_stds_D[3, 0] = [[0.6, 0.7], [0.8, 0.9]]

    system = build_station_conditioning(inp, mean_stds_D, distances)
    phi = mean_stds_D[3, 0].reshape(-1)
    expected = compute_within_event_covariance_matrix(
        inp.within_event_model, None, distances,
        imts, imts, phi, phi, dtype=numpy.float64)
    expected = expected.astype(numpy.float64)
    numpy.fill_diagonal(
        expected, numpy.diag(expected) +
        numpy.array([0.1, 0.2, 0.3, 0.4]) ** 2)
    expected += system.T_D @ system.cov_HD_HD @ system.T_D.T

    aac(system.zeta_D, [0.0, 0.0, 0.3, -0.2])
    aac(system.cov_YD_YD, expected)
    identity = numpy.eye(len(expected))
    aac(system.solve(identity), numpy.linalg.pinv(expected, hermitian=True))


def test_missing_station_observations():
    imts = [PGA(), SA(0.3)]
    station_data = test_data.CASE01_STATION_DATA.copy()
    station_data['PGA_std'] = [0.1, 0.2]
    station_data['SA(0.3)_mean'] = numpy.exp([0.3, -0.2])
    station_data['SA(0.3)_std'] = [0.3, 0.4]
    station_data.loc[1, 'PGA_mean'] = numpy.nan
    station_data.loc[0, 'SA(0.3)_std'] = numpy.nan
    inp = Input(
        test_data.CASE01_TARGET_SITECOL,
        test_data.CASE01_STATION_SITECOL,
        imts, imts, station_data, DuNing2021(),
        NoCrossCorrelation(), None)
    distances = compute_distance_matrix(inp.sites_D, inp.sites_D)
    mean_stds_D = numpy.zeros((4, 1, 2, 2))
    mean_stds_D[2, 0] = [[0.2, 0.3], [0.4, 0.5]]
    mean_stds_D[3, 0] = [[0.6, 0.7], [0.8, 0.9]]

    system = build_station_conditioning(inp, mean_stds_D, distances)
    numpy.testing.assert_array_equal(
        system.observation_mask, [True, False, False, True])
    numpy.testing.assert_array_equal(system.observed_imt_indices, [0, 1])
    aac(system.zeta_D, [0.0, -0.2])
    assert system.cov_YD_YD.shape == (2, 2)


def test_du_ning_pgv_observations():
    imts = [PGA(), PGV()]
    station_data = test_data.CASE01_STATION_DATA.copy()
    station_data['PGA_std'] = [0.1, 0.2]
    station_data['PGV_mean'] = numpy.exp([0.4, -0.2])
    station_data['PGV_std'] = [0.3, 0.4]
    inp = Input(
        test_data.CASE07_TARGET_SITECOL,
        test_data.CASE01_STATION_SITECOL,
        imts, imts, station_data, DuNing2021(),
        NoCrossCorrelation(), None)
    DD = compute_distance_matrix(inp.sites_D, inp.sites_D)
    mean_stds_D = numpy.zeros((4, 1, 2, 2))
    mean_stds_D[2, 0] = [[0.2, 0.3], [0.4, 0.5]]
    mean_stds_D[3, 0] = [[0.6, 0.7], [0.8, 0.9]]
    mean_stds_Y = numpy.zeros((4, 1, 2, 1))
    mean_stds_Y[2, 0, :, 0] = [0.25, 0.45]
    mean_stds_Y[3, 0, :, 0] = [0.65, 0.85]

    station = build_station_conditioning(inp, mean_stds_D, DD)
    mean = conditioned_mean_in_chunks(
        inp, mean_stds_Y, station, max_block_elements=8)
    aac(station.zeta_D, [0.0, 0.0, 0.4, -0.2])
    assert mean.shape == (2, 1)
    assert numpy.all(numpy.isfinite(mean))
    assert mean[1, 0] != 0


def _engler_posterior(mu_Y, zeta_D, cov_WD_WD, cov_WY_WD,
                       cov_WY_WY, T_D, T_Y, cov_HD_HD):
    """Evaluate Engler et al. (2022), equations B8-B9 and B16-B17."""
    inverse_WD = numpy.linalg.pinv(cov_WD_WD, hermitian=True)
    cov_HD_HD_yD = numpy.linalg.pinv(
        T_D.T @ inverse_WD @ T_D + numpy.linalg.pinv(cov_HD_HD),
        hermitian=True)
    mu_HD_yD = cov_HD_HD_yD @ T_D.T @ inverse_WD @ zeta_D
    RC = cov_WY_WD @ inverse_WD
    C = T_Y - RC @ T_D
    mu_Y_yD = mu_Y + T_Y @ mu_HD_yD + RC @ (
        zeta_D - T_D @ mu_HD_yD)
    cov_YY_yD = (cov_WY_WY - RC @ cov_WY_WD.T +
                  C @ cov_HD_HD_yD @ C.T)
    return mu_Y_yD, cov_YY_yD


def test_engler_equivalence():
    imts = [PGA(), SA(0.3)]
    spatial = numpy.array([
        [1.0, 0.4, 0.2],
        [0.4, 1.0, 0.3],
        [0.2, 0.3, 1.0]])
    cross_imt = numpy.array([[1.0, 0.5], [0.5, 1.0]])
    complete = numpy.kron(cross_imt, spatial)
    target_indices = [0, 3]
    station_indices = [1, 2, 4, 5]
    blocks = {
        (1, 1): complete[numpy.ix_(target_indices, target_indices)],
        (1, 2): complete[numpy.ix_(target_indices, station_indices)],
        (2, 2): complete[numpy.ix_(station_indices, station_indices)]}

    class MatrixModel(SpatialCrossIMTCorrelationModel):
        DEFINED_FOR_RESIDUAL_COMPONENT = ResidualComponent.WITHIN_EVENT

        def correlation_block(self, distances, imts1, imts2=None,
                              component=None, context=None):
            return blocks[distances.shape]

    zeta_D = numpy.array([[0.4, -0.3], [0.2, 0.1]])
    predicted_D = numpy.array([[0.1, -0.1], [0.2, -0.2]])
    stations = {
        'PGA_mean': numpy.exp(predicted_D[0] + zeta_D[0]),
        'PGA_std': [0.1, 0.2],
        'SA(0.3)_mean': numpy.exp(predicted_D[1] + zeta_D[1]),
        'SA(0.3)_std': [0.15, 0.25]}
    between = numpy.array([[1.0, 0.35], [0.35, 1.0]])
    inp = Input(
        range(1), range(2), imts, imts, pandas.DataFrame(stations),
        MatrixModel(),
        SimpleNamespace(correlation_matrix=lambda _: between), None)
    mean_stds_D = numpy.zeros((4, 1, 2, 2))
    mean_stds_D[0, 0] = predicted_D
    mean_stds_D[2, 0] = [[0.2, 0.3], [0.4, 0.5]]
    mean_stds_D[3, 0] = [[0.6, 0.7], [0.8, 0.9]]
    mean_stds_Y = numpy.zeros((4, 1, 2, 1))
    mean_stds_Y[0, 0, :, 0] = [1.0, 2.0]
    mean_stds_Y[2, 0, :, 0] = [0.25, 0.45]
    mean_stds_Y[3, 0, :, 0] = [0.65, 0.85]

    station = build_station_conditioning(
        inp, mean_stds_D, numpy.zeros((2, 2)))
    joint = build_joint_conditioning(
        inp, mean_stds_Y, station,
        numpy.zeros((1, 1)), numpy.zeros((1, 2)))

    phi_D = numpy.array([0.6, 0.7, 0.8, 0.9])
    phi_Y = numpy.array([0.65, 0.85])
    tau_D = numpy.array([
        [0.2, 0.0], [0.3, 0.0], [0.0, 0.4], [0.0, 0.5]])
    tau_Y = numpy.array([[0.25, 0.0], [0.0, 0.45]])
    cov_WD_WD = (blocks[(2, 2)] * phi_D[:, None] * phi_D +
                 numpy.diag([0.1, 0.2, 0.15, 0.25]) ** 2)
    cov_WY_WD = blocks[(1, 2)] * phi_Y[:, None] * phi_D
    cov_WY_WY = blocks[(1, 1)] * phi_Y[:, None] * phi_Y
    aac(station.cov_YD_YD, cov_WD_WD + tau_D @ between @ tau_D.T)
    aac(joint.cov_Y_YD, cov_WY_WD + tau_Y @ between @ tau_D.T)
    aac(joint.cov_YY, cov_WY_WY + tau_Y @ between @ tau_Y.T)
    expected_mean, expected_covariance = _engler_posterior(
        numpy.array([1.0, 2.0]), zeta_D.reshape(-1),
        cov_WD_WD, cov_WY_WD, cov_WY_WY,
        tau_D, tau_Y, between)

    mean, covariance = joint.mean_covariance()
    aac(mean, expected_mean, rtol=1E-7, atol=1E-7)
    aac(covariance, expected_covariance, rtol=1E-7, atol=1E-7)


def test_matheron_transform():
    # Paired prior draws must reproduce the Schur-complement posterior.
    imts = [PGA(), SA(0.3)]
    station_data = test_data.CASE01_STATION_DATA.copy()
    station_data['PGA_std'] = [0.1, 0.2]
    station_data['SA(0.3)_mean'] = 1.0
    station_data['SA(0.3)_std'] = [0.3, 0.4]
    inp = Input(
        test_data.CASE07_TARGET_SITECOL,
        test_data.CASE01_STATION_SITECOL,
        imts, imts, station_data, DuNing2021(),
        NoCrossCorrelation(), None)
    DD = compute_distance_matrix(inp.sites_D, inp.sites_D)
    YD = compute_distance_matrix(inp.sites_Y, inp.sites_D)
    YY = compute_distance_matrix(inp.sites_Y, inp.sites_Y)
    mean_stds_D = numpy.zeros((4, 1, 2, 2))
    mean_stds_D[2, 0] = [[0.2, 0.3], [0.4, 0.5]]
    mean_stds_D[3, 0] = [[0.6, 0.7], [0.8, 0.9]]
    mean_stds_Y = numpy.zeros((4, 1, 2, 1))
    mean_stds_Y[0, 0, :, 0] = [0.1, 0.2]
    mean_stds_Y[2, 0, :, 0] = [0.25, 0.45]
    mean_stds_Y[3, 0, :, 0] = [0.65, 0.85]

    station = build_station_conditioning(inp, mean_stds_D, DD)
    joint = build_joint_conditioning(inp, mean_stds_Y, station, YY, YD)
    mean, covariance = joint.mean_covariance()
    expected = joint.cov_YY - (
        joint.cov_Y_YD @ station.solve(joint.cov_Y_YD.T))
    aac(mean, joint.mu_Y)
    aac(covariance, expected)

    prior = numpy.block([
        [joint.cov_YY, joint.cov_Y_YD],
        [joint.cov_Y_YD.T, station.cov_YD_YD]])
    factor = numpy.linalg.cholesky(prior)
    num_targets = len(joint.mu_Y)
    transformed = joint.condition(
        factor[:num_targets], factor[num_targets:])
    centered = transformed - mean[:, None]
    aac(centered @ centered.T, covariance, atol=1E-12)


def test_joint_sampling_path():
    # A joint model must bypass the historical per-IMT calculation.
    imts = [PGA(), SA(0.3)]
    station_data = test_data.CASE01_STATION_DATA.copy()
    station_data['PGA_std'] = [0.1, 0.2]
    station_data['SA(0.3)_mean'] = 1.0
    station_data['SA(0.3)_std'] = [0.3, 0.4]
    inp = Input(
        test_data.CASE07_TARGET_SITECOL,
        test_data.CASE01_STATION_SITECOL,
        imts, imts, station_data, DuNing2021(),
        NoCrossCorrelation(), None)
    cmaker = simple_cmaker(
        [test_data.ZeroMeanGMM()], [str(imt) for imt in imts],
        maximum_distance=test_data.MAX_DIST, truncation_level=99)
    cmaker.oq.truncated_mvn = False
    cmaker.oq.correlation_cutoff = 2E-4
    pre = build_precomputed(test_data.RUP, cmaker, inp)
    assert pre.DY is None
    conditioner = pre.conditioners[0]
    conditioner.get_mu_tau_phi = mock.Mock(
        side_effect=AssertionError('legacy per-IMT path used'))
    computer = SimpleNamespace(
        E=2, M=2, N=1, seed=7, inp=inp, cmaker=cmaker,
        tlw=cmaker.truncation_level_within,
        tlb=cmaker.truncation_level_between)
    monitor = performance.Monitor()
    monitor.set_shared(YY=pre.YY, YD=pre.YD, DD=pre.DD)

    result = conditioned(computer, conditioner, monitor)[0]
    station = build_station_conditioning(
        inp, conditioner.mean_stds_D, pre.DD)
    joint = build_joint_conditioning(
        inp, conditioner.mean_stds_Y, station, pre.YY, pre.YD)
    expected = joint.sample(
        numpy.random.default_rng(7), 2, cmaker.oq.correlation_cutoff)
    mean, _ = joint.mean_covariance()
    aac(result[:, :, :2], expected.reshape(2, 1, 2))
    aac(result[:, :, 2], mean.reshape(2, 1))


def test_joint_mean_path():
    # A deterministic joint calculation must not build target covariances.
    imts = [PGA(), SA(0.3)]
    station_data = test_data.CASE01_STATION_DATA.copy()
    station_data['PGA_std'] = [0.1, 0.2]
    station_data['SA(0.3)_mean'] = numpy.exp([0.3, -0.2])
    station_data['SA(0.3)_std'] = [0.3, 0.4]
    inp = Input(
        test_data.CASE07_TARGET_SITECOL,
        test_data.CASE01_STATION_SITECOL,
        imts, imts, station_data, DuNing2021(),
        NoCrossCorrelation(), None)
    cmaker = simple_cmaker(
        [test_data.ZeroMeanGMM()], [str(imt) for imt in imts],
        maximum_distance=test_data.MAX_DIST, truncation_level=0)
    cmaker.oq.truncated_mvn = True
    pre = build_precomputed(
        test_data.RUP, cmaker, inp, compute_covs=False)
    conditioner = pre.conditioners[0]
    conditioner.get_mu_tau_phi = mock.Mock(
        side_effect=AssertionError('legacy per-IMT path used'))
    computer = SimpleNamespace(
        E=2, M=2, N=1, seed=7, inp=inp, cmaker=cmaker,
        tlw=cmaker.truncation_level_within,
        tlb=cmaker.truncation_level_between,
        conditioning_block_elements=8)
    monitor = performance.Monitor()
    monitor.set_shared(DD=pre.DD)

    result = conditioned(computer, conditioner, monitor)[0]
    station = build_station_conditioning(
        inp, conditioner.mean_stds_D, pre.DD)
    expected = conditioned_mean_in_chunks(
        inp, conditioner.mean_stds_Y, station,
        computer.conditioning_block_elements)
    aac(result[:, :, :2], numpy.repeat(expected[:, :, None], 2, axis=2))
    aac(result[:, :, 2], expected)

    computer.tlw = computer.tlb = 3
    with numpy.testing.assert_raises_regex(
            ValueError, 'Finite truncated multivariate-normal'):
        conditioned(computer, conditioner, monitor)


def test_singular_station_sampling():
    cov_YD_YD = numpy.ones((2, 2))
    station = StationConditioning(
        numpy.zeros(2), (), (), numpy.ones(2, dtype=bool),
        numpy.zeros(2, dtype=int), numpy.ones(2), numpy.ones(2),
        numpy.ones(2), numpy.ones((2, 1)), numpy.ones((1, 1)),
        cov_YD_YD, numpy.linalg.pinv(cov_YD_YD, hermitian=True))
    joint = JointConditioning(
        numpy.array([0.5]), numpy.ones((1, 1)),
        numpy.ones((1, 2)), station)

    samples = joint.sample(numpy.random.default_rng(7), 3)
    aac(samples, numpy.full((1, 3), 0.5), atol=1E-12)


def test_incompatible_station_system():
    stations = pandas.DataFrame({
        'PGA_mean': [1.0, numpy.e],
        'PGA_std': [0.0, 0.0]})
    inp = Input(
        range(1), range(2), [PGA()], [PGA()], stations,
        DuNing2021(), NoCrossCorrelation(), None)
    mean_stds_D = numpy.zeros((4, 1, 1, 2))
    mean_stds_D[2, 0] = 0.6
    mean_stds_D[3, 0] = 0.8

    with numpy.testing.assert_raises_regex(
            ValueError, 'incompatible with their singular covariance'):
        build_station_conditioning(
            inp, mean_stds_D, numpy.zeros((2, 2)))

    inp.stations['PGA_mean'] = 1.0
    station = build_station_conditioning(
        inp, mean_stds_D, numpy.zeros((2, 2)))
    mean_stds_Y = numpy.zeros((4, 1, 1, 1))
    mean_stds_Y[2, 0] = 0.6
    mean_stds_Y[3, 0] = 0.8
    joint = build_joint_conditioning(
        inp, mean_stds_Y, station,
        numpy.zeros((1, 1)), numpy.zeros((1, 2)))
    aac(joint.posterior_mean(), 0.0, atol=1E-12)


def test_chunked_joint_mean():
    imts = [PGA(), SA(0.3)]
    target_sites = test_data.CASE01_TARGET_SITECOL.filtered(
        numpy.array([0, 2, 4, 6, 8]))
    numpy.testing.assert_array_equal(target_sites.sids, [0, 2, 4, 6, 8])
    station_data = test_data.CASE01_STATION_DATA.copy()
    station_data['PGA_std'] = [0.1, 0.2]
    station_data['SA(0.3)_mean'] = numpy.exp([0.3, -0.2])
    station_data['SA(0.3)_std'] = [0.3, 0.4]
    inp = Input(
        target_sites, test_data.CASE01_STATION_SITECOL,
        imts, imts, station_data, DuNing2021(),
        NoCrossCorrelation(), None)
    DD = compute_distance_matrix(inp.sites_D, inp.sites_D)
    YD = compute_distance_matrix(inp.sites_Y, inp.sites_D)
    mean_stds_D = numpy.zeros((4, 1, 2, 2))
    mean_stds_D[2, 0] = [[0.2, 0.3], [0.4, 0.5]]
    mean_stds_D[3, 0] = [[0.6, 0.7], [0.8, 0.9]]
    mean_stds_Y = numpy.zeros((4, 1, 2, 5))
    mean_stds_Y[0, 0, 0] = numpy.arange(5) / 10
    mean_stds_Y[0, 0, 1] = numpy.arange(5) / 5
    mean_stds_Y[2, 0] = 0.4
    mean_stds_Y[3, 0] = 0.8

    station = build_station_conditioning(inp, mean_stds_D, DD)
    full = build_joint_conditioning(
        inp, mean_stds_Y, station, None, YD)
    expected, _ = full.mean_covariance()
    block_for_two_sites = 2 * len(imts) * len(imts) * len(inp.sites_D)
    chunked = conditioned_mean_in_chunks(
        inp, mean_stds_Y, station, block_for_two_sites)
    aac(chunked, expected.reshape(2, 5))


def mc(rupture, cmaker, station_sitecol, station_data,
       observed_imt_strs, target_sitecol, target_imts,
       spatial_correl, cross_correl_between, cross_correl_within):
    observed_imts = [from_string(x) for x in observed_imt_strs]
    inp = Input(
        target_sitecol, station_sitecol,
        target_imts, observed_imts, station_data,
        spatial_correl,
        cross_correl_between,
        cross_correl_within)
    return get_mean_covs(rupture, cmaker, inp)


class SetUSGSTestCase(unittest.TestCase):
    def test_mean_only(self):
        cmaker = simple_cmaker(
            [test_data.ZeroMeanGMM()], [],
            maximum_distance=test_data.MAX_DIST, truncation_level=0)
        inp = Input(
            test_data.CASE01_TARGET_SITECOL,
            test_data.CASE01_STATION_SITECOL,
            test_data.CASE01_TARGET_IMTS,
            [from_string(imt) for imt in test_data.CASE01_OBSERVED_IMTS],
            test_data.CASE01_STATION_DATA,
            test_data.DummySpatialCorrelationModel(),
            test_data.DummyCrossCorrelationBetween(),
            test_data.DummyCrossCorrelationWithin())

        with mock.patch(
                'openquake.hazardlib.calc.conditioned_gmfs.'
                'compute_distance_matrix',
                wraps=compute_distance_matrix) as compute_distances:
            pre = build_precomputed(
                test_data.RUP, cmaker, inp, compute_covs=False)
        self.assertEqual(compute_distances.call_count, 2)
        self.assertIsNone(pre.YY)
        self.assertIsNone(pre.DY)
        monitor = performance.Monitor()
        monitor.set_shared(YD=pre.YD, DD=pre.DD)
        mu, cov_within, cov_between, _ = (
            pre.conditioners[0].get_mu_tau_phi(
                0, inp.imts_Y[0], monitor, compute_covs=False))

        aac(mu, 0)
        self.assertIsNone(cov_within)
        self.assertIsNone(cov_between)

    def test_case_01(self):
        case_name = "test_case_01"
        rupture = test_data.RUP
        cmaker = simple_cmaker([test_data.ZeroMeanGMM()], [],
                               maximum_distance=test_data.MAX_DIST)
        station_sitecol = test_data.CASE01_STATION_SITECOL
        station_data = test_data.CASE01_STATION_DATA
        observed_imts = test_data.CASE01_OBSERVED_IMTS
        target_sitecol = test_data.CASE01_TARGET_SITECOL
        target_imts = test_data.CASE01_TARGET_IMTS
        spatial_correl = test_data.DummySpatialCorrelationModel()
        cross_correl_between = test_data.DummyCrossCorrelationBetween()
        cross_correl_within = test_data.DummyCrossCorrelationWithin()
        mean_covs = mc(
            rupture, cmaker, station_sitecol, station_data,
            observed_imts, target_sitecol, target_imts,
            spatial_correl, cross_correl_between, cross_correl_within)
        mu = mean_covs[0][0, 0, :, 0]
        sig = numpy.sqrt(numpy.diag(mean_covs[1][0, 0]))
        aac(numpy.zeros_like(mu), mu)
        numpy.testing.assert_almost_equal(numpy.min(sig), 0)
        assert numpy.max(sig) > 0.8 and numpy.max(sig) < 1.0
        plot_test_results(target_sitecol.lons, mu, sig, 0,
                          case_name)

    def test_case_02(self):
        case_name = "test_case_02"
        rupture = test_data.RUP
        cmaker = simple_cmaker([test_data.ZeroMeanGMM()], [],
                               maximum_distance=test_data.MAX_DIST)
        station_sitecol = test_data.CASE02_STATION_SITECOL
        station_data = test_data.CASE02_STATION_DATA
        observed_imt_strs = test_data.CASE02_OBSERVED_IMTS
        target_sitecol = test_data.CASE02_TARGET_SITECOL
        target_imts = test_data.CASE02_TARGET_IMTS
        spatial_correl = test_data.DummySpatialCorrelationModel()
        cross_correl_between = test_data.DummyCrossCorrelationBetween()
        cross_correl_within = test_data.DummyCrossCorrelationWithin()
        mean_covs = mc(
            rupture, cmaker, station_sitecol, station_data,
            observed_imt_strs, target_sitecol, target_imts,
            spatial_correl, cross_correl_between, cross_correl_within)
        mu = mean_covs[0][0, 0, :, 0]
        sig = numpy.sqrt(numpy.diag(mean_covs[1][0, 0]))
        aac(numpy.min(mu), -1, rtol=1e-4)
        aac(numpy.max(mu), 1, rtol=1e-4)
        aac(numpy.min(numpy.abs(mu)), 0, atol=1e-4)
        aac(numpy.min(sig), 0, atol=1e-4)
        assert numpy.max(sig) > 0.8 and numpy.max(sig) < 1.0
        plot_test_results(target_sitecol.lons, mu, sig, 0,
                          case_name)

    def test_case_03(self):
        case_name = "test_case_03"
        rupture = test_data.RUP
        cmaker = simple_cmaker([test_data.ZeroMeanGMM()], [],
                               maximum_distance=test_data.MAX_DIST)
        station_sitecol = test_data.CASE03_STATION_SITECOL
        station_data = test_data.CASE03_STATION_DATA
        observed_imt_strs = test_data.CASE03_OBSERVED_IMTS
        target_sitecol = test_data.CASE03_TARGET_SITECOL
        target_imts = test_data.CASE03_TARGET_IMTS
        spatial_correl = test_data.DummySpatialCorrelationModel()
        cross_correl_between = test_data.DummyCrossCorrelationBetween()
        cross_correl_within = test_data.DummyCrossCorrelationWithin()
        mean_covs = mc(
            rupture, cmaker, station_sitecol, station_data,
            observed_imt_strs, target_sitecol, target_imts,
            spatial_correl, cross_correl_between, cross_correl_within)
        mu = mean_covs[0][0, 0, :, 0]
        sig = numpy.sqrt(numpy.diag(mean_covs[1][0, 0]))
        aac(numpy.min(mu), 0.36, rtol=1e-4)
        aac(numpy.max(mu), 1, rtol=1e-4)
        aac(numpy.min(sig), 0, rtol=1e-4)
        aac(numpy.max(sig), numpy.sqrt(0.8704), rtol=1e-4)
        plot_test_results(target_sitecol.lons, mu, sig, 0,
                          case_name)

    def test_case_04(self):
        case_name = "test_case_04"
        rupture = test_data.RUP
        cmaker = simple_cmaker([test_data.ZeroMeanGMM()], [],
                               maximum_distance=test_data.MAX_DIST)
        station_sitecol = test_data.CASE04_STATION_SITECOL
        station_data = test_data.CASE04_STATION_DATA
        observed_imt_strs = test_data.CASE04_OBSERVED_IMTS
        target_sitecol = test_data.CASE04_TARGET_SITECOL
        target_imts = test_data.CASE04_TARGET_IMTS
        spatial_correl = test_data.DummySpatialCorrelationModel()
        cross_correl_between = test_data.DummyCrossCorrelationBetween()
        cross_correl_within = test_data.DummyCrossCorrelationWithin()
        mean_covs = mc(
            rupture, cmaker, station_sitecol, station_data,
            observed_imt_strs, target_sitecol, target_imts,
            spatial_correl, cross_correl_between, cross_correl_within)
        mu = mean_covs[0][0, 0, :, 0]
        sig = numpy.sqrt(numpy.diag(mean_covs[1][0, 0]))
        aac(numpy.min(mu), 0.36, rtol=1e-4)
        aac(numpy.max(mu), 1)
        aac(numpy.min(sig), 0, atol=3e-4)
        aac(numpy.max(sig), numpy.sqrt(0.8704), rtol=1e-4)
        plot_test_results(target_sitecol.lons, mu, sig, 0,
                          case_name)

    def test_case_04b(self):
        case_name = "test_case_04b"
        rupture = test_data.RUP
        cmaker = simple_cmaker([test_data.ZeroMeanGMM()], [],
                               maximum_distance=test_data.MAX_DIST)
        station_sitecol = test_data.CASE04B_STATION_SITECOL
        station_data = test_data.CASE04_STATION_DATA
        observed_imt_strs = test_data.CASE04_OBSERVED_IMTS
        target_sitecol = test_data.CASE04_TARGET_SITECOL
        target_imts = test_data.CASE04_TARGET_IMTS
        spatial_correl = test_data.DummySpatialCorrelationModel()
        cross_correl_between = test_data.DummyCrossCorrelationBetween()
        cross_correl_within = test_data.DummyCrossCorrelationWithin()
        mean_covs = mc(
            rupture, cmaker, station_sitecol, station_data,
            observed_imt_strs, target_sitecol, target_imts,
            spatial_correl, cross_correl_between, cross_correl_within)
        mu = mean_covs[0][0, 0, :, 0]
        sig = numpy.sqrt(numpy.diag(mean_covs[1][0, 0]))
        aac(numpy.min(mu), 0.52970, rtol=1e-4)
        aac(numpy.max(mu), 1)
        aac(numpy.min(sig), 0, atol=3e-4)
        aac(numpy.max(sig), 0.89955, rtol=1e-4)
        plot_test_results(target_sitecol.lons, mu, sig, 0,
                          case_name)

    def test_case_05(self):
        case_name = "test_case_05"
        rupture = test_data.RUP
        cmaker = simple_cmaker([test_data.ZeroMeanGMM()], [],
                               maximum_distance=test_data.MAX_DIST)
        station_sitecol = test_data.CASE05_STATION_SITECOL
        station_data = test_data.CASE05_STATION_DATA
        observed_imt_strs = test_data.CASE05_OBSERVED_IMTS
        target_sitecol = test_data.CASE05_TARGET_SITECOL
        target_imts = test_data.CASE05_TARGET_IMTS
        spatial_correl = test_data.DummySpatialCorrelationModel()
        cross_correl_between = test_data.DummyCrossCorrelationBetween()
        cross_correl_within = test_data.DummyCrossCorrelationWithin()
        mean_covs = mc(
            rupture, cmaker, station_sitecol, station_data,
            observed_imt_strs, target_sitecol, target_imts,
            spatial_correl, cross_correl_between, cross_correl_within)
        mu = mean_covs[0][0, 0, :, 0]
        sig = numpy.sqrt(numpy.diag(mean_covs[1][0, 0]))
        aac(numpy.zeros_like(mu), mu, atol=1e-4)
        aac(numpy.min(sig), 0, atol=3e-4)
        aac(numpy.max(sig), numpy.sqrt(0.8704), rtol=1e-4)
        plot_test_results(target_sitecol.lons, mu, sig, 0,
                          case_name)

    def test_case_06(self):
        case_name = "test_case_06"
        rupture = test_data.RUP
        cmaker = simple_cmaker([test_data.ZeroMeanGMM()], [],
                               maximum_distance=test_data.MAX_DIST)
        station_sitecol = test_data.CASE06_STATION_SITECOL
        station_data = test_data.CASE06_STATION_DATA
        observed_imt_strs = test_data.CASE06_OBSERVED_IMTS
        target_sitecol = test_data.CASE06_TARGET_SITECOL
        target_imts = test_data.CASE06_TARGET_IMTS
        spatial_correl = test_data.DummySpatialCorrelationModel()
        cross_correl_between = test_data.DummyCrossCorrelationBetween()
        cross_correl_within = test_data.DummyCrossCorrelationWithin()
        mean_covs = mc(
            rupture, cmaker, station_sitecol, station_data,
            observed_imt_strs, target_sitecol, target_imts,
            spatial_correl, cross_correl_between, cross_correl_within)
        mu = mean_covs[0][0, 0, :, 0]
        sig = numpy.sqrt(numpy.diag(mean_covs[1][0, 0]))
        plot_test_results(target_sitecol.lons, mu, sig, 0,
                          case_name)

    def test_case_07(self):
        case_name = "test_case_07"
        rupture = test_data.RUP
        cmaker = simple_cmaker([test_data.ZeroMeanGMM()], [],
                               maximum_distance=test_data.MAX_DIST)
        station_sitecol = test_data.CASE07_STATION_SITECOL
        station_data = test_data.CASE07_STATION_DATA
        observed_imt_strs = test_data.CASE07_OBSERVED_IMTS
        target_sitecol = test_data.CASE07_TARGET_SITECOL
        target_imts = test_data.CASE07_TARGET_IMTS
        spatial_correl = test_data.DummySpatialCorrelationModel()
        cross_correl_between = test_data.DummyCrossCorrelationBetween()
        cross_correl_within = test_data.DummyCrossCorrelationWithin()
        mean_covs = mc(
            rupture, cmaker, station_sitecol, station_data,
            observed_imt_strs, target_sitecol, target_imts,
            spatial_correl, cross_correl_between, cross_correl_within)
        mu = mean_covs[0][0]
        sig = mean_covs[1][0]
        periods = [imt.period for imt in target_imts]
        plot_test_results_spectra(periods, mu, sig, case_name)

    def test_case_08(self):
        case_name = "test_case_08"
        rupture = test_data.RUP
        cmaker = simple_cmaker([test_data.ZeroMeanGMM()], [],
                               maximum_distance=test_data.MAX_DIST)
        station_sitecol = test_data.CASE08_STATION_SITECOL
        station_data_list = test_data.CASE08_STATION_DATA_LIST
        observed_imt_strs = test_data.CASE08_OBSERVED_IMTS
        target_sitecol = test_data.CASE08_TARGET_SITECOL
        target_imts = test_data.CASE08_TARGET_IMTS
        spatial_correl = test_data.DummySpatialCorrelationModel()
        cross_correl_between = test_data.DummyCrossCorrelationBetween()
        cross_correl_within = test_data.DummyCrossCorrelationWithin()
        std_addon_d = test_data.CASE08_STD_ADDON_D
        bias_mean = test_data.CASE08_BD_YD
        conditioned_mean_obs = test_data.CASE08_MU_YD_OBS
        conditioned_std_obs = test_data.CASE08_SIG_YD_OBS
        conditioned_std_far = test_data.CASE08_SIG_YD_FAR
        mus = []
        sigs = []
        for i, station_data in enumerate(station_data_list):
            mean_covs = mc(
                rupture, cmaker, station_sitecol, station_data,
                observed_imt_strs, target_sitecol, target_imts,
                spatial_correl, cross_correl_between, cross_correl_within)
            mu = mean_covs[0][0, 0, :, 0]
            sig = numpy.sqrt(numpy.diag(mean_covs[1][0, 0]))
            aac(numpy.min(mu), bias_mean[i], rtol=1e-4)
            aac(numpy.max(mu), conditioned_mean_obs[i], rtol=1e-4)
            aac(numpy.min(sig), conditioned_std_obs[i], rtol=1e-4)
            aac(numpy.max(sig), conditioned_std_far[i], rtol=1e-4)
            mus.append(mu)
            sigs.append(sig)
        plot_test_results_multi(target_sitecol.lons, mus, sigs, std_addon_d,
                                0, case_name)

    def test_case_09(self):
        case_name = "test_case_09"
        rupture = test_data.RUP
        cmaker = simple_cmaker([test_data.ZeroMeanGMM()], [],
                               maximum_distance=test_data.MAX_DIST)
        station_sitecol = test_data.CASE09_STATION_SITECOL
        station_data = test_data.CASE09_STATION_DATA
        observed_imt_strs = test_data.CASE09_OBSERVED_IMTS
        target_sitecol = test_data.CASE09_TARGET_SITECOL
        target_imts = test_data.CASE09_TARGET_IMTS
        spatial_correl = test_data.DummySpatialCorrelationModel()
        cross_correl_between = test_data.DummyCrossCorrelationBetween()
        cross_correl_within = test_data.DummyCrossCorrelationWithin()
        mean_covs = mc(
            rupture, cmaker, station_sitecol, station_data,
            observed_imt_strs, target_sitecol, target_imts,
            spatial_correl, cross_correl_between, cross_correl_within)
        mu = mean_covs[0][0, 0, :, 0]
        sig = numpy.sqrt(numpy.diag(mean_covs[1][0, 0]))
        plot_test_results(target_sitecol.lons, mu, sig, 0,
                          case_name)

    def test_case_10(self):
        case_name = "test_case_10"
        rupture = test_data.RUP
        cmaker = simple_cmaker([test_data.ZeroMeanGMM()], [],
                               maximum_distance=test_data.MAX_DIST)
        station_sitecol = test_data.CASE10_STATION_SITECOL
        station_data = test_data.CASE10_STATION_DATA
        observed_imt_strs = test_data.CASE10_OBSERVED_IMTS
        target_sitecol = test_data.CASE10_TARGET_SITECOL
        target_imts = test_data.CASE10_TARGET_IMTS
        spatial_correl = test_data.DummySpatialCorrelationModel()
        cross_correl_between = test_data.DummyCrossCorrelationBetween()
        cross_correl_within = test_data.DummyCrossCorrelationWithin()
        mean_covs = mc(
            rupture, cmaker, station_sitecol, station_data,
            observed_imt_strs, target_sitecol, target_imts,
            spatial_correl, cross_correl_between, cross_correl_within)
        mu = mean_covs[0][0, 0, :, 0]
        sig = numpy.sqrt(numpy.diag(mean_covs[1][0, 0]))
        plot_test_results(target_sitecol.lons, mu, sig, 0,
                          case_name)


# Functions useful for debugging purposes. Recreates the plots on
# https://usgs.github.io/shakemap/manual4_0/tg_verification.html
# Original code is from the ShakeMap plotting modules
# XTestPlot, XTestPlotSpectra, and XTestPlotMulti:
# https://github.com/usgs/shakemap/blob/main/shakemap/coremods/xtestplot.py
# https://github.com/usgs/shakemap/blob/main/shakemap/coremods/xtestplot_spectra.py
# https://github.com/usgs/shakemap/blob/main/shakemap/coremods/xtestplot_multi.py
def plot_test_results(lons, means, stds, target_imt, case_name):
    return  # remove the return to enable debug plotting
    import matplotlib.pyplot as plt
    _fig, ax = plt.subplots(2, sharex=True, figsize=(10, 8))
    plt.subplots_adjust(hspace=0.1)
    ax[0].plot(lons, means, color="k", label="mean")
    ax[0].plot(
        lons, means + stds, "--b", label="mean +/- stddev"
    )
    ax[0].plot(lons, means - stds, "--b")
    ax[1].plot(lons, stds, "-.r", label="stddev")
    plt.xlabel("Longitude")
    ax[0].set_ylabel(f"Mean ln({target_imt}) (g)")
    ax[1].set_ylabel(f"Stddev ln({target_imt}) (g)")
    ax[0].legend(loc="best")
    ax[1].legend(loc="best")
    ax[0].set_title(case_name)
    ax[0].grid()
    ax[1].grid()
    ax[1].set_ylim(bottom=0)
    plt.show()


def plot_test_results_spectra(periods, means, stds, case_name):
    return  # remove the return to show the plot
    import matplotlib.pyplot as plt
    _fig, ax = plt.subplots(2, sharex=True, figsize=(10, 8))
    plt.subplots_adjust(hspace=0.1)
    ax[0].semilogx(periods, means, color="k", label="mean")
    ax[0].semilogx(
        periods, means + stds, "--b", label="mean +/- stddev"
    )
    ax[0].semilogx(periods, means - stds, "--b")
    ax[1].semilogx(periods, stds, "-.r", label="stddev")
    plt.xlabel("Period (s)")
    ax[0].set_ylabel("Mean ln(SA) (g)")
    ax[1].set_ylabel("Stddev ln(SA) (g)")
    ax[0].legend(loc="best")
    ax[1].legend(loc="best")
    ax[0].set_title(case_name)
    ax[0].grid()
    ax[1].grid()
    ax[1].set_ylim(bottom=0)
    plt.show()


def plot_test_results_multi(lons, means_list, stds_list, std_addon, target_imt,
                            case_name):
    return  # remove the return to show the plot
    import matplotlib.pyplot as plt
    colors = ["k", "b", "g", "r", "c", "m"]
    _fig, ax = plt.subplots(2, sharex=True, figsize=(10, 8))
    plt.subplots_adjust(hspace=0.1)
    for i in range(len(means_list)):
        means = means_list[i]
        stds = stds_list[i]
        ax[0].plot(lons, means, color=colors[i],
                   label=r"$\sigma_\epsilon = %.2f$" % std_addon[i])
        ax[1].plot(lons, stds, "-.", color=colors[i],
                   label=r"$\sigma_\epsilon = %.2f$" % std_addon[i])
    plt.xlabel("Longitude")
    ax[0].set_ylabel(f"Mean ln({target_imt}) (g)")
    ax[1].set_ylabel(f"Stddev ln({target_imt}) (g)")
    ax[0].legend(loc="best")
    ax[1].legend(loc="best")
    ax[0].set_title(case_name)
    ax[0].grid()
    ax[1].grid()
    ax[1].set_ylim(bottom=0)
    plt.show()
