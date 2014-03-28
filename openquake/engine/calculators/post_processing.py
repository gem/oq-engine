# -*- coding: utf-8 -*-
# pylint: enable=W0511,W0142,I0011,E1101,E0611,F0401,E1103,R0801,W0232

# Copyright (c) 2010-2014, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

"""
Post processing functionality for computing mean and quantile curves.
"""

import numpy


def mean_curve(curves, weights=None):
    """
    Compute the mean or weighted average of a set of curves.

    :param curves:
        2D array-like collection of hazard curve PoE values. Each element
        should be a sequence of PoE `float` values. Example::

            [[0.5, 0.4, 0.3], [0.6, 0.59, 0.1]]

        .. note::
            This data represents the curves for all realizations for a given
            site and IMT.

    :param weights:
        List or numpy array of weights, 1 weight value for each of the input
        ``curves``. This is only used for weighted averages.

    :returns:
        A curve representing the mean/average (or weighted average, in case
        ``weights`` are specified) of all the input ``curves``.
    """
    if weights is not None:
        # If all of the weights are None, don't compute a weighted average
        none_weights = [x is None for x in weights]
        if all(none_weights):
            weights = None
        elif any(none_weights):
            # some weights are defined, but some are none;
            # this is invalid input
            raise ValueError('`None` value found in weights: %s' % weights)

    return numpy.average(curves, weights=weights, axis=0)


def weighted_quantile_curve(curves, weights, quantile):
    """
    Compute the weighted quantile aggregate of a set of curves. This method is
    used in the case where hazard curves are computed using the logic tree
    end-branch enumeration approach. In this case, the weights are explicit.

    :param curves:
        2D array-like of curve PoEs. Each row represents the PoEs for a single
        curve
    :param weights:
        Array-like of weights, 1 for each input curve.
    :param quantile:
        Quantile value to calculate. Should in the range [0.0, 1.0].

    :returns:
        A numpy array representing the quantile aggregate of the input
        ``curves`` and ``quantile``, weighting each curve with the specified
        ``weights``.
    """
    # Each curve needs to be associated with a weight:
    assert len(weights) == len(curves)
    # NOTE(LB): Weights might be passed as a list of `decimal.Decimal`
    # types, and numpy.interp can't handle this (it throws TypeErrors).
    # So we explicitly cast to floats here before doing interpolation.
    weights = numpy.array(weights, dtype=numpy.float64)

    result_curve = []

    np_curves = numpy.array(curves)
    np_weights = numpy.array(weights)

    for poes in np_curves.transpose():
        sorted_poe_idxs = numpy.argsort(poes)
        sorted_weights = np_weights[sorted_poe_idxs]
        sorted_poes = poes[sorted_poe_idxs]

        # cumulative sum of weights:
        cum_weights = numpy.cumsum(sorted_weights)

        result_curve.append(numpy.interp(quantile, cum_weights, sorted_poes))

    return numpy.array(result_curve)


def quantile_curve(curves, quantile):
    """
    Compute the quantile aggregate of a set of curves. This method is used in
    the case where hazard curves are computed using the Monte-Carlo logic tree
    sampling approach. In this case, the weights are implicit.

    :param curves:
        2D array-like collection of hazard curve PoE values. Each element
        should be a sequence of PoE `float` values. Example::

            [[0.5, 0.4, 0.3], [0.6, 0.59, 0.1]]
    :param float quantile:
        The quantile value. We expected a value in the range [0.0, 1.0].

    :returns:
        A numpy array representing the quantile aggregate of the input
        ``curves`` and ``quantile``.
    """
    # this implementation is an alternative to:
    # return numpy.array(mstats.mquantiles(curves, prob=quantile, axis=0))[0]

    # more or less copied from the scipy mquantiles function, just special
    # cased for what we need (and a lot faster)

    arr = numpy.array(curves)

    p = numpy.array(quantile)
    m = 0.4 + p * 0.2

    n = len(arr)
    aleph = n * p + m
    k = numpy.floor(aleph.clip(1, n - 1)).astype(int)
    gamma = (aleph - k).clip(0, 1)

    data = numpy.sort(arr, axis=0).transpose()
    return (1.0 - gamma) * data[:, k - 1] + gamma * data[:, k]
