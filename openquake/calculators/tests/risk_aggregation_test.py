# Copyright (C) 2026 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

from types import SimpleNamespace
from unittest.mock import MagicMock, patch
import numpy
import pandas
import pytest

from openquake.baselib.general import AccumDict
from openquake.calculators.event_based_damage import damage_from_gmfs
from openquake.calculators.event_based_risk import aggreg, build_alt
from openquake.calculators.post_risk import compute_aggrisk


def test_no_damage_per_loss_type():
    # Each loss type must conserve the ten buildings, including missing GMFs.
    oq = SimpleNamespace(loss_types=['structural', 'contents'],
                         number_of_logic_tree_samples=0,
                         investigation_time=None, quantiles=[])
    dstore = {'weights': numpy.array([1.]),
              'agg_values': {'number': numpy.array([10.])}}
    df = pandas.DataFrame(dict(agg_id=[0, 0], rlz_id=[0, 0], loss_id=[3, 0],
                               event_id=[0, 0], dmg_1=[10., 4.]))
    result, _, _, _ = compute_aggrisk(
        dstore, oq, df, numpy.array([2]), [0])
    result = result.set_index('loss_id')
    numpy.testing.assert_allclose(result.loc[[3, 0], 'dmg_0'], [5., 8.])
    numpy.testing.assert_allclose(result.dmg_0 + result.dmg_1, 10.)


@pytest.mark.parametrize('correlation, variance', [(0, 13.), (1, 25.)])
def test_variance_independent_of_asset_chunks(correlation, variance):
    # Taxonomies and exposure chunks can split assets of the same event.
    oq = SimpleNamespace(asset_correlation=correlation,
                         xtypes=['structural'], avg_losses=False, K=2)
    alt = pandas.DataFrame(dict(
        eid=numpy.array([0, 0], numpy.uint32), aid=[0, 1],
        variance=[4., 9.], loss=[10., 20.]))
    aggids = numpy.array([[0, 0], [1, 1]])
    results = []
    for parts in ([alt], [alt.iloc[:1], alt.iloc[1:]]):
        loss2 = AccumDict(accum=numpy.zeros((1, 2)))
        for part in parts:
            aggreg({'structural': part.copy()}, aggids, numpy.array([0]),
                   oq, loss2, {})
        results.append(build_alt(loss2, oq.xtypes, correlation))
    pandas.testing.assert_frame_equal(*results)
    numpy.testing.assert_allclose(results[0].variance, variance)
    numpy.testing.assert_allclose(results[0].loss, 30.)


@pytest.mark.parametrize('number', [0., .5, 1., 10.])
@pytest.mark.parametrize('realizations', [1, 2])
def test_compose_peril_damage_counts(number, realizations):
    # Compose probabilities, then recover counts; keep per-peril data intact.
    crmodel = SimpleNamespace(
        perils=['groundshaking', 'liquefaction'],
        damage_states=['no_damage', 'ds1'],
        get_dmg_csq=lambda: ['dmg_1', 'losses'])
    assets = pandas.DataFrame(dict(
        ordinal=[0], site_id=[0], taxonomy=[1],
        **{'value-number': [number]}))
    assetcol = MagicMock()
    assetcol.__len__.return_value = 1
    assetcol.__getitem__.return_value = numpy.array([0])
    assetcol.to_dframe.return_value = assets
    monitor = MagicMock()
    monitor.read.side_effect = {'crmodel': crmodel,
                                'aggids': numpy.array([[0]])}.__getitem__
    oq = SimpleNamespace(R=realizations, L=1, K=1, float_dmg_dist=True)
    gmfs = pandas.DataFrame(dict(sid=[0, 0], eid=[0, 1]))
    dd5 = numpy.array([[[[[0., 1., 3.]], [[.8, .2, 3.]]]],
                       [[[[0., 1., 7.]], [[.5, .5, 7.]]]]]) * number
    with patch('openquake.risklib.scientific.RiskComputer') as rc:
        rc.return_value.get_dd5.return_value = dd5
        totals, damages, ords = damage_from_gmfs(
            gmfs, assetcol, oq, numpy.array([0, 1]), monitor)
    for agg_id in (0, 1):
        numpy.testing.assert_allclose(
            totals[0, agg_id], [[0., number, 7. * number]])
        numpy.testing.assert_allclose(
            totals[1, agg_id], [[.4 * number, .6 * number, 7. * number]])
    numpy.testing.assert_allclose(damages.sum(axis=2), dd5.sum(axis=2))
    numpy.testing.assert_equal(ords, [0])
