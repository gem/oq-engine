# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

"""
Probabilistic Event Mixin: defines the behaviour of a Job. Calls the
compute_risk task
"""

import json

from celery.exceptions import TimeoutError
from scipy.stats import norm

from openquake import job
from openquake import kvs
from openquake import logs
from openquake import shapes

from openquake.risk import common
from openquake.risk import probabilistic_event_based
from openquake.risk import job as risk_job
from openquake.parser import exposure
from openquake.parser import vulnerability
from openquake.risk.job import output, RiskJobMixin
from openquake.risk.job import aggregate_loss_curve

LOGGER = logs.LOG

DEFAULT_CONDITIONAL_LOSS_POE = 0.01


def preload(fn):
    """ Preload decorator """

    def preloader(self, *args, **kwargs):
        """A decorator for preload steps that must run on the Jobber"""

        self.store_exposure_assets()
        self.store_vulnerability_model()

        return fn(self, *args, **kwargs)
    return preloader


class ProbabilisticEventMixin:
    # TODO (al-maisan) Consider refactoring our job system to make use of
    # dependency injection techniques as opposed to monkey patching python's
    # internal class structures. See also:
    #       https://github.com/gem/openquake/issues/56
    # pylint: disable=W0232,W0201
    """Mixin for Probalistic Event Risk Job"""

    @preload
    @output
    def execute(self):
        """ Execute a ProbabilisticLossRatio Job """

        results = []
        tasks = []
        for block_id in self.blocks_keys:
            LOGGER.debug("starting task block, block_id = %s of %s"
                        % (block_id, len(self.blocks_keys)))
            # pylint: disable-msg=E1101
            tasks.append(risk_job.compute_risk.delay(self.id, block_id))

        # task compute_risk has return value 'True' (writes its results to
        # kvs)
        for task in tasks:
            try:
                # TODO(chris): Figure out where to put that timeout.
                task.wait(timeout=None)
            except TimeoutError:
                # TODO(jmc): Cancel and respawn this task
                return []

        try:
            # this task must be executed after the slicing
            # of the gmfs has been completed
            aggregate_computation_task = \
                    aggregate_loss_curve.compute_aggregate_curve.delay(self.id)

            aggregate_computation_task.wait()
        except TimeoutError:
            return []

        return results  # TODO(jmc): Move output from being a decorator

    def slice_gmfs(self, block_id):
        """Load and collate GMF values for all sites in this block. """
        # TODO(JMC): Confirm this works regardless of the method of haz calc.
        histories = int(self['NUMBER_OF_SEISMICITY_HISTORIES'])
        realizations = int(self['NUMBER_OF_LOGIC_TREE_SAMPLES'])
        num_ses = histories * realizations

        block = job.Block.from_kvs(block_id)
        sites_list = block.sites
        gmfs = {}
        for site in sites_list:
            risk_point = self.region.grid.point_at(site)
            key = "%s!%s" % (risk_point.row, risk_point.column)
            gmfs[key] = []

        for i in range(0, histories):
            for j in range(0, realizations):
                key = kvs.generate_product_key(
                        self.id, kvs.tokens.STOCHASTIC_SET_TOKEN, "%s!%s" %
                            (i, j))
                fieldset = shapes.FieldSet.from_json(kvs.get(key),
                    self.region.grid)

                for field in fieldset:
                    for key in gmfs.keys():
                        (row, col) = key.split("!")
                        gmfs[key].append(field.get(int(row), int(col)))

        for key, gmf_slice in gmfs.items():
            (row, col) = key.split("!")
            key_gmf = kvs.tokens.gmfs_key(self.id, col, row)
            LOGGER.debug("GMF_SLICE for %s X %s : \n\t%s" % (
                    col, row, gmf_slice))
            timespan = float(self['INVESTIGATION_TIME'])
            gmf = {"IMLs": gmf_slice, "TSES": num_ses * timespan,
                    "TimeSpan": timespan}
            kvs.set_value_json_encoded(key_gmf, gmf)

    def store_exposure_assets(self):
        """ Load exposure assets and write to memcache """

        exposure_parser = exposure.ExposurePortfolioFile("%s/%s" %
            (self.base_path, self.params[job.EXPOSURE]))

        for site, asset in exposure_parser.filter(self.region):
            # TODO(JMC): This is kludgey
            asset['lat'] = site.latitude
            asset['lon'] = site.longitude
            gridpoint = self.region.grid.point_at(site)
            asset_key = kvs.tokens.asset_key(self.id, gridpoint.row,
                gridpoint.column)
            kvs.get_client().rpush(asset_key, json.JSONEncoder().encode(asset))

    def store_vulnerability_model(self):
        """ load vulnerability and write to memcache """
        vulnerability.load_vulnerability_model(self.id,
            "%s/%s" % (self.base_path, self.params["VULNERABILITY"]))

    def compute_risk(self, block_id, **kwargs): #pylint: disable=W0613
        """This task computes risk for a block of sites. It requires to have
        pre-initialized in kvs:
         1) list of sites
         2) gmfs
         3) exposure portfolio (=assets)
         4) vulnerability

        TODO(fab): make conditional_loss_poe (set of probabilities of
        exceedance for which the loss computation is done)
        a list of floats, and read it from the job configuration.
        """

        conditional_loss_poes = [float(x) for x in self.params.get(
                    'CONDITIONAL_LOSS_POE', "0.01").split()]
        self.slice_gmfs(block_id)

        #pylint: disable=W0201
        self.vuln_curves = \
                vulnerability.load_vuln_model_from_kvs(self.job_id)

        # TODO(jmc): DONT assumes that hazard and risk grid are the same
        block = job.Block.from_kvs(block_id)

        for point in block.grid(self.region):
            key = kvs.generate_product_key(self.job_id,
                kvs.tokens.GMF_KEY_TOKEN, point.column, point.row)
            gmf_slice = kvs.get_value_json_decoded(key)

            asset_key = kvs.tokens.asset_key(self.id, point.row, point.column)
            asset_list = kvs.get_client().lrange(asset_key, 0, -1)
            for asset in [json.JSONDecoder().decode(x) for x in asset_list]:
                LOGGER.debug("processing asset %s" % (asset))
                loss_ratio_curve = self.compute_loss_ratio_curve(
                        point.column, point.row, asset, gmf_slice)
                if loss_ratio_curve is not None:

                    # compute loss curve
                    loss_curve = self.compute_loss_curve(
                            point.column, point.row,
                            loss_ratio_curve, asset)

                    for loss_poe in conditional_loss_poes:
                        self.compute_conditional_loss(point.column, point.row,
                                loss_curve, asset, loss_poe)
        return True

    def compute_conditional_loss(self, col, row, loss_curve, asset, loss_poe):
        """ Compute the conditional loss for a loss curve and probability of
        exceedance """

        loss_conditional = common.compute_conditional_loss(
                loss_curve, loss_poe)

        key = kvs.tokens.loss_key(
                self.id, row, col, asset["assetID"], loss_poe)

        LOGGER.debug("RESULT: conditional loss is %s, write to key %s" % (
            loss_conditional, key))
        kvs.set(key, loss_conditional)

    def compute_loss_ratio_curve(self, col, row, asset, gmf_slice):
        """Compute the loss ratio curve for a single site."""

        # fail if the asset has an unknown vulnerability code
        vuln_function = self.vuln_curves.get(
                asset["vulnerabilityFunctionReference"], None)

        if not vuln_function:
            LOGGER.error(
                "Unknown vulnerability function %s for asset %s"
                % (asset["vulnerabilityFunctionReference"], asset["assetID"]))

            return None

        loss_ratio_curve = probabilistic_event_based.compute_loss_ratio_curve(
                vuln_function, gmf_slice, self._get_number_of_samples())

        # NOTE(JMC): Early exit if the loss ratio is all zeros
        if not False in (loss_ratio_curve.ordinates == 0.0):
            return None

        key = kvs.tokens.loss_ratio_key(self.id, row, col, asset["assetID"])
        kvs.set(key, loss_ratio_curve.to_json())

        LOGGER.warn("RESULT: loss ratio curve is %s, write to key %s" % (
                loss_ratio_curve, key))

        return loss_ratio_curve

    def _get_number_of_samples(self):
        """Return the number of samples used to compute the loss ratio
        curve specified by the PROB_NUM_OF_SAMPLES parameter.

        Return None if the parameter is not specified, or empty or
        the value can't be casted to int.
        """

        number_of_samples = None
        raw_value = getattr(self, "PROB_NUM_OF_SAMPLES", None)

        if raw_value:
            try:
                number_of_samples = int(raw_value)
            except ValueError:
                LOGGER.error("PROB_NUM_OF_SAMPLES %s can't be converted "
                             "to int, using default value..." % raw_value)

        return number_of_samples

    def compute_loss_curve(self, column, row, loss_ratio_curve, asset):
        """Compute the loss curve for a single site."""
        if asset is None:
            return None

        loss_curve = loss_ratio_curve.rescale_abscissae(asset["assetValue"])
        key = kvs.tokens.loss_curve_key(self.id, row, column, asset["assetID"])

        LOGGER.warn("RESULT: loss curve is %s, write to key %s" % (
                loss_curve, key))
        kvs.set(key, loss_curve.to_json())
        return loss_curve

    def epsilon(self, asset):
        """Sample from the standard normal distribution for the given asset.

        For uncorrelated risk calculation jobs we sample the standard normal
        distribution for each asset.
        In the opposite case ("perfectly correlated" assets) we sample for each
        building typology i.e. two assets with the same typology will "share"
        the same standard normal distribution sample.

        Two assets are considered to be of the same building typology if their
        structure category is the same. The asset's `structureCategory` is
        only needed for correlated jobs and unlikely to be available for
        uncorrelated ones.
        """
        correlation = getattr(self, "ASSET_CORRELATION", None)
        if not correlation:
            # Sample per asset
            return norm.rvs(loc=0, scale=1)
        elif correlation != "perfect":
            raise ValueError('Invalid "ASSET_CORRELATION": %s' % correlation)
        else:
            # Sample per building typology
            samples = getattr(self, "samples", None)
            if samples is None:
                # These are two references for the same dictionary.
                samples = self.samples = dict()

            category = asset.get("structureCategory")
            if category is None:
                raise ValueError(
                    "Asset %s has no structure category" % asset["assetID"])

            if category not in samples:
                samples[category] = norm.rvs(loc=0, scale=1)
            return samples[category]


RiskJobMixin.register("Probabilistic Event", ProbabilisticEventMixin)
