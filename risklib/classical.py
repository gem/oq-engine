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

from math import exp
from scipy import sqrt, log, stats
from numpy import array, empty, concatenate, linspace

from risklib.curve import Curve


def _loss_ratio_exceedance_matrix(vuln_function, steps):
    """Compute the LREM (Loss Ratio Exceedance Matrix).

    :param vuln_function:
        The vulnerability function used to compute the LREM.
    :type vuln_function:
        :class:`risklib.vulnerability_function.VulnerabilityFunction`
    :param int steps:
        Number of steps between loss ratios.
    """
    loss_ratios = _evenly_spaced_loss_ratios(
        vuln_function.loss_ratios, steps, [0.0], [1.0])

    # LREM has number of rows equal to the number of loss ratios
    # and number of columns equal to the number of imls
    lrem = empty((loss_ratios.size, vuln_function.imls.size), float)

    for col, _ in enumerate(vuln_function):
        for row, loss_ratio in enumerate(loss_ratios):
            mean_loss_ratio = vuln_function.loss_ratios[col]
            loss_ratio_stddev = vuln_function.stddevs[col]

            if vuln_function.distribution == "BT":
                lrem[row][col] = stats.beta.sf(
                    loss_ratio,
                    _alpha_value(mean_loss_ratio, loss_ratio_stddev),
                    _beta_value(mean_loss_ratio, loss_ratio_stddev))
            elif vuln_function.distribution == "LN":
                variance = loss_ratio_stddev ** 2.0
                sigma = sqrt(log((variance / mean_loss_ratio ** 2.0) + 1.0))
                mu = exp(log(mean_loss_ratio ** 2.0 /
                             sqrt(variance + mean_loss_ratio ** 2.0)))

                lrem[row][col] = stats.lognorm.sf(loss_ratio, sigma, scale=mu)
            else:
                raise RuntimeError(
                    "Only beta or lognormal distributions are supported")

    return lrem


def _alpha_value(mean_loss_ratio, stddev):
    """
    Compute alpha value

    :param mean_loss_ratio: current loss ratio
    :type mean_loss_ratio: float

    :param stdev: current standard deviation
    :type stdev: float


    :returns: computed alpha value
    """

    return (((1 - mean_loss_ratio) / stddev ** 2 - 1 / mean_loss_ratio) *
            mean_loss_ratio ** 2)


def _beta_value(mean_loss_ratio, stddev):
    """
    Compute beta value

    :param mean_loss_ratio: current loss ratio
    :type mean_loss_ratio: float

    :param stdev: current standard deviation
    :type stdev: float


    :returns: computed beta value
    """
    return (((1 - mean_loss_ratio) / stddev ** 2 - 1 / mean_loss_ratio) *
            (mean_loss_ratio - mean_loss_ratio ** 2))


def _conditional_loss(curve, probability):
    """
    Return the loss (or loss ratio) corresponding to the given
    PoE (Probability of Exceendance).

    Return the max loss (or loss ratio) if the given PoE is smaller
    than the lowest PoE defined.

    Return zero if the given PoE is greater than the
    highest PoE defined.
    """
    # the loss curve is always decreasing
    if curve.ordinate_out_of_bounds(probability):
        if probability < curve.ordinates[-1]:  # min PoE
            return curve.abscissae[-1]  # max loss
        else:
            return 0.0

    return curve.abscissa_for(probability)


def _loss_ratio_curve(vuln_function, lrem, hazard_curve_values, steps):
    """Compute a loss ratio curve for a specific hazard curve (e.g., site),
    by applying a given vulnerability function.

    A loss ratio curve is a function that has loss ratios as X values
    and PoEs (Probabilities of Exceendance) as Y values.

    This is the main (and only) public function of this module.

    :param vuln_function: the vulnerability function used
        to compute the curve.
    :type vuln_function: :py:class:`risklib.vulnerability_function.VulnerabilityFunction`
    :param hazard_curve_values: the hazard curve used to compute the curve.
    :type hazard_curve_values: an association list with the
    imls/values of the hazard curve
    :param int steps:
        Number of steps between loss ratios.
    """
    lrem_po = _loss_ratio_exceedance_matrix_per_poos(
        vuln_function, lrem, hazard_curve_values)
    loss_ratios = _evenly_spaced_loss_ratios(
        vuln_function.loss_ratios, steps, [0.0], [1.0])
    return Curve(zip(loss_ratios, lrem_po.sum(axis=1)))


def _loss_ratio_exceedance_matrix_per_poos(
        vuln_function, lrem, hazard_curve_values):
    """Compute the LREM * PoOs (Probability of Occurence) matrix.

    :param vuln_function: the vulnerability function used
        to compute the matrix.
    :type vuln_function: :py:class:`risklib.vulnerability_function.VulnerabilityFunction`
    :param hazard_curve: the hazard curve used to compute the matrix.
    :type hazard_curve_values: an association list with the hazard
    curve imls/values
    :param lrem: the LREM used to compute the matrix.
    :type lrem: 2-dimensional :py:class:`numpy.ndarray`
    """
    lrem = array(lrem)
    lrem_po = empty(lrem.shape)
    imls = vuln_function.mean_imls()
    if hazard_curve_values:
        # compute the PoOs (Probability of Occurence) from the PoEs
        pos = Curve(hazard_curve_values).ordinate_diffs(imls)
        for idx, po in enumerate(pos):
            lrem_po[:, idx] = lrem[:, idx] * po  # column * po
    return lrem_po


def _evenly_spaced_loss_ratios(loss_ratios, steps, first=(), last=()):
    """
    Split the loss ratios, producing a new set of loss ratios.

    :param loss_ratios: the loss ratios to split.
    :type loss_ratios: list of floats
    :param int steps: the number of steps we make to go from one loss
        ratio to the next. For example, if we have [1.0, 2.0]:

        steps = 1 produces [1.0, 2.0]
        steps = 2 produces [1.0, 1.5, 2.0]
        steps = 3 produces [1.0, 1.33, 1.66, 2.0]
    :param first: optional array of ratios to put first (ex. [0.0])
    :param last: optional array of ratios to put last (ex. [1.0])
    """
    loss_ratios = concatenate([first, loss_ratios, last])
    ls = concatenate([linspace(x, y, num=steps + 1)[:-1]
                      for x, y in zip(loss_ratios, loss_ratios[1:])])
    return concatenate([ls, [loss_ratios[-1]]])
