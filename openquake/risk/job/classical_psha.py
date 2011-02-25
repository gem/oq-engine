# pylint: disable=W0232
""" Mixin for Classical PSHA Risk Calculation """

import json
from openquake import job
#from celery.exceptions import TimeoutError
#from celery.decorators import task


from openquake.shapes import Curve
from openquake.parser import exposure
from openquake.parser import vulnerability
from openquake.risk import classical_psha_based
from openquake import kvs
from openquake import logs
from openquake.risk.job import output, RiskJobMixin
from math import exp
LOGGER = logs.LOG

def preload(fn):
    """ Preload decorator """
    def preloader(self, *args, **kwargs):
        """A decorator for preload steps that must run on the Jobber"""

        self.store_exposure_assets()
        self.store_vulnerability_model()

        return fn(self, *args, **kwargs)
    return preloader


class ClassicalPSHABasedMixin:

    # TODO: move to the RiskJobMixin
    def store_exposure_assets(self):
        """ Load exposure assets and write to kvs """
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

    # TODO: move to the RiskJobMixin
    def store_vulnerability_model(self):
        """ load vulnerability and write to kvs """
        vulnerability.load_vulnerability_model(self.id,
            "%s/%s" % (self.base_path, self.params["VULNERABILITY"]))

    @preload
    @output
    def execute(self):
        tasks = []
        results = []
        for block_id in self.blocks_keys:
            LOGGER.debug("starting task block, block_id = %s of %s"
                        % (block_id, len(self.blocks_keys)))
            # pylint: disable-msg=E1101
            #tasks.append(risk_job.compute_risk.delay(self.id,block_id))
            tasks.append(self.compute_risk(block_id))

        # task compute_risk has return value 'True' (writes its results to
        # redis).
#        for task in tasks:
#            try:
#                # TODO(chris): Figure out where to put that timeout.
#                task.wait(timeout=None)
#            except TimeoutError:
#                # TODO(jmc): Cancel and respawn this task
#                return []
        return results

    def compute_risk(self, block_id, **kwargs):  # pylint: disable=W0613
        block = job.Block.from_kvs(block_id)

        #pylint: disable=W0201
        self.vuln_curves = \
                vulnerability.load_vuln_model_from_kvs(self.job_id)

        for point in block.grid(self.region):
            curve_token = kvs.tokens.mean_hazard_curve_key(self.job_id,
                                point.site)

            decoded_curve = kvs.get_value_json_decoded(curve_token)

            curve = Curve([(exp(float(el['x'])), el['y'])for el in decoded_curve['curve']])

            LOGGER.debug('hazard_curve')
            LOGGER.debug(curve)

            asset_key = kvs.tokens.asset_key(self.id, point.row, point.column)
            asset_list = kvs.get_client().lrange(asset_key, 0, -1)
            for asset in [json.JSONDecoder().decode(x) for x in asset_list]:
                LOGGER.debug("processing asset %s" % (asset))

                vuln_function = self.vuln_curves.get(
                        asset["vulnerabilityFunctionReference"], None)
                if not vuln_function:
                    LOGGER.error("Unknown vulnerability function %s for asset %s"
                        % (asset["vulnerabilityFunctionReference"], asset["assetID"]))
                    return None
                LOGGER.debug('vuln_function')
                LOGGER.debug(vuln_function)
                loss_ratio_curve = classical_psha_based.compute_loss_ratio_curve(vuln_function,
                                                                    curve)

                LOGGER.debug('loss_ratio_curve')
                LOGGER.debug(loss_ratio_curve)

                loss_key = kvs.tokens.loss_ratio_key(self.job_id,point.row,point.column,asset['assetID'])
                kvs.set(loss_key, loss_ratio_curve.to_json())
                self._write_output_for_block(self.job_id, block_id)
        return True

