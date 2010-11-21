# pylint: disable-msg=W0232

""" Probabilistic Event Mixin: 

    Defines the behaviour of a Job. Calls the compute_risk task

"""

import os

import numpy
from celery.exceptions import TimeoutError

from opengem import hazard
from opengem import job
from opengem import kvs
from opengem import logs
from opengem import producer
from opengem import risk
from opengem import settings
from opengem import shapes

from opengem.risk import engines
from opengem.output.risk import RiskXMLWriter
from opengem.parser import exposure
from opengem.parser import hazard as hazparser
from opengem.parser import vulnerability
from opengem.risk import tasks
from opengem.risk.job import output, RiskJobMixin


LOGGER = logs.LOG

DEFAULT_conditional_loss_poe = 0.01

def preload(fn):
    """ Preload decorator """
    def preloader(self, *args, **kwargs):
        """A decorator for preload steps that must run on the Jobber"""

        self.store_exposure_assets()
        self.store_vulnerability_model()

        return fn(self, *args, **kwargs)
    return preloader


class ProbabilisticEventMixin:
    """ Mixin for Probalistic Event Risk Job """

    @preload
    @output
    def execute(self):
        """ Execute a ProbabilisticLossRatio Job """

        results = []
        for block_id in self.blocks_keys:
            LOGGER.debug("starting task block, block_id = %s of %s" 
                        % (block_id, len(self.blocks_keys)))
            # pylint: disable-msg=E1101
            results.append(tasks.compute_risk.delay(self.id, block_id))

        # task compute_risk has return value 'True' (writes its results to
        # memcache).
        for task in results:
            try:
                # TODO(chris): Figure out where to put that timeout.
                task.wait(timeout=None)
            except TimeoutError:
                # TODO(jmc): Cancel and respawn this task
                return None

    def slice_gmfs(self, block_id):
        """Load and collate GMF values for all sites in this block. """
        # TODO(JMC): Confirm this works regardless of the method of haz calc.
        histories = int(self['NUMBER_OF_SEISMICITY_HISTORIES'])
        realizations = int(self['NUMBER_OF_HAZARD_CURVE_CALCULATIONS'])
        num_ses = histories * realizations
        
        block = job.Block.from_kvs(block_id)
        sites_list = [x for x in block.sites]
        gmfs = numpy.zeros((len(sites_list), num_ses))
        gmf_idx = 0
        for i in range(0, histories):
            for j in range(0, realizations):
                stochastic_set_id = "%s!%s" % (i, j)
                stochastic_set_key = kvs.generate_product_key(
                        self.id, hazard.STOCHASTIC_SET_TOKEN, stochastic_set_id)
                ses = kvs.get_value_json_decoded(stochastic_set_key)
                for event_set in ses:
                    for rupture in ses[event_set]:
                        for site_key in ses[event_set][rupture]:
                            gmf_site = ses[event_set][rupture][site_key]
                            # TODO(JMC): ACK! Naive, use latlon hash
                            site_obj = shapes.Site(gmf_site['lon'], gmf_site['lat'])
                            for (site_idx, (gridpoint, site)) in enumerate(sites_list):
                                if site == site_obj:
                                    gmfs[idx][gmf_idx] = float(gmf_site['mag'])
                        gmf_idx += 1
        for (site_idx, (gridpoint, site)) in enumerate(sites_list):
            key_gmf = kvs.generate_product_key(self.id,
                risk.GMF_KEY_TOKEN, block_id, site_idx)
            gmf_slice = gmfs[site_idx]
            timespan = self['INVESTIGATION_TIME']
            gmf = {"IMLs": gmf_slice, "TSES": num_ses * timespan, 
            "TimeSpan": timespan}
            print "Final gmf is %s" % gmf
            kvs.set_value_json_encoded(key_gmf, gmf)

    def store_exposure_assets(self):
        """ Load exposure assets and write to memcache """
        
        exposure_parser = exposure.ExposurePortfolioFile("%s/%s" % 
            (self.base_path, self.params[job.EXPOSURE]))

        for site, asset in exposure_parser.filter(self.region):
            gridpoint = self.region.grid.point_at(site)

            memcache_key_asset = kvs.generate_product_key(
                self.id, risk.EXPOSURE_KEY_TOKEN, gridpoint)

            LOGGER.debug("Loading asset %s at %s, %s" % (asset,
                site.longitude,  site.latitude))

            success = kvs.set_value_json_encoded(memcache_key_asset, asset)
            if not success:
                raise ValueError(
                    "jobber: cannot write asset to memcache")

    def store_vulnerability_model(self):
        """ load vulnerability and write to memcache """
        vulnerability.load_vulnerability_model(self.id,
            "%s/%s" % (self.base_path, self.params["VULNERABILITY"]))
    
    
    def compute_risk(self, block_id, conditional_loss_poe=None, **kwargs):
        """This task computes risk for a block of sites. It requires to have
        pre-initialized in memcache:
         1) list of sites
         2) gmfs
         3) exposure portfolio (=assets)
         4) vulnerability

        TODO(fab): make conditional_loss_poe (set of probabilities of exceedance
        for which the loss computation is done) a list of floats, and read it from
        the job configuration.
        """

        self.slice_gmfs(block_id)
        if conditional_loss_poe is None:
            conditional_loss_poe = DEFAULT_conditional_loss_poe

        # start up memcache client
        memcache_client = kvs.get_client(binary=False)

        risk_engine = engines.ProbabilisticEventBasedCalculator(
                self.id, block_id)

        # TODO(jmc): DONT assumes that hazard, assets, and output risk grid are the same
        # (no nearest-neighbour search to find hazard)
        block = job.Block.from_kvs(block_id)
        sites_list = block.sites # kvs.get_sites_from_memcache(job_id, block_id)

        LOGGER.debug("sites list for job_id %s, block_id %s:\n%s" % (
            self.id, block_id, sites_list))

        for (gridpoint, site) in sites_list:

            logger.debug("processing gridpoint %s, site %s" % (gridpoint, site))
            loss_ratio_curve = risk_engine.compute_loss_ratio_curve(gridpoint)

            if loss_ratio_curve is not None:

                # write to memcache: loss_ratio
                key = kvs.generate_product_key(self.id,
                    risk.LOSS_RATIO_CURVE_KEY_TOKEN, block_id, gridpoint)

                logger.debug("RESULT: loss ratio curve is %s, write to key %s" % (
                    loss_ratio_curve, key))
                memcache_client.set(key, loss_ratio_curve)
            
                # compute loss curve
                loss_curve = risk_engine.compute_loss_curve(gridpoint, 
                                                            loss_ratio_curve)
                key = kvs.generate_product_key(self.id, 
                    risk.LOSS_CURVE_KEY_TOKEN, block_id, gridpoint)

                logger.debug("RESULT: loss curve is %s, write to key %s" % (
                    loss_curve, key))
                memcache_client.set(key, loss_curve)
            
                # compute conditional loss
                loss_conditional = engines.compute_loss(loss_curve, 
                                                        conditional_loss_poe)
                key = kvs.generate_product_key(self.id, 
                    risk.CONDITIONAL_LOSS_KEY_TOKEN, block_id, gridpoint)

                logger.debug("RESULT: conditional loss is %s, write to key %s" % (
                    loss_conditional, key))
                memcache_client.set(key, loss_conditional)

        # assembling final product needs to be done by jobber, collecting the
        # results from all tasks
        return True


RiskJobMixin.register("Probabilistic Event", ProbabilisticEventMixin)
