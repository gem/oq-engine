# -*- coding: utf-8 -*-
"""
This module defines functions used to compute loss ratio and loss curves
using the probabilistic event based approach.
"""

import math

from numpy import zeros, array, linspace # pylint: disable=E1101, E0611
from numpy import histogram, where, mean # pylint: disable=E1101, E0611

from openquake import kvs, shapes
from openquake.parser import vulnerability
from openquake.logs import LOG
from openquake.risk.common import collect, loop

DEFAULT_NUMBER_OF_SAMPLES = 25


def _compute_loss_ratios(vuln_function, ground_motion_field_set,
        epsilon_provider, asset):
    """Compute the set of loss ratios using the set of
    ground motion fields passed."""

    if vuln_function.is_empty:
        return array([])

    all_covs_are_zero = (vuln_function.covs <= 0.0).all()

    if all_covs_are_zero:
        return _mean_based(vuln_function, ground_motion_field_set)
    else:
        return _sampled_based(vuln_function, ground_motion_field_set,
                epsilon_provider, asset)


def _sampled_based(vuln_function, ground_motion_field_set,
        epsilon_provider, asset):
    """Compute the set of loss ratios when all CVs (Coefficent of Variation)
    defined in the vulnerability function are greater than zero."""

    loss_ratios = []

    for ground_motion_field in ground_motion_field_set["IMLs"]:
        mean_ratio = vuln_function.ordinate_for(ground_motion_field)

        if mean_ratio <= 0.0:
            loss_ratios.append(0.0)
        else:
            variance = (mean_ratio * vuln_function.cov_for(
                    ground_motion_field)) ** 2.0

            epsilon = epsilon_provider.epsilon(asset)
            sigma = math.sqrt(math.log((variance / mean_ratio ** 2.0) + 1.0))

            mu = math.log(mean_ratio ** 2.0 / math.sqrt(
                    variance + mean_ratio ** 2.0))

            loss_ratios.append(math.exp(mu + (epsilon * sigma)))

    return array(loss_ratios)


def _mean_based(vuln_function, ground_motion_field_set):
    """Compute the set of loss ratios when the vulnerability function
    has at least one CV (Coefficent of Variation) set to zero."""

    loss_ratios = []
    imls = vuln_function.imls

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


def _compute_loss_ratios_range(loss_ratios,
        number_of_samples=DEFAULT_NUMBER_OF_SAMPLES):
    """Compute the range of loss ratios used to build the loss ratio curve."""
    return linspace(loss_ratios.min(), loss_ratios.max(), number_of_samples)


def _compute_cumulative_histogram(loss_ratios, loss_ratios_range):
    "Compute the cumulative histogram."

    # ruptures (earthquake) occured but probably due to distance,
    # magnitude and soil conditions, no ground motion was felt at that location
    if (loss_ratios <= 0.0).all():
        return zeros(loss_ratios_range.size - 1)

    invalid_ratios = lambda ratios: where(array(ratios) <= 0.0)[0].size

    hist = histogram(loss_ratios, bins=loss_ratios_range)
    hist = hist[0][::-1].cumsum()[::-1]

    # ratios with value 0.0 must be deleted on the first bin
    hist[0] = hist[0] - invalid_ratios(loss_ratios)
    return hist


def _compute_rates_of_exceedance(cum_histogram, tses):
    """Compute the rates of exceedance for the given cumulative histogram
    using the given tses (tses is time span * number of realizations)."""

    if tses <= 0:
        raise ValueError("TSES is not supposed to be less than zero!")

    return (array(cum_histogram).astype(float) / tses)


def _compute_probs_of_exceedance(rates_of_exceedance, time_span):
    """Compute the probabilities of exceedance using the given rates of
    exceedance and the given time span."""

    poe = lambda rate: 1 - math.exp((rate * -1) * time_span)
    return array([poe(rate) for rate in rates_of_exceedance])