#        results = []
#        tasks = []
#        for block_id in self.blocks_keys:
#            LOGGER.debug("starting task block, block_id = %s of %s"
#                        % (block_id, len(self.blocks_keys)))
#            # pylint: disable-msg=E1101
#            tasks.append(risk_job.compute_risk.delay(self.id, block_id))
#
#        # task compute_risk has return value 'True' (writes its results to
#        # memcache).
#        for task in tasks:
#            try:
#                # TODO(chris): Figure out where to put that timeout.
#                task.wait(timeout=None)
#            except TimeoutError:
#                # TODO(jmc): Cancel and respawn this task
#                return []
#        return results # TODO(jmc): Move output from being a decorator
#        return True
#    def store_hazard_curves(self):
#        """ Get the regions from the region file and store them in kvs
#        """
#
#        # load hazard curve file and write to memcache_client
#        # TODO(JMC): Replace this with GMF slicing
#        nrml_parser = hazard.NrmlFile("%s/%s" % (self.base_path,
#            self.params[job.HAZARD_CURVES]))
#        attribute_constraint = producer.AttributeConstraint({'IMT' : 'MMI'})
#        sites_hash_list = []
#
#        for site, hazard_curve_data in \
#            nrml_parser.filter(self.region_constraint, attribute_constraint):
#
#            gridpoint = self.region_constraint.grid.point_at(site)
#
#            # store site hashes in memcache
#            # TODO(fab): separate this from hazard curves. Regions of interest
#            # should not be taken from hazard curve input, should be
#            # idependent from the inputs (hazard, exposure)
#            sites_hash_list.append((str(gridpoint),
#                                   (site.longitude, site.latitude)))
#
#            hazard_curve = shapes.Curve(zip(hazard_curve_data['IML'],
#                                                hazard_curve_data['Values']))
#
#            memcache_key_hazard = kvs.generate_product_key(self.id,
#                hazard.HAZARD_CURVE_KEY_TOKEN, self.block_id, gridpoint)
#
#            LOGGER.debug("Loading hazard curve %s at %s, %s" % (
#                        hazard_curve, site.latitude,  site.longitude))
#
#            success = self.memcache_client.set(memcache_key_hazard,
#                hazard_curve.to_json())
#
#            if not success:
#                raise ValueError(
#                    "jobber: cannot write hazard curve to memcache")
#
#    def compute_risk(self, block_id, conditional_loss_poe=None, **kwargs):
#        """This task computes risk for a block of sites. It requires to have
#        pre-initialized in memcache:
#         1) list of sites
#         2) hazard curves
#         3) exposure portfolio (=assets)
#         4) vulnerability
#
#        TODO(fab): make conditional_loss_poe (set of probabilities of exceedance
#        for which the loss computation is done) a list of floats, and read it from
#        the job configuration.
#        """
#
#        if conditional_loss_poe is None:
#            conditional_loss_poe = DEFAULT_CONDITIONAL_LOSS_POE
#
#        risk_engine = engines.ClassicalPSHABasedLossRatioCalculator(job_id,
#            block_id)
#
#        # TODO(jmc): DONT assumes that hazard, assets, and output risk grid are
#        # the same (no nearest-neighbour search to find hazard)
#        block = job.Block.from_kvs(block_id)
#        sites_list = block.sites
#
#        LOGGER.debug("sites list for job_id %s, block_id %s:\n%s" % (
#            job_id, block_id, sites_list))
#
#        for (gridpoint, site) in sites_list:
#
#            logger.debug("processing gridpoint %s, site %s" % (gridpoint, site))
#            loss_ratio_curve = risk_engine.compute_loss_ratio_curve(gridpoint)
#
#            if loss_ratio_curve is not None:
#
#                # write to memcache: loss_ratio
#                key = kvs.generate_product_key(job_id,
#                    risk.LOSS_RATIO_CURVE_KEY_TOKEN, block_id, gridpoint)
#
#                logger.debug("RESULT: loss ratio curve is %s, write to key %s"
#                     % (loss_ratio_curve, key))
#                memcache_client.set(key, loss_ratio_curve)
#
#                # compute loss curve
#                loss_curve = risk_engine.compute_loss_curve(gridpoint,
#                                                            loss_ratio_curve)
#                key = kvs.generate_product_key(job_id,
#                    risk.LOSS_CURVE_KEY_TOKEN, block_id, gridpoint)
#
#                logger.debug("RESULT: loss curve is %s, write to key %s" % (
#                    loss_curve, key))
#                memcache_client.set(key, loss_curve)
#
#                # compute conditional loss
#                loss_conditional = engines.compute_loss(loss_curve,
#                                                        conditional_loss_poe)
#                key = kvs.generate_product_key(job_id,
#                    risk.loss_token(conditional_loss_poe), block_id, gridpoint)
#
#                logger.debug("RESULT: conditional loss i %s, write to key %s"
#                    % (loss_conditional, key))
#                memcache_client.set(key, loss_conditional)
#
#        # assembling final product needs to be done by jobber, collecting the
#        # results from all tasks
#        return True

RiskJobMixin.register("Classical PSHA", ClassicalPSHABasedMixin)
