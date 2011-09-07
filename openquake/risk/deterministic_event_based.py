# -*- coding: utf-8 -*-

# Copyright (c) 2010-2011, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# only, as published by the Free Software Foundation.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License version 3 for more details
# (a copy is included in the LICENSE file that accompanied this code).
#
# You should have received a copy of the GNU Lesser General Public License
# version 3 along with OpenQuake.  If not, see
# <http://www.gnu.org/licenses/lgpl-3.0.txt> for a copy of the LGPLv3 License.

"""
This module defines functions used to compute losses
using the deterministic event based approach.
"""

import numpy

from openquake.risk import probabilistic_event_based as prob
from openquake.logs import LOG


def _mean_loss_from_loss_ratios(loss_ratios, asset):
    """Compute the mean loss using the set of loss ratios given.

    :param loss_ratios: the set of loss ratios used.
    :type loss_ratios: numpy.ndarray
    :param asset: the asset used to compute the losses.
    :type asset: :py:class:`dict` as provided by
        :py:class:`openquake.parser.exposure.ExposurePortfolioFile`
    """

    losses = loss_ratios * asset["assetValue"]
    return numpy.mean(losses)


def _stddev_loss_from_loss_ratios(loss_ratios, asset):
    """Compute the standard deviation of the losses
    using the set of loss ratios given.

    :param loss_ratios: the set of loss ratios used.
    :type loss_ratios: numpy.ndarray
    :param asset: the asset used to compute the losses.
    :type asset: :py:class:`dict` as provided by
        :py:class:`openquake.parser.exposure.ExposurePortfolioFile`
    """

    losses = loss_ratios * asset["assetValue"]
    return numpy.std(losses, ddof=1)


def compute_mean_loss(vuln_function, ground_motion_field_set,
                      epsilon_provider, asset):
    """Compute the mean loss for the given asset using the
    related ground motion field set and vulnerability function.

    :param vuln_function: the vulnerability function used to
        compute the loss ratios.
    :type vuln_function: :py:class:`openquake.shapes.VulnerabilityFunction`
    :param ground_motion_field_set: the set of ground motion
        fields used to compute the loss ratios.
    :type ground_motion_field_set: :py:class:`dict` with the following
        keys:
        **IMLs** - tuple of ground motion fields (float)
    :param epsilon_provider: service used to get the epsilon when
        using the sampled based algorithm.
    :type epsilon_provider: object that defines an :py:meth:`epsilon` method
    :param asset: the asset used to compute the loss ratios and losses.
    :type asset: :py:class:`dict` as provided by
        :py:class:`openquake.parser.exposure.ExposurePortfolioFile`
    """

    loss_ratios = prob.compute_loss_ratios(
        vuln_function, ground_motion_field_set, epsilon_provider, asset)

    return _mean_loss_from_loss_ratios(loss_ratios, asset)


def compute_stddev_loss(vuln_function, ground_motion_field_set,
                        epsilon_provider, asset):
    """Compute the standard deviation of the losses for the given asset
    using the related ground motion field set and vulnerability function.

    :param vuln_function: the vulnerability function used to
        compute the loss ratios.
    :type vuln_function: :py:class:`openquake.shapes.VulnerabilityFunction`
    :param ground_motion_field_set: the set of ground motion
        fields used to compute the loss ratios.
    :type ground_motion_field_set: :py:class:`dict` with the following
        keys:
        **IMLs** - tuple of ground motion fields (float)
    :param epsilon_provider: service used to get the epsilon when
        using the sampled based algorithm.
    :type epsilon_provider: object that defines an :py:meth:`epsilon` method
    :param asset: the asset used to compute the loss ratios and losses.
    :type asset: :py:class:`dict` as provided by
        :py:class:`openquake.parser.exposure.ExposurePortfolioFile`
    """

    loss_ratios = prob.compute_loss_ratios(
        vuln_function, ground_motion_field_set, epsilon_provider, asset)

    return _stddev_loss_from_loss_ratios(loss_ratios, asset)


class SumPerGroundMotionField(object):
    """This class computes the mean and the standard deviation of
    the sum of the losses per ground motion field set."""

    def __init__(self, vuln_model, epsilon_provider, lr_calculator=None):
        """Initialize an instance of this class.

        :param vuln_model: the vulnerability model used to lookup the
            functions referenced by each asset.
        :type vuln_model: :py:class:`dict` where each key is the id
            of the function and the value is an instance of
            `openquake.shapes.VulnerabilityFunction`
        :param epsilon_provider: service used to get the epsilon when
            using the sampled based algorithm.
        :type epsilon_provider: object that defines
            an :py:method:`epsilon` method
        :param lr_calculator: service used to compute the loss ratios.
            For the list of parameters, see
    :py:function:`openquake.risk.probabilistic_event_based.compute_loss_ratios`
        :type lr_calculator: object that defines an :py:meth:`epsilon` method
        """
        self.vuln_model = vuln_model
        self.lr_calculator = lr_calculator
        self.epsilon_provider = epsilon_provider

        self.losses = numpy.array([])

        if lr_calculator is None:
            self.lr_calculator = prob.compute_loss_ratios

    def add(self, ground_motion_field_set, asset):
        """Compute the losses for the given ground motion field set, and
        sum those to the current sum of the losses.

        If the asset refers to a vulnerability function that is not
        supported by the vulnerability model, the distribution
        of the losses is discarded.

        :param ground_motion_field_set: the set of ground motion
            fields used to compute the loss ratios.
        :type ground_motion_field_set: :py:class:`dict` with the following
            keys:
            **IMLs** - tuple of ground motion fields (float)
        :param asset: the asset used to compute the loss ratios and losses.
        :type asset: :py:class:`dict` as provided by
            :py:class:`openquake.parser.exposure.ExposurePortfolioFile`
        """

        if asset["vulnerabilityFunctionReference"] not in self.vuln_model:
            LOG.debug("Unknown vulnerability function %s, asset %s will " \
                      "not be included in the aggregate computation"
                      % (asset["vulnerabilityFunctionReference"],
                      asset["assetID"]))

            return

        vuln_function = self.vuln_model[
            asset["vulnerabilityFunctionReference"]]

        loss_ratios = self.lr_calculator(
            vuln_function, ground_motion_field_set,
            self.epsilon_provider, asset)

        losses = numpy.array(loss_ratios) * asset["assetValue"]

        self.sum_losses(losses)

    def sum_losses(self, losses):
        """
        Accumulate losses into a single sum.

        :param losses: an array of loss values (1 per realization)
        :type losses: 1-dimensional :py:class:`numpy.ndarray`

        The `losses` arrays passed to this function must be empty or
        all the same lenght.
        """
        if len(self.losses) == 0:
            self.losses = losses
        elif len(losses) > 0:
            self.losses = self.losses + losses

    @property
    def mean(self):
        """Return the mean of the current sum of the losses.

        :returns: the mean of the current sum of the losses
        :rtype: numpy.float64
        """
        return numpy.mean(self.losses)

    @property
    def stddev(self):
        """Return the standard deviation of the sum of the losses.

        :returns: the standard deviation of the current sum of the losses
        :rtype: numpy.float64
        """
        return numpy.std(self.losses, ddof=1)
