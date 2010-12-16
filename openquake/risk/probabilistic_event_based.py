# -*- coding: utf-8 -*-
"""
This module defines the functions used to compute loss ratio and loss curves
using the probabilistic event based approach.
"""

import math
from numpy import array # pylint: disable=E1101, E0611
from numpy import linspace # pylint: disable=E1101, E0611
from numpy import histogram # pylint: disable=E1101, E0611
from numpy import where # pylint: disable=E1101, E0611

from openquake import kvs
from openquake import shapes
from openquake.logs import LOG

DEFAULT_NUMBER_OF_SAMPLES = 25


def compute_loss_ratios(vuln_function, ground_motion_field_set):
    """Compute loss ratios using the ground motion field set passed."""
    if vuln_function == shapes.EMPTY_VULN_FUNCTION or not \
                        ground_motion_field_set["IMLs"]:
        return []
    
    imls = vuln_function.imls
    loss_ratios = []
    
    # seems like with numpy you can only specify a single fill value
    # if the x_new is outside the range. Here we need two different values,
    # depending if the x_new is below or upon the defined values
    for ground_motion_field in ground_motion_field_set["IMLs"]:
        if ground_motion_field < imls[0]:
            loss_ratios.append(0.0)
        elif ground_motion_field > imls[-1]:
            loss_ratios.append(imls[-1])
        else:
            loss_ratios.append(vuln_function.ordinate_for(
                    ground_motion_field))
    
    print loss_ratios
    
    return array(loss_ratios)


def compute_loss_ratios_range(loss_ratios, num=DEFAULT_NUMBER_OF_SAMPLES):
    """Compute the range of loss ratios used to build the loss ratio curve."""
    
    print linspace(loss_ratios.min(), loss_ratios.max(), num)
    
    return linspace(loss_ratios.min(), loss_ratios.max(), num)


def compute_cumulative_histogram(loss_ratios, loss_ratios_range):
    "Compute the cumulative histogram."
    
    # TODO(JMC): I think this is wrong. where doesn't return zero values.
    invalid_ratios = lambda ratios: len(where(array(ratios) <= 0.0)[0])

    hist = histogram(loss_ratios, bins=loss_ratios_range)
    hist = hist[0][::-1].cumsum()[::-1]

    # ratios with value 0.0 must be deleted
    hist[0] = hist[0] - invalid_ratios(loss_ratios)
    
    print hist
    
    return hist


def compute_rates_of_exceedance(cum_histogram, tses):
    """Compute the rates of exceedance for the given cumulative histogram
    using the passed tses (tses is time span * number of realizations)."""
    if tses <= 0:
        raise ValueError("TSES is not supposed to be less than zero!")
    
    return (array(cum_histogram).astype(float) / tses)


def compute_probs_of_exceedance(rates_of_exceedance, time_span):
    """Compute the probabilities of exceedance using the given rates of
    exceedance unsing the passed time span."""
    probs_of_exceedance = []
    for idx in xrange(len(rates_of_exceedance)):
        probs_of_exceedance.append(1 - math.exp(
                (rates_of_exceedance[idx] * -1) \
                *  time_span))
    
    return array(probs_of_exceedance)


def compute_loss_ratio_curve(vuln_function, ground_motion_field_set,
        num=DEFAULT_NUMBER_OF_SAMPLES):
    """Compute the loss ratio curve using the probailistic event approach."""

    # with no gmfs (no earthquakes), an empty curve is enough
    if not ground_motion_field_set["IMLs"]:
        return shapes.EMPTY_CURVE

    loss_ratios = compute_loss_ratios(vuln_function, ground_motion_field_set)
    loss_ratios_range = compute_loss_ratios_range(loss_ratios, num)

    probs_of_exceedance = compute_probs_of_exceedance(
            compute_rates_of_exceedance(compute_cumulative_histogram(
            loss_ratios, loss_ratios_range), ground_motion_field_set["TSES"]),
            ground_motion_field_set["TimeSpan"])

    return _generate_curve(loss_ratios_range, probs_of_exceedance)


def _generate_curve(losses, probs_of_exceedance):
    """Generate a loss ratio (or loss) curve, given a set of losses
    and corresponding probabilities of exceedance. This function
    is intended to be used internally."""

    data = []
    for idx in xrange(len(losses) - 1):
        mean_loss_ratio = (losses[idx] + losses[idx + 1]) / 2
        data.append((mean_loss_ratio, probs_of_exceedance[idx]))

    return shapes.Curve(data)


class AggregateLossCurve(object):
    """Aggregate a set of loss curves and produce the resulting loss curve."""

    @staticmethod
    def from_kvs(job_id):
        """Return an aggregate curve using the computed
        loss curves in the kvs system."""
        client = kvs.get_client(binary=False)
        keys = client.keys("%s*%s*" % (job_id,
                kvs.tokens.LOSS_CURVE_KEY_TOKEN))

        LOG.debug("Found %s stored loss curves..." % len(keys))

        aggregate_curve = AggregateLossCurve()

        for key in keys:
            aggregate_curve.append(shapes.Curve.from_json(kvs.get(key)))
        
        return aggregate_curve

    def __init__(self, vuln_functions):
        self.tses = None
        self.time_span = None
        self.gmfs_length = None

        self.distribution = []
        self.vuln_functions = vuln_functions

    def append(self, gmfs, asset):
        """Add the given loss distribution to the set of losses used to
        compute the final aggregate curve."""

        if self.time_span is None:
            self.time_span = gmfs["TimeSpan"]

        if self.tses is None:
            self.tses = gmfs["TSES"]

        if self.gmfs_length is None:
            self.gmfs_length = len(gmfs["IMLs"])

        self._check_gmfs_length(gmfs)
        self._check_parameter(self.tses, gmfs, "TSES")
        self._check_parameter(self.time_span, gmfs, "TimeSpan")

        loss_ratios = compute_loss_ratios(self.vuln_functions[
                asset["VulnerabilityFunction"]], gmfs)

        if len(loss_ratios):
            self.distribution.append(loss_ratios * asset["AssetValue"])

    def _check_gmfs_length(self, gmfs):
        """Check if the GMFs passed has the same length of
        the stored GMFs."""

        if self.gmfs_length != len(gmfs["IMLs"]):
            raise ValueError("GMFs must be of the same size. " \
                    "Expected %s, but was %s" % (
                    self.gmfs_length, len(gmfs["IMLs"])))

    def _check_parameter(self, value, gmfs, name):
        """Check if the parameter of the GMFs passed is the
        same of the stored GMFs."""

        if value != gmfs[name]:
            raise ValueError("%s parameter must be the same for all " \
                    "the GMFs used. Expected %s, but was %s"
                    % (name, self.tses, gmfs[name]))

    @property
    def losses(self):
        """Return the losses used to compute the aggregate curve."""
        if not self.distribution:
            return []

        return array(self.distribution).sum(axis=0)

    def compute(self, num=DEFAULT_NUMBER_OF_SAMPLES):
        """Compute the aggregate loss curve."""
        losses = self.losses
        
        if not len(losses):
            return shapes.EMPTY_CURVE

        loss_range = compute_loss_ratios_range(losses, num)

        probs_of_exceedance = compute_probs_of_exceedance(
                compute_rates_of_exceedance(compute_cumulative_histogram(
                losses, loss_range), self.tses), self.time_span)

        return _generate_curve(loss_range, probs_of_exceedance)
