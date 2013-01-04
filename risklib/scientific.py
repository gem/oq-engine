# -*- coding: utf-8 -*-

# Copyright (c) 2010-2012, GEM Foundation.
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
This module includes the scientific API of the oq-risklib
"""

import collections
import numpy
from scipy import interpolate


#  ___                   _                         _       _
# |_ _|_ __  _ __  _   _| |_   _ __ ___   ___   __| | ___ | | ___
#  | || '_ \| '_ \| | | | __| | '_ ` _ \ / _ \ / _` |/ _ \| |/ __|
#  | || | | | |_) | |_| | |_  | | | | | | (_) | (_| |  __/| |\__ \
# |___|_| |_| .__/ \__,_|\__| |_| |_| |_|\___/ \__,_|\___||_||___/
#           |_|


class Asset(object):
    # FIXME (lp). Provide description
    def __init__(self, asset_ref, taxonomy, value, site,
                 ins_limit=None, deductible=None,
                 retrofitting_cost=None):
        self.site = site
        self.value = value
        self.taxonomy = taxonomy
        self.asset_ref = asset_ref
        self.ins_limit = ins_limit
        self.deductible = deductible
        self.retrofitting_cost = retrofitting_cost


class VulnerabilityFunction(object):
    # FIXME (lp). Provide description
    def __init__(self, imls, mean_loss_ratios, covs, distribution):
        """
        :param list imls: Intensity Measure Levels for the
            vulnerability function. All values must be >= 0.0, values
            must be arranged in ascending order with no duplicates

        :param list mean_loss_ratios: Mean Loss ratio values, equal in
        length to imls, where 0.0 <= value <= 1.0.

        :param list covs: Coefficients of Variation. Equal in length
        to mean loss ratios. All values must be >= 0.0.

        :param string distribution: The probabilistic distribution
            related to this function.
        """
        self._check_vulnerability_data(
            imls, mean_loss_ratios, covs, distribution)
        self.imls = numpy.array(imls)
        self.mean_loss_ratios = numpy.array(mean_loss_ratios)
        self.covs = numpy.array(covs)
        self.distribution = distribution
        self._mlr_i1d = interpolate.interp1d(self.imls, self.mean_loss_ratios)
        self._covs_i1d = interpolate.interp1d(self.imls, self.covs)

    def _check_vulnerability_data(self, imls, loss_ratios, covs, distribution):
        assert imls == sorted(set(imls))
        assert all(x >= 0.0 for x in imls)
        assert len(covs) == len(imls)
        assert len(loss_ratios) == len(imls)
        assert all(x >= 0.0 for x in covs)
        assert all(x >= 0.0 and x <= 1.0 for x in loss_ratios)
        assert distribution in ["LN", "BT"]

    @property
    def stddevs(self):
        """
        Convenience method: returns a list of calculated Standard Deviations
        """
        return self.covs * self.mean_loss_ratios

    def __call__(self, imls):
        """
        Given IML values, interpolate the corresponding loss ratio
        value(s) on the curve.

        Input IML value(s) is/are clipped to IML range defined for this
        vulnerability function.

        :param float array iml: IML value

        :returns: :py:class:`numpy.ndarray` containing a number of interpolated
            values equal to the size of the input (1 or many)
        """
        ret = numpy.zeros(len(imls))

        saturated = numpy.where(imls > self.imls[-1])
        ret[saturated] = numpy.ones(len(saturated)) * self.mean_loss_ratios[-1]

        to_interpolate = numpy.intersect1d(
            numpy.where(imls <= self.imls[-1])[0],
            numpy.where(imls >= self.imls[0])[0],
            assume_unique=True)

        ret[to_interpolate] = self._mlr_i1d(numpy.array(imls)[to_interpolate])

        return ret

    def _cov_for(self, imls):
        """
        Given IML values, interpolate the corresponding Coefficient of
        Variation value(s) on the curve.

        Input IML value(s) is/are clipped to IML range defined for this
        vulnerability function.

        :param float array imls: IML values

        :returns: :py:class:`numpy.ndarray` containing a number of interpolated
            values equal to the size of the input (1 or many)
        """
        return self._covs_i1d(imls)

    def mean_imls(self):
        """
        Compute the mean IMLs (Intensity Measure Level)
        for the given vulnerability function.

        :param vulnerability_function: the vulnerability function where
            the IMLs (Intensity Measure Level) are taken from.
        :type vuln_function:
           :py:class:`risklib.vulnerability_function.VulnerabilityFunction`
        """
        return ([max(0, self.imls[0] - ((self.imls[1] - self.imls[0]) / 2))] +
                [numpy.mean(x) for x in zip(self.imls, self.imls[1:])] +
                [self.imls[-1] + ((self.imls[-1] - self.imls[-2]) / 2)])


#   ___        _               _     __  __           _       _
#  / _ \ _   _| |_ _ __  _   _| |_  |  \/  | ___   __| | ___ | | ___
# | | | | | | | __| '_ \| | | | __| | |\/| |/ _ \ / _` |/ _ \| |/ __|
# | |_| | |_| | |_| |_) | |_| | |_  | |  | | (_) | (_| |  __/| |\__ \
#  \___/ \__,_|\__| .__/ \__,_|\__| |_|  |_|\___/ \__,_|\___||_||___/
#                 |_|


ClassicalOutput = collections.namedtuple(
    "ClassicalOutput",
    ["asset", "loss_ratio_curve", "loss_curve", "conditional_losses"])


ScenarioDamageOutput = collections.namedtuple(
    "ScenarioDamageOutput",
    ["asset", "damage_distribution_asset", "collapse_map"])


BCROutput = collections.namedtuple(
    "BCROutput", ["asset", "bcr", "eal_original", "eal_retrofitted"])


ProbabilisticEventBasedOutput = collections.namedtuple(
    "ProbabilisticEventBasedOutput", ["asset", "losses",
    "loss_ratio_curve", "loss_curve", "insured_loss_ratio_curve",
    "insured_loss_curve", "insured_losses", "conditional_losses"])


ScenarioRiskOutput = collections.namedtuple(
    "ScenarioRiskOutput", ["asset", "mean", "standard_deviation"])


#       _                  _            _   ____   ____  _   _     _
#   ___| | __ _  ___  ___ (_) ___  __ _| | |  _ \ / ___|| | | |   / \
#  / __| |/ _` |/ __|/ __|| |/ __|/ _` | | | |_) |\___ \| |_| |  / _ \
# | (__| | (_| |\__ \\__ \| | (__| (_| | | |  __/  ___) |  _  | / ___ \
#  \___|_|\__,_||___/|___/|_|\___|\__,_|_| |_|    |____/|_| |_|/_/   \_\


