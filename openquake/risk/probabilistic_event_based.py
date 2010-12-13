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
from openquake import risk
from openquake import shapes
from openquake.logs import LOG

DEFAULT_NUMBER_OF_SAMPLES = 25

def compute_loss_ratios(vuln_function, ground_motion_field_set):
    """Compute loss ratios using the ground motion field set passed."""
    if vuln_function == shapes.EMPTY_CURVE or not \
                        ground_motion_field_set["IMLs"]:
        return []
    
    imls = vuln_function.abscissae
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
    
    return array(loss_ratios)


def compute_loss_ratios_range(vuln_function):
    """Compute the range of loss ratios used to build the loss ratio curve."""
    loss_ratios = vuln_function.ordinates[:, 0]
    return linspace(0.0, loss_ratios[-1], num=DEFAULT_NUMBER_OF_SAMPLES)


def compute_cumulative_histogram(loss_ratios, loss_ratios_range):
    "Compute the cumulative histogram."
    
    def invalid_ratios(ratios):
        """ Return the number of invalid ratios or None """
        invalids = where(ratios <= 0.0)
        # TODO(JMC): I think this is wrong. where doesn't return zero values
        if invalids:
            return len(invalids[0])
        return None
    
    hist = histogram(loss_ratios, bins=loss_ratios_range)
    hist = hist[0][::-1].cumsum()[::-1]

    # ratios with value 0.0 must be deleted
    hist[0] = hist[0] - invalid_ratios(loss_ratios)
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


def compute_loss_ratio_curve(vuln_function, ground_motion_field_set):
    """Compute the loss ratio curve using the probailistic event approach."""
    loss_ratios = compute_loss_ratios(vuln_function, ground_motion_field_set)
    loss_ratios_range = compute_loss_ratios_range(vuln_function)
    
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
        mean_loss_ratios = (losses[idx] + \
                losses[idx + 1]) / 2
        data.append((mean_loss_ratios, probs_of_exceedance[idx]))

    return shapes.Curve(data)


class AggregateLossCurve(object):
    """Aggregate a set of loss curves and produce the resulting loss curve."""

    @staticmethod
    def from_kvs(job_id):
        """Return an aggregate curve using the computed
        loss curves in the kvs system."""
        client = kvs.get_client(binary=False)
        keys = client.keys("%s*%s*" % (job_id, risk.LOSS_CURVE_KEY_TOKEN))

        LOG.debug("Found %s stored loss curves..." % len(keys))

        aggregate_curve = AggregateLossCurve()

        for key in keys:
            aggregate_curve.append(shapes.Curve.from_json(kvs.get(key)))
        
        return aggregate_curve

    def __init__(self):
        self.size = None
        self.values = []

    def append(self, loss_curve):
        """Add the given loss curve to the set of curves used to 
        compute the final aggregate curve."""
        
        size = len(loss_curve.abscissae)
        
        if self.size is None:
            self.size = size
        
        if size != self.size:
            raise ValueError("Loss curves must be of the same size, \
                    expected %s, but was %s" % (self.size, size))
        
        self.values.append(loss_curve.abscissae)

    @property
    def losses(self):
        """Return the losses used to compute the aggregate curve."""
        result = []

        if not self.values:
            return result

        return array(self.values).sum(axis=0)

# TODO (ac): Test with pre computed data
    def compute(self, tses, time_span):
        """Compute the aggregate loss curve."""
        losses = self.losses
        loss_range = linspace(losses.min(), losses.max(),
                num=DEFAULT_NUMBER_OF_SAMPLES)

        probs_of_exceedance = compute_probs_of_exceedance(
                compute_rates_of_exceedance(compute_cumulative_histogram(
                losses, loss_range), tses), time_span)

        return _generate_curve(losses, probs_of_exceedance)