def compute_loss_ratio_curve(vuln_function, ground_motion_field_set,
        epsilon_provider, asset, number_of_samples=DEFAULT_NUMBER_OF_SAMPLES):
    """Compute a loss ratio curve using the probabilistic event based approach.

    A loss ratio curve is a function that has loss ratios as X values
    and PoEs (Probabilities of Exceendance) as Y values.
    """

    # with no gmfs (no earthquakes), an empty curve is enough
    if not ground_motion_field_set["IMLs"]:
        return shapes.EMPTY_CURVE

    loss_ratios = _compute_loss_ratios(vuln_function,
            ground_motion_field_set, epsilon_provider, asset)

    loss_ratios_range = _compute_loss_ratios_range(
            loss_ratios, number_of_samples)

    probs_of_exceedance = _compute_probs_of_exceedance(
            _compute_rates_of_exceedance(_compute_cumulative_histogram(
            loss_ratios, loss_ratios_range), ground_motion_field_set["TSES"]),
            ground_motion_field_set["TimeSpan"])

    return _generate_curve(loss_ratios_range, probs_of_exceedance)


def _generate_curve(losses, probs_of_exceedance):
    """Generate a loss ratio (or loss) curve, given a set of losses
    and corresponding PoEs (Probabilities of Exceedance).

    This function is intended to be used internally.
    """

    mean_losses = collect(loop(losses, lambda x, y: mean([x, y])))
    return shapes.Curve(zip(mean_losses, probs_of_exceedance))


def _asset_for_gmfs(job_id, gmfs_key):
    """Return the asset related to the GMFs given."""

    row = lambda key: key.split(kvs.MEMCACHE_KEY_SEPARATOR)[2]
    column = lambda key: key.split(kvs.MEMCACHE_KEY_SEPARATOR)[3]

    key = kvs.tokens.asset_key(
            job_id, row(gmfs_key), column(gmfs_key))

    return kvs.get_value_json_decoded(key)


class AggregateLossCurve(object):
    """Aggregate a set of losses and produce the resulting loss curve."""

    @staticmethod
    def from_kvs(job_id):
        """Return an aggregate curve using the GMFs and assets
        stored in the underlying kvs system."""

        vuln_model = vulnerability.load_vuln_model_from_kvs(job_id)
        aggregate_curve = AggregateLossCurve(vuln_model)

        client = kvs.get_client(binary=False)
        gmfs_keys = client.keys("%s*%s*" % (job_id, kvs.tokens.GMF_KEY_TOKEN))
        LOG.debug("Found %s stored GMFs..." % len(gmfs_keys))

        for gmfs_key in gmfs_keys: # O(2*n)
            asset = _asset_for_gmfs(job_id, gmfs_key)
            gmfs = kvs.get_value_json_decoded(gmfs_key)
            aggregate_curve.append(gmfs, asset)

        return aggregate_curve

    def __init__(self, vuln_model):
        self._tses = self._time_span = self._gmfs_length = None

        self.distribution = []
        self.vuln_model = vuln_model

    def append(self, gmfs, asset):
        """Add the losses distribution identified by the given GMFs
        and asset to the set used to compute the aggregate curve."""

        if self.empty:
            self._initialize_parameters(gmfs)

        assert gmfs["TimeSpan"] is self._time_span
        assert gmfs["TSES"] is self._tses
        assert len(gmfs["IMLs"]) is self._gmfs_length

        loss_ratios = _compute_loss_ratios(self.vuln_model[
                asset["VulnerabilityFunction"]], gmfs, None, None)

        self.distribution.append(loss_ratios * asset["AssetValue"])

    def _initialize_parameters(self, gmfs):
        """Initialize the GMFs parameters."""
        self._tses = gmfs["TSES"]
        self._time_span = gmfs["TimeSpan"]
        self._gmfs_length = len(gmfs["IMLs"])

    @property
    def empty(self):
        """Return true is this aggregate curve has no losses
        associated, false otherwise."""
        return len(self.distribution) == 0

    @property
    def losses(self):
        """Return the losses used to compute the aggregate curve."""
        if self.empty:
            return array([])
        else: # if needed because numpy returns a scalar if the list is empty
            return array(self.distribution).sum(axis=0)

    def compute(self, number_of_samples=DEFAULT_NUMBER_OF_SAMPLES):
        """Compute the aggregate loss curve."""

        if self.empty:
            return shapes.EMPTY_CURVE

        losses = self.losses
        loss_range = _compute_loss_ratios_range(losses, number_of_samples)

        probs_of_exceedance = _compute_probs_of_exceedance(
                _compute_rates_of_exceedance(_compute_cumulative_histogram(
                losses, loss_range), self._tses), self._time_span)

        return _generate_curve(loss_range, probs_of_exceedance)
